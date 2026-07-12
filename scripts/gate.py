"""The whole-system scorecard — one command, one JSON per flight mode.

The number the hardware-unfreeze decision will someday read
(docs/REVIEW-2026-07.md): per flight mode, the deployment gate plus the
governance layer. The QUICK layer always runs live (seconds): the
embedded-budget selftest, the artifact-lock check, the flight-mode
WM+head binding verification. The SLOW layers (the two n=100 gates)
default to INGESTING the committed gate-of-record JSONs with their
provenance, and re-fly on request:

  transit        79/100 of record: experiments/transit_gate_v2/r3_formal_n100.json
                 (promoted 2026-07-12; lineage 72/100 hybrid4_n100.json)
                 (--run-transit N re-flies eval.eval_integration --suite)
  indoor_search  91/100 of record: experiments/indoor_gate_v1/gate_results.json
                 (--run-indoor N re-flies eval.eval_indoor_gate --gate)

The safety suite (eval/safety_selftest.py — geofence, imminent veto,
vertical envelope, emergency land, budget return, log replay) flies in
the quick layer.

Run:
  python -m scripts.gate                       # quick + ingest both gates
  python -m scripts.gate --run-indoor 100      # re-fly the indoor gate (slow)
  python -m scripts.gate --selftest
"""

import argparse
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRANSIT_RECORD = os.path.join("experiments", "transit_gate_v2", "r3_formal_n100.json")
TRANSIT_SCRATCH = os.path.join(
    "experiments", "transit_gate_v2", "scorecard_transit.json"
)
INDOOR_RECORD = os.path.join("experiments", "indoor_gate_v1", "gate_results.json")

QUICK = (
    ("budget", ("eval.eval_latency_budget", "--selftest")),
    ("lock", ("scripts.fetch_champions", "--check")),
    ("bindings", ("planner.flight_mode", "--verify")),
    ("safety", ("eval.safety_selftest", "--all")),
)


def _run_module(mod, *args):
    """Run a module CLI of record; return (ok, last non-empty line)."""
    p = subprocess.run(
        [sys.executable, "-m", mod, *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    lines = [ln for ln in (p.stdout + p.stderr).splitlines() if ln.strip()]
    ok_lines = [ln for ln in lines if "OK" in ln]
    return p.returncode == 0, (
        ok_lines[-1] if ok_lines else (lines[-1] if lines else "")
    )


def quick_layer():
    out = {}
    for name, cmd in QUICK:
        ok, line = _run_module(*cmd)
        out[name] = {"ok": bool(ok), "line": line}
        print(f"  [quick] {name:9s} {'OK ' if ok else 'FAIL'} {line}", flush=True)
    out["ok"] = all(v["ok"] for v in out.values() if isinstance(v, dict))
    return out


def ingest_transit(path=TRANSIT_RECORD):
    d = json.load(open(os.path.join(ROOT, path)))
    return {
        "gate": f"{d['success_rate'] * d['n']:.0f}/{d['n']}",
        "success_rate": float(d["success_rate"]),
        "threshold": float(d["deployment_threshold"]),
        "pass": d["deployment_gate"] == "PASS",
        "n": int(d["n"]),
        "seed0": int(d["seed0"]),
        "source": path,
    }


def ingest_indoor(path=INDOOR_RECORD):
    d = json.load(open(os.path.join(ROOT, path)))
    return {
        "gate": f"{d['composite'] * 100:.0f}/100",
        "composite": float(d["composite"]),
        "collision_missions": float(d["collision_missions"]),
        "threshold": 0.80,
        "pass": bool(d["pass"]),
        "families": {k: v["composite"] for k, v in d["families"].items()},
        "source": path,
    }


def scorecard(run_transit=0, run_indoor=0, out=None):
    print("=== whole-system scorecard ===", flush=True)
    res = {"quick": quick_layer(), "modes": {}}
    if run_transit:
        ok, line = _run_module(
            "eval.eval_integration",
            "--suite",
            str(run_transit),
            "--contender",
            "hybrid",
            "--out",
            TRANSIT_SCRATCH,
        )
        res["modes"]["transit"] = (
            ingest_transit(TRANSIT_SCRATCH) if ok else {"pass": False, "error": line}
        )
    else:
        res["modes"]["transit"] = ingest_transit()
    if run_indoor:
        ok, line = _run_module(
            "eval.eval_indoor_gate",
            "--gate",
            str(run_indoor),
            "--out",
            INDOOR_RECORD.replace("gate_results", "scorecard_indoor"),
        )
        src = INDOOR_RECORD.replace("gate_results", "scorecard_indoor")
        res["modes"]["indoor_search"] = (
            ingest_indoor(src) if ok else {"pass": False, "error": line}
        )
    else:
        res["modes"]["indoor_search"] = ingest_indoor()
    for mode, m in res["modes"].items():
        print(
            f"  [{mode}] {m.get('gate', '--')} "
            f"{'PASS' if m.get('pass') else 'FAIL'} (source {m.get('source', '-')})",
            flush=True,
        )
    res["verdict"] = bool(
        res["quick"]["ok"] and all(m.get("pass") for m in res["modes"].values())
    )
    print(
        f"[scorecard] quick {'OK' if res['quick']['ok'] else 'FAIL'} · "
        f"transit {res['modes']['transit'].get('gate')} · "
        f"indoor {res['modes']['indoor_search'].get('gate')} -> "
        f"{'GREEN' if res['verdict'] else 'FAIL'}"
    )
    if out:
        with open(out, "w") as f:
            json.dump(res, f, indent=1)
        print(f"[scorecard] wrote {out}")
    return res


def selftest() -> None:
    # the committed gates-of-record parse, and their verdicts hold
    t = ingest_transit()
    assert t["pass"] and t["n"] == 100 and abs(t["success_rate"] - 0.79) < 1e-9
    assert t["gate"] == "79/100"
    # the re-fly scratch path must never shadow the record itself
    assert TRANSIT_SCRATCH != TRANSIT_RECORD
    i = ingest_indoor()
    assert i["pass"] and abs(i["composite"] - 0.91) < 1e-9
    assert i["gate"] == "91/100" and len(i["families"]) == 4
    assert i["collision_missions"] == 0.0
    # the quick layer runs the commands of record (names only — CI-safe)
    assert [n for n, _ in QUICK] == ["budget", "lock", "bindings", "safety"]
    print(
        f"GATE OK: records parse (transit {t['gate']}, indoor {i['gate']}), "
        "quick layer = budget/lock/bindings"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-transit", type=int, default=0, help="re-fly transit n")
    ap.add_argument("--run-indoor", type=int, default=0, help="re-fly indoor n")
    ap.add_argument("--out", default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    scorecard(args.run_transit, args.run_indoor, args.out)


if __name__ == "__main__":
    sys.exit(main())

"""coverage v1 — the A/B/C gate in one reproducible command.

Runs all three arms (Frontier privileged ceiling / WM-coverage policy /
grid-only ablation) on clean `single_room` AND cluttered
`n_room(3,clutter=2)`, on the SAME seeds, under `run_coverage_episode`
(plateau-terminated, beams8, speed 0.6), and checks the bars FROZEN in
experiments/coverage_v1/journal.md before training:

  A (match clean): WM clean coverage >= 0.758, collision <= 0.113,
                   return_rate >= 0.80
  B (beat clutter): WM clutter coverage >= 0.557
  C (WM necessity): WM clutter coverage >= grid-only clutter coverage + 0.05

PASS = A and B and C. Any WM read within +-0.08 of a bar prints a
BORDERLINE flag (re-run that cell as a fresh pooled block, per discipline).

Run (after Phase 2 trains finish):
  python -m eval.eval_coverage_gate --wm <wm.zip> --grid <gridonly.zip> --n 30
"""

import argparse
import json
import sys

# frozen bars (experiments/coverage_v1/journal.md)
A_COV, A_COLL, A_RET = 0.758, 0.113, 0.80
B_COV = 0.557
C_MARGIN = 0.05
MARGIN = 0.08  # borderline band -> pooled recheck


def _run(arm, room, n, seed0, wm_off, threshold=0.99):
    from eval.eval_coverage import suite

    md = 800 if room == "single" else 1500
    agg, _ = suite(
        arm, n, seed0, room=room, max_decisions=md, threshold=threshold, wm_off=wm_off
    )
    return agg


def _bar(name, ok, got, rel):
    flag = "  <BORDERLINE>" if abs(got - rel) <= MARGIN else ""
    print(f"  {name}: {'PASS' if ok else 'FAIL'} ({got:.3f} vs {rel:.3f}){flag}")
    return ok


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wm", required=True, help="WM-coverage policy zip")
    ap.add_argument("--grid", required=True, help="grid-only ablation zip")
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--seed0", type=int, default=310000)
    ap.add_argument("--out", default="experiments/coverage_v1/gate.json")
    args = ap.parse_args()

    r = {}
    for arm, tag, wm_off in (
        ("frontier", "fr", False),
        (args.wm, "wm", False),
        (args.grid, "grid", True),
    ):
        for room in ("single", "clutter"):
            r[f"{tag}_{room}"] = _run(arm, room, args.n, args.seed0, wm_off)
            a = r[f"{tag}_{room}"]
            print(
                f"[{tag}/{room}] cov {a['coverage_mean']:.3f} "
                f"return {a['return_rate']:.3f} collision {a['collision_rate']:.3f}",
                flush=True,
            )

    wm_s, wm_c, gr_c = r["wm_single"], r["wm_clutter"], r["grid_clutter"]
    print("\n=== coverage v1 A/B/C gate ===")
    print(
        f"  ceiling: Frontier clean {r['fr_single']['coverage_mean']:.3f}, "
        f"clutter {r['fr_clutter']['coverage_mean']:.3f}"
    )
    a = (
        _bar(
            "A match-clean cov",
            wm_s["coverage_mean"] >= A_COV,
            wm_s["coverage_mean"],
            A_COV,
        )
        & _bar(
            "A clean collision",
            wm_s["collision_rate"] <= A_COLL,
            wm_s["collision_rate"],
            A_COLL,
        )
        & _bar(
            "A clean return", wm_s["return_rate"] >= A_RET, wm_s["return_rate"], A_RET
        )
    )
    b = _bar(
        "B beat-clutter cov",
        wm_c["coverage_mean"] >= B_COV,
        wm_c["coverage_mean"],
        B_COV,
    )
    cbar = gr_c["coverage_mean"] + C_MARGIN
    c = _bar(
        "C WM-necessity", wm_c["coverage_mean"] >= cbar, wm_c["coverage_mean"], cbar
    )
    verdict = "PASS" if (a and b and c) else "FAIL / honest-negative"
    print(f"\n  VERDICT: {verdict}  (A={bool(a)} B={bool(b)} C={bool(c)})")
    with open(args.out, "w") as f:
        json.dump({k: v for k, v in r.items()}, f, indent=1)
    print(f"  wrote {args.out}")


if __name__ == "__main__":
    sys.exit(main())

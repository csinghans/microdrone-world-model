"""The moving-gap rendezvous, measured (integration_k6_v1 K3).

MovingGapFence drifts linearly and is AIMED with a cold-start
assumption (gap centre near the centreline at t = x_gap/cruise from
the STAGE's own origin). In a composite course every fence slides
from launch, so deep stages meet a rendezvous that is long past —
displacement grows linearly with position. This probe records the
fence and the drone at every decision inside moving_gap stages and
judges the frozen reads in experiments/integration_k6_v1/journal.md.

Run:
  python -m eval.eval_gap_phase --probe
  python -m eval.eval_gap_phase --selftest
"""

import argparse
import json
import os

import numpy as np

STAGE_LEN = 3.0
SEED0 = 140000
N = 100
K = 6
K6_RECORD = "experiments/integration_k6_v1/k6_n100.json"
OUT_JSON = "experiments/integration_k6_v1/k3_rendezvous.json"
OUT_NPZ = "experiments/integration_k6_v1/k3_rendezvous_rows.npz"

# frozen in the journal before any number
PREMISE_RATIO = 2.0  # deep/early mean |gap-centre y| at crossing
LINK_RATIO = 1.5  # broke/cleared mean |gap offset|
CORRIDOR_HALF = 1.0  # open-bypass audit: fence must cover +-this


def _gap_center(ys):
    """The weave-gate rule: widest spacing midpoint (valid at any slide)."""
    ys = sorted(ys)
    if len(ys) < 2:
        return 0.0
    spacing, mid = max((b - a, (a + b) / 2.0) for a, b in zip(ys, ys[1:]))
    del spacing
    return float(mid)


class GapPhaseProbe:
    """Read-only: inside moving_gap stages, record drone + fence state
    at every decision."""

    def __init__(self):
        self.rows: list = []

    def begin_course(self, seed: int, names) -> None:
        self.seed, self.names = int(seed), tuple(names)

    def __call__(self, t, frame, state, a, scenario) -> None:
        del frame, a
        x = float(state[0])
        k = int(np.clip(x // STAGE_LEN, 0, len(self.names) - 1))
        if self.names[k] != "moving_gap":
            return
        lo, hi = k * STAGE_LEN - 0.2, (k + 1) * STAGE_LEN + 0.2
        pil = [(float(p[0]), float(p[1])) for p in scenario.positions()]
        stage = [p for p in pil if lo <= p[0] < hi]
        if not stage:
            return
        plane = float(np.median([p[0] for p in stage]))
        ys = [p[1] for p in stage]
        self.rows.append(
            {
                "seed": self.seed,
                "pos": k,
                "t": int(t),
                "x": x,
                "y": float(state[1]),
                "plane_x": plane,
                "gap_y": _gap_center(ys),
                "fence_lo": float(min(ys)),
                "fence_hi": float(max(ys)),
            }
        )


def _instances(rows, outcomes):
    """Group rows per (seed, pos); attach the crossing-or-break tick's
    fence state and the instance outcome."""
    by_seed = {o["seed"]: o for o in outcomes}
    inst: dict = {}
    for r in rows:
        inst.setdefault((r["seed"], r["pos"]), []).append(r)
    out = []
    for (seed, pos), rs in sorted(inst.items()):
        rs.sort(key=lambda r: r["t"])
        o = by_seed[seed]
        stop = int(o.get("stage_break_at", K))
        crossed = [r for r in rs if r["x"] >= r["plane_x"]]
        at = crossed[0] if crossed else rs[-1]
        broke = (not o["success"]) and stop == pos
        # phantom guard: rows past an EARLIER break are dead flight
        if (not o["success"]) and pos > stop:
            continue
        out.append(
            {
                "seed": seed,
                "pos": pos,
                "broke": broke,
                "gap_abs": abs(at["gap_y"]),
                "gap_rel": abs(at["gap_y"] - at["y"]),
                "bypass": at["fence_lo"] > -CORRIDOR_HALF
                or at["fence_hi"] < CORRIDOR_HALF,
                "t_at": at["t"],
            }
        )
    return out


def _verdict(insts):
    early = [i for i in insts if i["pos"] in (1, 2)]
    deep = [i for i in insts if i["pos"] >= 3]

    def mean(xs, key):
        return float(np.mean([x[key] for x in xs])) if xs else 0.0

    premise_ratio = mean(deep, "gap_abs") / max(mean(early, "gap_abs"), 1e-9)
    premise = "CONFIRMED" if premise_ratio >= PREMISE_RATIO - 1e-9 else "REFUTED"

    seam = [i for i in insts if i["pos"] >= 1]
    broke = [i for i in seam if i["broke"]]
    clear = [i for i in seam if not i["broke"]]
    link_ratio = mean(broke, "gap_rel") / max(mean(clear, "gap_rel"), 1e-9)
    linked = bool(link_ratio >= LINK_RATIO - 1e-9)

    med = float(np.median([i["gap_rel"] for i in seam])) if seam else 0.0
    hi = [i for i in seam if i["gap_rel"] >= med]
    lo = [i for i in seam if i["gap_rel"] < med]
    split = {
        "fail_wide": mean(hi, "broke"),
        "fail_narrow": mean(lo, "broke"),
    }
    return {
        "premise": {
            "early_mean_gap_abs": mean(early, "gap_abs"),
            "deep_mean_gap_abs": mean(deep, "gap_abs"),
            "ratio": float(premise_ratio),
            "verdict": premise,
            "by_pos": {
                p: mean([i for i in insts if i["pos"] == p], "gap_abs")
                for p in range(K)
            },
        },
        "death_link": {
            "broke_mean_gap_rel": mean(broke, "gap_rel"),
            "cleared_mean_gap_rel": mean(clear, "gap_rel"),
            "ratio": float(link_ratio),
            "linked": linked,
            "median_split": split,
            "n_broke": len(broke),
            "n_cleared": len(clear),
        },
        "bypass": {
            "deep_bypass_frac": mean(deep, "bypass"),
            "early_bypass_frac": mean(early, "bypass"),
        },
    }


def probe_run(n=N, seed0=SEED0, out=OUT_JSON):
    import torch  # noqa: F401

    from eval.eval_integration import (
        HYBRID,
        PerStageExperts,
        _load_all_skills,
        run_composite_episode,
    )
    from sim.composite import (
        course_for_seed,
        integration_metrics,
        integration_success,
        register_course,
    )
    from sim.envs import make_env

    _load_all_skills()
    gp = GapPhaseProbe()
    env = make_env()
    outcomes = []
    for i in range(n):
        seed = seed0 + i
        names = course_for_seed(seed, k=K)
        world = register_course(seed, k=K)
        gp.begin_course(seed, names)
        ep = run_composite_episode(
            env,
            PerStageExperts(names, 1.0, experts=dict(HYBRID)),
            seed,
            world,
            k=K,
            probe=gp,
        )
        m = integration_metrics(ep)
        outcomes.append(
            {
                "seed": seed,
                "success": bool(integration_success(ep)),
                "stage_break_at": int(m.get("stage_break_at", -1)),
            }
        )
        print(f"  [{i + 1}/{n}] seed={seed} rows={len(gp.rows)}", flush=True)
    env.close()

    with open(K6_RECORD) as f:
        rec = {r["seed"]: r["success"] for r in json.load(f)["records"]}
    match = float(np.mean([o["success"] == rec[o["seed"]] for o in outcomes]))

    insts = _instances(gp.rows, outcomes)
    res = _verdict(insts)
    res["instrument"] = {"outcome_match": match, "n_instances": len(insts)}
    p, d = res["premise"], res["death_link"]
    print(
        f"[rendezvous] instrument {match:.3f} | premise: early "
        f"{p['early_mean_gap_abs']:.2f} -> deep {p['deep_mean_gap_abs']:.2f} m "
        f"(x{p['ratio']:.1f}, bar {PREMISE_RATIO}) -> {p['verdict']}"
    )
    print(
        f"[rendezvous] death link: broke {d['broke_mean_gap_rel']:.2f} vs "
        f"cleared {d['cleared_mean_gap_rel']:.2f} m (x{d['ratio']:.2f}, bar "
        f"{LINK_RATIO}) -> {'LINKED' if d['linked'] else 'not linked'} "
        f"({d['n_broke']} broke / {d['n_cleared']} cleared)"
    )
    print(f"[rendezvous] bypass: deep {res['bypass']['deep_bypass_frac']:.2f}")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(res, f, indent=1)
    np.savez_compressed(
        OUT_NPZ, **{k: np.asarray([r[k] for r in gp.rows]) for k in gp.rows[0]}
    )
    print(f"[rendezvous] wrote {out} + rows npz")
    return res


def selftest() -> None:
    # gap-centre rule: widest spacing midpoint, at any slide
    assert abs(_gap_center([-2.0, -1.0, 0.5, 1.5]) - (-0.25)) < 1e-9
    assert abs(_gap_center([3.0, 4.5, 5.0]) - 3.75) < 1e-9

    # instance assembly: crossing tick chosen, phantom rows dropped
    rows = [
        {
            "seed": 1,
            "pos": 1,
            "t": 10,
            "x": 3.5,
            "y": 0.0,
            "plane_x": 4.8,
            "gap_y": 0.2,
            "fence_lo": -3,
            "fence_hi": 3,
        },
        {
            "seed": 1,
            "pos": 1,
            "t": 20,
            "x": 4.9,
            "y": 0.1,
            "plane_x": 4.8,
            "gap_y": 0.9,
            "fence_lo": -3,
            "fence_hi": 3,
        },
        {
            "seed": 2,
            "pos": 4,
            "t": 10,
            "x": 13.0,
            "y": 0.0,
            "plane_x": 13.8,
            "gap_y": 2.0,
            "fence_lo": 0.5,
            "fence_hi": 6.5,
        },
    ]
    outs = [
        {"seed": 1, "success": True, "stage_break_at": 6},
        {"seed": 2, "success": False, "stage_break_at": 4},
    ]
    insts = _instances(rows, outs)
    assert len(insts) == 2
    a, b = insts
    assert a["gap_abs"] == 0.9 and not a["broke"]  # crossing tick, not entry
    assert b["broke"] and b["bypass"]  # slid fence exposes the corridor edge

    # verdict arithmetic: deep displacement + linked deaths
    fake = []
    for p in (1, 2):
        fake += [
            {
                "pos": p,
                "broke": False,
                "gap_abs": 0.5,
                "gap_rel": 0.4,
                "bypass": False,
                "seed": 0,
                "t_at": 0,
            }
        ] * 10
    for p in (3, 4, 5):
        fake += [
            {
                "pos": p,
                "broke": i < 3,
                "gap_abs": 2.0,
                "gap_rel": 1.5 if i < 3 else 0.5,
                "bypass": False,
                "seed": 0,
                "t_at": 0,
            }
            for i in range(10)
        ]
    v = _verdict(fake)
    assert v["premise"]["verdict"] == "CONFIRMED" and v["premise"]["ratio"] >= 2
    assert v["death_link"]["linked"]

    assert (PREMISE_RATIO, LINK_RATIO, CORRIDOR_HALF) == (2.0, 1.5, 1.0)
    print(
        "GAP-PHASE OK: gap-centre rule, crossing-tick assembly, phantom "
        "guard, bypass audit, verdict arithmetic, frozen thresholds"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--n", type=int, default=N)
    ap.add_argument("--out", default=OUT_JSON)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    if args.probe:
        probe_run(args.n, out=args.out)
        return
    ap.print_help()


if __name__ == "__main__":
    main()

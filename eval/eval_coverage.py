"""Complete-coverage gate suite — the WM-coverage campaign's grader.

Runs an arm (a geometric strategy now; a trained WM-coverage policy in
Phase 2) over N rooms under `run_coverage_episode` (roam until covered
fraction >= threshold, then BFS home) and aggregates the coverage
scorecard. Phase 0 uses this to measure the geometric Frontier CEILING on
a clean room and a cluttered room, and to freeze the gate bars before any
training (experiments/coverage_v1/journal.md).

Arms compared at the gate (all same seeds / mission / safety=beams8 /
speed 0.6): Frontier (privileged geometric ceiling) vs the WM-coverage
policy vs a grid-only ablation. Metric of record: `coverage_mean`.

Run:
  python -m eval.eval_coverage --arm frontier --room single --n 20
  python -m eval.eval_coverage --arm frontier --room clutter --n 20
  python -m eval.eval_coverage --selftest
"""

import argparse
import json
import sys

import numpy as np


def make_room(room, seed, clutter=2):
    """clean = single_room (the standard 5x5, 2 boxes); clutter =
    3-room line with `clutter` boxes/room and NO clear lane (the setting
    where the geometric Frontier's safe-cell graph fragments — the
    coverage win condition)."""
    from sim.indoor.rooms import n_room, single_room

    if room == "single":
        return single_room(seed)
    if room == "clutter":
        return n_room(seed, n_rooms=3, clutter=clutter, clutter_lane=0.0)
    raise ValueError(f"unknown room {room!r}")


def suite(
    arm,
    n,
    seed0=300000,
    room="single",
    clutter=2,
    max_decisions=800,
    speed=0.6,
    safety="beams8",
    threshold=0.90,
    wm_off=False,
):
    from eval.search_episode import run_coverage_episode
    from search.strategies import STRATEGIES, get_strategy
    from sim.envs import make_env

    env = make_env()
    rows = []
    pol_cache = None
    for i in range(n):
        sc = make_room(room, seed0 + i, clutter)
        if arm in STRATEGIES:
            pol = get_strategy(arm)  # Phase 0: geometric baselines/ceiling
        else:  # a trained policy zip (Phase 2+); load once, reuse
            from search.coverage_policy import CoveragePolicy

            if pol_cache is None:
                pol_cache = CoveragePolicy(arm, speed=speed, wm_off=wm_off)
            pol = pol_cache
        m = run_coverage_episode(
            env,
            sc,
            pol,
            seed=seed0 + i,
            max_decisions=max_decisions,
            speed=speed,
            safety=safety,
            coverage_threshold=threshold,
        )
        m.pop("path", None)
        rows.append(m)
        print(
            f"  {arm}/{room} seed {seed0 + i}: cov {m['coverage']:.2f} "
            f"complete={int(m['coverage_complete'])} return={int(m['returned'])} "
            f"crash={int(m['crashed'])} steps_to_cover={m['steps_to_cover']}",
            flush=True,
        )
    env.close()
    done = [r for r in rows if r["coverage_complete"]]
    agg = {
        "arm": arm,
        "room": room,
        "n": n,
        "threshold": threshold,
        "coverage_mean": float(np.mean([r["coverage"] for r in rows])),
        "coverage_complete_rate": float(
            np.mean([r["coverage_complete"] for r in rows])
        ),
        # return_rate is conditional on completing coverage (its own leg)
        "return_rate": float(np.mean([r["returned"] for r in done])) if done else 0.0,
        "steps_to_cover_median": (
            float(np.median([r["steps_to_cover"] for r in done])) if done else -1.0
        ),
        "collision_rate": float(np.mean([r["crashed"] for r in rows])),
    }
    return agg, rows


def selftest() -> None:
    # sim group: Frontier runs one coverage mission end to end (low
    # threshold so the return leg fires), aggregate schema present
    agg, rows = suite("frontier", n=1, room="single", max_decisions=40, threshold=0.3)
    assert set(agg) >= {"coverage_mean", "coverage_complete_rate", "collision_rate"}
    assert 0.0 <= agg["coverage_mean"] <= 1.0 and len(rows) == 1
    print(
        f"EVAL-COVERAGE OK: suite aggregates (cov {agg['coverage_mean']:.2f}, "
        f"complete {agg['coverage_complete_rate']:.2f})"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", default="frontier", help="strategy name or policy zip")
    ap.add_argument("--room", default="single", choices=("single", "clutter"))
    ap.add_argument("--clutter", type=int, default=2, help="boxes/room (clutter room)")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--seed0", type=int, default=300000)
    ap.add_argument("--max-decisions", type=int, default=800)
    ap.add_argument("--speed", type=float, default=0.6)
    ap.add_argument("--safety", default="beams8")
    ap.add_argument("--threshold", type=float, default=0.90)
    ap.add_argument("--wm-off", action="store_true", help="grid-only ablation policy")
    ap.add_argument("--out", default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    agg, rows = suite(
        args.arm,
        args.n,
        args.seed0,
        args.room,
        args.clutter,
        args.max_decisions,
        args.speed,
        args.safety,
        args.threshold,
        args.wm_off,
    )
    print(
        f"\n[coverage] {agg['arm']}/{agg['room']} n={agg['n']} thr={agg['threshold']}"
        f"\n  coverage {agg['coverage_mean']:.3f} | "
        f"complete {agg['coverage_complete_rate']:.3f} | "
        f"return|done {agg['return_rate']:.3f} | "
        f"collision {agg['collision_rate']:.3f} | "
        f"steps_to_cover(med) {agg['steps_to_cover_median']:.0f}"
    )
    if args.out:
        with open(args.out, "w") as f:
            json.dump({"agg": agg, "rows": rows}, f, indent=1)
        print(f"[coverage] wrote {args.out}")


if __name__ == "__main__":
    sys.exit(main())

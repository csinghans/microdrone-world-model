"""The search suite runner — aggregate a strategy over N single rooms.

Serves two roles in Phase 1a: the feasibility CEILING probe (run the
privileged Frontier strategy — it reads ground-truth free cells — to
confirm the room is coverable / the beacon findable / home reachable
within the decision budget, BEFORE any bar is frozen) and the
three-strategy BASELINE comparison (random / wall_follow / frontier on
the same seeds). All flights use the real 48 Hz env and the privileged
geometric safety filter (Phase 1a isolates search strategy from
perception; the world model enters in Phase 1b).

Run:
  python -m eval.eval_search --strategy frontier --n 20 --max-decisions 600
  python -m eval.eval_search --selftest
"""

import argparse
import json
import sys

import numpy as np


def suite(
    strategy,
    n,
    seed0=90000,
    max_decisions=600,
    n_obstacles=2,
    los=False,
    speed=1.0,
    safety="geometric",
    room="single",
):
    from eval.search_episode import run_search_episode
    from search.strategies import get_strategy
    from sim.envs import make_env
    from sim.indoor.rooms import single_room, two_room

    env = make_env()
    rows = []
    for i in range(n):
        if room == "two":
            sc = two_room(seed0 + i, los=los)
        else:
            sc = single_room(seed0 + i, n_obstacles=n_obstacles, los=los)
        m = run_search_episode(
            env,
            sc,
            get_strategy(strategy),
            seed=seed0 + i,
            max_decisions=max_decisions,
            speed=speed,
            safety=safety,
        )
        m.pop("path", None)  # drop the array for the aggregate record
        rows.append(m)
        print(
            f"  {strategy} seed {seed0 + i}: found={int(m['target_found'])} "
            f"success={int(m['success'])} cov={m['coverage']:.2f} "
            f"steps_to_find={m['steps_to_find']} crash={int(m['crashed'])}",
            flush=True,
        )
    env.close()
    found = [r for r in rows if r["target_found"]]
    agg = {
        "strategy": strategy,
        "n": n,
        "seed0": seed0,
        "max_decisions": max_decisions,
        "find_rate": float(np.mean([r["target_found"] for r in rows])),
        # return_rate is conditional on having found (the return leg's own rate)
        "return_rate": float(np.mean([r["returned"] for r in found])) if found else 0.0,
        "success_rate": float(np.mean([r["success"] for r in rows])),
        "coverage_mean": float(np.mean([r["coverage"] for r in rows])),
        "collision_rate": float(np.mean([r["crashed"] for r in rows])),
        "steps_to_find_median": (
            float(np.median([r["steps_to_find"] for r in found])) if found else -1.0
        ),
    }
    return agg, rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategy", default="frontier")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--seed0", type=int, default=90000)
    ap.add_argument("--max-decisions", type=int, default=600)
    ap.add_argument("--n-obstacles", type=int, default=2)
    ap.add_argument("--los", action="store_true")
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument(
        "--safety",
        default="geometric",
        choices=("geometric", "rangefinder", "beams4", "beams8", "beams16"),
    )
    ap.add_argument("--room", default="single", choices=("single", "two"))
    ap.add_argument("--out", default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        agg, rows = suite("frontier", n=1, max_decisions=8)
        assert set(agg) >= {
            "find_rate",
            "success_rate",
            "coverage_mean",
            "collision_rate",
        }
        assert 0.0 <= agg["coverage_mean"] <= 1.0 and len(rows) == 1
        print("EVAL-SEARCH OK: suite aggregates find/success/coverage/collision")
        return

    agg, rows = suite(
        args.strategy,
        args.n,
        args.seed0,
        args.max_decisions,
        args.n_obstacles,
        args.los,
        args.speed,
        args.safety,
        args.room,
    )
    print(
        f"[{agg['strategy']}] n={agg['n']}  find {agg['find_rate']:.3f}  "
        f"success {agg['success_rate']:.3f}  return|found {agg['return_rate']:.3f}  "
        f"coverage {agg['coverage_mean']:.3f}  collision {agg['collision_rate']:.3f}  "
        f"steps_to_find(med) {agg['steps_to_find_median']:.0f}"
    )
    if args.out:
        with open(args.out, "w") as f:
            json.dump({"agg": agg, "rows": rows}, f, indent=1)
        print(f"[eval-search] wrote {args.out}")


if __name__ == "__main__":
    sys.exit(main())

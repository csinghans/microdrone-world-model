"""Top-down trajectory portrait of a passing search mission — the
Phase-1a "god view" the plan asks to eyeball (coverage sweep + beacon
find + return home). Regenerable from a seed; no stored data.

Run:
  python -m eval.eval_search_gallery --seed 120000 --out docs/figures
  python -m eval.eval_search_gallery --selftest
"""

import argparse
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

GREEN, BLUE, RED, GREY = "#2e7d32", "#1565c0", "#c62828", "#9e9e9e"


def render(scenario, result, found_step, out_path):
    """Draw room walls, obstacles, beacon, start, and the flown path
    (search leg blue, return leg green)."""
    x0, x1, y0, y1 = scenario.bounds
    fig, ax = plt.subplots(figsize=(5.2, 5.2))
    ax.add_patch(
        plt.Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, lw=2, ec="black")
    )
    for ox, oy, r in scenario.obstacles:
        ax.add_patch(plt.Circle((ox, oy), r, color=GREY, alpha=0.7, zorder=2))
    # sensor-range ring around the beacon (what "found from afar" means)
    bx, by = scenario.beacon_xy
    ax.add_patch(
        plt.Circle((bx, by), scenario.sensor_range, color=RED, alpha=0.08, zorder=1)
    )
    ax.plot(bx, by, marker="*", ms=20, color=RED, zorder=5, label="beacon")
    sx, sy = scenario.start_xy
    ax.plot(sx, sy, marker="s", ms=11, color="black", zorder=5, label="start/home")

    path = np.asarray(result["path"])
    k = found_step + 1 if found_step >= 0 else len(path)
    ax.plot(path[:k, 0], path[:k, 1], "-", color=BLUE, lw=1.4, zorder=3, label="search")
    if found_step >= 0:
        ax.plot(
            path[k - 1 :, 0],
            path[k - 1 :, 1],
            "-",
            color=GREEN,
            lw=1.4,
            zorder=3,
            label="return",
        )
    ax.set_xlim(x0 - 0.3, x1 + 0.3)
    ax.set_ylim(y0 - 0.3, y1 + 0.3)
    ax.set_aspect("equal")
    ax.set_title(
        f"Indoor search — frontier, seed {scenario.meta.get('seed')}\n"
        f"found @ decision {found_step}, coverage {result['coverage']:.2f}, "
        f"{'returned' if result['returned'] else 'no return'}, "
        f"{result['collisions']} collisions",
        fontsize=9,
    )
    ax.legend(fontsize=7, loc="upper left")
    fig.tight_layout()
    fig.savefig(out_path, dpi=110)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=120000)
    ap.add_argument("--speed", type=float, default=0.6)
    ap.add_argument("--max-decisions", type=int, default=2400)
    ap.add_argument("--out", default="docs/figures")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        # env-free: render a synthetic passing path, check the file writes
        from sim.indoor.rooms import single_room

        sc = single_room(120000)
        p = np.array([sc.start_xy, (0.0, 0.0), sc.beacon_xy, (0.0, 0.0), sc.start_xy])
        res = {"path": p, "coverage": 0.8, "returned": True, "collisions": 0}
        out = os.path.join("/tmp", "search_traj_selftest.png")
        render(sc, res, found_step=2, out_path=out)
        assert os.path.getsize(out) > 10_000, "figure wrote"
        print("SEARCH-GALLERY OK: trajectory portrait renders (search+return legs)")
        return

    from eval.search_episode import run_search_episode
    from search.strategies import get_strategy
    from sim.envs import make_env
    from sim.indoor.rooms import single_room

    env, sc = make_env(), single_room(args.seed)
    res = run_search_episode(
        env,
        sc,
        get_strategy("frontier"),
        seed=args.seed,
        max_decisions=args.max_decisions,
        speed=args.speed,
    )
    env.close()
    # recover found_step from the metrics (steps_to_find), fall back to end
    fs = res["steps_to_find"] if res["target_found"] else -1
    os.makedirs(args.out, exist_ok=True)
    out = os.path.join(args.out, "search_room_trajectory.png")
    render(sc, res, fs, out)
    print(
        f"[search-gallery] seed {args.seed}: found@{fs} coverage {res['coverage']:.2f} "
        f"returned {res['returned']} collisions {res['collisions']} -> {out}"
    )


if __name__ == "__main__":
    sys.exit(main())

"""Gate — does the drone report the right room graph ("beacon in room k of N")?

Runs deployable search flights (frontier + beams8, speed 0.6) on N-room
lines, then `track_rooms` post-processes each path into (n_detected,
beacon_room) and compares to ground truth. Pre-registered bars
(experiments/search_roomgraph_v1/journal.md): beacon-room accuracy and
room-count accuracy both >= 0.85 on found episodes, pooled over 3- and
4-room.

Run:
  python -m eval.eval_room_graph --n 30
  python -m eval.eval_room_graph --selftest
"""

import argparse
import sys


def gate(n=30, seed0=230000, n_rooms_list=(3, 4), speed=0.6, clutter=0):
    from eval.search_episode import run_search_episode
    from search.room_graph import track_rooms
    from search.strategies import get_strategy
    from sim.envs import make_env
    from sim.indoor.rooms import ROOM_W, n_room

    env = make_env()
    beacon_ok, count_ok, found = 0, 0, 0
    rows = []
    for nr in n_rooms_list:
        for i in range(n):
            sc = n_room(seed0 + i, n_rooms=nr, clutter=clutter)
            m = run_search_episode(
                env,
                sc,
                get_strategy("frontier"),
                seed=seed0 + i,
                max_decisions=1000 * nr,
                speed=speed,
                safety="beams8",
            )
            if not m["target_found"]:
                continue
            found += 1
            fs = m["steps_to_find"]
            g = track_rooms(sc, m["path"], found_step=fs)
            x0 = sc.bounds[0]
            true_room = int((sc.beacon_xy[0] - x0) / ROOM_W)
            b_ok = g["beacon_room"] == true_room
            n_ok = g["n_detected"] == nr
            beacon_ok += b_ok
            count_ok += n_ok
            rows.append(
                (nr, seed0 + i, true_room, g["beacon_room"], nr, g["n_detected"])
            )
            print(
                f"  {nr}-room seed {seed0 + i}: beacon room "
                f"{g['beacon_room']} (true {true_room}) {'OK' if b_ok else 'MISS'}, "
                f"N {g['n_detected']} (true {nr}) {'OK' if n_ok else 'MISS'}",
                flush=True,
            )
    env.close()
    return {
        "found": found,
        "beacon_room_acc": beacon_ok / found if found else 0.0,
        "count_acc": count_ok / found if found else 0.0,
        "rows": rows,
    }


def selftest() -> None:
    # the ground-truth room formula and track_rooms agree on a synthetic
    # straight march (env-free) — the sim gate is exercised in CI's sim group
    import numpy as np

    from search.room_graph import track_rooms
    from sim.indoor.rooms import ROOM_W, n_room

    sc = n_room(5, n_rooms=4)
    x0 = sc.bounds[0]
    path = [(x, 0.0) for x in np.arange(x0 + 0.6, sc.bounds[1] - 0.6, 0.1)]
    g = track_rooms(sc, path, found_step=len(path) - 1)
    assert g["n_detected"] == 4, g
    assert g["beacon_room"] == int((sc.beacon_xy[0] - x0) / ROOM_W) == 3
    print(
        "EVAL-ROOM-GRAPH OK: track_rooms matches ground-truth room index (4-room march)"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--seed0", type=int, default=230000)
    ap.add_argument("--speed", type=float, default=0.6)
    ap.add_argument("--clutter", type=int, default=0, help="box obstacles per room")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    r = gate(args.n, args.seed0, speed=args.speed, clutter=args.clutter)
    b, c = r["beacon_room_acc"], r["count_acc"]
    print(
        f"\n[room-graph] clutter={args.clutter} found {r['found']} episodes | "
        f"beacon-room acc {b:.3f} {'PASS' if b >= 0.85 else 'FAIL'} (bar 0.85) | "
        f"room-count acc {c:.3f} {'PASS' if c >= 0.85 else 'FAIL'} (bar 0.85)"
    )


if __name__ == "__main__":
    sys.exit(main())

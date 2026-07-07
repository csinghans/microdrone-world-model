"""N-room diagnostic — WHY does threading multiple doorways crash?

search_nroom_v1 found the flat-grid Frontier finds through N doorways
(find 1.0) but crashes at them, rising with doorway count even at the
geometric ceiling (3-room 0.10 -> 4-room 0.30). Before building a
doorway-aware traversal, pin the mechanism with the on_collision
forensics hook (same one that settled search_hybrid_v1).

For each first-contact clip we ask two geometric questions:
  * Is it AT a doorway? (distance from the nearest divider plane, the
    only obstacles in an n_room besides the outer walls)
  * If so, how OFF-CENTRE was the drone? The doorway's clear opening is
    |y| < DOOR_HALF (0.9); the flanking bricks' surfaces start at
    |y| = 0.9. A clip at |y| ~ 0.9 is an edge clip on an off-centre
    approach; a clip at |y| ~ 0 would mean the gap itself is too tight.

If the clips are doorway edge clips on off-centre approaches, the fix is
"centre up on the doorway before threading" — a doorway-aware traversal,
not a wider gap.

Run:
  python -m eval.diagnose_nroom_doorway --n 40 --n-rooms 4
  python -m eval.diagnose_nroom_doorway --selftest
"""

import argparse
import sys

import numpy as np

from planner.nav_action_set import NAV_ACTION_NAMES
from sim.indoor.rooms import DOOR_HALF

NEAR_DIVIDER = 0.5  # a clip within this of a divider plane is "at a doorway"


def _divider_xs(scenario):
    """The x of each dividing wall (all n_room obstacles are divider bricks)."""
    return sorted({round(float(ox), 3) for ox, _, _ in scenario.obstacles})


def diagnose(n_rooms=4, n=40, seed0=210000, max_decisions=4000, speed=0.6):
    from eval.search_episode import run_search_episode
    from search.strategies import get_strategy
    from sim.envs import make_env
    from sim.indoor.rooms import n_room

    env = make_env()
    clips, n_crashed = [], 0
    for i in range(n):
        sc = n_room(seed0 + i, n_rooms=n_rooms)
        dxs = _divider_xs(sc)
        ep = []
        m = run_search_episode(
            env,
            sc,
            get_strategy("frontier"),
            seed=seed0 + i,
            max_decisions=max_decisions,
            speed=speed,
            safety="geometric",
            on_collision=ep.append,
        )
        if m["crashed"]:
            n_crashed += 1
        if ep:
            c = ep[0]  # first contact = the failure event
            x, y = c["rpos"]
            c["d2div"] = min(abs(x - dx) for dx in dxs)
            c["yoff"] = abs(y)
            c["at_doorway"] = c["d2div"] < NEAR_DIVIDER
            c["seed"] = seed0 + i
            clips.append(c)
            print(
                f"  CLIP seed {seed0 + i} phase={c['phase']} "
                f"exec={NAV_ACTION_NAMES[c['executed']]} "
                f"d2div={c['d2div']:.2f} yoff={c['yoff']:.2f} "
                f"{'DOORWAY' if c['at_doorway'] else 'elsewhere'}",
                flush=True,
            )
    env.close()
    return clips, n_crashed


def _summary(clips):
    door = [c for c in clips if c["at_doorway"]]
    off_centre = [c for c in door if c["yoff"] > DOOR_HALF - 0.25]
    return door, off_centre


def selftest() -> None:
    # classifier: a clip near a divider plane with |y| ~ DOOR_HALF is an
    # off-centre doorway edge clip; one far from any divider is elsewhere
    clips = [
        {"at_doorway": True, "yoff": DOOR_HALF},  # edge clip, off-centre
        {"at_doorway": True, "yoff": 0.1},  # at doorway but centred
        {"at_doorway": False, "yoff": 0.1},  # elsewhere
    ]
    door, off_centre = _summary(clips)
    assert len(door) == 2 and len(off_centre) == 1
    print("DIAGNOSE-NROOM OK: doorway / off-centre-edge classifier")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--n-rooms", type=int, default=4)
    ap.add_argument("--seed0", type=int, default=210000)
    ap.add_argument("--max-decisions", type=int, default=4000)
    ap.add_argument("--speed", type=float, default=0.6)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return

    clips, n_crashed = diagnose(
        args.n_rooms, args.n, args.seed0, args.max_decisions, args.speed
    )
    door, off_centre = _summary(clips)
    print(
        f"\n[diagnose-nroom] {args.n} episodes ({args.n_rooms}-room), "
        f"{n_crashed} crashed; {len(clips)} failure events"
    )
    if clips:
        print(
            f"  AT a doorway (< {NEAR_DIVIDER} m from a divider): "
            f"{len(door)}/{len(clips)}"
        )
        print(
            f"  of those, OFF-CENTRE edge clips (|y| > {DOOR_HALF - 0.25:.2f}): "
            f"{len(off_centre)}/{len(door)}"
        )
        if door:
            ys = np.array([c["yoff"] for c in door])
            print(
                f"  doorway-clip |y| offset: mean {ys.mean():.2f} "
                f"(doorway clear half-width {DOOR_HALF:.2f}; 0 = centred)"
            )
        share = len(door) / len(clips)
        print(
            f"\n  VERDICT INPUT: {share:.0%} of crashes are AT a doorway; if the "
            f"|y| offset clusters near {DOOR_HALF:.1f}, the fix is a centred\n"
            f"  doorway approach (thread straight through the middle), not a "
            f"wider gap."
        )


if __name__ == "__main__":
    sys.exit(main())

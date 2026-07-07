"""Phase 1b diagnostic — WHICH failure mode are the v3 residual collisions?

The v3 rangefinder-only baseline crashes at 0.033 (2/60), attributed to
"the off-axis-corner gap the 4 beams don't cover." Before building a
WM-forward + rangefinder-side HYBRID safety layer, answer the one
question that decides whether the WM can help at all:

  Is the drone flying FORWARD (+x) when it clips, or STRAFING / REVERSING?

Because the camera is locked to +x (yaw=0, the constraint that protects
the world model's body==world coordinate assumption):
  * FORWARD collision  -> the obstacle sits in the +-28 deg camera cone,
    which is WIDER than the single +x rangefinder beam. The WM-forward
    warn CAN see the between-beam corner the beam missed -> hybrid helps.
  * STRAFE / REVERSE collision -> the camera looks 90-180 deg away from
    the motion. The WM-forward is blind to it by construction -> a
    hybrid cannot help; the fix would be more beams, not vision.

For each collision we also record `fwd_clear` (the +x forward-cone
clearance, exactly what the WM-forward warn scores): a FORWARD collision
with low fwd_clear is one the WM warn would have fired on.

This is MODE characterization, not a rate re-measurement — it reuses the
exact v3 config (frontier, rangefinder safety, speed 0.6, 2 obstacles)
over a larger seed range only to accumulate enough clips to classify.

Run:
  python -m eval.diagnose_v3_collisions --n 200 --seed0 140000
  python -m eval.diagnose_v3_collisions --selftest
"""

import argparse
import sys

from eval.eval_search_wm_probe import DANGER_CLEAR
from planner.nav_action_set import (
    FORWARD,
    NAV_ACTION_NAMES,
    REVERSE,
    STRAFE_L,
    STRAFE_R,
)

LATERAL = {STRAFE_L, STRAFE_R, REVERSE}


def diagnose(n=200, seed0=140000, max_decisions=600, speed=0.6, n_obstacles=2):
    from eval.search_episode import run_search_episode
    from search.strategies import get_strategy
    from sim.envs import make_env
    from sim.indoor.rooms import single_room

    env = make_env()
    clips = []  # ONE entry per crashed episode: the FIRST contact (the failure
    # event). A collision does not end the episode, so a drone that ends up
    # against a wall logs a contact every decision — those grind-repeats are
    # counted only as `total_contacts`, never classified (they'd swamp the
    # real failure events and misstate the forward/lateral split).
    n_ep_crashed = 0
    total_contacts = 0
    for i in range(n):
        sc = single_room(seed0 + i, n_obstacles=n_obstacles)
        ep_clips = []
        m = run_search_episode(
            env,
            sc,
            get_strategy("frontier"),
            seed=seed0 + i,
            max_decisions=max_decisions,
            speed=speed,
            safety="rangefinder",
            on_collision=ep_clips.append,
        )
        if m["crashed"]:
            n_ep_crashed += 1
        total_contacts += len(ep_clips)
        if ep_clips:
            c = ep_clips[0]  # the first contact = the failure event
            c["seed"] = seed0 + i
            clips.append(c)
            print(
                f"  CLIP seed {seed0 + i} d{c['decision']} phase={c['phase']} "
                f"exec={NAV_ACTION_NAMES[c['executed']]} "
                f"(proposed {NAV_ACTION_NAMES[c['proposed']]}) "
                f"fwd_clear={c['fwd_clear']:.2f}",
                flush=True,
            )
    env.close()
    return clips, n_ep_crashed, total_contacts


def _classify(clips):
    fwd = [c for c in clips if c["executed"] == FORWARD]
    lat = [c for c in clips if c["executed"] in LATERAL]
    other = [c for c in clips if c not in fwd and c not in lat]
    # of the FORWARD clips, how many would the WM-forward warn have caught
    # (its warn ring is DANGER_CLEAR = 0.7 m; a low forward-cone clearance
    # is a fired warn)
    wm_catch = [c for c in fwd if c["fwd_clear"] < DANGER_CLEAR]
    return fwd, lat, other, wm_catch


def selftest() -> None:
    # classifier: a forward low-clearance clip is WM-catchable; a strafe
    # clip is not; buckets are disjoint and exhaustive
    clips = [
        {"executed": FORWARD, "fwd_clear": 0.3},
        {"executed": FORWARD, "fwd_clear": 1.5},
        {"executed": STRAFE_L, "fwd_clear": 0.3},
        {"executed": REVERSE, "fwd_clear": 0.3},
    ]
    fwd, lat, other, wm_catch = _classify(clips)
    assert len(fwd) == 2 and len(lat) == 2 and len(other) == 0
    assert len(wm_catch) == 1, "only the low-fwd_clear forward clip is catchable"
    print("DIAGNOSE-V3 OK: forward/lateral split + WM-catchable classifier")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--seed0", type=int, default=140000)
    ap.add_argument("--max-decisions", type=int, default=600)
    ap.add_argument("--speed", type=float, default=0.6)
    ap.add_argument("--n-obstacles", type=int, default=2)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return

    clips, n_ep_crashed, total_contacts = diagnose(
        args.n, args.seed0, args.max_decisions, args.speed, args.n_obstacles
    )
    fwd, lat, other, wm_catch = _classify(clips)
    print(
        f"\n[diagnose-v3] {args.n} episodes, {n_ep_crashed} crashed "
        f"(rate {n_ep_crashed / args.n:.3f}); {len(clips)} failure events "
        f"(first contact per episode), {total_contacts} total contact-decisions"
    )
    print(
        f"  FORWARD failures        : {len(fwd)}  "
        f"(WM-forward WOULD catch {len(wm_catch)}, fwd_clear<{DANGER_CLEAR}; the rest "
        f"clipped a corner OUTSIDE the +-28 deg cone)"
    )
    print(
        f"  STRAFE/REVERSE failures : {len(lat)}  "
        f"(camera locked +x, orthogonal to motion -> WM-forward blind)"
    )
    if other:
        print(f"  other (slow/hover)      : {len(other)}")
    if clips:
        catch = len(wm_catch) / len(clips)
        print(
            f"\n  VERDICT INPUT: a WM-forward + rangefinder-side hybrid could "
            f"prevent {len(wm_catch)}/{len(clips)} = {catch:.0%} of the failure "
            f"events.\n  The rest are lateral/reverse ({len(lat)}) or forward-but-"
            f"off-cone ({len(fwd) - len(wm_catch)}) — geometry a +x-locked camera "
            f"cannot see."
        )


if __name__ == "__main__":
    sys.exit(main())

"""Fly ONE episode in a chosen flight mode — the "set the mode at flight
start" entrypoint for the alongside deployment (see planner/flight_mode.py).

  python -m scripts.fly --mode transit --seed 7 [--gui]
  python -m scripts.fly --mode indoor_search --seed 130000
  python -m scripts.fly --selftest        # wiring only, no sim / no artifacts

`transit` rides the pinned champion WM; `indoor_search` rides the unified WM.
The mode owns its (WM, action set, controller, safety, runner); this script
just picks one, builds the env, and reports the scorecard.
"""

import argparse
import sys

from planner.flight_mode import get_mode, list_modes


def _report(name: str, r: dict) -> None:
    if "reached" in r:  # transit scorecard (assisted adds the authority line)
        print(
            f"[{name}] reached={r['reached']} crashed={r['crashed']} "
            f"min_clear={r['min_clear']:.2f}m steps={r['steps']}"
        )
        au = r.get("authority")
        if au:
            print(
                f"[{name}] overrides={au['n_overridden']}/{au['n_decisions']} "
                f"escalations={au['n_escalations']} "
                f"handbacks={au['n_handbacks']} frac_auto={au['frac_auto']}"
            )
    else:  # indoor search scorecard
        print(
            f"[{name}] found={r['target_found']} returned={r['returned']} "
            f"success={r['success']} collisions={r['collisions']} "
            f"coverage={r['coverage']:.2f} steps={r['steps']}"
        )


def selftest() -> None:
    modes = list_modes()
    assert {"transit", "indoor_search", "assisted"} <= set(modes), modes
    for n in modes:
        m = get_mode(n)
        assert callable(m.build) and m.wm_path
    print(f"FLY OK: modes {modes} (wiring only, no sim)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="transit", help=f"one of {list_modes()}")
    ap.add_argument("--seed", type=int, default=None, help="default: the mode's own")
    ap.add_argument("--speed", type=float, default=None)
    ap.add_argument("--gui", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return

    from sim.envs import make_env

    mode = get_mode(args.mode)  # raises SystemExit on an unknown mode
    kw = {}
    if args.seed is not None:
        kw["seed"] = args.seed
    if args.speed is not None:
        kw["speed"] = args.speed
    print(f"[fly] mode={mode.name} wm={mode.wm_path}")
    env = make_env(gui=args.gui)
    try:
        r = mode.build(env, **kw)
    finally:
        env.close()
    _report(mode.name, r)


if __name__ == "__main__":
    sys.exit(main())

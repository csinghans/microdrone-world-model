"""Does stop-and-observe (hover after each gate) help slalom — and does it
let slalom survive the unified-WM swap?

2x2 head-to-head on slalom3_fixed, same seeds, the slalom exam predicate
(`slalom_success`), with tmax raised to pay for the hover steps:

    {continuous, stop-observe} x {champion WM, unified WM}

Pre-registered reads (frozen before running):
  * continuous x champion ~= 80% (the known baseline);
    continuous x unified  ~= 0%  (the collapse the full-zoo pass found).
  * cautious:   stop-observe x champion >= continuous x champion
                (stopping must not hurt on the native WM).
  * robustness: stop-observe x unified  >> continuous x unified
                (breaking the ~40-decision chain resets the compounding
                latent drift, so each gate is an independent short decision).

The wrapper (`skills/corridor_slalom_v2/stop_observe.py`) needs the fences;
we read them env-free per seed (`_spawn_slalom3_fixed(None, rng)`) — the
SAME seed reproduces the course the runner flies.

Run:
  python -m eval.eval_slalom_stopobserve --seeds 20 [--hover 10]
  python -m eval.eval_slalom_stopobserve --selftest
"""

import argparse
import os
import sys

import numpy as np

from world_model.training import MODEL

UNIFIED_WM = os.path.join(os.path.dirname(MODEL), "world_model_unified.pth")
SLALOM_CHAMPION = "experiments/slalom_v2_promotion/artifacts/ppo_anchor_sched_edge.zip"
N_GATES = 3
WORLD = "slalom3_fixed"


def _fences(seed: int):
    from skills.corridor_slalom_v2.skill import _spawn_slalom3_fixed

    return _spawn_slalom3_fixed(None, np.random.default_rng(seed)).meta["fences"]


def run_cell(env, model, wm, stop_observe: bool, hover: int, n: int, seed0: int, speed):
    from eval.episode import run_scenario_episode
    from planner.latent_mpc import DECIDE_EVERY
    from planner.learned_policy import LearnedPolicy
    from sim.scenarios import TMAX
    from skills.corridor_slalom.skill import slalom_success
    from skills.corridor_slalom_v2.stop_observe import StopObserveSlalom

    enc, pred, cheads, _n, meta = wm
    tmax = TMAX + hover * N_GATES * DECIDE_EVERY  # hovering makes no x-progress
    ok = 0
    for i in range(n):
        seed = seed0 + i
        inner = LearnedPolicy(model, enc, pred, cheads, meta, speed=speed)
        pol = (
            StopObserveSlalom(inner, _fences(seed), hover=hover)
            if stop_observe
            else inner
        )
        ep = run_scenario_episode(env, pol, seed, WORLD, speed=speed, tmax=tmax)
        ok += int(bool(slalom_success(ep)))
    return ok / n


def selftest() -> None:
    # env-free: fences reproduce (3, alternating sides) and the wrapper wires
    from skills.corridor_slalom_v2.stop_observe import StopObserveSlalom

    f = _fences(22000)
    assert len(f) == N_GATES, f"slalom3 has {N_GATES} gates, got {len(f)}"
    sides = [np.sign(yc) for _x, yc, _w in f]
    assert sides == [-1, 1, -1] or sides == [1, -1, 1], f"gaps alternate: {sides}"

    class _Stub:
        def begin(self, p):
            pass

        def decide(self, fr, st):
            return 0

    pol = StopObserveSlalom(_Stub(), f, hover=4)
    pol.begin([])
    assert pol.hover == 4 and pol.fences == list(f)
    assert SLALOM_CHAMPION.endswith(".zip")
    print(f"EVAL-SLALOM-STOPOBSERVE OK: {N_GATES} gates (sides {sides}), wrapper wires")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--seed0", type=int, default=22000)
    ap.add_argument("--hover", type=int, default=10, help="hover decisions per gate")
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument(
        "--policy",
        default=SLALOM_CHAMPION,
        help="policy zip; a stop-AWARE policy self-hovers, so read its "
        "'continuous' (raw) column",
    )
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return

    from planner.learned_policy import load_policy
    from sim.envs import make_env
    from skills.base import load_skill
    from world_model.training import load_model

    load_skill("skills/corridor_slalom_v2")  # register slalom3_fixed
    model = load_policy(args.policy)
    wms = {
        "champion": load_model(MODEL, device="cpu"),
        "unified": load_model(UNIFIED_WM, device="cpu"),
    }
    env = make_env()
    print(
        f"slalom stop-observe 2x2: {args.seeds} seeds, hover={args.hover}, "
        f"speed={args.speed*0.8:.1f} m/s"
    )
    print(f"  {'WM':9} {'continuous':>11}  {'stop-observe':>12}")
    results = {}
    for name, wm in wms.items():
        cont = run_cell(
            env, model, wm, False, args.hover, args.seeds, args.seed0, args.speed
        )
        stop = run_cell(
            env, model, wm, True, args.hover, args.seeds, args.seed0, args.speed
        )
        results[name] = (cont, stop)
        print(f"  {name:9} {cont*100:9.0f}%  {stop*100:10.0f}%")
    env.close()
    cch, sch = results["champion"]
    cun, sun = results["unified"]
    print(
        "VERDICT: "
        f"cautious {'PASS' if sch >= cch else 'FAIL'} "
        f"(stop-observe {sch*100:.0f}% vs continuous {cch*100:.0f}% on champion); "
        f"robustness {'PASS' if sun > cun else 'FAIL'} "
        f"(stop-observe {sun*100:.0f}% vs continuous {cun*100:.0f}% on unified)"
    )


if __name__ == "__main__":
    sys.exit(main())

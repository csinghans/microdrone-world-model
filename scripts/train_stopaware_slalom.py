"""Fine-tune the slalom champion into a STOP-AWARE slalom policy.

The post-hoc hover wrapper (experiments/slalom_stopobserve_v1) failed: the
CONTINUOUS champion cannot resume from a dead stop (OOD), so forcing hovers
collapsed it 80%->10%. The fix is to BUILD the stop into the policy — warm-
start the champion and fine-tune it in a WMPolicyEnv with `stop_hover` on
(after each threaded gate, a window that PAYS for HOVER and penalises moving,
suppressing progress). The policy LEARNS to stop after a gate and RESUME, so
it experiences the very states the wrapper could not supply. Then we test
whether the (now-independent, chain-broken) gates survive the unified-WM swap
(eval/eval_slalom_stopobserve.py --policy).

Warm start keeps the champion's obs layout (576 = 48*12: x_progress + the
HISTORY=12 stack); PPO.load(..., env=env) resumes weights + optimiser.

  python -m scripts.train_stopaware_slalom --timesteps 500000 --stop-hover 8
  python -m scripts.train_stopaware_slalom --selftest
"""

import argparse
import os
import sys

CHAMPION = "experiments/slalom_v2_promotion/artifacts/ppo_anchor_sched_edge.zip"
OUT = "output/ppo_slalom_stopaware.zip"
# slalom-focused FT: teach the stop rhythm IN slalom (the champion already
# generalises; this experiment measures slalom robustness, not the zoo).
WORLDS = ("slalom3_fixed",)


def selftest() -> None:
    assert CHAMPION.endswith(".zip") and OUT.endswith(".zip")
    assert isinstance(WORLDS, tuple) and "slalom3_fixed" in WORLDS
    print(f"TRAIN-STOPAWARE OK: warm-start {os.path.basename(CHAMPION)} -> {OUT}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--timesteps", type=int, default=500_000)
    ap.add_argument("--stop-hover", type=int, default=8)
    ap.add_argument(
        "--aug-wm",
        default=None,
        help="second WM checkpoint for per-episode encoder data-aug (two-WM "
        "training -> swap-invariance); e.g. output/world_model_unified.pth",
    )
    ap.add_argument(
        "--aug-p",
        type=float,
        default=0.5,
        help="P(aug encoder) per episode; 0.5 = the measured two-WM recipe, "
        "0.34 = zoo_transfer_v1 K1's champion-weighted mix",
    )
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return

    from stable_baselines3 import PPO
    from stable_baselines3.common.env_util import make_vec_env

    from planner.learned_policy import WMPolicyEnv
    from skills.base import load_skill

    load_skill("skills/corridor_slalom_v2")  # register slalom3_fixed
    env = make_vec_env(
        lambda: WMPolicyEnv(
            seed0=args.seed,
            worlds=WORLDS,
            x_progress=True,
            edge_bias=True,  # match the champion's speed diet
            stop_hover=args.stop_hover,
            aug_wm_path=args.aug_wm,
            aug_p=args.aug_p,
        ),
        n_envs=1,
    )
    print(
        f"[train-stopaware] warm start {CHAMPION} | worlds={WORLDS} "
        f"stop_hover={args.stop_hover} aug_wm={args.aug_wm} "
        f"aug_p={args.aug_p} timesteps={args.timesteps}"
    )
    model = PPO.load(CHAMPION, env=env)  # resume weights + optimiser on the new env
    model.learn(total_timesteps=args.timesteps)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    model.save(args.out)
    env.close()
    print(f"STOP-AWARE SLALOM SAVED: {args.out}")


if __name__ == "__main__":
    sys.exit(main())

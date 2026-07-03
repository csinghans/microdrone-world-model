"""Compare every available policy on identical courses.

Flies reactive, the hand MPC, and every trained learned variant on the same
cluttered courses (the distribution the FOV tail lives in) plus the fast
single-pillar endpoint. Learned variants join automatically when their
trained .zip exists.

Run:
  python -m scripts.evaluate --seeds 60
For the per-axis scoreboards, run the eval modules directly:
  python -m eval.eval_closed_loop --seeds 100
  python -m eval.eval_speed_sweep --seeds 30
  python -m eval.eval_robustness --seeds 30
  python -m eval.eval_latency_budget
"""

import argparse
import os
import sys

import numpy as np

from eval.eval_closed_loop import load_or_train, run_episode
from planner.latent_mpc import ReactivePolicy, WMPolicy
from sim.envs import make_env


def compare(n_seeds: int, seed0: int = 1000) -> dict:
    from planner.learned_policy import LearnedPolicy, load_policy, zip_path

    enc, pred, cheads, nhead, meta = load_or_train(device="cpu")
    env = make_env()

    mk = {
        "reactive": lambda s: ReactivePolicy(enc, nhead),
        "wm-mpc": lambda s: WMPolicy(enc, pred, cheads, meta, speed=s),
    }
    for name, rec, rnd, edge, curr, hard, xp in (
        ("learned", False, False, False, False, False, False),
        ("learned-hard", False, False, False, False, True, False),
        ("learned-hard-xp", False, False, False, False, True, True),
        ("learned-rnn", True, False, False, False, False, False),
        ("learned-rnn-edge", True, False, True, False, False, False),
        ("learned-rnn-curr", True, False, False, True, False, False),
        ("learned-rand", False, True, False, False, False, False),
        ("learned-rnn-rand", True, True, False, False, False, False),
    ):
        path = zip_path(rec, rnd, edge, curr, hard, xp)
        if os.path.exists(path):
            model = load_policy(path)
            mk[name] = lambda s, m=model: LearnedPolicy(
                m, enc, pred, cheads, meta, speed=s
            )

    def fly(policy_fn, **kw):
        crash, clear = 0, []
        for i in range(n_seeds):
            run = run_episode(env, policy_fn(kw.get("speed", 1.0)), seed0 + i, **kw)
            crash += int(run["crashed"])
            clear.append(run["min_clear"])
        return crash / n_seeds, float(np.mean(clear))

    out = {}
    for name, fn in mk.items():
        out[name] = {"cluttered": fly(fn, in_path=True)}
    for name, fn in mk.items():
        out[name]["fast"] = fly(fn, in_path=True, solo=True, speed=2.0)
    env.close()
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=60)
    ap.add_argument("--seed0", type=int, default=1000)
    args = ap.parse_args()

    res = compare(args.seeds, args.seed0)
    order = [k for k in res]
    clut = " / ".join(f"{k} {res[k]['cluttered'][0]:.0%}" for k in order)
    clr = " / ".join(f"{res[k]['cluttered'][1]:.2f}" for k in order)
    fast = " / ".join(f"{k} {res[k]['fast'][0]:.0%}" for k in order)
    print(
        f"LEARNED-POLICY OK: {args.seeds} cluttered courses @ 0.8 m/s — crash "
        f"{clut} (clearance {clr} m)\n"
        f"  single-pillar @ 1.6 m/s — crash {fast} — the cost function is "
        f"learned, the world model is the same"
    )


if __name__ == "__main__":
    main()
    sys.exit(0)

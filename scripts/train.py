"""Train entry point: the world model by default, the policy with --policy.

Run:
  python -m scripts.train --epochs 80                 # world model
  python -m scripts.train --robust                    # + appearance DR
  python -m scripts.train --policy --timesteps 300000 # stacked PPO policy
  python -m scripts.train --policy --recurrent        # LSTM flavour
  python -m scripts.train --policy --recurrent --edge-bias
  python -m scripts.train --policy --curriculum
  python -m scripts.train --selftest                  # tiny world model, asserts
Saves output/world_model[.._robust].pth / output/ppo_wm_policy*.zip.
"""

import argparse
import os
import sys

import numpy as np
import torch

from datasets.generate_rollouts import OUT as DATA
from datasets.generate_rollouts import gen
from datasets.intervention_labels import HORIZONS
from world_model.training import GAP8_BUDGET_KB, MODEL, train


def _load_or_make(selftest: bool) -> dict:
    if selftest:
        return gen(20, 110)  # self-contained tiny set (no prior npz needed)
    if os.path.exists(DATA):
        blob = np.load(DATA)
        return {k: blob[k] for k in blob.files}
    print(f"[INFO] no dataset at {DATA}; generating a default one ...")
    return gen(64, 120)


def train_world_model(args) -> None:
    epochs = 60 if args.selftest else args.epochs
    data = _load_or_make(args.selftest)
    ckpt, m = train(data, epochs=epochs, batch=args.batch, robust=args.robust)

    # a selftest must not clobber a real trained checkpoint with its toy one
    # (and a robust experiment gets its own file — see eval_robustness)
    out = MODEL.replace(".pth", "_selftest.pth") if args.selftest else MODEL
    if args.robust and not args.selftest:
        out = MODEL.replace(".pth", "_robust.pth")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    torch.save(ckpt, out)
    auc_str = "/".join(f"{a:.2f}" for a in m["auc"])
    h_str = "/".join(str(k) for k in HORIZONS)
    print(
        f"WORLD-MODEL OK: {m['n_train']} train seqs, "
        f"latent MSE@32={m['mse'][-1]:.3f} (no-op {m['noop'][-1]:.3f}), "
        f"AUC@{h_str}={auc_str}, now-AUC={m['now_auc']:.2f}, "
        f"veer-ranking={m['side']:.2f} (n={m['n_side']}), "
        f"int8 weights={m['int8_kb']:.1f} KB (<{GAP8_BUDGET_KB} fits), saved {out}"
    )
    if args.selftest:
        # k=4 (~83 ms) is near-degenerate — "future == present" is genuinely
        # strong there — so the meaningful claims are the *long* horizon and
        # the overall average, not every horizon individually
        assert m["mse"][-1] < m["noop"][-1], "no long-horizon predictive gain"
        assert float(np.mean(m["mse"])) < float(
            np.mean(m["noop"])
        ), "predictor no better than 'future == present' overall"
        assert m["auc"][1] > 0.70, f"AUC@8 barely predicts danger ({m['auc'][1]:.2f})"
        assert m["auc"][-1] > 0.70, f"AUC@32 barely anticipates ({m['auc'][-1]:.2f})"
        assert m["now_auc"] > 0.65, f"danger-now head weak ({m['now_auc']:.2f})"
        if m["n_side"] >= 20:
            assert m["side"] > 0.60, f"veer ranking at chance ({m['side']:.2f})"
        assert m["int8_kb"] < GAP8_BUDGET_KB, f"too big ({m['int8_kb']:.1f} KB)"


def train_policy(args) -> None:
    from planner.learned_policy import train as train_ppo
    from planner.learned_policy import train_curriculum, zip_path

    if args.curriculum:
        print(f"[INFO] RecurrentPPO mixed-diet curriculum, {args.timesteps} steps")
        train_curriculum(args.timesteps, n_steps=args.n_steps, lstm_size=args.lstm_size)
        print(f"[INFO] saved {zip_path(recurrent=True, curr=True)}")
        return
    tag = (
        ("recurrent " if args.recurrent else "stacked ")
        + ("+ randomized" if args.randomize else "clean")
        + (" + edge-bias" if args.edge_bias else "")
    )
    print(f"[INFO] PPO over world-model outputs ({tag}), {args.timesteps} steps")
    train_ppo(
        args.timesteps,
        recurrent=args.recurrent,
        randomize=args.randomize,
        edge_bias=args.edge_bias,
        n_steps=args.n_steps,
        lstm_size=args.lstm_size,
    )
    print(f"[INFO] saved {zip_path(args.recurrent, args.randomize, args.edge_bias)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", action="store_true", help="train the PPO policy")
    # world-model knobs
    ap.add_argument("--epochs", type=int, default=80)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--robust", action="store_true")
    # policy knobs
    ap.add_argument("--timesteps", type=int, default=300_000)
    ap.add_argument("--recurrent", action="store_true")
    ap.add_argument("--edge-bias", action="store_true")
    ap.add_argument("--curriculum", action="store_true")
    ap.add_argument("--randomize", action="store_true")
    ap.add_argument("--n-steps", type=int, default=256)
    ap.add_argument("--lstm-size", type=int, default=64)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.policy:
        train_policy(args)
    else:
        train_world_model(args)


if __name__ == "__main__":
    main()
    sys.exit(0)

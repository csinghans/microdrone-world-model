"""Train entry point: the world model by default, the policy with --policy.

Run:
  python -m scripts.train --epochs 80                 # world model
  python -m scripts.train --robust                    # + appearance DR
  python -m scripts.train --ground                    # + v0.5 metric grounding
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
from world_model.training import GAP8_BUDGET_KB, MODEL, MODEL_GRU, train


def _load_or_make(selftest: bool, data_path: str = None) -> dict:
    if selftest:
        return gen(20, 110)  # self-contained tiny set (no prior npz needed)
    path = data_path or DATA
    if os.path.exists(path):
        blob = np.load(path)
        return {k: blob[k] for k in blob.files}
    if data_path:  # an explicit dataset was named but is missing — fail loud
        raise SystemExit(f"--data {data_path} not found")
    print(f"[INFO] no dataset at {DATA}; generating a default one ...")
    return gen(64, 120)


def train_world_model(args) -> None:
    # the temporal and grounded smokes get a longer leash: an extra objective
    # moves the shared trunk while the EMA target chases it (GRU: a new
    # mapping; grounding: metric structure pulled into the latent), so they
    # converge later — but the predictive-gain claim itself is never waived
    leash = args.temporal or args.ground
    epochs = (120 if leash else 60) if args.selftest else args.epochs
    data = _load_or_make(args.selftest, args.data)
    rep = {}  # representation knobs ride explicit flags only (defaults stay)
    if args.latent_d is not None:
        rep["latent_d"] = args.latent_d
    if args.strips is not None:
        rep["strips"] = args.strips
    ckpt, m = train(
        data,
        epochs=epochs,
        batch=args.batch,
        seed=args.seed,
        robust=args.robust,
        temporal=args.temporal,
        ground=args.ground,
        ground_lambda=args.ground_lambda,
        **rep,
    )

    # a selftest must not clobber a real trained checkpoint with its toy one
    # (robust / temporal / grounded experiments get their own files)
    base = MODEL_GRU if args.temporal else MODEL
    out = base.replace(".pth", "_selftest.pth") if args.selftest else base
    if args.robust and not args.selftest:
        out = base.replace(".pth", "_robust.pth")
    if args.ground and not args.selftest:
        out = out.replace(".pth", "_ground.pth")
    if args.out and not args.selftest:  # gate runs park checkpoints elsewhere
        out = args.out
    os.makedirs(os.path.dirname(out), exist_ok=True)
    torch.save(ckpt, out)
    auc_str = "/".join(f"{a:.2f}" for a in m["auc"])
    h_str = "/".join(str(k) for k in HORIZONS)
    by_world = m.get("auc_by_world") or {}
    world_str = (
        " | AUC@32 by world: " + " ".join(f"{k}={v:.2f}" for k, v in by_world.items())
        if by_world
        else ""
    )
    gnd_str = (
        f", gnd-AUC={m['gnd_auc']:.2f} (aux +{m['aux_kb']:.1f} KB, train-only)"
        if "gnd_auc" in m
        else ""
    )
    print(
        f"WORLD-MODEL OK: {m['n_train']} train seqs, "
        f"latent MSE@32={m['mse'][-1]:.3f} (no-op {m['noop'][-1]:.3f}), "
        f"AUC@{h_str}={auc_str}{world_str}, now-AUC={m['now_auc']:.2f}{gnd_str}, "
        f"veer-ranking={m['side']:.2f} (n={m['n_side']}), "
        f"int8 weights={m['int8_kb']:.1f} KB (<{GAP8_BUDGET_KB} fits), saved {out}"
    )
    if args.selftest:
        # Smoke asserts are harness checks — dead heads, collapse, shape
        # bugs — not the science. Recalibrated 2026-07-03 after a measured
        # finding: the *shipped v0.4.0* static smoke fails the old MSE bars
        # deterministically (val MSE@32 5.01 vs no-op 1.39, same digits on
        # every rerun), i.e. the old asserts promised more than a 20-rollout
        # classic-only draw can deliver — val Δ overfits below ~1k samples
        # and the EMA-target scale itself swings across runs (no-op 1.4-9.5).
        # The latent-regression claim therefore lives at the full-scale
        # gates, where it is actually measured (G2 at 96-rollout scale:
        # MSE@32 1.31 vs no-op 1.94; every M-gate control re-verifies it).
        # What a smoke CAN promise: the decision metrics rank, no head is
        # dead, and the budget holds.
        assert m["now_auc"] > 0.52, f"danger-now head dead ({m['now_auc']:.2f})"
        assert m["auc"][1] > 0.70, f"AUC@8 barely predicts danger ({m['auc'][1]:.2f})"
        assert m["auc"][-1] > 0.70, f"AUC@32 barely anticipates ({m['auc'][-1]:.2f})"
        if m["n_side"] >= 20:
            assert m["side"] > 0.60, f"veer ranking at chance ({m['side']:.2f})"
        assert m["int8_kb"] < GAP8_BUDGET_KB, f"too big ({m['int8_kb']:.1f} KB)"
        if args.ground:
            # pillars are visually loud; even a smoke run must read the grid
            # far better than a coin — and the aux head must stay tiny
            assert m["gnd_auc"] > 0.60, f"grounding unlearned ({m['gnd_auc']:.2f})"
            assert m["aux_kb"] < 2.0, f"aux head too big ({m['aux_kb']:.1f} KB)"


def train_policy(args) -> None:
    from planner.learned_policy import train as train_ppo
    from planner.learned_policy import train_curriculum, zip_path

    if args.curriculum:
        print(f"[INFO] RecurrentPPO mixed-diet curriculum, {args.timesteps} steps")
        train_curriculum(args.timesteps, n_steps=args.n_steps, lstm_size=args.lstm_size)
        print(f"[INFO] saved {zip_path(recurrent=True, curr=True)}")
        return
    hard = args.worlds == "hard"
    tag = (
        ("recurrent " if args.recurrent else "stacked ")
        + ("+ randomized" if args.randomize else "clean")
        + (" + edge-bias" if args.edge_bias else "")
        + (" + hard worlds" if hard else "")
        + (" + x-progress" if args.x_progress else "")
    )
    print(f"[INFO] PPO over world-model outputs ({tag}), {args.timesteps} steps")
    train_ppo(
        args.timesteps,
        recurrent=args.recurrent,
        randomize=args.randomize,
        edge_bias=args.edge_bias,
        hard=hard,
        x_progress=args.x_progress,
        n_steps=args.n_steps,
        lstm_size=args.lstm_size,
    )
    saved = zip_path(
        args.recurrent, args.randomize, args.edge_bias, hard=hard, xp=args.x_progress
    )
    print(f"[INFO] saved {saved}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", action="store_true", help="train the PPO policy")
    # world-model knobs
    ap.add_argument("--epochs", type=int, default=80)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--robust", action="store_true")
    ap.add_argument("--temporal", action="store_true")  # model-side GRU (v3)
    ap.add_argument("--ground", action="store_true")  # v0.5 metric-grounding aux
    ap.add_argument("--ground-lambda", type=float, default=0.5)  # the N-knob
    ap.add_argument("--out", default=None, help="world-model save path override")
    ap.add_argument("--seed", type=int, default=0)  # borderline reruns use seed+1
    ap.add_argument("--data", default=None, help="dataset npz override (e.g. search)")
    # representation knobs (defaults = the deployed architecture)
    ap.add_argument("--latent-d", type=int, default=None, help="latent width")
    ap.add_argument("--strips", type=int, default=None, help="lateral pool bins")
    # policy knobs
    ap.add_argument("--timesteps", type=int, default=300_000)
    ap.add_argument("--recurrent", action="store_true")
    ap.add_argument("--edge-bias", action="store_true")
    ap.add_argument("--curriculum", action="store_true")
    ap.add_argument("--randomize", action="store_true")
    ap.add_argument("--n-steps", type=int, default=256)
    ap.add_argument("--lstm-size", type=int, default=64)
    ap.add_argument(
        "--worlds",
        default="classic",
        help="'classic' | 'hard' | comma-list of registered worlds",
    )
    ap.add_argument("--x-progress", action="store_true")  # odometry map pin in obs
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.policy:
        train_policy(args)
    else:
        train_world_model(args)


if __name__ == "__main__":
    main()
    sys.exit(0)

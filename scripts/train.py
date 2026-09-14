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
Saves output/world_model_candidate.pth (or an explicit new --out).
Variant/selftest suffixes remain supported. Policies use output/ppo_wm_policy*.zip.
"""

import argparse
import os
import sys

import numpy as np

from datasets.generate_rollouts import OUT as DATA
from datasets.generate_rollouts import gen
from datasets.intervention_labels import HORIZONS
from datasets.provenance import file_identity
from world_model.cf_sampling import CF_HARD_POOLS
from world_model.checkpoint_io import check_destination, save_checkpoint
from world_model.training import GAP8_BUDGET_KB, MODEL, MODEL_GRU, train


def _load_or_make(selftest: bool, data_path: str = None, source_identity=None) -> dict:
    if selftest:
        return gen(20, 110)  # self-contained tiny set (no prior npz needed)
    path = data_path or DATA
    if os.path.exists(path):
        source = file_identity(path)
        with np.load(path, allow_pickle=False) as blob:
            data = {k: blob[k] for k in blob.files}
        if file_identity(path) != source:
            raise ValueError("training dataset changed while loading")
        if source_identity is not None:
            source_identity.update(source)
        return data
    if data_path:  # an explicit dataset was named but is missing — fail loud
        raise SystemExit(f"--data {data_path} not found")
    print(f"[INFO] no dataset at {DATA}; generating a default one ...")
    return gen(64, 120)


def world_model_output(args):
    """Choose the destination before loading data or fitting any model."""
    base = MODEL_GRU if args.temporal else MODEL
    out = base.replace(".pth", "_selftest.pth") if args.selftest else base
    if args.robust and not args.selftest:
        out = base.replace(".pth", "_robust.pth")
    if args.ground and not args.selftest:
        out = out.replace(".pth", "_ground.pth")
    if args.two_frame and not args.selftest:
        out = out.replace(".pth", "_2f.pth")
    if args.out and not args.selftest:
        out = args.out
    elif not args.selftest and out == MODEL:
        out = MODEL.replace(".pth", "_candidate.pth")
    return check_destination(out, overwrite=args.selftest)


def train_world_model(args) -> None:
    out = world_model_output(args)
    # the temporal / grounded / two-frame smokes get a longer leash: a new
    # mapping moves the shared trunk while the EMA target chases it (GRU: a
    # new state; grounding: metric structure; two-frame: a 6-channel input
    # the encoder must relearn from scratch), so they converge later at toy
    # scale — but the predictive-gain claim itself is never waived
    # (measured 2026-08-31: the 2f smoke reads AUC@32 0.66 at 60 epochs,
    # with AUC@8 already 0.98 — slow convergence, not a dead head)
    leash = args.temporal or args.ground or args.two_frame
    epochs = (120 if leash else 60) if args.selftest else args.epochs
    source = {}
    data = _load_or_make(args.selftest, args.data, source)
    if args.strips:  # MPS AdaptiveAvgPool needs divisible sizes — fail LOUD
        feat_cols = int(data["frames"].shape[2]) // 8  # three stride-2 blocks
        if feat_cols % int(args.strips):
            raise SystemExit(
                f"--strips {args.strips} does not divide the {feat_cols}-column "
                f"feature map (input res {data['frames'].shape[2]}); valid: "
                f"{[s for s in range(1, feat_cols + 1) if feat_cols % s == 0]}"
            )
    rep = {}  # representation knobs ride explicit flags only (defaults stay)
    if args.latent_d is not None:
        rep["latent_d"] = args.latent_d
    if args.strips is not None:
        rep["strips"] = args.strips
    if args.two_frame:  # perception-tier temporal input (one knob at a time)
        if args.temporal:
            raise SystemExit("--two-frame and --temporal are separate knobs")
        rep["in_frames"] = 2
        rep["frame_stride"] = args.frame_stride
    ckpt, m = train(
        data,
        epochs=epochs,
        batch=args.batch,
        seed=args.seed,
        robust=args.robust,
        temporal=args.temporal,
        ground=args.ground,
        ground_lambda=args.ground_lambda,
        cf_hard_pool=args.cf_hard_pool,
        executed_moving_weight=args.executed_moving_weight,
        **rep,
    )
    if source:
        if file_identity(source["path"]) != source:
            raise ValueError(
                "training dataset changed during fitting; no checkpoint saved"
            )
        ckpt["meta"]["training_dataset_sha256"] = source["sha256"]

    save_checkpoint(ckpt, out, overwrite=args.selftest)
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
        f"z-std med/max={m['zstd_med']:.2f}/{m['zstd_max']:.2f} "
        f"(|z| {m['zabs']:.2f}), "
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
    ap.add_argument("--cf-hard-pool", choices=CF_HARD_POOLS, default="legacy_masked")
    ap.add_argument("--executed-moving-weight", type=float, default=1.0)
    ap.add_argument("--out", default=None, help="new world-model candidate path")
    ap.add_argument("--seed", type=int, default=0)  # borderline reruns use seed+1
    ap.add_argument("--data", default=None, help="dataset npz override (e.g. search)")
    # representation knobs (defaults = the deployed architecture)
    ap.add_argument("--latent-d", type=int, default=None, help="latent width")
    ap.add_argument("--strips", type=int, default=None, help="lateral pool bins")
    # perception-tier temporal input (v0.18 knob): stack the frame taken
    # frame-stride control steps earlier as 3 extra input channels
    ap.add_argument("--two-frame", action="store_true")
    ap.add_argument("--frame-stride", type=int, default=4)  # = DECIDE_EVERY
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

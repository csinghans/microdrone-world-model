"""Score a saved world-model checkpoint against a dataset — the gate probe.

Model-axis gates (G/M series) compare checkpoints trained on the same draw.
The training printout rounds to two decimals, which cannot resolve a
borderline bar (is dense +0.048 or +0.052?), and its veer-ranking sample
can be tiny (n=20 on a 19-rollout val split). This probe recomputes the
decision metrics from the *saved* checkpoint at four decimals, on exactly
the split the training run used (same seed -> same rollout split —
the CLI reads the seed from the checkpoint's meta, refuses a
contradicting --seed, and warns on legacy checkpoints without one), and
scores veer-ranking both on the val rollouts and widened to every rollout
(the probe never trains on labels, so widening stays meaningful — the
same rule training.py itself applies when val is thin).

Honest limit: the latent-MSE-vs-no-op check is *not* recomputable here —
the JEPA target is the EMA encoder, which checkpoints do not persist. That
claim is read off the training log, where it is printed at k=32.

Run:
  python -m eval.eval_wm_checkpoint --ckpt experiments/.../wm_m1_ground.pth
  python -m eval.eval_wm_checkpoint --selftest
"""

import argparse
import sys

import numpy as np
import torch

from datasets.generate_rollouts import OUT as DATA
from datasets.intervention_labels import HORIZONS
from planner.action_set import A_NORM
from sim.scenarios import DANGER_R
from world_model.losses import roc_auc
from world_model.training import (
    _index_samples,
    _split_rollouts,
    load_model,
    veer_ranking,
)


def evaluate(ckpt_path: str, data: dict, seed: int = 0) -> dict:
    """Rebuild the seed-`seed` train/val split and score the checkpoint:
    per-world AUC@32, overall AUC per horizon, danger-now AUC (all at val),
    and veer-ranking on val rollouts + widened to all rollouts."""
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    enc, pred, cheads, nhead, _meta = load_model(ckpt_path, device)
    return evaluate_components(enc, pred, cheads, nhead, data, seed, device)


def evaluate_components(enc, pred, cheads, nhead, data, seed=0, device="cpu"):
    """The same scoring loop on already-loaded modules — the seam through
    which candidate/quantized components are graded on the identical split
    without any checkpoint swap (int8_parity_v1). `evaluate` is a thin
    load_model wrapper around this; the selftest's probe==train-val assert
    guards both."""
    tgru = getattr(enc, "temporal", None)

    rng = np.random.default_rng(seed)
    idx, c_h = _index_samples(data)
    _tr_rolls, va_rolls = _split_rollouts(data, rng)
    va = np.where(np.isin(idx[:, 0], va_rolls))[0]
    R, L = data["frames"].shape[:2]

    def frames_at(pairs):  # (n,2) [r,t] -> (n,3,64,64) float on device
        x = np.stack([data["frames"][r, t] for r, t in pairs])
        x = torch.tensor(x, dtype=torch.float32, device=device)
        return x.permute(0, 3, 1, 2) / 255.0

    with torch.no_grad():
        scores, zs = [], []
        for i in range(0, len(va), 512):
            pairs = idx[va[i : i + 512]]
            z = enc(frames_at(pairs))
            if tgru is not None:  # v3: judge from the single frame is wrong;
                # gate probes for temporal models feed the K-frame window
                raise SystemExit("temporal checkpoints need the training probe")
            a = torch.tensor(
                np.stack([data["actions"][r, t] / A_NORM for r, t in pairs]),
                dtype=torch.float32,
                device=device,
            )
            z_hat = pred(z, a, base=z)
            scores.append(torch.sigmoid(cheads(z_hat)).cpu().numpy()[:, :, 0])
            zs.append(z)
        scores = np.concatenate(scores)

        now_pairs = [(r, t) for r in va_rolls for t in range(L)]
        now_scores = []
        for i in range(0, len(now_pairs), 512):
            z = enc(frames_at(now_pairs[i : i + 512]))
            now_scores.append(torch.sigmoid(nhead(z)).cpu().numpy())
        now_scores = np.concatenate(now_scores)
    now_lbl = np.array(
        [float(data["dists"][r, t] < DANGER_R) for r, t in now_pairs],
        dtype=np.float32,
    )

    auc_h = [roc_auc(scores[:, i], c_h[va][:, i, 0]) for i in range(len(HORIZONS))]
    auc_by_world = {}
    if "world_id" in data:
        wn = (
            [str(x) for x in np.asarray(data["world_names"])]
            if "world_names" in data
            else ["classic", "dense", "moving"]
        )
        sw = np.asarray(data["world_id"])[idx[va][:, 0]]
        for w in sorted({int(x) for x in sw}):
            m = sw == w
            if int(m.sum()) >= 20:
                auc_by_world[wn[w] if w < len(wn) else str(w)] = roc_auc(
                    scores[m][:, -1], c_h[va][m][:, -1, 0]
                )
    side_val, n_val = veer_ranking(data, va_rolls, enc, pred, cheads, device)
    side_all, n_all = veer_ranking(data, range(R), enc, pred, cheads, device)
    return {
        "auc_h": auc_h,
        "auc_by_world": auc_by_world,
        "now_auc": roc_auc(now_scores, now_lbl),
        "veer_val": (side_val, n_val),
        "veer_all": (side_all, n_all),
        "n_val_samples": int(len(va)),
        "va_rolls": list(map(int, va_rolls)),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default=None)
    ap.add_argument("--data", default=DATA)
    ap.add_argument("--seed", type=int, default=None, help="the training run's seed")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.ckpt and not args.selftest:
        meta_seed = (
            torch.load(args.ckpt, map_location="cpu", weights_only=False)
            .get("meta", {})
            .get("seed")
        )
        if meta_seed is not None:
            if args.seed is not None and int(args.seed) != int(meta_seed):
                raise SystemExit(
                    f"--seed {args.seed} contradicts the checkpoint's own "
                    f"training seed {meta_seed}: a mismatched split makes "
                    "the val rollouts overlap the model's TRAIN set "
                    "(leakage) — refuse to grade"
                )
            args.seed = int(meta_seed)
        elif args.seed is None:
            print(
                "[wm-probe] WARNING: checkpoint stores no training seed and "
                "--seed not given; grading on the seed-0 split. If this "
                "model trained on another seed, these val reads LEAK its "
                "training data."
            )
            args.seed = 0
    elif args.seed is None:
        args.seed = 0

    if args.selftest:
        from datasets.generate_rollouts import gen
        from world_model.training import train

        data = gen(8, 90, seed=3, worlds=("classic", "dense", "moving"))
        ckpt, m = train(data, epochs=2, batch=64, seed=0)
        import os
        import tempfile

        path = os.path.join(tempfile.mkdtemp(), "wm_probe_selftest.pth")
        torch.save(ckpt, path)
        r = evaluate(path, data, seed=0)
        # the probe must agree with training's own val computation: same
        # split (seed), same heads -> same AUC@32 to float precision
        assert abs(r["auc_h"][-1] - m["auc"][-1]) < 1e-4, "probe drifted from train"
        assert 0.0 <= r["now_auc"] <= 1.0 and r["n_val_samples"] > 0
        print(
            f"WM-PROBE OK: probe AUC@32={r['auc_h'][-1]:.4f} == "
            f"train val {m['auc'][-1]:.4f}, veer widened n={r['veer_all'][1]}"
        )
        return

    if not args.ckpt:
        raise SystemExit("--ckpt required (or --selftest)")
    blob = np.load(args.data)
    data = {k: blob[k] for k in blob.files}
    r = evaluate(args.ckpt, data, seed=args.seed)
    h_str = "/".join(str(k) for k in HORIZONS)
    w_str = " ".join(f"{k}={v:.4f}" for k, v in r["auc_by_world"].items())
    sv, nv = r["veer_val"]
    sa, na = r["veer_all"]
    print(
        f"WM-PROBE OK: {args.ckpt}\n"
        f"  val samples={r['n_val_samples']} (rollouts {r['va_rolls']})\n"
        f"  AUC@{h_str}=" + "/".join(f"{a:.4f}" for a in r["auc_h"]) + "\n"
        f"  AUC@32 by world: {w_str}\n"
        f"  now-AUC={r['now_auc']:.4f}\n"
        f"  veer: val {sv:.4f} (n={nv}) | widened-all {sa:.4f} (n={na})"
    )


if __name__ == "__main__":
    main()
    sys.exit(0)

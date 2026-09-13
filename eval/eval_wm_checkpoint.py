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

For a dataset generated independently of ALL compared checkpoints, use
--independent-holdout to score every rollout on the same exam, regardless
of training seed. Known exact training-file reuse is rejected by SHA-256.
This flag still asserts independently generated rollouts: missing/different
file hashes cannot exclude overlap from subsets or repacking.
--out records provenance; --scores-out saves aligned per-sample scores
for paired, rollout-level uncertainty analysis. Neither mode changes gates.

Honest limit: the latent-MSE-vs-no-op check is *not* recomputable here —
the JEPA target is the EMA encoder, which checkpoints do not persist. That
claim is read off the training log, where it is printed at k=32.

Run:
  python -m eval.eval_wm_checkpoint --ckpt experiments/.../wm_m1_ground.pth
  python -m eval.eval_wm_checkpoint --selftest
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch

from datasets.generate_rollouts import OUT as DATA
from datasets.intervention_labels import HORIZONS
from datasets.provenance import file_identity as _file_identity
from datasets.provenance import reject_training_file
from planner.action_set import A_NORM
from sim.scenarios import DANGER_R
from world_model.losses import roc_auc
from world_model.metrics import AUC_METHOD
from world_model.training import (
    _index_samples,
    _split_rollouts,
    load_model,
    veer_ranking,
)


def evaluate(
    ckpt_path: str,
    data: dict,
    seed: int | None = None,
    *,
    independent_holdout: bool = False,
    sample_output: dict | None = None,
    device: str | None = None,
    dataset_sha256: str | None = None,
) -> dict:
    """Rebuild the seed-`seed` train/val split and score the checkpoint:
    per-world AUC@32, overall AUC per horizon, danger-now AUC (all at val),
    and veer-ranking on val rollouts + widened to all rollouts. File callers
    should pass dataset_sha256 for the known-training-file rejection. An
    in-memory dict alone carries no verifiable file identity."""
    device = device or ("mps" if torch.backends.mps.is_available() else "cpu")
    enc, pred, cheads, nhead, meta = load_model(ckpt_path, device)
    if independent_holdout:
        reject_training_file(meta.get("training_dataset_sha256"), dataset_sha256)
    seed = _evaluation_seed(meta.get("seed"), seed, independent_holdout)
    result = evaluate_components(
        enc,
        pred,
        cheads,
        nhead,
        data,
        seed,
        device,
        frame_stride=int(meta.get("frame_stride", 4)),
        independent_holdout=independent_holdout,
        sample_output=sample_output,
    )
    result["training_seed"] = meta.get("seed")
    result["checkpoint_meta"] = meta
    result["runtime"] = {
        "device": device,
        "torch": str(torch.__version__),
        "numpy": np.__version__,
    }
    return result


def _json_ready(value):
    """Missing veer probes are null in JSON, never a fabricated score or NaN."""
    if isinstance(value, dict):
        return {k: _json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(v) for v in value]
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def _evaluation_seed(training_seed, requested_seed, independent_holdout):
    if independent_holdout:
        if requested_seed is not None:
            raise ValueError("--seed is incompatible with --independent-holdout")
        return 0  # ignored: every independent rollout is scored
    if training_seed is not None:
        if requested_seed is not None and int(requested_seed) != int(training_seed):
            raise ValueError(
                f"--seed {requested_seed} contradicts checkpoint training seed "
                f"{training_seed}; a changed training-data split leaks train rollouts"
            )
        return int(training_seed)
    if requested_seed is None:
        print(
            "[wm-probe] WARNING: no checkpoint training seed; using seed 0. "
            "Training-data validation may overlap training rollouts.",
            file=sys.stderr,
        )
    return 0 if requested_seed is None else int(requested_seed)


def evaluate_components(
    enc,
    pred,
    cheads,
    nhead,
    data,
    seed=0,
    device="cpu",
    frame_stride=4,
    *,
    independent_holdout=False,
    sample_output=None,
):
    """The same scoring loop on already-loaded modules — the seam through
    which candidate/quantized components are graded on the identical split
    without any checkpoint swap (int8_parity_v1). `evaluate` is a thin
    load_model wrapper around this; the selftest's probe==train-val assert
    guards both."""
    tgru = getattr(enc, "temporal", None)

    rng = np.random.default_rng(seed)
    idx, c_h = _index_samples(data)
    R, L = data["frames"].shape[:2]
    if independent_holdout:
        va_rolls = list(range(R))
    else:
        _tr_rolls, va_rolls = _split_rollouts(data, rng)
    if idx.size == 0:
        raise ValueError("dataset has no valid held-command prediction windows")
    va = np.where(np.isin(idx[:, 0], va_rolls))[0]
    if len(va) == 0:
        raise ValueError("evaluation split has no valid prediction windows")

    # two-frame checkpoints (in_ch=6) get the same stacked input the
    # training side builds: current frame + the clamped previous frame
    in_frames = int(enc.features[0].in_channels) // 3
    stride = int(frame_stride)

    def frames_at(pairs):  # (n,2) [r,t] -> (n,C,H,W) float on device
        x = np.stack([data["frames"][r, t] for r, t in pairs])
        if in_frames == 2:
            xp = np.stack([data["frames"][r, max(t - stride, 0)] for r, t in pairs])
            x = np.concatenate([x, xp], axis=-1)
        x = torch.tensor(x, dtype=torch.float32, device=device)
        return x.permute(0, 3, 1, 2) / 255.0

    with torch.no_grad():
        scores = []
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
    label_counts_by_world = {}
    if "world_id" in data:
        wn = (
            [str(x) for x in np.asarray(data["world_names"])]
            if "world_names" in data
            else ["classic", "dense", "moving"]
        )
        sw = np.asarray(data["world_id"])[idx[va][:, 0]]
        for w in sorted({int(x) for x in sw}):
            m = sw == w
            name = wn[w] if w < len(wn) else str(w)
            positive = int(c_h[va][m][:, -1, 0].sum())
            label_counts_by_world[name] = {
                "positive": positive,
                "negative": int(m.sum()) - positive,
            }
            if int(m.sum()) >= 20:
                auc_by_world[name] = roc_auc(scores[m][:, -1], c_h[va][m][:, -1, 0])
    side_val, n_val = veer_ranking(
        data,
        va_rolls,
        enc,
        pred,
        cheads,
        device,
        in_frames=in_frames,
        frame_stride=stride,
    )
    veer_samples = {}
    side_all, n_all = veer_ranking(
        data,
        range(R),
        enc,
        pred,
        cheads,
        device,
        in_frames=in_frames,
        frame_stride=stride,
        sample_output=veer_samples,
    )
    if sample_output is not None:
        sample_output.update(veer_samples)
        sample_output.update(
            pairs=idx[va].copy(),
            scores=scores.copy(),
            labels=c_h[va, :, 0].copy(),
            world_id=np.asarray(data.get("world_id", np.zeros(R, dtype=int)))[
                idx[va, 0]
            ],
            world_names=np.asarray(
                data.get("world_names", ["classic", "dense", "moving"])
            ),
            horizons=np.asarray(HORIZONS),
        )
    return {
        "auc_h": auc_h,
        "auc_by_world": auc_by_world,
        "label_counts_by_world": label_counts_by_world,
        "label_counts_h": [
            {"positive": int(p), "negative": int(len(va) - p)}
            for p in c_h[va, :, 0].sum(axis=0)
        ],
        "now_auc": roc_auc(now_scores, now_lbl),
        "now_label_counts": {
            "positive": int(now_lbl.sum()),
            "negative": int(len(now_lbl) - now_lbl.sum()),
        },
        "veer_val": (side_val, n_val),
        "veer_all": (side_all, n_all),
        "veer_rollouts": int(len(np.unique(veer_samples["veer_pairs"][:, 0]))),
        "n_val_samples": int(len(va)),
        "va_rolls": list(map(int, va_rolls)),
        "split": "independent_holdout_all" if independent_holdout else "training_val",
        "split_seed": None if independent_holdout else int(seed),
        "auc_method": AUC_METHOD,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default=None)
    ap.add_argument("--data", default=DATA)
    ap.add_argument("--seed", type=int, default=None, help="the training run's seed")
    ap.add_argument(
        "--independent-holdout",
        action="store_true",
        help="assert data is disjoint from every compared model's training; score all",
    )
    ap.add_argument("--out", help="write metrics and file hashes to a NEW JSON file")
    ap.add_argument("--scores-out", help="write paired sample scores to a NEW NPZ file")
    ap.add_argument("--device", choices=("cpu", "mps"), default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        from datasets.generate_rollouts import gen
        from world_model.training import train

        data = gen(8, 90, seed=3, worlds=("classic", "dense", "moving"))
        assert np.std(data["frames"]) > 1, "vision selftest frames are blank"
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
        sample_a, sample_b = {}, {}
        modules = load_model(path, "cpu")[:4]
        a = evaluate_components(
            *modules, data, seed=0, independent_holdout=True, sample_output=sample_a
        )
        b = evaluate_components(
            *modules, data, seed=19, independent_holdout=True, sample_output=sample_b
        )
        assert _json_ready(a) == _json_ready(b), "holdout exam drifted"
        for world, support in m["label_counts_by_world"].items():
            assert {key: support[key] for key in ("positive", "negative")} == r[
                "label_counts_by_world"
            ][world], "train/probe label support differs"
            assert support["auc_defined"] == (
                support["positive"] > 0 and support["negative"] > 0
            )
        assert a["va_rolls"] == list(range(8))
        assert _json_ready((float("nan"), 0)) == [None, 0]
        json.dumps(_json_ready(a), allow_nan=False)
        assert np.array_equal(sample_a["pairs"], sample_b["pairs"])
        assert np.array_equal(sample_a["scores"], sample_b["scores"])
        for key in ("veer_pairs", "veer_gt_left", "veer_correct", "veer_world_id"):
            assert np.array_equal(sample_a[key], sample_b[key]), key
        assert len(sample_a["veer_correct"]) == a["veer_all"][1]
        if a["veer_all"][1]:
            assert np.isclose(sample_a["veer_correct"].mean(), a["veer_all"][0])
        assert a["veer_rollouts"] == len(np.unique(sample_a["veer_pairs"][:, 0]))
        assert _evaluation_seed(19, None, False) == 19
        for meta_seed, supplied_seed, holdout in ((19, 0, False), (19, 0, True)):
            try:
                _evaluation_seed(meta_seed, supplied_seed, holdout)
            except ValueError:
                pass
            else:
                raise AssertionError("conflicting split request accepted")
        assert _evaluation_seed(19, None, True) == 0
        # Exercise the optional recipe through optimization and checkpoint
        # serialization. This is a wiring test, not a performance comparison.
        assert ckpt["meta"]["cf_hard_pool"] == "legacy_masked"
        candidate, cm = train(
            data, epochs=2, batch=64, seed=0, cf_hard_pool="answerable"
        )
        candidate_path = os.path.join(
            os.path.dirname(path), "wm_answerable_selftest.pth"
        )
        torch.save(candidate, candidate_path)
        assert load_model(candidate_path, "cpu")[4]["cf_hard_pool"] == "answerable"
        assert (m["n_train"], m["n_val"]) == (cm["n_train"], cm["n_val"])
        assert cm["cf_hard_pool_frames"] <= m["cf_hard_pool_frames"]
        assert cm["cf_hard_pool_fallback"] == (cm["cf_hard_pool_frames"] == 0)
        cr = evaluate(candidate_path, data)
        assert np.isfinite(cr["now_auc"])
        print(
            f"WM-PROBE OK: probe AUC@32={r['auc_h'][-1]:.4f} == "
            f"train val {m['auc'][-1]:.4f}, veer widened n={r['veer_all'][1]}"
        )
        return

    if not args.ckpt:
        raise SystemExit("--ckpt required (or --selftest)")
    outputs = [Path(p).resolve() for p in (args.out, args.scores_out) if p]
    if len(set(outputs)) != len(outputs) or any(p.exists() for p in outputs):
        raise SystemExit("output paths must be distinct and new; preserve old records")
    sources = (("checkpoint", args.ckpt), ("dataset", args.data))
    provenance = {name: _file_identity(path) for name, path in sources}
    with np.load(args.data) as blob:
        data = {k: blob[k] for k in blob.files}
    samples = {} if args.scores_out else None
    try:
        r = evaluate(
            args.ckpt,
            data,
            seed=args.seed,
            independent_holdout=args.independent_holdout,
            sample_output=samples,
            device=args.device,
            dataset_sha256=provenance["dataset"]["sha256"],
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if provenance != {name: _file_identity(path) for name, path in sources}:
        raise SystemExit(
            "checkpoint or dataset changed during evaluation; no record saved"
        )
    r["provenance"] = provenance
    record = _json_ready(r)
    for p in outputs:
        p.parent.mkdir(parents=True, exist_ok=True)
    if args.scores_out:
        with open(args.scores_out, "xb") as stream:
            np.savez_compressed(
                stream, **samples, metadata=json.dumps(record, allow_nan=False)
            )
    if args.out:
        with open(args.out, "x") as stream:
            json.dump(record, stream, indent=2, allow_nan=False)
            stream.write("\n")
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

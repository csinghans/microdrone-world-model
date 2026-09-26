"""Audit available supervision in saved rollout metadata; never fit/score a WM.

    python -m eval.eval_dataset_support --data corpus.npz --out new.json
    python -m eval.eval_dataset_support --selftest

Uses the training index, split and CF oracle. Pixels are not loaded: this
is a metadata audit of an already verified corpus. Sampler exposure is an
expectation, not observed draws or a gradient-contribution estimate.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from datasets.intervention_labels import HORIZONS, counterfactual_labels
from planner.action_set import ACTION_NAMES, ACTION_VECS
from planner.nav_action_set import NAV_ACTION_NAMES, NAV_ACTION_VECS
from world_model.checkpoint_io import check_destination, publish_checkpoint
from world_model.training import _index_samples, _split_rollouts


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def sampler_masks(labels, visible):
    """Current zero-masked hard pool versus answerable candidate contrast."""
    labels = np.asarray(labels, dtype=np.int8)
    weighted = labels * visible[..., None, None]
    current = (weighted.max(axis=2) != weighted.min(axis=2)).any(axis=(2, 3))
    high = np.where(visible[..., None, None], labels, -1).max(axis=2)
    low = np.where(visible[..., None, None], labels, 2).min(axis=2)
    answerable = (high > low).any(axis=(2, 3))
    return current, answerable


def label_support(labels, rolls):
    labels, rolls = np.asarray(labels), np.asarray(rolls)
    positive, negative = labels == 1, labels == 0
    if not (positive | negative).all():
        raise ValueError("nonbinary label")
    return {
        "positive": int(positive.sum()),
        "negative": int(negative.sum()),
        "positive_rollouts": int(len(np.unique(rolls[positive]))),
        "negative_rollouts": int(len(np.unique(rolls[negative]))),
        "auc_defined": bool(positive.any() and negative.any()),
    }


def partition(data, pairs, labels, cf, visible, selected, batch, epochs):
    length = data["dists"].shape[1]
    selected = np.asarray(selected, dtype=int)
    in_split = np.isin(pairs[:, 0], selected)
    selected_pairs, selected_labels = pairs[in_split], labels[in_split]
    current, answerable = sampler_masks(cf, visible)
    hard_count = int(current[selected].sum())
    all_frames = len(selected) * length
    n_windows = len(selected_pairs)
    batches = [min(batch, n_windows - i) for i in range(0, n_windows, batch)]
    half_draws = sum(max(1, n // 2) for n in batches)
    rows = {}
    for wid in np.unique(data["world_id"][selected]):
        world = str(data["world_names"][wid])
        if world not in ("classic", "dense", "moving", "room"):
            raise ValueError(f"no action-catalog mapping registered for {world}")
        rolls = selected[data["world_id"][selected] == wid]
        mask = np.isin(selected_pairs[:, 0], rolls)
        wp, wy = selected_pairs[mask], selected_labels[mask]
        names, vectors = (
            (NAV_ACTION_NAMES, NAV_ACTION_VECS)
            if world == "room"
            else (ACTION_NAMES, ACTION_VECS)
        )
        ids = data["act_id"][rolls]
        if (ids < 0).any() or (ids >= len(names)).any():
            raise ValueError(f"invalid action id in {world}")
        expected = data["speed"][rolls, None, None] * vectors[ids]
        if not np.allclose(expected, data["actions"][rolls], rtol=1e-5, atol=1e-6):
            raise ValueError(f"{world}: ids do not match recorded physical commands")
        actions = {}
        wp_ids = data["act_id"][wp[:, 0], wp[:, 1]]
        for aid in np.unique(wp_ids):
            use = wp_ids == aid
            actions[names[aid]] = {
                "windows": int(use.sum()),
                **label_support(wy[use, -1, 0], wp[use, 0]),
            }
        world_hard = int(current[rolls].sum())
        frame_share = len(rolls) * length / all_frames if all_frames else 0
        hard_share = world_hard / hard_count if hard_count else frame_share
        visible_mask = visible[rolls].astype(bool)
        cf_warn = cf[rolls, :, :, -1, 0]
        rows[world] = {
            "rollout_ids": rolls.tolist(),
            "rollouts": len(rolls),
            "passive_rollouts": int((data["seg"][rolls].max(axis=1) == 0).sum()),
            "rollouts_with_actual_action_changes": int(
                (np.diff(ids, axis=1) != 0).any(axis=1).sum()
            ),
            "frames": len(rolls) * length,
            "valid_windows": len(wp),
            "eligible_fraction": len(wp) / (len(rolls) * (length - HORIZONS[-1])),
            "executed_window_share": len(wp) / n_windows if n_windows else 0,
            "labels_at_32": label_support(wy[:, -1, 0], wp[:, 0]),
            "now_labels": label_support(
                (data["dists"][rolls].ravel() < float(data["danger_r"])).astype(int),
                np.repeat(rolls, length),
            ),
            "actions": actions,
            "counterfactual": {
                "visible_frame_candidates": int(visible_mask.sum()),
                "positive_at_32": int(cf_warn[visible_mask].sum()),
                "negative_at_32": int((1 - cf_warn[visible_mask]).sum()),
                "current_hard_frames": world_hard,
                "answerable_contrast_frames": int(answerable[rolls].sum()),
                "hard_without_answerable_contrast": int(
                    (current[rolls] & ~answerable[rolls]).sum()
                ),
                "expected_sampled_frames_per_epoch": half_draws
                * (frame_share + hard_share),
            },
        }
    return {
        "rollouts": len(selected),
        "valid_windows": n_windows,
        "nominal_optimizer_steps_per_epoch": math.ceil(n_windows / batch),
        "nominal_optimizer_steps_total": epochs * math.ceil(n_windows / batch),
        "nominal_executed_window_presentations_total": epochs * n_windows,
        "cf_draws_per_half_per_epoch": half_draws,
        "hard_pool_falls_back_to_all_frames": hard_count == 0,
        "worlds": rows,
    }


def analyze(data, seeds=(0, 1, 2), batch=64, epochs=80, holdout=False):
    if batch < 1 or epochs < 1 or len(set(seeds)) != len(seeds):
        raise ValueError("positive batch/epochs and distinct seeds required")
    if list(data["horizons"]) != list(HORIZONS):
        raise ValueError("dataset horizons differ from active oracle")
    if data["dists"].shape[1] <= HORIZONS[-1]:
        raise ValueError("rollouts too short for horizon 32")
    pairs, labels = _index_samples(data)
    if len(pairs) == 0:
        raise ValueError("no eligible held-command windows")
    cf, visible = counterfactual_labels(data)
    args = (data, pairs, labels, cf, visible)
    result = {
        "schema_version": 1,
        "target": f"executed_warn_at_{HORIZONS[-1]}",
        "scope": "Metadata/label audit, not a causal test or pass/fail gate. "
        "Only train partitions describe recorded optimization. All/val step "
        "counts are hypothetical. CF frame expectations also describe now-head "
        "sampling; not observed draws or gradient weights (CF normalizes by "
        "each batch's visible labels).",
        "horizons": list(HORIZONS),
        "batch": batch,
        "epochs": epochs,
        "all": partition(*args, range(len(data["world_id"])), batch, epochs),
        "splits": {},
    }
    if not holdout:
        for seed in seeds:
            train, val = _split_rollouts(data, np.random.default_rng(seed))
            result["splits"][str(seed)] = {
                "train": partition(*args, train, batch, epochs),
                "val": partition(*args, val, batch, epochs),
            }
    return result


def load_metadata(path):
    with np.load(path, allow_pickle=False) as blob:
        data = {key: blob[key] for key in blob.files if key != "frames"}
    r, length = data["dists"].shape
    # The oracle/index need only dimensions. Never feed this shape-only
    # stand-in to a model or present it as a rendered frame.
    data["frames"] = np.empty((r, length, 0, 0, 3), dtype=np.uint8)
    return data


def selftest():
    from datasets.combine_rollouts import _synth

    cf = np.ones((1, 3, 6, 4, 2), dtype=np.uint8)
    vis = np.ones((1, 3, 6), dtype=np.uint8)
    vis[0, 0, 0] = 0  # masking creates a false contrast
    cf[0, 1, 0] = 0  # two answerable labels truly disagree
    vis[0, 2] = 0  # no oracle support, e.g. room
    current, real = sampler_masks(cf, vis)
    assert current.tolist() == [[True, True, False]]
    assert real.tolist() == [[False, True, False]]
    data = _synth([0] * 6, length=40)
    data["actions"][:] = ACTION_VECS[0]
    data["dists"][:3] = 0.1
    data["seg"][0, 20:] = 2  # no held 32-step window in this rollout
    result = analyze(data, seeds=(0,), batch=7, epochs=2)
    assert result["all"]["valid_windows"] == 40
    row = result["all"]["worlds"]["classic"]
    assert row["actions"]["forward"]["windows"] == 40
    assert row["labels_at_32"]["positive"] == 16
    split = result["splits"]["0"]
    assert split["train"]["valid_windows"] + split["val"]["valid_windows"] == 40
    assert not label_support(np.ones(8), np.zeros(8))["auc_defined"]
    room = _synth([0] * 3, length=40, nan_pillars=True)
    room["world_names"] = np.array(["room"])
    room["act_id"][:] = 1  # room reverse, not transit slow
    room["actions"][:] = NAV_ACTION_VECS[1]
    rr = analyze(room, holdout=True)["all"]["worlds"]["room"]
    assert set(rr["actions"]) == {"reverse"}
    assert rr["counterfactual"]["visible_frame_candidates"] == 0
    assert rr["counterfactual"]["current_hard_frames"] == 0
    json.dumps(result, allow_nan=False)
    print(
        "DATASET-SUPPORT OK: windows/splits, classless labels, "
        "action catalogs, masked contrast"
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data")
    ap.add_argument("--out")
    ap.add_argument("--seeds", default="0,1,2")
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--epochs", type=int, default=80)
    ap.add_argument("--independent-holdout", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    if not args.data or not args.out:
        ap.error("--data and a new --out are required")
    try:
        output = check_destination(args.out)
    except (OSError, ValueError) as exc:
        ap.error(str(exc))
    root = Path(__file__).resolve().parents[1]
    sources = [
        Path(__file__),
        root / "world_model/training.py",
        root / "datasets/intervention_labels.py",
        root / "planner/action_set.py",
        root / "planner/nav_action_set.py",
        root / "sim/envs.py",
        root / "sim/scenarios.py",
        root / "world_model/checkpoint_io.py",
    ]
    source_hashes = {str(p): digest(p) for p in sources}
    identity = {"path": str(Path(args.data).resolve()), "sha256": digest(args.data)}
    result = analyze(
        load_metadata(args.data),
        seeds=tuple(int(s) for s in args.seeds.split(",")),
        batch=args.batch,
        epochs=args.epochs,
        holdout=args.independent_holdout,
    )
    result["provenance"] = {
        "dataset": identity,
        "sources": source_hashes,
        "numpy": np.__version__,
    }
    payload = (json.dumps(result, indent=2, allow_nan=False) + "\n").encode()
    if digest(args.data) != identity["sha256"]:
        raise RuntimeError("dataset changed during audit")
    if any(digest(p) != expected for p, expected in source_hashes.items()):
        raise RuntimeError("source changed during audit")
    publish_checkpoint(output, lambda stream: stream.write(payload))
    print(f"DATASET-SUPPORT OK: {output}")


if __name__ == "__main__":
    main()

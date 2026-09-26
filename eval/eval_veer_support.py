"""Count geometric veer support before fitting, without reading pixels/models.

    python -m eval.eval_veer_support --data exam.npz --out preflight.json
    python -m eval.eval_veer_support --selftest

All rollouts are inspected. Freeze this accounting and the intended support
requirements before training. It neither certifies rendered visibility nor
sets a promotion gate. An optional --check-export checks selection parity
with a saved independent-exam export, without rescoring either checkpoint.
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from datasets.provenance import file_identity
from world_model.checkpoint_io import check_destination, publish_checkpoint
from world_model.veer_probe import select

METADATA = (
    "act_id",
    "pillars",
    "pillar_vel",
    "pos",
    "speed",
    "world_id",
    "world_names",
)
PROBE_KEYS = ("veer_pairs", "veer_gt_left", "veer_world_id")


def load_metadata(path):
    with np.load(path, allow_pickle=False) as blob:
        return {key: blob[key] for key in METADATA if key in blob.files}


def names_for(data):
    return np.asarray(data.get("world_names", ["classic", "dense", "moving"]))


def analyze(data):
    """Exactly the scorer's geometric selection, with zero-support worlds shown."""
    sample = select(data)
    pairs, ids = sample["veer_pairs"], sample["veer_world_id"]
    names = names_for(data)
    if len(set(map(str, names))) != len(names):
        raise ValueError("duplicate world names")
    all_ids = np.asarray(data.get("world_id", np.zeros(len(data["act_id"]), dtype=int)))
    if (
        not np.issubdtype(all_ids.dtype, np.integer)
        or not np.isin(all_ids, np.arange(len(names))).all()
    ):
        raise ValueError("world ids must index the world catalog")
    rows = {}
    for wid, name in enumerate(names):
        mask = ids == wid
        rolls, counts = np.unique(pairs[mask, 0], return_counts=True)
        rows[str(name)] = {
            "available_rollouts": int((all_ids == wid).sum()),
            "frames": int(mask.sum()),
            "rollouts": len(rolls),
            "rollout_ids": rolls.tolist(),
            "frames_per_rollout": counts.tolist(),
        }
    active = [w for w, row in rows.items() if row["frames"]]
    singletons = [w for w in active if rows[w]["rollouts"] < 2]
    reason = (
        "no eligible veer probe frames"
        if not len(pairs)
        else "fewer than two probe rollouts in a world stratum" if singletons else None
    )
    identity = hashlib.sha256()
    for key, dtype in zip(PROBE_KEYS, ("<i8", "?", "<i8")):
        value = np.asarray(sample[key], dtype=dtype)
        identity.update(f"{key}:{value.shape}:{dtype}".encode())
        identity.update(value.tobytes())
    return {
        "scope": "Metadata-only support accounting on all rollouts, using the "
        "scorer's unchanged yaw-zero pillar geometry. No pixels, fitting, model "
        "scoring, bootstrap or promotion verdict. Does not verify rendering "
        "or prove that courses are independently generated.",
        "available_rollouts": len(data["act_id"]),
        "n_frames": len(pairs),
        "n_rollouts": len(np.unique(pairs[:, 0])),
        "by_world": rows,
        "selection_sha256": identity.hexdigest(),
        "world_stratified_bootstrap_support": {
            "supported": reason is None,
            "reason": reason,
            "singleton_worlds": singletons,
            "zero_support_worlds": [w for w, row in rows.items() if not row["frames"]],
            "scope": "Matches compare_wm_scores' minimum of two courses in each "
            "observed stratum. Zero-support worlds are excluded, not validated. "
            "This is a structural minimum, not a power/precision guarantee.",
        },
    }, sample


def check_export(path, sample, names, dataset_sha256):
    before = file_identity(path)
    with np.load(path, allow_pickle=False) as blob:
        metadata = json.loads(str(blob["metadata"]))
        if metadata["provenance"]["dataset"]["sha256"] != dataset_sha256:
            raise ValueError("export belongs to a different dataset")
        if metadata["split"] != "independent_holdout_all":
            raise ValueError("export is not an all-rollout independent exam")
        for key in PROBE_KEYS:
            if not np.array_equal(blob[key], sample[key]):
                raise ValueError(f"geometric selection differs from export: {key}")
        if not np.array_equal(blob["world_names"], names):
            raise ValueError("export world catalog differs")
    if file_identity(path) != before:
        raise ValueError("export changed during audit")
    return before


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data")
    ap.add_argument("--out")
    ap.add_argument("--check-export", action="append", default=[])
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
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
    sources = (
        "eval/eval_veer_support.py",
        "world_model/veer_probe.py",
        "world_model/training.py",
        "datasets/intervention_labels.py",
        "planner/action_set.py",
        "sim/envs.py",
        "sim/scenarios.py",
        "datasets/provenance.py",
        "eval/compare_wm_scores.py",
        "world_model/checkpoint_io.py",
    )
    source_hashes = {p: file_identity(root / p)["sha256"] for p in sources}
    source = file_identity(args.data)
    data = load_metadata(args.data)
    result, sample = analyze(data)
    exports = [
        check_export(path, sample, names_for(data), source["sha256"])
        for path in args.check_export
    ]
    result["provenance"] = {
        "dataset": source,
        "matched_exports": exports,
        "sources": source_hashes,
        "numpy": np.__version__,
    }
    payload = (json.dumps(result, indent=2, allow_nan=False) + "\n").encode()
    if file_identity(args.data) != source:
        raise ValueError("dataset changed during audit")
    if any(file_identity(row["path"]) != row for row in exports):
        raise ValueError("checked export changed during audit")
    if any(
        file_identity(root / p)["sha256"] != digest
        for p, digest in source_hashes.items()
    ):
        raise ValueError("source changed during audit")
    publish_checkpoint(output, lambda stream: stream.write(payload))
    support = result["world_stratified_bootstrap_support"]
    print(
        f"VEER-SUPPORT OK: {result['n_frames']} frames / {result['n_rollouts']} "
        f"courses; bootstrap support={support['supported']}; {output}"
    )
    if support["reason"]:
        print(f"[INFO] {support['reason']}")


def selftest():
    import tempfile

    from world_model.veer_probe import fixture

    data = fixture()
    result, sample = analyze(data)
    assert result["n_frames"] == 4 and result["n_rollouts"] == 2
    support = result["world_stratified_bootstrap_support"]
    assert not support["supported"]
    assert support["singleton_worlds"] == ["classic", "dense"]
    assert support["zero_support_worlds"] == ["moving", "room"]
    doubled = {
        k: np.concatenate([v, v]) if k != "world_names" else v for k, v in data.items()
    }
    assert analyze(doubled)[0]["world_stratified_bootstrap_support"]["supported"]
    empty = dict(data, pillars=np.full_like(data["pillars"], np.nan))
    result0, _ = analyze(empty)
    assert result0["n_frames"] == result0["n_rollouts"] == 0
    assert result0["world_stratified_bootstrap_support"]["reason"] == (
        "no eligible veer probe frames"
    )
    with tempfile.TemporaryDirectory(prefix="veer_support_selftest_") as tmp:
        path, export, out = (
            Path(tmp) / n for n in ("data.npz", "scores.npz", "out.json")
        )
        # Accessing this object-valued frame payload with allow_pickle=False
        # would fail: the preflight must never read it or treat it as pixels.
        np.savez(path, **data, frames=np.array([object()], dtype=object))
        metadata = {
            "split": "independent_holdout_all",
            "provenance": {"dataset": file_identity(path)},
        }
        np.savez(
            export,
            **sample,
            world_names=data["world_names"],
            metadata=np.array(json.dumps(metadata)),
        )
        main(["--data", str(path), "--out", str(out), "--check-export", str(export)])
        assert (
            json.loads(out.read_text())["selection_sha256"]
            == result["selection_sha256"]
        )
        before = out.read_bytes()
        try:
            main(["--data", str(path), "--out", str(out)])
        except SystemExit as exc:
            assert exc.code == 2
        else:
            raise AssertionError("overwrote a support record")
        assert out.read_bytes() == before
        bad = dict(sample, veer_gt_left=~sample["veer_gt_left"])
        try:
            check_export(
                export, bad, data["world_names"], file_identity(path)["sha256"]
            )
        except ValueError as exc:
            assert "veer_gt_left" in str(exc)
        else:
            raise AssertionError("changed geometric truth accepted")
    print("VEER-SUPPORT SELFTEST OK: no pixel reads, support, identity, no overwrite")


if __name__ == "__main__":
    main()

"""Fixed-checkpoint raw veer replay: --selftest, --run, or --verify."""

import argparse
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import torch

from eval.compare_wm_scores import _load, _validate
from eval.eval_dataset_support import load_metadata
from scripts.schedule_layout_study import read, sha, verify_files, write_new
from world_model.training import load_model, veer_ranking
from world_model.veer_probe import select

ROOT = Path(__file__).resolve().parents[2]
FOLDER = Path(__file__).resolve().parent
OLD_KEYS = ("veer_pairs", "veer_world_id", "veer_gt_left", "veer_correct")
SCORE_KEYS = ("veer_score_left", "veer_score_right")


def identity(config):
    inputs = {str(ROOT / p): h for p, h in config["inputs"].items()}
    verify_files(inputs)
    verify_files(config["protected"])
    paths = subprocess.check_output(
        ["git", "ls-files", "*.py", "environment.yml", "artifacts.lock.json"],
        cwd=ROOT,
        text=True,
    ).splitlines()
    sources = {str(ROOT / p): sha(ROOT / p) for p in paths}
    for name in ("replay.py", "registration.json", "definition.md"):
        sources[str(FOLDER / name)] = sha(FOLDER / name)
    return {
        "inputs": inputs,
        "protected": config["protected"],
        "sources": sources,
        "runtime": {
            "python": sys.version,
            "numpy": np.__version__,
            "torch": torch.__version__,
            "platform": platform.platform(),
            "threads": torch.get_num_threads(),
            "interop_threads": torch.get_num_interop_threads(),
            "device": config["device"],
        },
    }


def require_equal(old, new, keys):
    for key in keys:
        if not np.array_equal(old[key], new[key]):
            raise ValueError(f"instrument mismatch: {key}")


def count_preferences(truth, left, right):
    truth, left, right = map(np.asarray, (truth, left, right))
    if truth.ndim != 1 or left.shape != truth.shape or right.shape != truth.shape:
        raise ValueError("aligned one-dimensional scores required")
    if not np.isin(truth, [0, 1]).all():
        raise ValueError("binary truth required")
    for value in (left, right):
        if (
            value.dtype.kind not in "fiu"
            or not np.isfinite(value).all()
            or ((value < 0) | (value > 1)).any()
        ):
            raise ValueError("finite probabilities required")

    def counts(mask):
        return {
            "frames": int(mask.sum()),
            "strict_left": int((mask & (left < right)).sum()),
            "strict_right": int((mask & (right < left)).sum()),
            "exact_tie": int((mask & (left == right)).sum()),
        }

    result = counts(np.ones(len(truth), dtype=bool))
    result["truth_sides"] = {
        "safer_left": counts(truth.astype(bool)),
        "safer_right": counts(~truth.astype(bool)),
    }
    assert sum(result[k] for k in ("strict_left", "strict_right", "exact_tie")) == len(
        truth
    )
    return result


def load_raw(path):
    with np.load(path, allow_pickle=False) as blob:
        return {k: blob[k] for k in blob.files}


def analyze(config, data, selected):
    rows, hashes = [], {}
    for model in config["models"]:
        old = _load(ROOT / model["old_export"])
        path = FOLDER / "artifacts" / f"{model['name']}.npz"
        raw = load_raw(path)
        if set(raw) != set(OLD_KEYS + SCORE_KEYS):
            raise ValueError("unexpected raw export schema")
        require_equal(selected, raw, OLD_KEYS[:3])
        require_equal(old, raw, OLD_KEYS)
        _validate(old, {**old, **raw})
        hashes[str(path)] = sha(path)
        ids = raw["veer_pairs"][:, 0]
        blocks = data["study_timing_block"][ids]
        assert np.isin(blocks, [0, 1]).all()
        for world in config["worlds"]:
            wid = list(data["world_names"]).index(world)
            for block in config["blocks"]:
                mask = raw["veer_world_id"] == wid
                if block != "all":
                    mask &= blocks == (0 if block == "approach" else 1)
                rows.append(
                    {
                        "model": model["name"],
                        "world": world,
                        "block": block,
                        "courses": len(np.unique(ids[mask])),
                        **count_preferences(
                            raw["veer_gt_left"][mask],
                            raw["veer_score_left"][mask],
                            raw["veer_score_right"][mask],
                        ),
                    }
                )
    assert len(rows) == 54
    return {"status": "exact_probe_parity", "cells": rows, "outputs": hashes}


def run(config, current):
    # Manifest and output directory refuse reuse, including after a mismatch.
    write_new(FOLDER / "manifest.json", current)
    (FOLDER / "artifacts").mkdir()
    with np.load(ROOT / config["data"], allow_pickle=False) as blob:
        data = {k: blob[k] for k in blob.files}
    selected = select(data)
    pairs = selected["veer_pairs"]
    assert len(pairs) == 1347 and len(data["act_id"]) == 1440
    stds = np.array([data["frames"][r, t].std() for r, t in pairs])
    frame_check = {
        "frames": len(pairs),
        "minimum_std": float(stds.min()),
        "required_std": config["minimum_frame_std"],
        "dataset_sha256": config["inputs"][config["data"]],
    }
    write_new(FOLDER / "frame_check.json", frame_check)
    assert np.isfinite(stds).all() and (stds > config["minimum_frame_std"]).all()
    for model in config["models"]:
        old = _load(ROOT / model["old_export"])
        _validate(old, old)
        require_equal(old, selected, OLD_KEYS[:3])
        enc, pred, heads, _, meta = load_model(
            str(ROOT / model["checkpoint"]), config["device"]
        )
        assert meta == old["metadata"]["checkpoint_meta"]
        assert not hasattr(enc, "temporal") and int(meta.get("in_frames", 1)) == 1
        sample = {}
        veer_ranking(
            data,
            range(len(data["act_id"])),
            enc,
            pred,
            heads,
            config["device"],
            in_frames=int(meta.get("in_frames", 1)),
            frame_stride=int(meta.get("frame_stride", 4)),
            sample_output=sample,
        )
        # Preserve the measured arrays before enforcing old correctness parity.
        path = FOLDER / "artifacts" / f"{model['name']}.npz"
        with path.open("xb") as stream:
            np.savez_compressed(stream, **sample)
        require_equal(old, sample, OLD_KEYS)
        _validate(old, {**old, **sample})
        print(f"{model['name']}: exact parity on {len(pairs)} frames", flush=True)
    result = analyze(config, data, selected)
    result["frame_check_sha256"] = sha(FOLDER / "frame_check.json")
    assert identity(config) == current
    write_new(FOLDER / "report.json", result)


def verify(config, current):
    assert read(FOLDER / "manifest.json") == current
    report = read(FOLDER / "report.json")
    verify_files(report["outputs"])
    frame_check = read(FOLDER / "frame_check.json")
    assert frame_check["minimum_std"] > config["minimum_frame_std"]
    assert frame_check["dataset_sha256"] == config["inputs"][config["data"]]
    data = load_metadata(ROOT / config["data"])
    selected = select(data)
    assert frame_check["frames"] == len(selected["veer_pairs"])
    result = analyze(config, data, selected)
    result["frame_check_sha256"] = sha(FOLDER / "frame_check.json")
    assert result == report
    assert identity(config) == current


def selftest():
    truth = np.array([True, True, False, False, True, False])
    left = np.array([0.1, 0.8, 0.9, 0.3, 0.5, 0.5])
    right = np.array([0.9, 0.2, 0.1, 0.7, 0.5, 0.5])
    result = count_preferences(truth, left, right)
    assert [
        result[k] for k in ("frames", "strict_left", "strict_right", "exact_tie")
    ] == [
        6,
        2,
        2,
        2,
    ]
    assert all(
        side == {"frames": 3, "strict_left": 1, "strict_right": 1, "exact_tie": 1}
        for side in result["truth_sides"].values()
    )
    assert count_preferences(truth[:0], left[:0], right[:0])["frames"] == 0
    for values in ((truth, left[:-1], right), (truth, left * np.nan, right)):
        try:
            count_preferences(*values)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid score accepted")
    old = {"veer_correct": np.array([True, False])}
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "replay_selftest.npz"
        np.savez_compressed(path, **old)
        require_equal(old, load_raw(path), ("veer_correct",))
    try:
        require_equal(old, {"veer_correct": ~old["veer_correct"]}, ("veer_correct",))
    except ValueError:
        pass
    else:
        raise AssertionError("changed correctness accepted")
    print("VEER REPLAY OK: strict sides, exact ties, truth splits, empty, parity")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    choices = parser.add_mutually_exclusive_group(required=True)
    for flag in ("selftest", "run", "verify"):
        choices.add_argument(f"--{flag}", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return
    config = read(FOLDER / "registration.json")
    current = identity(config)
    try:
        (run if args.run else verify)(config, current)
    except Exception as error:
        if args.run and not (FOLDER / "failure.json").exists():
            write_new(FOLDER / "failure.json", {"instrument_error": repr(error)})
        raise
    finally:
        verify_files(config["protected"])
    print("VEER REPLAY COMPLETE: 6 models, 54 cells; original NO-GO preserved")


if __name__ == "__main__":
    main()

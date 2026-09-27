"""Fixed, exploratory timing-mixture accounting; no fitting or inference.

python -m experiments.timing_mixture_audit_v1.audit --selftest
python -m experiments.timing_mixture_audit_v1.audit --run
python -m experiments.timing_mixture_audit_v1.audit --verify
"""

import argparse
import fcntl
import platform
import sys
from pathlib import Path

import numpy as np

from eval.compare_wm_scores import _load, _validate
from eval.eval_action_auc_audit import link_actions
from eval.eval_dataset_support import load_metadata
from planner.action_set import ACTION_NAMES
from scripts.schedule_layout_study import read, sha, verify_files, write_new
from world_model.auc_decomposition import decompose
from world_model.training import _index_samples

ROOT = Path(__file__).resolve().parents[2]
FOLDER = Path(__file__).resolve().parent
OUT = ROOT / "output/timing_mixture_audit_v1"


def identity(config):
    original = read(ROOT / config["source_folder"] / "manifest.json")
    for key in ("sources", "inputs", "protected"):
        verify_files(original[key])
    inputs = {str(ROOT / p): digest for p, digest in config["inputs"].items()}
    verify_files(inputs)
    sources = [
        FOLDER / name
        for name in ("audit.py", "definition.md", "registration.json", "run.sh")
    ]
    return {
        "sources": {str(p): sha(p) for p in sources},
        "original_sources": original["sources"],
        "inputs": inputs,
        "protected": original["protected"],
        "runtime": {
            "python": sys.version,
            "numpy": np.__version__,
            "platform": platform.platform(),
        },
    }


def validate_blocks(data, config):
    n, room = config["transit_courses_per_block"], config["room_courses"]
    expected = np.repeat([0, 1, 2], [n, n, room])
    actual = data["study_timing_block"]
    if actual.dtype.kind not in "iu" or not np.array_equal(actual, expected):
        raise ValueError("exam timing identities differ from the frozen concatenation")
    names = data["world_names"]
    if names.tolist() != ["classic", "dense", "moving", "room"]:
        raise ValueError("unexpected world catalog")
    for wid in range(3):
        for block in (0, 1):
            count = int(((data["world_id"] == wid) & (actual == block)).sum())
            if count != config["per_world_courses_per_block"]:
                raise ValueError("world/timing block course count differs")
    if not np.array_equal(data["world_id"] == 3, actual == 2):
        raise ValueError("room/timing identity mismatch")


def contrast(a, b, minimum, tolerance):
    if a["groups"] != b["groups"] or a["total_pairs"] != b["total_pairs"]:
        raise ValueError("unmatched label/course support")
    if a["auc"] is None or b["auc"] is None:
        raise ValueError("original action cell lacks a label class")
    rows, within_blocks = [], {}
    for aa, bb in zip(a["pairs"], b["pairs"]):
        for key in (
            "positive_group",
            "negative_group",
            "positive",
            "negative",
            "pairs",
            "weight",
        ):
            if aa[key] != bb[key]:
                raise ValueError("unmatched positive/negative group pair")
        row = {
            key: aa[key]
            for key in (
                "positive_group",
                "negative_group",
                "positive",
                "negative",
                "pairs",
                "weight",
            )
        }
        row.update(
            auc_baseline=aa["auc"],
            auc_candidate=bb["auc"],
            auc_delta=bb["auc"] - aa["auc"] if aa["auc"] is not None else None,
            contribution_delta=bb["contribution"] - aa["contribution"],
        )
        rows.append(row)
        if aa["positive_group"] == aa["negative_group"]:
            name = aa["positive_group"]
            support = a["groups"][name]
            within_blocks[name] = {
                "support": support,
                "meets_original_count_floors_descriptively": all(
                    support[k] >= v for k, v in minimum.items()
                ),
                "auc_baseline": aa["auc"],
                "auc_candidate": bb["auc"],
                "delta": row["auc_delta"],
            }
    within = b["within"]["contribution"] - a["within"]["contribution"]
    across = b["across"]["contribution"] - a["across"]["contribution"]
    delta = b["auc"] - a["auc"]
    error = max(
        abs(delta - within - across),
        abs(delta - sum(r["contribution_delta"] for r in rows)),
    )
    if error > tolerance:
        raise ValueError("timing pair contributions do not reconstruct pooled delta")
    return {
        "auc_baseline": a["auc"],
        "auc_candidate": b["auc"],
        "delta": delta,
        "within_timing_pair_share": a["within"]["share"],
        "across_timing_pair_share": a["across"]["share"],
        "within_contribution_delta": within,
        "across_contribution_delta": across,
        "reconstruction_error": error,
        "blocks": within_blocks,
        "pairs": rows,
    }


def analyze(config):
    data = load_metadata(ROOT / config["data"])
    validate_blocks(data, config)
    expected_pairs, expected_labels = _index_samples(data)
    original = read(ROOT / config["source_folder"] / "report.json")
    assert original["decision"]["verdict"] == "NO-GO"
    assert [p["seed"] for p in original["pairs"]] == config["seeds"]
    results = []
    for seed, old in zip(config["seeds"], original["pairs"]):
        models = []
        for arm in config["arms"]:
            spec = config["models"][f"{arm}/{seed}"]
            export = _load(ROOT / spec["scores"])
            receipt = read(ROOT / spec["receipt"])["result"]["scores"]
            assert export["metadata"] == receipt, "score/receipt metadata differ"
            assert receipt["training_seed"] == seed
            assert (
                receipt["provenance"]["dataset"]["sha256"]
                == config["inputs"][config["data"]]
            )
            assert np.array_equal(export["pairs"], expected_pairs)
            assert np.array_equal(export["labels"], expected_labels[:, :, 0])
            models.append(export)
        _validate(*models)
        cells = {}
        for world, action in config["cells"]:
            values = []
            for export in models:
                mask, actions, rolls = link_actions(export, data, world)
                use = actions == ACTION_NAMES.index(action)
                values.append(
                    decompose(
                        export["scores"][mask, -1][use],
                        export["labels"][mask, -1][use],
                        data["study_timing_block"][rolls[use]],
                        rolls[use],
                        config["blocks"],
                    )
                )
            row = contrast(
                *values,
                config["support_annotation"],
                config["absolute_reconstruction_tolerance"],
            )
            key = f"{world}/{action}"
            previous = old["readings"]["primary_cells"][key]
            for name, source in (
                ("auc_baseline", "baseline"),
                ("auc_candidate", "candidate"),
                ("delta", "delta"),
            ):
                assert (
                    abs(row[name] - previous[source])
                    <= config["absolute_reconstruction_tolerance"]
                )
            cells[key] = row
        macro = float(np.mean([r["delta"] for r in cells.values()]))
        assert (
            abs(macro - old["readings"]["primary_delta"])
            <= config["absolute_reconstruction_tolerance"]
        )
        results.append({"seed": seed, "cells": cells, "original_primary_delta": macro})
    return {
        "scope": config["scope"],
        "original_verdict": original["decision"]["verdict"],
        "pairs": results,
        "maximum_reconstruction_error": max(
            r["reconstruction_error"] for p in results for r in p["cells"].values()
        ),
        "limitations": "Unblinded fixed-exam accounting, without intervals or "
        "causal/flight claims. Block differences also contain simulator-draw "
        "variation. Pair comparisons are correlated, not independent trials. "
        "No default or gate changes.",
    }


def selftest():
    import copy

    minimum = {
        "positive": 2,
        "negative": 2,
        "positive_rollouts": 2,
        "negative_rollouts": 2,
    }
    rng = np.random.default_rng(2)
    for _ in range(20):
        y = np.tile([0, 1], 8)
        g = np.repeat([0, 1], 8)
        rolls = np.repeat(np.arange(8), 2)
        aa, bb = rng.integers(0, 4, size=(2, 16))
        models = [
            decompose(s, y, g, rolls, ["approach", "immediate"]) for s in (aa, bb)
        ]
        result = contrast(*models, minimum, 1e-12)
        contributions = []
        for pg in range(2):
            for ng in range(2):
                positive, negative = (y == 1) & (g == pg), (y == 0) & (g == ng)
                deltas = []
                for scores in (aa, bb):
                    p, n = scores[positive, None], scores[None, negative]
                    deltas.append(float(((p > n) + 0.5 * (p == n)).mean()))
                weight = int(positive.sum()) * int(negative.sum()) / 64
                contributions.append((deltas[1] - deltas[0]) * weight)
        assert np.isclose(sum(contributions), result["delta"], rtol=0, atol=1e-12)
        assert np.allclose(
            contributions,
            [p["contribution_delta"] for p in result["pairs"]],
            rtol=0,
            atol=1e-12,
        )
        bad = copy.deepcopy(models[1])
        bad["groups"]["approach"]["positive_rollouts"] += 1
        try:
            contrast(models[0], bad, minimum, 1e-12)
        except ValueError:
            pass
        else:
            raise AssertionError("unpaired support accepted")
    # A model can lose pooled AUC solely in cross-block comparisons while
    # both within-block AUCs remain at the tie value 0.5.
    y = np.r_[1, np.zeros(9), np.ones(9), 0]
    g = np.repeat([0, 1], 10)
    values = [
        decompose(s, y, g, np.arange(20), ["approach", "immediate"]) for s in (g, 1 - g)
    ]
    result = contrast(*values, minimum, 1e-12)
    assert result["within_contribution_delta"] == 0
    assert np.isclose(result["delta"], -0.8)
    assert all(r["delta"] == 0 for r in result["blocks"].values())
    assert not all(
        r["meets_original_count_floors_descriptively"]
        for r in result["blocks"].values()
    )
    y = np.array([1, 1, 0, 0])
    values = [
        decompose(s, y, [0, 0, 1, 1], np.arange(4), ["approach", "immediate"])
        for s in (y, 1 - y)
    ]
    result = contrast(*values, minimum, 1e-12)
    assert all(r["delta"] is None for r in result["blocks"].values())
    assert result["within_contribution_delta"] == 0
    fixture = {
        "study_timing_block": np.repeat([0, 1, 2], [6, 6, 2]),
        "world_id": np.r_[np.tile([0, 1, 2], 4), [3, 3]],
        "world_names": np.array(["classic", "dense", "moving", "room"]),
    }
    settings = {
        "transit_courses_per_block": 6,
        "room_courses": 2,
        "per_world_courses_per_block": 2,
    }
    validate_blocks(fixture, settings)
    fixture["study_timing_block"][0] = 1
    try:
        validate_blocks(fixture, settings)
    except ValueError:
        pass
    else:
        raise AssertionError("wrong block assignment accepted")
    print("TIMING MIXTURE AUDIT OK: pair oracle, ties, mixtures, nulls, identities")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--run", action="store_true")
    choice.add_argument("--verify", action="store_true")
    choice.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return
    config = read(FOLDER / "registration.json")
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "runner.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        current = identity(config)
        if not args.verify:
            write_new(FOLDER / "manifest.json", current)
        assert read(FOLDER / "manifest.json") == current
        result = analyze(config)
        assert identity(config) == current
        if args.verify:
            assert read(FOLDER / "report.json") == result
        else:
            write_new(FOLDER / "report.json", result)
        print(
            "TIMING MIXTURE COMPLETE: original NO-GO preserved; "
            "all 12 cells reconstruct"
        )


if __name__ == "__main__":
    main()

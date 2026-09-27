"""Frozen exploratory score join: --selftest, --run, or --verify."""

import argparse
import platform
import sys
from pathlib import Path

import numpy as np

from datasets.intervention_labels import counterfactual_labels
from eval.compare_wm_scores import _load, _validate
from eval.eval_action_auc_audit import link_actions
from eval.eval_dataset_support import load_metadata
from experiments.executed_cf_agreement_v1.audit import confusion
from planner.action_set import ACTION_NAMES
from scripts.schedule_layout_study import read, sha, verify_files, write_new
from world_model.auc_decomposition import decompose
from world_model.training import _index_samples

ROOT = Path(__file__).resolve().parents[2]
FOLDER = Path(__file__).resolve().parent


def identity(config):
    sources, protected = {}, {}
    for name in ("timing_mixture_audit_v1", "executed_cf_agreement_v1"):
        old = read(ROOT / "experiments" / name / "manifest.json")
        for key in ("sources", "original_sources"):
            sources.update(old[key])
        protected.update(old["protected"])
    verify_files(sources)
    verify_files(protected)
    sources.update(
        {
            str(FOLDER / n): sha(FOLDER / n)
            for n in ("audit.py", "registration.json", "definition.md")
        }
    )
    inputs = {str(ROOT / p): h for p, h in config["inputs"].items()}
    verify_files(inputs)
    return {
        "sources": sources,
        "inputs": inputs,
        "protected": protected,
        "runtime": {
            "python": sys.version,
            "numpy": np.__version__,
            "platform": platform.platform(),
        },
    }


def categories(executed, cf, visible):
    if any(not np.isin(a, [0, 1]).all() for a in (executed, cf, visible)):
        raise ValueError("binary labels/answerability required")
    if executed.shape != cf.shape or executed.shape != visible.shape:
        raise ValueError("aligned targets required")
    return np.where(visible == 0, 2, np.where(executed == cf, 0, 1))


def accounting(sa, sb, labels, groups, rolls):
    names = ["agree", "conflict", "masked"]
    a, b = [decompose(s, labels, groups, rolls, names) for s in (sa, sb)]
    if a["auc"] is None or b["auc"] is None:
        raise ValueError("full action/block cell lacks both classes")
    assert a["groups"] == b["groups"]
    terms = []
    for aa, bb in zip(a["pairs"], b["pairs"]):
        terms.append(
            {
                "positive_group": aa["positive_group"],
                "negative_group": aa["negative_group"],
                "pairs": aa["pairs"],
                "weight": aa["weight"],
                "auc_baseline": aa["auc"],
                "auc_candidate": bb["auc"],
                "contribution_delta": bb["contribution"] - aa["contribution"],
            }
        )
    totals = {"involving_conflict": 0.0, "without_conflict": 0.0}
    for term in terms:
        key = (
            "involving_conflict"
            if "conflict" in (term["positive_group"], term["negative_group"])
            else "without_conflict"
        )
        totals[key] += term["contribution_delta"]
    delta = b["auc"] - a["auc"]
    return {
        "auc_baseline": a["auc"],
        "auc_candidate": b["auc"],
        "delta": delta,
        "support": a["groups"],
        "pairs": terms,
        **totals,
        "reconstruction_error": abs(sum(totals.values()) - delta),
    }


def analyze(config):
    data = load_metadata(ROOT / config["data"])
    pairs, labels = _index_samples(data)
    cf, visible = counterfactual_labels(data)
    prior = read(ROOT / "experiments/timing_mixture_audit_v1/report.json")
    agreement = read(ROOT / "experiments/executed_cf_agreement_v1/report.json")
    assert prior["original_verdict"] == agreement["original_verdict"] == "NO-GO"
    results = []
    for seed, previous in zip(config["seeds"], prior["pairs"]):
        assert previous["seed"] == seed
        exports = []
        for arm in config["arms"]:
            spec = config["models"][f"{arm}/{seed}"]
            export = _load(ROOT / spec["scores"])
            assert (
                export["metadata"] == read(ROOT / spec["receipt"])["result"]["scores"]
            )
            assert export["metadata"]["training_seed"] == seed
            assert (
                export["metadata"]["provenance"]["dataset"]["sha256"]
                == config["inputs"][config["data"]]
            )
            assert np.array_equal(export["pairs"], pairs)
            assert np.array_equal(export["labels"], labels[:, :, 0])
            exports.append(export)
        _validate(*exports)
        cells = {}
        for world, action in config["cells"]:
            mask, actions, _ = link_actions(exports[0], data, world)
            selected = np.flatnonzero(mask)[actions == ACTION_NAMES.index(action)]
            rr, tt = pairs[selected].T
            aid = ACTION_NAMES.index(action)
            y = labels[selected, -1, 0]
            c, v = cf[rr, tt, aid, -1, 0], visible[rr, tt, aid]
            groups = categories(y, c, v)
            key = f"{world}/{action}"
            readings = {}
            for block in config["blocks"]:
                use = (
                    np.ones(len(rr), dtype=bool)
                    if block == "all"
                    else data["study_timing_block"][rr]
                    == (0 if block == "approach" else 1)
                )
                if block != "all":
                    assert (
                        confusion(y[use], c[use], v[use], rr[use])
                        == agreement["inputs"]["exam"]["partitions"][block][key]
                    )
                values = [e["scores"][selected, -1][use] for e in exports]
                result = accounting(*values, y[use], groups[use], rr[use])
                old = previous["cells"][key]
                old = old if block == "all" else old["blocks"][block]
                for name in ("auc_baseline", "auc_candidate", "delta"):
                    assert (
                        abs(result[name] - old[name])
                        <= config["absolute_reconstruction_tolerance"]
                    )
                assert (
                    result["reconstruction_error"]
                    <= config["absolute_reconstruction_tolerance"]
                )
                readings[block] = result
            cells[key] = readings
        results.append({"seed": seed, "cells": cells})
    return {"scope": config["scope"], "original_verdict": "NO-GO", "results": results}


def selftest():
    assert categories(
        np.array([0, 1, 0, 1]), np.array([0, 0, 1, 1]), np.array([1, 1, 0, 0])
    ).tolist() == [0, 1, 2, 2]
    rng = np.random.default_rng(9)
    for _ in range(24):
        y = np.tile([0, 1], 9)
        groups = np.repeat([0, 1, 2], 6)
        sa, sb = rng.integers(0, 4, (2, 18))
        result = accounting(sa, sb, y, groups, np.arange(18) // 2)
        totals = [0.0, 0.0]
        for i in np.flatnonzero(y == 1):
            for j in np.flatnonzero(y == 0):
                before = float(sa[i] > sa[j]) + 0.5 * (sa[i] == sa[j])
                after = float(sb[i] > sb[j]) + 0.5 * (sb[i] == sb[j])
                totals[int(groups[i] == 1 or groups[j] == 1)] += (after - before) / 81
        assert np.allclose(
            totals,
            [result["without_conflict"], result["involving_conflict"]],
            rtol=0,
            atol=1e-12,
        )
        assert result["reconstruction_error"] <= 1e-12
    result = accounting(
        [0, 1, 0, 1], [1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 2, 2], np.arange(4)
    )
    assert result["involving_conflict"] == 0 and result["without_conflict"] == -1
    assert result["support"]["conflict"]["samples"] == 0
    assert all(p["auc_baseline"] is None for p in result["pairs"] if p["pairs"] == 0)
    print("CF SCORE ATTRIBUTION OK: category precedence, pair oracle, ties, nulls")


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
    if args.run:
        write_new(FOLDER / "manifest.json", current)
    assert read(FOLDER / "manifest.json") == current
    result = analyze(config)
    assert identity(config) == current
    if args.verify:
        assert read(FOLDER / "report.json") == result
    else:
        write_new(FOLDER / "report.json", result)
    print("CF SCORE ATTRIBUTION COMPLETE: 36 cells reconstruct; NO-GO preserved")


if __name__ == "__main__":
    main()

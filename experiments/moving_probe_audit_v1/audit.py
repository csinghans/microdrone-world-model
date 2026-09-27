"""Fixed-export probe accounting: --selftest, --run, or --verify."""

import argparse
import platform
import sys
from pathlib import Path

import numpy as np

from eval.compare_wm_scores import _load, _validate
from eval.eval_dataset_support import load_metadata
from scripts.schedule_layout_study import read, sha, verify_files, write_new
from world_model.training import _index_samples
from world_model.veer_probe import select

ROOT = Path(__file__).resolve().parents[2]
FOLDER = Path(__file__).resolve().parent


def identity(config):
    old = read(ROOT / config["source_study"] / "manifest.json")
    for key in ("sources", "inputs", "protected"):
        verify_files(old[key])
    inputs = {str(ROOT / p): h for p, h in config["inputs"].items()}
    verify_files(inputs)
    return {
        "original_sources": old["sources"],
        "original_inputs": old["inputs"],
        "protected": old["protected"],
        "inputs": inputs,
        "sources": {
            str(FOLDER / name): sha(FOLDER / name)
            for name in ("audit.py", "registration.json", "definition.md")
        },
        "runtime": {
            "python": sys.version,
            "numpy": np.__version__,
            "platform": platform.platform(),
        },
    }


def accounting(truth, baseline, candidate, rolls, world_frames=None):
    """Preserve frame weighting and bound preferences without inventing ties."""
    truth, baseline, candidate, rolls = map(
        np.asarray, (truth, baseline, candidate, rolls)
    )
    n = len(truth)
    if any(x.shape != (n,) for x in (truth, baseline, candidate, rolls)):
        raise ValueError("aligned one-dimensional probe arrays required")
    if any(not np.isin(x, [0, 1]).all() for x in (truth, baseline, candidate)):
        raise ValueError("binary truth/correctness required")
    if rolls.dtype.kind not in "iu" or (rolls < 0).any():
        raise ValueError("nonnegative integer course IDs required")
    if world_frames is None:
        world_frames = n
    if type(world_frames) is not int or world_frames < n:
        raise ValueError("full-world denominator must include every cell frame")
    truth, baseline, candidate = [x.astype(bool) for x in (truth, baseline, candidate)]
    ids = np.unique(rolls)
    delta = candidate.astype(int) - baseline.astype(int)

    def count(mask):
        return {"frames": int(mask.sum()), "courses": len(np.unique(rolls[mask]))}

    arms = {}
    for name, correct in (("baseline", baseline), ("candidate", candidate)):
        sides = {}
        for side, mask in (("left", truth), ("right", ~truth)):
            nc = int(correct[mask].sum())
            sides[side] = dict(
                count(mask),
                correct=nc,
                accuracy=nc / mask.sum() if mask.any() else None,
            )
        left, right = int((truth & correct).sum()), int((~truth & correct).sum())
        arms[name] = {
            "correct": int(correct.sum()),
            "accuracy": float(correct.mean()) if n else None,
            "truth_sides": sides,
            "strict_preference_count_bounds": {
                "left": [left, left + int((~truth & ~correct).sum())],
                "right": [right, right + int((truth & ~correct).sum())],
                "tie": [0, int((~correct).sum())],
            },
        }
    transitions = {
        name: count(mask)
        for name, mask in (
            ("both_correct", baseline & candidate),
            ("lost", baseline & ~candidate),
            ("gained", ~baseline & candidate),
            ("both_incorrect", ~baseline & ~candidate),
        )
    }
    courses = []
    for rid in ids:
        mask = rolls == rid
        ca, cb = int(baseline[mask].sum()), int(candidate[mask].sum())
        size = int(mask.sum())
        courses.append(
            {
                "course_id": int(rid),
                "frames": size,
                "baseline_correct": ca,
                "candidate_correct": cb,
                "delta": (cb - ca) / size,
                "net_correct": cb - ca,
                "contribution_to_world_delta": (cb - ca) / world_frames,
            }
        )
    macro = {
        arm: (
            float(np.mean([c[f"{arm}_correct"] / c["frames"] for c in courses]))
            if courses
            else None
        )
        for arm in ("baseline", "candidate")
    }
    macro["delta"] = macro["candidate"] - macro["baseline"] if courses else None
    result = {
        "frames": n,
        "courses": len(ids),
        "course_ids": ids.tolist(),
        "truth_left": count(truth),
        "truth_right": count(~truth),
        "constant_direction_reference": {
            "left": float(truth.mean()) if n else None,
            "right": float((~truth).mean()) if n else None,
        },
        **arms,
        "transitions": transitions,
        "delta": float(delta.mean()) if n else None,
        "world_frames": world_frames,
        "contribution_to_world_delta": (
            int(delta.sum()) / world_frames if world_frames else 0.0
        ),
        "equal_course_accuracy": macro,
        "course_change_counts": {
            "improved": sum(c["net_correct"] > 0 for c in courses),
            "declined": sum(c["net_correct"] < 0 for c in courses),
            "unchanged": sum(c["net_correct"] == 0 for c in courses),
        },
        "per_course": courses,
    }
    assert sum(row["frames"] for row in transitions.values()) == n
    assert transitions["gained"]["frames"] - transitions["lost"]["frames"] == int(
        delta.sum()
    )
    return result


def analyze(config):
    data = load_metadata(ROOT / config["data"])
    pairs, labels = _index_samples(data)
    sample = select(data)
    ids = sample["veer_pairs"][:, 0]
    blocks = data["study_timing_block"][ids]
    assert np.isin(blocks, [0, 1]).all(), "transit probe has unknown timing block"
    prior = read(ROOT / config["source_study"] / "report.json")
    assert prior["decision"]["verdict"] == "NO-GO"
    assert [p["seed"] for p in prior["pairs"]] == config["seeds"]
    results, errors = [], []
    for seed, previous in zip(config["seeds"], prior["pairs"]):
        exports = []
        for arm in config["arms"]:
            spec = config["models"][f"{arm}/{seed}"]
            export = _load(ROOT / spec["scores"])
            meta = export["metadata"]
            assert meta == read(ROOT / spec["receipt"])["result"]["scores"]
            assert meta["training_seed"] == seed
            assert (
                meta["provenance"]["dataset"]["sha256"]
                == config["inputs"][config["data"]]
            )
            assert meta["va_rolls"] == list(range(len(data["world_id"])))
            assert np.array_equal(export["pairs"], pairs)
            assert np.array_equal(export["labels"], labels[:, :, 0])
            for key in ("veer_pairs", "veer_gt_left", "veer_world_id"):
                assert np.array_equal(export[key], sample[key]), key
            exports.append(export)
        _validate(*exports)
        truth = sample["veer_gt_left"]
        a, b = [e["veer_correct"] for e in exports]
        aggregate = accounting(truth, a, b, ids)
        for row in aggregate["per_course"]:
            rid = row["course_id"]
            row["world"] = str(data["world_names"][data["world_id"][rid]])
            row["timing_block"] = config["blocks"][int(data["study_timing_block"][rid])]
        worlds = {}
        for world in config["worlds"]:
            wid = data["world_names"].tolist().index(world)
            world_mask = sample["veer_world_id"] == wid
            cells = {}
            for block in config["blocks"]:
                mask = world_mask & (
                    np.ones(len(ids), dtype=bool)
                    if block == "all"
                    else blocks == config["blocks"].index(block)
                )
                cell = accounting(
                    truth[mask], a[mask], b[mask], ids[mask], int(world_mask.sum())
                )
                for row in cell["per_course"]:
                    row["world"] = world
                    row["timing_block"] = config["blocks"][
                        int(data["study_timing_block"][row["course_id"]])
                    ]
                errors.append(
                    abs(
                        sum(
                            c["contribution_to_world_delta"] for c in cell["per_course"]
                        )
                        - cell["contribution_to_world_delta"]
                    )
                )
                cells[block] = cell
            errors.append(
                abs(
                    cells["approach"]["contribution_to_world_delta"]
                    + cells["immediate"]["contribution_to_world_delta"]
                    - cells["all"]["delta"]
                )
            )
            worlds[world] = cells
        for world, actual in [("all", aggregate)] + [
            (w, worlds[w]["all"]) for w in config["worlds"]
        ]:
            old = previous["readings"]["veer"][world]
            assert (
                old["frames"] == actual["frames"]
                and old["courses"] == actual["courses"]
            )
            for key, value in (
                ("baseline", actual["baseline"]["accuracy"]),
                ("candidate", actual["candidate"]["accuracy"]),
                ("delta", actual["delta"]),
            ):
                errors.append(abs(value - old[key]))
        results.append({"seed": seed, "all_worlds": aggregate, "worlds": worlds})
    assert max(errors) <= config["absolute_reconstruction_tolerance"]
    return {
        "scope": config["scope"],
        "original_verdict": "NO-GO",
        "identifiability": (
            "Incorrect can mean opposite strict preference or tie; "
            "exact directions, margins and tie counts are unavailable."
        ),
        "maximum_reconstruction_error": max(errors),
        "results": results,
    }


def selftest():
    import itertools

    # Independent three-way prediction oracle proves bounds are tight. A false
    # correctness flag must never be recoded as an observed opposite direction.
    for truth in (np.array([0, 0, 1, 1]), np.ones(4, int), np.zeros(4, int)):
        for correct in itertools.product((0, 1), repeat=4):
            candidates = []
            for predicted in itertools.product((-1, 0, 1), repeat=4):
                pred = np.array(predicted)
                if np.array_equal(pred == truth, correct):
                    candidates.append(
                        [int((pred == side).sum()) for side in (1, 0, -1)]
                    )
            possible = np.array(candidates)
            result = accounting(truth, correct, correct, np.arange(4))
            bounds = result["baseline"]["strict_preference_count_bounds"]
            for i, side in enumerate(("left", "right", "tie")):
                assert bounds[side] == [possible[:, i].min(), possible[:, i].max()]
            assert result["delta"] == 0
    rolls = np.array([0, 0, 0, 0, 1, 2])
    result = accounting(
        [0, 1, 1, 0, 0, 1], [1, 1, 1, 1, 0, 0], [0, 0, 0, 1, 1, 1], rolls
    )
    assert result["transitions"]["lost"] == {"frames": 3, "courses": 1}
    assert result["transitions"]["gained"] == {"frames": 2, "courses": 2}
    assert result["delta"] == -1 / 6
    assert result["equal_course_accuracy"]["delta"] > 0
    assert (
        abs(
            sum(c["contribution_to_world_delta"] for c in result["per_course"])
            - result["delta"]
        )
        < 1e-12
    )
    empty = accounting([], [], [], np.array([], int), 6)
    assert empty["delta"] is None and empty["equal_course_accuracy"]["delta"] is None
    assert empty["frames"] == 0 and empty["contribution_to_world_delta"] == 0
    single = accounting([1, 1], [0, 1], [1, 0], np.array([0, 0]))
    assert single["baseline"]["truth_sides"]["right"]["accuracy"] is None
    for values in (
        ([2], [1], [1], [0]),
        ([1], [0.5], [1], [0]),
        ([1], [1], [1], [-1]),
        ([1], [1], [1], [0.1]),
        ([1], [], [1], [0]),
    ):
        try:
            accounting(*values)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid probe data accepted")
    print(
        "MOVING PROBE AUDIT OK: tight tie-aware bounds, course weighting, "
        "nulls, malformed inputs"
    )


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
    print(
        "MOVING PROBE AUDIT COMPLETE: 27 cells, 12 original aggregates, NO-GO preserved"
    )


if __name__ == "__main__":
    main()

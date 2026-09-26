"""Frozen metadata audit: python -m experiments.early_intervention_split_v1.audit.

Choose --selftest, --run or --verify. No generation, pixels or model calls.
"""

import argparse
import fcntl
import platform
import sys
from pathlib import Path

import numpy as np

from datasets.intervention_labels import HORIZONS, RADII
from eval.eval_dataset_support import analyze, label_support, load_metadata
from eval.eval_support_requirements import check_support
from planner.action_set import ACTION_NAMES, ACTION_VECS
from scripts.schedule_layout_study import read, sha, verify_files, write_new
from world_model.training import _split_rollouts
from world_model.veer_probe import fixture, select

ROOT = Path(__file__).resolve().parents[2]
FOLDER = Path(__file__).resolve().parent
OUTPUT = ROOT / "output/early_intervention_split_v1"


def identity(config):
    sources = [
        Path(__file__).relative_to(ROOT),
        "eval/eval_dataset_support.py",
        "eval/eval_support_requirements.py",
        "world_model/training.py",
        "world_model/veer_probe.py",
        "world_model/checkpoint_io.py",
        "datasets/intervention_labels.py",
        "planner/action_set.py",
        "planner/nav_action_set.py",
        "sim/scenarios.py",
        "sim/envs.py",
        "scripts/schedule_layout_study.py",
    ]
    sources += [
        p.relative_to(ROOT)
        for p in (
            FOLDER / "definition.md",
            FOLDER / "registration.json",
            FOLDER / "source_receipts.json",
            FOLDER / "support_requirements.json",
        )
    ]
    inputs = {
        str(ROOT / row["path"]): row["sha256"] for row in config["inputs"].values()
    }
    receipts = {
        str(ROOT / p): digest
        for p, digest in read(FOLDER / "source_receipts.json").items()
    }
    locked = {
        str(ROOT / row["dest"]): row["sha256"]
        for row in read(ROOT / "artifacts.lock.json")["artifacts"]
    }
    for group in (inputs, receipts, locked):
        verify_files(group)
    return {
        "sources": {str(p): sha(ROOT / p) for p in sources},
        "datasets": inputs,
        "source_receipts": receipts,
        "protected": locked,
        "runtime": {
            "python": sys.version,
            "numpy": np.__version__,
            "platform": platform.platform(),
        },
    }


def probe(data, rolls, full):
    """Keep original course IDs; assert subset selection before counting."""
    direct = select(data, rolls)
    keep = np.isin(full["veer_pairs"][:, 0], rolls)
    for key in full:
        assert np.array_equal(direct[key], full[key][keep]), key
    rows = {}
    for wid, name in enumerate(data["world_names"]):
        mask = direct["veer_world_id"] == wid
        pairs = direct["veer_pairs"][mask]
        left = direct["veer_gt_left"][mask]
        ids, counts = np.unique(pairs[:, 0], return_counts=True)
        rows[str(name)] = {
            "available_rollouts": int((data["world_id"][rolls] == wid).sum()),
            "frames": int(mask.sum()),
            "rollouts": len(ids),
            "rollout_ids": ids.tolist(),
            "frames_per_rollout": counts.tolist(),
            "left_safer_frames": int(left.sum()),
            "right_safer_frames": int((~left).sum()),
            "zero_support": len(ids) == 0,
            "singleton": len(ids) == 1,
        }
    return rows


def complete_actions(report):
    parts = [report["all"], *[p for s in report["splits"].values() for p in s.values()]]
    for part in parts:
        for row in part["worlds"].values():
            for name in ACTION_NAMES:
                row["actions"].setdefault(name, {"windows": 0, **label_support([], [])})
    return report


def reconcile(report, previous):
    """Window/class counts partition additively; all matches the original pilot."""
    assert report["all"] == previous["all"]
    for seed, split in report["splits"].items():
        assert (
            sum(p["valid_windows"] for p in split.values())
            == report["all"]["valid_windows"]
        )
        for world, whole in report["all"]["worlds"].items():
            rows = [p["worlds"][world] for p in split.values()]
            ids = [set(r["rollout_ids"]) for r in rows]
            assert not ids[0] & ids[1], (seed, world)
            assert ids[0] | ids[1] == set(whole["rollout_ids"])
            for action, total in whole["actions"].items():
                for key in (
                    "windows",
                    "positive",
                    "negative",
                    "positive_rollouts",
                    "negative_rollouts",
                ):
                    assert sum(r["actions"][action][key] for r in rows) == total[key]


def measure(config, manifest_sha):
    requirements = read(FOLDER / "support_requirements.json")
    result = {"scope": config["scope"], "arms": {}, "paired_split_membership": True}
    memberships = {}
    for arm, source in config["inputs"].items():
        path = ROOT / source["path"]
        data = load_metadata(path)
        report = complete_actions(
            analyze(
                data,
                seeds=tuple(config["seeds"]),
                batch=config["batch"],
                epochs=config["nominal_epochs"],
            )
        )
        report["provenance"] = {
            "dataset": {"path": str(path), "sha256": source["sha256"]},
            "audit_manifest_sha256": manifest_sha,
        }
        old = read(
            ROOT / f"experiments/early_intervention_support_v1/{arm}_support.json"
        )
        reconcile(report, old)
        full = select(data)
        probes = {"all": probe(data, list(range(len(data["world_id"]))), full)}
        for seed in config["seeds"]:
            train, val = _split_rollouts(data, np.random.default_rng(seed))
            assert not set(train) & set(val)
            assert sorted(train + val) == list(range(len(data["world_id"])))
            for part, rolls in (("train", train), ("val", val)):
                name = f"splits/{seed}/{part}"
                if name in memberships:
                    assert memberships[name] == rolls, f"unpaired split: {name}"
                else:
                    memberships[name] = rolls
                recorded = report["splits"][str(seed)][part]["worlds"]
                assert (
                    sorted(r for row in recorded.values() for r in row["rollout_ids"])
                    == rolls
                )
                probes[name] = probe(data, rolls, full)
            for world in config["worlds"]:
                for key in ("frames", "left_safer_frames", "right_safer_frames"):
                    assert (
                        sum(
                            probes[f"splits/{seed}/{part}"][world][key]
                            for part in config["partitions"]
                        )
                        == probes["all"][world][key]
                    )
        result["arms"][arm] = {
            "support": report,
            "requirements": check_support(report, requirements),
            "veer_probe": probes,
        }
    result["split_memberships"] = memberships
    return result


def summary(result):
    lines = [
        "# Timing-pilot split support",
        "",
        "Fixed seeds 0/1/2; unchanged splitter and course IDs; no fitting or new data.",
        "Both arms have exactly equal train/validation memberships for every seed.",
        "The original whole-corpus pilot is unchanged. This diagnostic applies its",
        "same 20-window / 3-course per-class minima within each partition.",
        "",
        "| Arm | Partition | Satisfied action cells / 4 |",
        "|---|---|---:|",
    ]
    for arm, data in result["arms"].items():
        checks = data["requirements"]["checks"]
        for part in result["split_memberships"]:
            rows = [r for r in checks if r["partition"] == part]
            lines.append(
                f"| {arm} | {part} | {sum(r['satisfied'] for r in rows)} / 4 |"
            )
    lines += [
        "",
        "## All required executed-action cells",
        "",
        "Counts are positive / negative; courses can overlap across classes/actions.",
        "",
        "| Arm | Partition | World | Action | Windows | Courses | Deficits |",
        "|---|---|---|---|---:|---:|---|",
    ]
    for arm, data in result["arms"].items():
        for row in data["requirements"]["checks"]:
            v = row["observed"]
            deficit = (
                ", ".join(f"{k}: {n}" for k, n in row["deficits"].items()) or "none"
            )
            lines.append(
                f"| {arm} | {row['partition']} | {row['world']} | {row['action']} | "
                f"{v['positive']}/{v['negative']} | "
                f"{v['positive_rollouts']}/{v['negative_rollouts']} | {deficit} |"
            )
    lines += [
        "",
        "## Geometric veer-probe support",
        "",
        "| Arm | Partition | World | Frames | Courses | Left/right safer frames |",
        "|---|---|---|---:|---:|---:|",
    ]
    for arm, data in result["arms"].items():
        for part, worlds in data["veer_probe"].items():
            for world, v in worlds.items():
                lines.append(
                    f"| {arm} | {part} | {world} | {v['frames']} | {v['rollouts']} | "
                    f"{v['left_safer_frames']}/{v['right_safer_frames']} |"
                )
    lines += [
        "",
        "Zero/singleton worlds are explicit. No resampling or probe gate was run.",
        "Count presence does not establish statistical power, "
        "model performance or flight safety.",
        "No seed selection, new draws, relaxed bars or training follows this audit.",
        "",
    ]
    return "\n".join(lines)


def run(verify=False):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (OUTPUT / "runner.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        config = read(FOLDER / "registration.json")
        assert HORIZONS[-1] == config["horizon"] and RADII[0] == config["warn_radius"]
        state = identity(config)
        if verify:
            assert state == read(FOLDER / "manifest.json")
        else:
            write_new(FOLDER / "manifest.json", state)  # refuses a repeated audit
        result = measure(config, sha(FOLDER / "manifest.json"))
        rendered = summary(result)
        assert identity(config) == state, "audit inputs changed"
        if verify:
            assert result == read(FOLDER / "report.json")
            assert rendered == (FOLDER / "summary.md").read_text()
        else:
            write_new(FOLDER / "report.json", result)
            with (FOLDER / "summary.md").open("x") as stream:
                stream.write(rendered)
        print(
            "TIMING-SPLIT OK: paired splits, original counts, "
            "probe subsets, all requirements"
        )


def selftest():
    from copy import deepcopy

    from datasets.combine_rollouts import _synth

    data = fixture()
    full = select(data)
    assert probe(data, [0, 2, 4], full)["classic"]["rollout_ids"] == [0]
    assert probe(data, [0, 2, 4], full)["dense"]["zero_support"]
    assert probe(data, [1, 3], full)["dense"]["rollout_ids"] == [1]
    assert probe(data, [1, 3], full)["dense"]["left_safer_frames"] == 2
    assert probe(data, [], full)["moving"]["frames"] == 0
    malformed = dict(full, veer_gt_left=~full["veer_gt_left"])
    try:
        probe(data, [0], malformed)
    except AssertionError:
        pass
    else:
        raise AssertionError("damaged probe truth accepted")
    from eval.eval_support_requirements import expand_requirements

    checks = expand_requirements(read(FOLDER / "support_requirements.json"))
    assert len(checks) == 24
    assert len(set(r[0] for r in checks)) == 6
    sequences = _synth([0] * 12, length=64)
    sequences["actions"][:] = ACTION_VECS[0]
    sequences["dists"][:6] = 0.1
    synthetic = complete_actions(analyze(sequences, seeds=(0,)))
    reconcile(synthetic, synthetic)
    for key in ("windows", "positive_rollouts"):
        damaged = deepcopy(synthetic)
        damaged["splits"]["0"]["val"]["worlds"]["classic"]["actions"]["forward"][
            key
        ] += 1
        try:
            reconcile(damaged, synthetic)
        except AssertionError:
            pass
        else:
            raise AssertionError(f"partition accounting corruption accepted: {key}")
    print(
        "TIMING-SPLIT SELFTEST OK: original IDs, absent worlds, "
        "probe parity, frozen cells, partition accounting"
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    modes = ap.add_mutually_exclusive_group(required=True)
    modes.add_argument("--run", action="store_true")
    modes.add_argument("--verify", action="store_true")
    modes.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    selftest() if args.selftest else run(verify=args.verify)

"""Run the frozen moving-only timing study with a prospective support gate.

python -m scripts.moving_timing_study --selftest
bash experiments/moving_timing_v1/run.sh
python -m scripts.moving_timing_study --verify
"""

import argparse
import fcntl
import importlib.metadata
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from datasets.combine_rollouts import _STACK
from datasets.generate_rollouts import gen
from datasets.intervention_labels import HORIZONS, RADII
from datasets.rollout_schedule import plan
from datasets.search_rollouts import gen as indoor_gen
from eval.eval_dataset_support import analyze, label_support, load_metadata
from eval.eval_support_requirements import check_support
from eval.eval_veer_support import analyze as analyze_veer
from planner.action_set import ACTION_NAMES
from scripts import schedule_layout_study as shared
from scripts.intervention_timing_study import (
    complete_actions,
    fingerprint,
    load,
    merge_exam,
    publish_data,
)
from scripts.schedule_layout_study import read, sha, verify_files, write_new
from world_model.training import _index_samples

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "experiments/moving_timing_v1"
OUT = ROOT / "output/moving_timing_v1"
REGISTRATION = CAMPAIGN / "registration.json"
PREREQUISITES = [
    "vision",
    "paired_sources",
    "approach_train",
    "moving_immediate_train",
    "exam_approach",
    "exam_immediate",
    "indoor_exam",
    "holdout",
    "preflight",
]


def stages(config):
    return (
        PREREQUISITES
        + [f"train_{arm}_{seed}" for arm, seed in config["order"]]
        + [f"score_{arm}_{seed}" for seed in config["seeds"] for arm in config["arms"]]
        + ["report"]
    )


def identity(config):
    sources = subprocess.check_output(
        ["git", "ls-files", "*.py", "environment.yml", "artifacts.lock.json"],
        cwd=ROOT,
        text=True,
    ).splitlines()
    sources += [
        str((CAMPAIGN / name).relative_to(ROOT))
        for name in ("registration.json", "definition.md", "run.sh")
    ]
    protected = {
        str(ROOT / row["dest"]): row["sha256"]
        for row in read(ROOT / "artifacts.lock.json")["artifacts"]
    }
    inputs = {
        str(ROOT / row["path"]): row["sha256"]
        for row in config["training_inputs"].values()
    }
    inputs.update(
        {str(ROOT / p): value for p, value in config["source_records"].items()}
    )
    verify_files(protected)
    verify_files(inputs)
    return {
        "sources": {str(ROOT / p): sha(ROOT / p) for p in sources},
        "inputs": inputs,
        "protected": protected,
        "runtime": {
            "python": sys.version,
            "platform": platform.platform(),
            "packages": {
                p: importlib.metadata.version(p)
                for p in ("torch", "numpy", "pybullet", "gym-pybullet-drones", "Pillow")
            },
        },
    }


def check_manifest(config):
    if identity(config) != read(CAMPAIGN / "manifest.json"):
        raise RuntimeError(
            "frozen source, inputs, protected artifacts or runtime changed"
        )


def data_path(stage):
    return OUT / stage / "data.npz"


def same(a, b):
    return (
        a.dtype == b.dtype
        and a.shape == b.shape
        and np.array_equal(a, b, equal_nan=a.dtype.kind not in "US")
    )


def paired_sources(a, b):
    """Validate complete source pairing, including unchanged passive/room rows."""
    for key in ("world_names", "a_norm", "horizons", "danger_r"):
        assert same(a[key], b[key]), key
    assert a["world_names"].tolist() == ["classic", "dense", "moving", "room"]
    for key in _STACK:
        assert a[key].shape == b[key].shape and a[key].dtype == b[key].dtype, key
    for key in ("world_id", "in_path", "speed", "pillars", "pillar_vel"):
        assert same(a[key], b[key]), f"unpaired {key}"
    for key in ("frames", "pos", "dists"):
        assert same(a[key][:, 0], b[key][:, 0]), f"unpaired initial {key}"
    passive = a["seg"].max(axis=1) == 0
    assert np.array_equal(passive, b["seg"].max(axis=1) == 0)
    room = a["world_id"] == 3
    for key in _STACK:
        assert same(a[key][room | passive], b[key][room | passive]), key
    for r in np.flatnonzero(~room & ~passive):
        offset = int(np.flatnonzero(a["seg"][r])[0])
        assert 24 <= offset <= 48
        for key in ("actions", "act_id", "seg"):
            assert same(a[key][r, offset:], b[key][r, :-offset]), (r, key)
    assert fingerprint(a) == fingerprint(b)
    moving = a["world_id"] == 2
    return {
        "paired_courses": len(moving),
        "moving_courses": int(moving.sum()),
        "passive_moving_courses": int((moving & passive).sum()),
        "identical_room_courses": int(room.sum()),
        "initial_scenes_equal": True,
        "held_command_prefixes_equal": True,
    }


def assemble(a, b, arm):
    if arm not in ("approach", "moving_immediate"):
        raise ValueError("unknown training arm")
    paired_sources(a, b)
    moving = a["world_id"] == 2
    result = dict(a)
    for key in _STACK:
        result[key] = a[key].copy()
        if arm == "moving_immediate":
            result[key][moving] = b[key][moving]
        assert same(result[key][~moving], a[key][~moving]), key
        target = b if arm == "moving_immediate" else a
        assert same(result[key][moving], target[key][moving]), key
    result["study_intervention_start"] = np.array(
        "mixed_by_world" if arm == "moving_immediate" else "approach"
    )
    result["study_timing_by_world"] = np.array(
        [
            "approach",
            "approach",
            "immediate" if arm == "moving_immediate" else "approach",
            "room_fixed",
        ]
    )
    return result


def stratified_support(data, config):
    pairs, labels = _index_samples(data)
    rolls, times = pairs.T
    blocks = data["study_timing_block"]
    assert blocks.shape == data["world_id"].shape
    assert np.isin(blocks, [0, 1, 2]).all()
    assert np.array_equal(blocks == 2, data["world_id"] == 3)
    result = {}
    for world, action in config["primary_cells"]:
        wid = data["world_names"].tolist().index(world)
        for block, name in enumerate(config["stratified_guard_blocks"]):
            mask = (
                (data["world_id"][rolls] == wid)
                & (data["act_id"][rolls, times] == ACTION_NAMES.index(action))
                & (blocks[rolls] == block)
            )
            result[f"{world}/{action}/{name}"] = label_support(
                labels[mask, -1, 0], rolls[mask]
            )
    return result


def support_gate(reports, veer, now, stratified, config):
    checks, training = {}, {}

    def check(name, actual, minimum):
        checks[name] = {
            "actual": {k: int(actual[k]) for k in minimum},
            "minimum": minimum,
            "passed": all(actual[k] >= v for k, v in minimum.items()),
        }

    requirements = {
        "schema_version": 1,
        "target": "executed_warn_at_32",
        "checks": [
            {
                "partition": f"splits/{seed}/train",
                "world": world,
                "actions": [action],
                "minimum": config["support"]["training_primary"],
            }
            for seed in config["seeds"]
            for world, action in config["primary_cells"]
        ],
    }
    for arm in config["arms"]:
        training[arm] = check_support(reports[arm], requirements)
        for seed in config["seeds"]:
            for world in config["worlds"] + ["room"]:
                actual = reports[arm]["splits"][str(seed)]["train"]["worlds"][world]
                check(
                    f"train/{arm}/{seed}/{world}",
                    actual["labels_at_32"],
                    config["support"]["training_worlds"],
                )
    exam = reports["holdout"]["all"]["worlds"]
    minimum = config["support"]["exam_auc"]
    for world in config["worlds"] + ["room"]:
        check(f"exam/{world}", exam[world]["labels_at_32"], minimum)
    for world, action in (
        config["primary_cells"]
        + config["extra_guard_cells"]
        + [[w, "forward"] for w in config["worlds"]]
    ):
        check(f"exam/{world}/{action}", exam[world]["actions"][action], minimum)
    for world, action in config["primary_cells"]:
        for block in config["stratified_guard_blocks"]:
            key = f"{world}/{action}/{block}"
            check(f"exam/{key}", stratified[key], minimum)
    check("exam/now", now, minimum)
    for world in config["worlds"]:
        check(
            f"exam/veer/{world}",
            veer["by_world"][world],
            config["support"]["exam_veer_each_world"],
        )
    passed = all(r["status"] == "satisfied" for r in training.values()) and all(
        r["passed"] for r in checks.values()
    )
    return {
        "status": "READY" if passed else "INSUFFICIENT_SUPPORT",
        "training_primary": training,
        "checks": checks,
        "scope": "Coverage floors only; no precision/power or performance claim.",
    }


def preflight(config, directory):
    reports = {}
    old = read(ROOT / config["old_training_support"])
    for arm in config["arms"] + ["holdout"]:
        path = data_path("holdout" if arm == "holdout" else f"{arm}_train")
        data = load_metadata(path)
        report = complete_actions(
            analyze(
                data,
                seeds=tuple(config["seeds"]),
                batch=config["train"]["batch"],
                epochs=config["train"]["epochs"],
                holdout=arm == "holdout",
            )
        )
        report["provenance"] = {"dataset": {"path": str(path), "sha256": sha(path)}}
        write_new(directory / f"{arm}_support.json", report)
        reports[arm] = report
        if arm != "holdout":
            for seed in config["seeds"]:
                for part in ("train", "val"):
                    current = report["splits"][str(seed)][part]
                    previous = old["splits"][str(seed)][part]
                    assert current["rollouts"] == previous["rollouts"]
                    for world in config["worlds"] + ["room"]:
                        assert (
                            current["worlds"][world]["rollout_ids"]
                            == previous["worlds"][world]["rollout_ids"]
                        )
        else:
            veer, _ = analyze_veer(data)
            now = label_support(
                (data["dists"] < float(data["danger_r"])).ravel().astype(int),
                np.repeat(np.arange(len(data["world_id"])), config["length"]),
            )
            stratified = stratified_support(data, config)
            for name, value in (
                ("veer", veer),
                ("now", now),
                ("stratified", stratified),
            ):
                write_new(directory / f"{name}_support.json", value)
    train_ids = [
        read(OUT / f"{arm}_train/course_identities.json") for arm in config["arms"]
    ]
    assert train_ids[0] == train_ids[1], "training scenes must remain paired"
    exam_ids = read(OUT / "holdout/course_identities.json")
    old_exam_ids = read(ROOT / config["closed_exam_identities"])
    assert not set(train_ids[0]) & set(exam_ids), "exam reuses a training scene"
    assert not set(old_exam_ids) & set(exam_ids), "exam reuses a closed exam scene"
    result = support_gate(reports, veer, now, stratified, config)
    result["identities"] = {
        "paired_training_scenes": len(train_ids[0]),
        "disjoint_exam_scenes": len(exam_ids),
        "disjoint_closed_exam_scenes": len(old_exam_ids),
        "original_approach_split_membership_preserved": True,
    }
    write_new(directory / "report.json", result)
    return result


def report(config, directory):
    from eval.compare_wm_scores import _load
    from eval.eval_moving_timing import decision, readings

    data = load_metadata(data_path("holdout"))
    pairs = []
    for seed in config["seeds"]:
        exports, bills = [], []
        for arm in config["arms"]:
            saved = read(CAMPAIGN / "records" / f"score_{arm}_{seed}.json")["result"]
            scores = _load(OUT / f"score_{arm}_{seed}/scores.npz")
            assert scores["metadata"] == saved["scores"]
            meta = scores["metadata"]
            assert meta["training_seed"] == seed
            assert meta["checkpoint_meta"]["training_dataset_sha256"] == sha(
                data_path(f"{arm}_train")
            )
            assert meta["provenance"]["dataset"]["sha256"] == sha(data_path("holdout"))
            exports.append(scores)
            bills.append({k: saved[k] for k in ("budget", "estimated_gap8_ms")})
        pairs.append(
            {
                "seed": seed,
                "readings": readings(*exports, data, config),
                "baseline_bill": bills[0],
                "candidate_bill": bills[1],
            }
        )
    result = {"decision": decision(pairs, config), "pairs": pairs}
    write_new(directory / "report.json", result)
    return result


def execute(stage, directory, config):
    if stage == "vision":
        return shared.vision(config, directory)
    if stage in ("paired_sources", "approach_train", "moving_immediate_train"):
        a, b = [
            load(ROOT / config["training_inputs"][s]["path"])
            for s in ("approach", "immediate")
        ]
        pairing = paired_sources(a, b)
        assert pairing["paired_courses"] == 276
        assert pairing["moving_courses"] == 60
        assert pairing["passive_moving_courses"] == 20
        assert pairing["identical_room_courses"] == 96
        for data, onset in ((a, "approach"), (b, "immediate")):
            assert str(data["study_intervention_start"]) == onset
            assert str(data["study_rng_layout"]) == "per_rollout"
            assert str(data["transit_schedule_layout"]) == "world_balanced"
            for r, role in enumerate(plan(180, config["worlds"])):
                assert str(data["world_names"][data["world_id"][r]]) == role.world
                assert bool(data["in_path"][r]) == role.in_path
                assert bool(data["seg"][r].max() == 0) == role.passive
        if stage == "paired_sources":
            return pairing
        data = assemble(a, b, stage.removesuffix("_train"))
    elif stage in ("exam_approach", "exam_immediate"):
        arm = stage.removeprefix("exam_")
        settings = config["exam_transit"]
        data = gen(
            settings["n_rollouts_per_timing"],
            config["length"],
            seed=settings["seeds"][arm],
            randomize=settings["randomize"],
            img_res=config["img_res"],
            worlds=tuple(config["worlds"]),
            schedule_layout=settings["schedule_layout"],
            rng_layout=settings["rng_layout"],
            intervention_start=arm,
        )
        return publish_data(data, directory, config, timing=arm)
    elif stage == "indoor_exam":
        data = indoor_gen(
            **config[stage], length=config["length"], img_res=config["img_res"]
        )
    elif stage == "holdout":
        data = merge_exam(
            *[
                load(data_path(s))
                for s in ("exam_approach", "exam_immediate", "indoor_exam")
            ]
        )
    elif stage == "preflight":
        return preflight(config, directory)
    elif stage == "report":
        return report(config, directory)
    else:
        shared.CAMPAIGN, shared.OUT = CAMPAIGN, OUT
        return shared.execute(stage, directory, config)
    return publish_data(data, directory, config)


def completed(stage):
    receipt = CAMPAIGN / "records" / f"{stage}.json"
    if not receipt.exists():
        return False
    saved = read(receipt)
    if saved["manifest_sha256"] != sha(CAMPAIGN / "manifest.json"):
        raise RuntimeError("receipt belongs to a different frozen study")
    verify_files(saved["files"])
    outcome = read(OUT / f"{stage}_exit.json")
    if outcome["exit_code"] != 0 or outcome["log_sha256"] != sha(OUT / f"{stage}.log"):
        raise RuntimeError("stage lacks a successful, unchanged complete process log")
    return True


def released(stage):
    if stage not in PREREQUISITES:
        status = read(CAMPAIGN / "records/preflight.json")["result"]["status"]
        if status != "READY":
            raise SystemExit(10)


def run_stage(stage, config):
    check_manifest(config)
    for previous in stages(config):
        if previous == stage:
            break
        if not completed(previous):
            raise RuntimeError(f"required earlier stage incomplete: {previous}")
    released(stage)
    if completed(stage):
        return
    directory = OUT / stage
    directory.mkdir()  # An unfinished stage must never silently repeat.
    started = time.time()
    try:
        result = execute(stage, directory, config)
        check_manifest(config)
        write_new(
            CAMPAIGN / "records" / f"{stage}.json",
            {
                "stage": stage,
                "exit_code": 0,
                "started_unix": started,
                "elapsed_seconds": time.time() - started,
                "manifest_sha256": sha(CAMPAIGN / "manifest.json"),
                "result": result,
                "files": {
                    str(p): sha(p) for p in sorted(directory.rglob("*")) if p.is_file()
                },
            },
        )
    except BaseException as exc:
        write_new(directory / "failure.json", {"error": repr(exc), "stage": stage})
        raise
    print(f"{stage}-DONE EXIT=0", flush=True)


def verify_readings(config, *, support_only=False):
    """Recompute frozen accounting without new rendering, fitting or inference."""
    import tempfile

    with tempfile.TemporaryDirectory(prefix="moving_timing_verify_") as tmp:
        folder = Path(tmp)
        preflight(config, folder)
        for path in folder.glob("*.json"):
            assert read(path) == read(OUT / "preflight" / path.name), path.name
    if not support_only:
        with tempfile.TemporaryDirectory(prefix="moving_timing_verify_") as tmp:
            folder = Path(tmp)
            report(config, folder)
            assert read(folder / "report.json") == read(OUT / "report/report.json")
    check_manifest(config)
    print("VERIFIED recomputed support and available score readings", flush=True)


def run(config, verify=False):
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "runner.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if not (CAMPAIGN / "manifest.json").exists() and not verify:
            write_new(CAMPAIGN / "manifest.json", identity(config))
        check_manifest(config)
        for stage in stages(config):
            if stage not in PREREQUISITES:
                result = read(CAMPAIGN / "records/preflight.json")["result"]
                if result["status"] != "READY":
                    print("INSUFFICIENT_SUPPORT: study closed without fits", flush=True)
                    if verify:
                        verify_readings(config, support_only=True)
                        return
                    raise SystemExit(10)
            if completed(stage):
                print(f"VERIFIED {stage}", flush=True)
                continue
            if verify:
                raise RuntimeError(f"missing stage: {stage}")
            with (OUT / f"{stage}.log").open("x") as log:
                print(f"START {stage}", flush=True)
                result = subprocess.run(
                    [
                        sys.executable,
                        "-u",
                        "-m",
                        "scripts.moving_timing_study",
                        "--stage",
                        stage,
                    ],
                    cwd=ROOT,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                )
                log.write(f"\nSTAGE PROCESS EXIT={result.returncode}\n")
            write_new(
                OUT / f"{stage}_exit.json",
                {
                    "exit_code": result.returncode,
                    "log_sha256": sha(OUT / f"{stage}.log"),
                },
            )
            if result.returncode:
                raise SystemExit(result.returncode)
            assert completed(stage)
        if verify:
            verify_readings(config)
        print("MOVING TIMING STUDY OK: all registered stages complete", flush=True)


def selftest():
    import copy
    import tempfile
    from unittest.mock import patch

    from datasets.combine_rollouts import _synth, combine
    from eval.eval_moving_timing import selftest as metrics_selftest
    from planner.action_set import ACTION_VECS

    config = read(REGISTRATION)
    assert len(stages(config)) == len(set(stages(config))) == 22
    a = _synth([0, 1, 2, 2], length=64)
    room = _synth([0], length=64, nan_pillars=True)
    room["world_names"] = np.array(["room"])
    a = combine(a, room)
    a["actions"][:] = ACTION_VECS[0]
    a["seg"][:] = 0
    a["act_id"][:] = 0
    a["seg"][2, 24:] = 1
    a["act_id"][2, 24:] = 2
    a["actions"][2, 24:] = ACTION_VECS[2]
    b = copy.deepcopy(a)
    b["seg"][2] = 1
    b["act_id"][2] = 2
    b["actions"][2] = ACTION_VECS[2]
    b["frames"][2, 1:] = 17
    b["pos"][2, 1:] = 0.1
    b["dists"][2, 1:] = 0.2
    hybrid = assemble(a, b, "moving_immediate")
    control = assemble(a, b, "approach")
    for key in _STACK:
        assert same(control[key], a[key])
        assert same(hybrid[key][[0, 1, 3, 4]], a[key][[0, 1, 3, 4]])
        assert same(hybrid[key][2], b[key][2])
    assert hybrid["study_timing_by_world"].tolist() == [
        "approach",
        "approach",
        "immediate",
        "room_fixed",
    ]
    for key, index in (
        ("frames", (3, 2)),
        ("speed", 2),
        ("actions", (2, 0)),
        ("dists", (4, 2)),
    ):
        bad = copy.deepcopy(b)
        bad[key][index] += 1
        try:
            paired_sources(a, bad)
        except AssertionError:
            pass
        else:
            raise AssertionError(f"missed source corruption: {key}")
    metric = {
        "positive": 100,
        "negative": 100,
        "positive_rollouts": 10,
        "negative_rollouts": 10,
        "auc_defined": True,
    }
    worlds = {}
    for wid, w in enumerate(config["worlds"] + ["room"]):
        actions = ["forward"] if w == "room" else ["forward", "veer_left", "veer_right"]
        worlds[w] = {
            "rollouts": 10,
            "rollout_ids": list(range(wid * 10, (wid + 1) * 10)),
            "valid_windows": 200 * len(actions),
            "labels_at_32": dict(
                metric, positive=100 * len(actions), negative=100 * len(actions)
            ),
            "actions": {a: dict(metric, windows=200) for a in actions},
        }
    partition = {"rollouts": 40, "valid_windows": 2000, "worlds": worlds}
    support = {
        "schema_version": 1,
        "target": "executed_warn_at_32",
        "horizons": [4, 8, 16, 32],
        "all": partition,
        "splits": {
            str(s): {"train": copy.deepcopy(partition)} for s in config["seeds"]
        },
    }
    reports = {arm: copy.deepcopy(support) for arm in config["arms"] + ["holdout"]}
    veer = {"by_world": {w: {"frames": 40, "rollouts": 10} for w in config["worlds"]}}
    stratified = {
        f"{w}/{a}/{b}": dict(metric)
        for w, a in config["primary_cells"]
        for b in config["stratified_guard_blocks"]
    }
    assert support_gate(reports, veer, metric, stratified, config)["status"] == "READY"
    for arm in config["arms"]:
        for seed in config["seeds"]:
            bad = copy.deepcopy(reports)
            bad[arm]["splits"][str(seed)]["train"]["worlds"]["moving"]["actions"][
                "veer_left"
            ]["negative_rollouts"] = 2
            assert (
                support_gate(bad, veer, metric, stratified, config)["status"]
                == "INSUFFICIENT_SUPPORT"
            )
    for key in stratified:
        bad = copy.deepcopy(stratified)
        bad[key]["positive_rollouts"] = 9
        assert (
            support_gate(reports, veer, metric, bad, config)["status"]
            == "INSUFFICIENT_SUPPORT"
        )
    for w, action in config["extra_guard_cells"]:
        bad = copy.deepcopy(reports)
        bad["holdout"]["all"]["worlds"][w]["actions"][action]["negative_rollouts"] = 9
        assert (
            support_gate(bad, veer, metric, stratified, config)["status"]
            == "INSUFFICIENT_SUPPORT"
        )
    for world in config["worlds"] + ["room"]:
        bad = copy.deepcopy(reports)
        bad["holdout"]["all"]["worlds"][world]["labels_at_32"]["positive_rollouts"] = 9
        assert (
            support_gate(bad, veer, metric, stratified, config)["status"]
            == "INSUFFICIENT_SUPPORT"
        )
    for world in config["worlds"]:
        bad_veer = copy.deepcopy(veer)
        bad_veer["by_world"][world]["frames"] = 39
        assert (
            support_gate(reports, bad_veer, metric, stratified, config)["status"]
            == "INSUFFICIENT_SUPPORT"
        )
    assert (
        support_gate(
            reports, veer, dict(metric, negative_rollouts=9), stratified, config
        )["status"]
        == "INSUFFICIENT_SUPPORT"
    )
    # Actual held-window indexing must route classes/courses to the right blocks.
    data = _synth([2] * 8, length=64)
    data["seg"][:] = 0
    data["study_timing_block"] = np.repeat([0, 1], 4)
    for r in range(8):
        data["act_id"][r] = 2 + (r % 4 // 2)
        data["actions"][r] = ACTION_VECS[data["act_id"][r]]
        data["dists"][r] = 0.1 if r % 2 else 2.0
    sliced = stratified_support(data, config)
    assert set(sliced) == set(stratified)
    for row in sliced.values():
        assert row["positive_rollouts"] == row["negative_rollouts"] == 1
        assert row["positive"] == row["negative"] > 0
    with tempfile.TemporaryDirectory(prefix="moving_timing_selftest_") as tmp:
        folder = Path(tmp)
        (folder / "records").mkdir()
        write_new(
            folder / "records/preflight.json",
            {"result": {"status": "INSUFFICIENT_SUPPORT"}},
        )
        with patch(__name__ + ".CAMPAIGN", folder):
            try:
                released("train_approach_0")
            except SystemExit as exc:
                assert exc.code == 10
            else:
                raise AssertionError("insufficient support released a fit")
    metrics_selftest()
    print("MOVING TIMING RUNNER OK: pairing, replacement, support, slices, stop gate")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--run", action="store_true")
    choice.add_argument("--verify", action="store_true")
    choice.add_argument("--stage")
    choice.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return
    config = read(REGISTRATION)
    assert HORIZONS[-1] == config["horizon"] and np.isclose(
        RADII[0], config["warn_radius"]
    )
    if args.stage:
        if args.stage not in stages(config):
            parser.error("unknown registered stage")
        run_stage(args.stage, config)
    else:
        run(config, verify=args.verify)


if __name__ == "__main__":
    main()

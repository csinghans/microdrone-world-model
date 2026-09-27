"""Execute the prospectively registered intervention-timing model study.

python -m scripts.intervention_timing_study --selftest
bash experiments/intervention_timing_v1/run.sh
python -m scripts.intervention_timing_study --verify
Fresh stages, fail-fast support gate, immutable receipts and resumable queue.
"""

import argparse
import fcntl
import hashlib
import importlib.metadata
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from datasets.combine_rollouts import _STACK, combine
from datasets.generate_rollouts import gen
from datasets.intervention_labels import HORIZONS, RADII
from datasets.provenance import save_dataset
from datasets.rollout_schedule import plan
from datasets.search_rollouts import gen as indoor_gen
from eval.eval_dataset_support import analyze, label_support, load_metadata
from eval.eval_support_requirements import CATALOGS, check_support
from eval.eval_veer_support import analyze as analyze_veer
from scripts import schedule_layout_study as shared
from scripts.early_intervention_study import paired
from scripts.schedule_layout_study import read, sha, verify_files, write_new
from sim.scenarios import DANGER_R

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "experiments/intervention_timing_v1"
OUT = ROOT / "output/intervention_timing_v1"
REGISTRATION = CAMPAIGN / "registration.json"
PREREQUISITES = [
    "vision",
    "pilot_pair",
    "indoor_train",
    "approach_train",
    "immediate_train",
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
    sources += [
        config["pilot_registration"],
        "experiments/early_intervention_split_v1/report.json",
    ]
    protected = {
        str(ROOT / row["dest"]): row["sha256"]
        for row in read(ROOT / "artifacts.lock.json")["artifacts"]
    }
    inputs = {
        str(ROOT / row["path"]): row["sha256"]
        for row in config["training_inputs"].values()
    }
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


def load(path):
    with np.load(path, allow_pickle=False) as blob:
        return dict(blob)


def data_path(stage):
    return OUT / stage / "data.npz"


def corpus_checks(data, config, *, timing=None):
    if data["frames"].shape[1:] != (
        config["length"],
        config["img_res"],
        config["img_res"],
        3,
    ):
        raise ValueError("wrong registered image/trajectory dimensions")
    if not np.isclose(data["danger_r"], DANGER_R):
        raise ValueError("danger-now radius differs from scorer")
    if timing is not None:
        for key, expected in (
            ("intervention_start", timing),
            ("schedule_layout", "world_balanced"),
            ("rng_layout", "per_rollout"),
        ):
            assert str(data[key]) == expected, key
        for r, role in enumerate(plan(len(data["world_id"]), config["worlds"])):
            assert str(data["world_names"][data["world_id"][r]]) == role.world
            assert bool(data["in_path"][r]) == role.in_path
            assert bool(data["seg"][r].max() == 0) == role.passive
    result = {}
    for wid in np.unique(data["world_id"]):
        selected = data["world_id"] == wid
        frames = data["frames"][selected, ::40]
        std = float(frames.std())
        if std <= config["instrument"]["minimum_frame_std"]:
            raise ValueError("blank sampled corpus frames")
        result[str(data["world_names"][wid])] = {
            "courses": int(selected.sum()),
            "passive": int((data["seg"][selected].max(axis=1) == 0).sum()),
            "clear": int((~data["in_path"][selected]).sum()),
            "sampled_frame_std": std,
        }
    return result


def fingerprint(data):
    """Exact initial scene/observation identities, not statistical independence."""
    result = []
    for r, wid in enumerate(data["world_id"]):
        h = hashlib.sha256(str(data["world_names"][wid]).encode())
        for key in ("speed", "pillars", "pillar_vel"):
            h.update(np.ascontiguousarray(data[key][r]).tobytes())
        for key in ("frames", "pos"):
            h.update(np.ascontiguousarray(data[key][r, 0]).tobytes())
        result.append(h.hexdigest())
    return result


def publish_data(data, directory, config, *, timing=None):
    result = corpus_checks(data, config, timing=timing)
    identities = fingerprint(data)
    if len(set(identities)) != len(identities):
        raise ValueError("duplicate exact initial scene identity within a corpus")
    write_new(directory / "course_identities.json", identities)
    save_dataset(data, directory / "data.npz")
    return {"coverage": result, "courses": len(identities)}


def merge_exam(a, b, indoor):
    for key in ("world_names", "a_norm", "horizons", "danger_r"):
        if not np.array_equal(a[key], b[key]):
            raise ValueError(f"transit block mismatch: {key}")
    data = {key: np.concatenate([a[key], b[key]]) for key in _STACK}
    data.update(
        {key: a[key] for key in ("world_names", "a_norm", "horizons", "danger_r")}
    )
    data["schedule_layout"] = np.array("world_balanced")
    merged = combine(data, indoor)
    merged["study_timing_block"] = np.concatenate(
        [
            np.full(len(d["world_id"]), i, dtype=np.int8)
            for i, d in enumerate((a, b, indoor))
        ]
    )
    return merged


def support_gate(reports, veer, now, config):
    checks = {}

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
                "minimum": config["support"]["candidate_training"],
            }
            for seed in config["seeds"]
            for world, action in config["primary_cells"]
        ],
    }
    candidate = check_support(reports["immediate"], requirements)
    for arm in config["arms"]:
        for seed in config["seeds"]:
            for world in config["worlds"] + ["room"]:
                actual = reports[arm]["splits"][str(seed)]["train"]["worlds"][world]
                check(
                    f"train/{arm}/{seed}/{world}",
                    actual["labels_at_32"],
                    config["support"]["both_training_worlds"],
                )
    exam = reports["holdout"]["all"]["worlds"]
    minimum = config["support"]["exam_auc"]
    for world in config["worlds"] + ["room"]:
        check(f"exam/{world}", exam[world]["labels_at_32"], minimum)
    for world, action in config["primary_cells"] + [
        [w, "forward"] for w in config["worlds"]
    ]:
        check(f"exam/{world}/{action}", exam[world]["actions"][action], minimum)
    check("exam/now", now, minimum)
    for world in config["worlds"]:
        check(
            f"exam/veer/{world}",
            veer["by_world"][world],
            config["support"]["exam_veer_each_world"],
        )
    passed = candidate["status"] == "satisfied" and all(
        row["passed"] for row in checks.values()
    )
    return {
        "status": "READY" if passed else "INSUFFICIENT_SUPPORT",
        "candidate_training": candidate,
        "checks": checks,
        "scope": "Coverage floors only; no precision/power or performance claim.",
    }


def complete_actions(report):
    parts = [report["all"], *[p for s in report["splits"].values() for p in s.values()]]
    for part in parts:
        for world, row in part["worlds"].items():
            for name in CATALOGS[world]:
                row["actions"].setdefault(name, {"windows": 0, **label_support([], [])})
    return report


def preflight(config, directory):
    reports = {}
    old = read(ROOT / "experiments/early_intervention_split_v1/report.json")
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
                    for world in config["worlds"]:
                        current = report["splits"][str(seed)][part]["worlds"][world]
                        previous = old["arms"][arm]["support"]["splits"][str(seed)][
                            part
                        ]["worlds"][world]
                        assert current["rollout_ids"] == previous["rollout_ids"]
        else:
            veer, _ = analyze_veer(data)
            now = label_support(
                (data["dists"] < float(data["danger_r"])).ravel().astype(int),
                np.repeat(np.arange(len(data["world_id"])), config["length"]),
            )
            write_new(directory / "veer_support.json", veer)
            write_new(directory / "now_support.json", now)
    for seed in config["seeds"]:
        for part in ("train", "val"):
            a, b = [reports[arm]["splits"][str(seed)][part] for arm in config["arms"]]
            assert a["rollouts"] == b["rollouts"]
            for world in config["worlds"] + ["room"]:
                assert (
                    a["worlds"][world]["rollout_ids"]
                    == b["worlds"][world]["rollout_ids"]
                )
    train_ids = [
        read(OUT / f"{arm}_train/course_identities.json") for arm in config["arms"]
    ]
    assert train_ids[0] == train_ids[1], "training scenes must remain paired"
    exam_ids = read(OUT / "holdout/course_identities.json")
    assert not set(train_ids[0]) & set(exam_ids), "exam reuses an exact training scene"
    result = support_gate(reports, veer, now, config)
    result["identities"] = {
        "paired_training_scenes": len(train_ids[0]),
        "disjoint_exam_scenes": len(exam_ids),
        "same_split_membership": True,
        "pilot_transit_membership_preserved": True,
    }
    write_new(directory / "report.json", result)
    return result


def report(config, directory):
    from eval.compare_wm_scores import _load
    from eval.eval_intervention_timing import decision, readings

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
    if stage == "pilot_pair":
        a, b = [
            load(ROOT / config["training_inputs"][arm]["path"])
            for arm in config["arms"]
        ]
        return paired(a, b, read(ROOT / config["pilot_registration"]))
    if stage in ("indoor_train", "indoor_exam"):
        data = indoor_gen(
            **config[stage], length=config["length"], img_res=config["img_res"]
        )
    elif stage in ("approach_train", "immediate_train"):
        arm = stage.removesuffix("_train")
        transit = load(ROOT / config["training_inputs"][arm]["path"])
        indoor = load(data_path("indoor_train"))
        data = combine(transit, indoor)
        data["study_intervention_start"] = np.array(arm)
        data["study_rng_layout"] = np.array("per_rollout")
        for key in _STACK:
            if key != "world_id":
                assert np.array_equal(data[key][180:], indoor[key], equal_nan=True)
        assert np.array_equal(
            data["world_names"][data["world_id"][180:]],
            indoor["world_names"][indoor["world_id"]],
        )
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
        # Reuse the established fit/scoring recipes in an explicit study namespace.
        # Their training paths already follow <arm>_train/data.npz; there is no
        # shared training_source because the sole knob lives in the paired data.
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
    directory.mkdir()  # refuses incomplete stages before any repeat measurement
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
                        "scripts.intervention_timing_study",
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
        print(
            "INTERVENTION TIMING STUDY OK: all registered stages complete", flush=True
        )


def selftest():
    import copy
    import tempfile
    from unittest.mock import patch

    from datasets.combine_rollouts import _synth
    from eval.eval_intervention_timing import selftest as metrics_selftest

    config = read(REGISTRATION)
    assert len(stages(config)) == len(set(stages(config))) == 23
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
    assert support_gate(reports, veer, metric, config)["status"] == "READY"
    bad = copy.deepcopy(reports)
    bad["immediate"]["splits"]["2"]["train"]["worlds"]["dense"]["actions"]["veer_left"][
        "negative_rollouts"
    ] = 2
    assert support_gate(bad, veer, metric, config)["status"] == "INSUFFICIENT_SUPPORT"
    for world in config["worlds"]:
        bad_veer = copy.deepcopy(veer)
        bad_veer["by_world"][world]["rollouts"] = 9
        assert (
            support_gate(reports, bad_veer, metric, config)["status"]
            == "INSUFFICIENT_SUPPORT"
        )
    bad = copy.deepcopy(reports)
    bad["holdout"]["all"]["worlds"]["moving"]["actions"]["forward"]["positive"] = 99
    assert support_gate(bad, veer, metric, config)["status"] == "INSUFFICIENT_SUPPORT"
    # Frozen thresholds are inclusive, except the model's strictly positive macro.
    bad_now = dict(metric, negative_rollouts=9)
    assert (
        support_gate(reports, veer, bad_now, config)["status"] == "INSUFFICIENT_SUPPORT"
    )
    a, b, room = _synth([0, 1, 2]), _synth([0, 1, 2]), _synth([0], nan_pillars=True)
    room["world_names"] = np.array(["room"])
    merged = merge_exam(a, b, room)
    assert merged["study_timing_block"].tolist() == [0, 0, 0, 1, 1, 1, 2]
    for key in _STACK:
        if key == "world_id":
            assert merged[key].tolist() == [0, 1, 2, 0, 1, 2, 3]
            continue
        assert np.array_equal(
            merged[key], np.concatenate([a[key], b[key], room[key]]), equal_nan=True
        )
    with tempfile.TemporaryDirectory(prefix="timing_selftest_") as tmp:
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
    print("INTERVENTION TIMING RUNNER OK")


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

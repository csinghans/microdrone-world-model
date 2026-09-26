"""Run the frozen support-only pilot; never fit or score a model.

    python -m scripts.early_intervention_study --selftest
    bash experiments/early_intervention_support_v1/run.sh
    python -m scripts.early_intervention_study --verify

Completed stages are checked and reused. An incomplete stage requires
inspection, not automatic regeneration. Counts never release training.
"""

import argparse
import fcntl
import importlib.metadata
import platform
import subprocess
import sys
import time
import types
from pathlib import Path

import numpy as np

from datasets.generate_rollouts import _schedule, _streams, gen
from datasets.intervention_labels import HORIZONS, RADII
from datasets.provenance import save_dataset
from datasets.rollout_schedule import plan
from eval.eval_dataset_support import analyze, label_support, load_metadata
from eval.eval_support_requirements import check_support
from eval.eval_support_requirements import run as check_files
from planner.action_set import ACTION_NAMES, ACTION_VECS, FORWARD
from scripts.schedule_layout_study import read, sha, verify_files, vision, write_new

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "experiments/early_intervention_support_v1"
OUT = ROOT / "output/early_intervention_support_v1"
STAGES = ("vision", "compatibility", "approach", "immediate", "pair", "support")


def identity():
    paths = subprocess.check_output(
        ["git", "ls-files", "*.py", "environment.yml", "artifacts.lock.json"],
        cwd=ROOT,
        text=True,
    ).splitlines()
    paths += [
        str((CAMPAIGN / name).relative_to(ROOT))
        for name in ("definition.md", "registration.json", "support_requirements.json")
    ]
    paths += [str((CAMPAIGN / "run.sh").relative_to(ROOT))]
    locked = read(ROOT / "artifacts.lock.json")["artifacts"]
    protected = {str(ROOT / row["dest"]): row["sha256"] for row in locked}
    verify_files(protected)
    return {
        "sources": {str(ROOT / p): sha(ROOT / p) for p in paths},
        "protected": protected,
        "runtime": {
            "python": sys.version,
            "platform": platform.platform(),
            "packages": {
                p: importlib.metadata.version(p)
                for p in ("numpy", "torch", "pybullet", "gym-pybullet-drones")
            },
        },
    }


def same(a, b):
    if a.dtype.kind in "fc":
        return np.array_equal(a, b, equal_nan=True)
    return np.array_equal(a, b)


def compatibility(config):
    """Actual simulator parity against the registered pre-change source."""
    source = subprocess.check_output(
        ["git", "show", f"{config['reference_commit']}:datasets/generate_rollouts.py"],
        cwd=ROOT,
        text=True,
    )
    old = types.ModuleType("_registered_generator")
    old.__file__ = str(ROOT / "datasets/generate_rollouts.py")
    exec(compile(source, old.__file__, "exec"), old.__dict__)
    fixture = config["instrument"]
    rows = []
    for layout in ("legacy", "world_balanced"):
        for randomize in (False, True):
            kwargs = dict(
                n_rollouts=fixture["compatibility_rollouts"],
                length=fixture["compatibility_length"],
                seed=fixture["compatibility_seed"],
                img_res=fixture["compatibility_img_res"],
                worlds=tuple(config["worlds"]),
                schedule_layout=layout,
                randomize=randomize,
            )
            before, after = old.gen(**kwargs), gen(**kwargs)
            assert list(before) == list(after), "default schema/order changed"
            for key in before:
                assert before[key].dtype == after[key].dtype, key
                assert same(before[key], after[key]), (layout, randomize, key)
            rows.append(dict(layout=layout, randomize=randomize, arrays=len(before)))
    return {"exact_default_parity": rows}


def generate(config, arm, directory):
    data = gen(
        **{
            key: config[key]
            for key in (
                "n_rollouts",
                "length",
                "seed",
                "randomize",
                "img_res",
                "schedule_layout",
                "rng_layout",
            )
        },
        worlds=tuple(config["worlds"]),
        intervention_start=arm,
    )
    save_dataset(data, directory / "data.npz")
    return {"arm": arm, "rollouts": config["n_rollouts"], "length": config["length"]}


def paired(control, candidate, config):
    """Assert the causal pairing before exposing any support count."""
    for data in (control, candidate):
        assert data["frames"].shape[:2] == (config["n_rollouts"], config["length"])
    for key in ("world_id", "world_names", "in_path", "speed", "pillars", "pillar_vel"):
        assert same(control[key], candidate[key]), f"unpaired {key}"
    for key in ("frames", "pos", "dists"):
        assert same(control[key][:, 0], candidate[key][:, 0]), f"unpaired initial {key}"
    roles = plan(config["n_rollouts"], config["worlds"], config["schedule_layout"])
    counts = {}
    for r, role in enumerate(roles):
        for arm, data in (("approach", control), ("immediate", candidate)):
            assert str(data["rng_layout"]) == config["rng_layout"]
            assert str(data["intervention_start"]) == arm
            assert str(data["schedule_layout"]) == config["schedule_layout"]
            assert str(data["world_names"][data["world_id"][r]]) == role.world
            assert bool(data["in_path"][r]) == role.in_path
            assert bool(data["seg"][r].max() == 0) == role.passive
            _, schedule_rng, _ = _streams(config["seed"], r, "per_rollout", None)
            ids, seg = _schedule(schedule_rng, config["length"], role.passive, arm)
            assert same(data["act_id"][r], ids) and same(data["seg"][r], seg)
        counts.setdefault(role.world, {"rollouts": 0, "passive": 0, "clear": 0})
        counts[role.world]["rollouts"] += 1
        counts[role.world]["passive"] += int(role.passive)
        counts[role.world]["clear"] += int(not role.in_path)
        if role.passive:
            for key in ("frames", "pos", "dists", "actions", "act_id", "seg"):
                assert same(control[key][r], candidate[key][r]), (r, key)
        else:
            offset = int(np.flatnonzero(control["seg"][r])[0])
            assert 24 <= offset <= 48
            for key in ("actions", "act_id", "seg"):
                assert same(control[key][r, offset:], candidate[key][r, :-offset])
    per_world = config["n_rollouts"] // len(config["worlds"])
    for row in counts.values():
        assert row["rollouts"] == per_world and row["passive"] == per_world // 3
    assert counts["classic"]["clear"] == per_world // 2
    return {"exact_pairing": True, "roles": counts}


def pair(config):
    with (
        np.load(OUT / "approach/data.npz") as a,
        np.load(OUT / "immediate/data.npz") as b,
    ):
        control, candidate = dict(a), dict(b)
    return paired(control, candidate, config)


def support_report(path):
    report = analyze(load_metadata(path), seeds=(), epochs=1, holdout=True)
    # The generic producer emits observed actions; this pilot prints zeros too.
    for row in report["all"]["worlds"].values():
        for action in ACTION_NAMES:
            row["actions"].setdefault(action, {"windows": 0, **label_support([], [])})
    report["provenance"] = {
        "dataset": {"path": str(path), "sha256": sha(path)},
        "manifest": {
            "path": str(CAMPAIGN / "manifest.json"),
            "sha256": sha(CAMPAIGN / "manifest.json"),
        },
    }
    return report


def support(config, directory):
    reports, receipts = {}, {}
    for arm in config["arms"]:
        path = OUT / arm / "data.npz"
        report = support_report(path)
        report_path = directory / f"{arm}_support.json"
        write_new(report_path, report)
        receipts[arm] = check_files(
            report_path,
            ROOT / config["requirements"],
            path,
            directory / f"{arm}_requirements.json",
        )
        reports[arm] = report
    rows = []
    for world in config["worlds"]:
        for action in ACTION_NAMES:
            values = {
                arm: reports[arm]["all"]["worlds"][world]["actions"][action]
                for arm in config["arms"]
            }
            rows.append({"world": world, "action": action, **values})
    result = {
        "scope": "Paired development-data support only; no training or model scores.",
        "statuses": {arm: receipt["status"] for arm, receipt in receipts.items()},
        "rows": rows,
        "next": "Close pilot; no extra seed/rollouts or automatic training.",
    }
    write_new(directory / "report.json", result)
    lines = [
        "# Early-intervention support pilot",
        "",
        "Exactly paired scene identities, initial pixels and passive trajectories.",
        "No fitting, inference, bootstrap or model promotion.",
        "",
        f"Control: **{result['statuses']['approach']}**; "
        f"immediate: **{result['statuses']['immediate']}**.",
        "",
        "Counts are positive / negative. Courses can overlap across labels/actions.",
        "The fixed minima are structural presence checks, not statistical power.",
        "",
        "| World | Action | Control windows | Immediate windows | "
        "Control courses | Immediate courses | Negative course delta |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        a, b = row["approach"], row["immediate"]
        lines.append(
            f"| {row['world']} | {row['action']} | {a['positive']}/{a['negative']} | "
            f"{b['positive']}/{b['negative']} | "
            f"{a['positive_rollouts']}/{a['negative_rollouts']} | "
            f"{b['positive_rollouts']}/{b['negative_rollouts']} | "
            f"{b['negative_rollouts'] - a['negative_rollouts']:+d} |"
        )
    lines += ["", result["next"], ""]
    (directory / "summary.md").write_text("\n".join(lines))
    return result


def run(verify=False):
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "runner.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        manifest_path = CAMPAIGN / "manifest.json"
        current = identity()
        if not manifest_path.exists() and not verify:
            write_new(manifest_path, current)
        assert read(manifest_path) == current, "frozen source/runtime identity changed"
        config = read(CAMPAIGN / "registration.json")
        assert HORIZONS[-1] == config["horizon"] and RADII[0] == config["warn_radius"]
        for stage in STAGES:
            receipt = CAMPAIGN / "records" / f"{stage}.json"
            if receipt.exists():
                saved = read(receipt)
                assert saved["manifest_sha256"] == sha(manifest_path)
                verify_files(saved["files"])
                print(f"VERIFIED {stage}", flush=True)
                continue
            if verify:
                raise RuntimeError(f"missing stage: {stage}")
            directory = OUT / stage
            directory.mkdir()  # unfinished stage is never silently repeated
            start = time.time()
            print(f"START {stage}", flush=True)
            if stage == "compatibility":
                result = compatibility(config)
            elif stage == "vision":
                result = vision(config, directory)
            elif stage in config["arms"]:
                result = generate(config, stage, directory)
            elif stage == "pair":
                result = pair(config)
            else:
                result = support(config, directory)
            assert identity() == current, "inputs changed during stage"
            write_new(
                receipt,
                {
                    "stage": stage,
                    "exit_code": 0,
                    "started_unix": start,
                    "elapsed_seconds": time.time() - start,
                    "manifest_sha256": sha(manifest_path),
                    "result": result,
                    "files": {
                        str(p): sha(p)
                        for p in sorted(directory.rglob("*"))
                        if p.is_file()
                    },
                },
            )
            print(f"{stage}-DONE EXIT=0", flush=True)
        if verify:
            assert pair(config) == read(CAMPAIGN / "records/pair.json")["result"]
            requirements = read(ROOT / config["requirements"])
            for arm in config["arms"]:
                report = support_report(OUT / arm / "data.npz")
                assert report == read(OUT / "support" / f"{arm}_support.json")
                checked = check_support(report, requirements)
                saved = read(OUT / "support" / f"{arm}_requirements.json")
                assert checked == {k: v for k, v in saved.items() if k != "provenance"}
            assert identity() == current
        print("EARLY-INTERVENTION-STUDY OK: all frozen stages verified", flush=True)


def selftest():
    def original(rng, length, passive):
        ids = np.full(length, FORWARD, dtype=np.int16)
        seg = np.zeros(length, dtype=np.int16)
        if passive:
            return ids, seg
        t, s = int(rng.integers(24, 49)), 0
        while t < length:
            s += 1
            n = int(rng.integers(40, 57))
            ids[t : t + n] = int(rng.integers(0, 6))
            seg[t : t + n] = s
            t += n
        return ids, seg

    for seed in range(20):
        for length in (1, 24, 49, 64, 160, 300):
            for passive in (False, True):
                a, b = np.random.default_rng(seed), np.random.default_rng(seed)
                expected, actual = original(a, length, passive), _schedule(
                    b, length, passive
                )
                assert all(same(x, y) for x, y in zip(expected, actual))
                assert a.bit_generator.state == b.bit_generator.state
            a, b = np.random.default_rng(seed), np.random.default_rng(seed)
            offset = int(np.random.default_rng(seed).integers(24, 49))
            normal = _schedule(a, length, False)
            early = _schedule(b, length, False, "immediate")
            if length > offset:
                assert all(same(x[offset:], y[:-offset]) for x, y in zip(normal, early))
        shared = np.random.default_rng(seed)
        assert all(rng is shared for rng in _streams(seed, 0, "shared", shared))
        a = _streams(seed, 3, "per_rollout", shared)
        b = _streams(seed, 3, "per_rollout", shared)
        a[1].random(1000)
        assert same(a[0].random(100), b[0].random(100))
        assert same(a[2].random(100), b[2].random(100))
    for kwargs in ({"rng_layout": "bad"}, {"intervention_start": "bad"}):
        try:
            gen(1, 64, **kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid generator recipe accepted")
    config = dict(
        n_rollouts=18,
        length=160,
        worlds=["classic", "dense", "moving"],
        schedule_layout="world_balanced",
        rng_layout="per_rollout",
        seed=3,
    )
    roles = plan(18, config["worlds"])
    arms = []
    for arm in ("approach", "immediate"):
        schedules = [
            _schedule(_streams(3, r, "per_rollout", None)[1], 160, role.passive, arm)
            for r, role in enumerate(roles)
        ]
        ids = np.stack([s[0] for s in schedules])
        arms.append(
            dict(
                world_names=np.array(config["worlds"]),
                world_id=np.arange(18) % 3,
                in_path=np.array([r.in_path for r in roles]),
                speed=np.ones(18),
                pillars=np.full((18, 8, 2), np.nan),
                pillar_vel=np.zeros((18, 8, 2)),
                frames=np.zeros((18, 160, 1, 1, 3), dtype=np.uint8),
                pos=np.zeros((18, 160, 3)),
                dists=np.ones((18, 160)),
                act_id=ids,
                seg=np.stack([s[1] for s in schedules]),
                actions=ACTION_VECS[ids],
                rng_layout=np.array("per_rollout"),
                intervention_start=np.array(arm),
                schedule_layout=np.array("world_balanced"),
            )
        )
    assert paired(*arms, config)["exact_pairing"]
    for key, index in (
        ("speed", 1),
        ("frames", (1, 0, 0, 0, 0)),
        ("dists", (6, 20)),
        ("act_id", (0, 20)),
        ("seg", (6, 0)),
    ):
        damaged = {**arms[1], key: arms[1][key].copy()}
        damaged[key][index] += 1
        try:
            paired(arms[0], damaged, config)
        except AssertionError:
            pass
        else:
            raise AssertionError(f"pairing corruption accepted: {key}")
    requirements = read(CAMPAIGN / "support_requirements.json")
    from eval.eval_support_requirements import expand_requirements

    assert len(expand_requirements(requirements)) == 4
    print(
        "EARLY-INTERVENTION-STUDY SELFTEST OK: old draws, time shift, "
        "isolated streams, pairing rejection"
    )


def main():
    ap = argparse.ArgumentParser()
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--selftest", action="store_true")
    group.add_argument("--run", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
    else:
        run(verify=args.verify)


if __name__ == "__main__":
    main()

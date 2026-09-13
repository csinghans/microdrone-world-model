"""Run registered paired WM studies, or their simulator-free selftests.

    python -m scripts.schedule_layout_study --selftest
    bash experiments/schedule_layout_v1/run.sh
    bash experiments/cf_hard_pool_v1/run.sh

Each stage owns a fresh directory and an immutable hashed receipt. A stage
left without a receipt requires inspection, never automatic remeasurement.
"""

import argparse
import fcntl
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "experiments/schedule_layout_v1"
OUT = ROOT / "output/schedule_layout_v1"
REGISTRATION = CAMPAIGN / "registration.json"


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def plain(value):
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items()}
    if isinstance(value, (tuple, list, np.ndarray)):
        return [plain(v) for v in value]
    if isinstance(value, np.generic):
        return plain(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def write_new(path, value):
    """Publish a complete JSON without replacing an existing record."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f".pending-{os.getpid()}")
    with temporary.open("x") as stream:
        json.dump(plain(value), stream, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.link(temporary, path)  # atomic, and refuses existing destination
    finally:
        temporary.unlink()


def verify_files(files):
    for path, expected in files.items():
        if not Path(path).is_file() or sha(path) != expected:
            raise RuntimeError(f"recorded file changed or missing: {path}")


def protected():
    lock = read(ROOT / "artifacts.lock.json")
    files = {
        str(ROOT / a["dest"]): a["sha256"]
        for a in lock["artifacts"]
        if a["name"] in ("world_model.pth", "world_model_unified.pth")
    }
    assert len(files) == 2
    verify_files(files)
    return files


def provenance():
    paths = subprocess.check_output(
        ["git", "ls-files", "*.py", "environment.yml", "artifacts.lock.json"],
        cwd=ROOT,
        text=True,
    ).splitlines()
    paths += [str(REGISTRATION.relative_to(ROOT))]
    extra = {}
    source = read(REGISTRATION).get("training_source")
    if source:
        extra["training_input"] = {str(ROOT / source["path"]): source["sha256"]}
        verify_files(extra["training_input"])
    return {
        "sources": {str(ROOT / p): sha(ROOT / p) for p in paths},
        "protected": protected(),
        "runtime": {
            "python": sys.version,
            "platform": platform.platform(),
            "packages": {
                p: importlib.metadata.version(p)
                for p in ("torch", "numpy", "pybullet", "gym-pybullet-drones")
            },
        },
        **extra,
    }


def check_manifest():
    current = provenance()
    saved = read(CAMPAIGN / "manifest.json")
    for key in current:
        if current[key] != saved[key]:
            raise RuntimeError(f"frozen {key} changed; inspect before continuing")


def data_path(stage):
    return OUT / stage / "data.npz"


def load_data(stage):
    with np.load(data_path(stage), allow_pickle=False) as blob:
        return dict(blob)


def training_path(arm, config):
    source = config.get("training_source")
    return ROOT / source["path"] if source else data_path(f"{arm}_train")


def cf_verdict(pairs, config):
    bars, checks, deltas = config["bars"], {}, []
    if [p["seed"] for p in pairs] != config["seeds"]:
        raise ValueError("requires every registered seed, exactly once and in order")
    for pair in pairs:
        seed, a, b = pair["seed"], pair["baseline"], pair["candidate"]
        values = [a["veer_all"][0], b["veer_all"][0], a["now_auc"], b["now_auc"]]
        values += [
            arm["auc_by_world"][w] for arm in (a, b) for w in bars["guard_worlds"]
        ]
        if any(v is None or not np.isfinite(v) for v in values):
            raise ValueError("missing or nonfinite decision metric")
        for arm in (a, b):
            if arm["veer_all"][1] < config["instrument"]["minimum_veer_samples"]:
                raise ValueError("insufficient veer frames")
            if arm["veer_rollouts"] < config["instrument"]["minimum_veer_rollouts"]:
                raise ValueError("insufficient independent veer rollouts")
            counts = [arm["now_label_counts"]] + [
                arm["label_counts_by_world"][w] for w in bars["guard_worlds"]
            ]
            if any(min(c["positive"], c["negative"]) == 0 for c in counts):
                raise ValueError("classless guarded AUC")
        delta = b["veer_all"][0] - a["veer_all"][0]
        deltas.append(delta)
        checks[f"seed{seed}/veer_nonnegative"] = delta >= bars["veer_each_delta_min"]
        for world in bars["guard_worlds"]:
            checks[f"seed{seed}/{world}_guard"] = (
                b["auc_by_world"][world] - a["auc_by_world"][world]
                >= bars["guard_each_auc_delta_min"]
            )
        checks[f"seed{seed}/now_auc_guard"] = (
            b["now_auc"] - a["now_auc"] >= bars["guard_each_now_auc_delta_min"]
        )
        ab, bb = pair["baseline_budget"], pair["candidate_budget"]
        if not all(np.isfinite(v) for budget in (ab, bb) for v in budget.values()):
            raise ValueError("nonfinite deployment bill")
        checks[f"seed{seed}/budget"] = (
            ab == bb and bb["total_kb"] <= bars["budget_kb_max"]
        )
    checks["veer_mean"] = float(np.mean(deltas)) >= bars["veer_mean_delta_min"]
    return {
        "verdict": "GO" if all(checks.values()) else "NO-GO",
        "checks": checks,
        "veer_deltas": deltas,
        "veer_mean": float(np.mean(deltas)),
        "veer_range": [min(deltas), max(deltas)],
        "scope": config["interpretation"],
    }


def coverage(data, config, layout=None):
    from datasets.rollout_schedule import plan
    from world_model.training import _index_samples

    names = [str(n) for n in data["world_names"]]
    ids = data["world_id"]
    if layout:
        actual = [i for i, w in enumerate(ids) if names[w] != "room"]
        expected = plan(len(actual), config["worlds"], layout)
        for r, role in zip(actual, expected):
            assert names[ids[r]] == role.world
            assert bool(data["in_path"][r]) == role.in_path
            assert (data["seg"][r].max() == 0) == role.passive
    pairs, labels = _index_samples(data)
    rows = {}
    for wid in np.unique(ids):
        mask = ids == wid
        y = labels[ids[pairs[:, 0]] == wid, -1, 0]
        row = {
            "rollouts": int(mask.sum()),
            "passive": int((data["seg"][mask].max(axis=1) == 0).sum()),
            "clear": int((~data["in_path"][mask]).sum()),
            "positive": int(y.sum()),
            "negative": int(len(y) - y.sum()),
            "frame_std": float(data["frames"][mask].std()),
        }
        minimum = config["instrument"]["minimum_labels_per_class_per_world"]
        assert min(row["positive"], row["negative"]) >= minimum, row
        assert row["frame_std"] > config["instrument"]["minimum_frame_std"], row
        rows[names[wid]] = row
    return rows


def vision(config, directory):
    """Same camera, scene present versus removed: pixels must see geometry."""
    import pybullet as p
    from PIL import Image

    from sim.envs import START, grab_frame, make_env
    from sim.indoor.rooms import single_room
    from sim.scenario_registry import get

    env = make_env(img_res=config["img_res"])
    rows = {}
    try:
        for name in config["worlds"] + ["room"]:
            seed = config["instrument"]["fixture_seed"]
            env.reset(seed=seed)
            before = {
                p.getBodyUniqueId(i, physicsClientId=env.CLIENT)
                for i in range(p.getNumBodies(physicsClientId=env.CLIENT))
            }
            if name == "room":
                sc = single_room(seed)
                sc.spawn_bodies(
                    env, offset=(sc.start_xy[0] - START[0], sc.start_xy[1] - START[1])
                )
                fixture_steps = 0
            else:
                sc = get(name).spawn(
                    env,
                    np.random.default_rng(seed),
                    speed=0.6,
                    randomize=False,
                    in_path=True,
                )
                # The crosser starts outside the body-fixed camera cone.
                # Observe its centreline crossing, with the camera unmoved;
                # otherwise a correct renderer looks like an empty scene.
                fixture_steps = (
                    round(abs(sc.y / sc.vy) / env.CTRL_TIMESTEP)
                    if name == "moving"
                    else 0
                )
                for _ in range(fixture_steps):
                    sc.step()
            frame = grab_frame(env)
            added = {
                p.getBodyUniqueId(i, physicsClientId=env.CLIENT)
                for i in range(p.getNumBodies(physicsClientId=env.CLIENT))
            } - before
            assert added, f"{name}: no bodies spawned"
            for body in added:
                p.removeBody(body, physicsClientId=env.CLIENT)
            blank = grab_frame(env)
            row = {
                "world": name,
                "fixture_steps": fixture_steps,
                "bodies": len(added),
                "frame_std": float(frame.std()),
                "render_difference": float(np.abs(frame.astype(float) - blank).mean()),
            }
            Image.fromarray(frame).save(directory / f"{name}.png")
            Image.fromarray(blank).save(directory / f"{name}_removed.png")
            assert row["frame_std"] > config["instrument"]["minimum_frame_std"], row
            assert (
                row["render_difference"]
                > config["instrument"]["minimum_render_difference"]
            ), row
            rows[name] = row
    finally:
        env.close()
    return rows


def make_data(stage, config):
    from datasets.combine_rollouts import combine
    from datasets.generate_rollouts import gen as transit
    from datasets.search_rollouts import gen as indoor

    exam = "holdout" in stage
    recipe = config["holdout" if exam else "train_data"]
    if stage.startswith("indoor_"):
        return (
            indoor(
                recipe["n_indoor"],
                recipe["length"],
                seed=recipe["indoor_seed"],
                img_res=config["img_res"],
                fov_honest=False,
            ),
            None,
        )
    layout = config["holdout"]["schedule_layout"] if exam else stage[:-6]
    data = transit(
        recipe["n_transit"],
        recipe["length"],
        seed=recipe["transit_seed"],
        worlds=tuple(config["worlds"]),
        img_res=config["img_res"],
        schedule_layout=layout,
        randomize=False,
    )
    data["schedule_layout"] = np.array(layout)  # explicit provenance even legacy
    return (
        combine(data, load_data("indoor_holdout" if exam else "indoor_train")),
        layout,
    )


def verdict(pairs, config):
    """All registered draws and per-draw guards are required; NaN cannot pass."""
    if config.get("kind") == "cf_hard_pool":
        return cf_verdict(pairs, config)
    bars = config["bars"]
    if [p["seed"] for p in pairs] != config["seeds"]:
        raise ValueError("missing, duplicate, or out-of-order registered seeds")
    checks, moving = {}, []
    for pair in pairs:
        seed, a, b = pair["seed"], pair["baseline"], pair["candidate"]
        values = []
        for world in config["worlds"] + ["room"]:
            delta = b["auc_by_world"][world] - a["auc_by_world"][world]
            values += [a["auc_by_world"][world], b["auc_by_world"][world], delta]
            if world == "moving":
                moving.append(delta)
                checks[f"seed{seed}/moving_positive"] = (
                    delta > bars["moving_each_delta_min_exclusive"]
                )
            else:
                checks[f"seed{seed}/{world}_guard"] = (
                    delta >= bars["guard_each_auc_delta_min"]
                )
        for metric, tolerance in (
            ("now_auc", "guard_each_now_auc_delta_min"),
            ("veer", "guard_each_veer_delta_min"),
        ):
            av = a["veer_all"][0] if metric == "veer" else a[metric]
            bv = b["veer_all"][0] if metric == "veer" else b[metric]
            values += [av, bv]
            checks[f"seed{seed}/{metric}_guard"] = bv - av >= bars[tolerance]
        minimum = config["instrument"]["minimum_veer_samples"]
        if min(a["veer_all"][1], b["veer_all"][1]) < minimum:
            raise ValueError("insufficient veer probe support")
        if not all(v is not None and np.isfinite(v) for v in values):
            raise ValueError("missing or nonfinite reading")
        ab, bb = pair["baseline_budget"], pair["candidate_budget"]
        if not all(np.isfinite(v) for budget in (ab, bb) for v in budget.values()):
            raise ValueError("nonfinite budget")
        checks[f"seed{seed}/budget"] = (
            bb["total_kb"] <= bars["budget_kb_max"] and ab == bb
        )
    checks["moving_mean"] = float(np.mean(moving)) >= bars["moving_mean_delta_min"]
    return {
        "verdict": "GO" if all(checks.values()) else "NO-GO",
        "checks": checks,
        "moving_deltas": moving,
        "moving_mean": float(np.mean(moving)),
        "moving_range": [min(moving), max(moving)],
        "scope": config["interpretation"],
    }


def execute(stage, directory, config):
    if stage == "vision":
        return vision(config, directory)
    if stage == "training_data":
        from datasets.intervention_labels import counterfactual_labels
        from world_model.cf_sampling import hard_pool_mask
        from world_model.training import _split_rollouts

        path = training_path(None, config)
        with np.load(path, allow_pickle=False) as blob:
            data = dict(blob)
        stats = coverage(data, config, config["train_data"]["schedule_layout"])
        cf, vis = counterfactual_labels(data)
        masks = {arm: hard_pool_mask(cf, vis, arm) for arm in config["arms"]}
        assert not (masks["answerable"] & ~masks["legacy_masked"]).any()
        pools = {}
        for seed in config["seeds"]:
            train_rolls, _ = _split_rollouts(data, np.random.default_rng(seed))
            pools[str(seed)] = {
                arm: int(mask[train_rolls].sum()) for arm, mask in masks.items()
            }
        return {
            "source": config["training_source"],
            "coverage": stats,
            "hard_pools": pools,
        }
    if stage.endswith("_train") or stage in ("holdout", "indoor_holdout"):
        data, layout = make_data(stage, config)
        stats = coverage(data, config, layout)
        with (directory / "data.npz").open("xb") as stream:
            np.savez_compressed(stream, **data)
        return stats
    if stage.startswith("train_"):
        import torch

        from world_model.training import train

        arm, seed = stage[6:].rsplit("_", 1)
        assert torch.backends.mps.is_available(), "registered training requires MPS"
        path = training_path(arm, config)
        with np.load(path, allow_pickle=False) as blob:
            data = dict(blob)
        knob = {"cf_hard_pool": arm} if config.get("kind") == "cf_hard_pool" else {}
        checkpoint, metrics = train(data, seed=int(seed), **config["train"], **knob)
        if knob:
            pool = read(CAMPAIGN / "records/training_data.json")["result"][
                "hard_pools"
            ][seed][arm]
            assert checkpoint["meta"]["cf_hard_pool"] == arm
            assert metrics["cf_hard_pool_frames"] == pool
            assert metrics["cf_hard_pool_fallback"] == (pool == 0)
        checkpoint["meta"]["training_dataset_sha256"] = sha(path)
        with (directory / "model.pth").open("xb") as stream:
            torch.save(checkpoint, stream)
        return {"metrics": metrics, "meta": checkpoint["meta"]}
    if stage.startswith("score_"):
        from eval.eval_latency_budget import GAP8_GMACS, onboard_budget
        from world_model.training import load_model

        model = OUT / stage.replace("score_", "train_", 1) / "model.pth"
        subprocess.run(
            [
                sys.executable,
                "-u",
                "-m",
                "eval.eval_wm_checkpoint",
                "--ckpt",
                str(model),
                "--data",
                str(data_path("holdout")),
                "--independent-holdout",
                "--device",
                config["evaluation_device"],
                "--out",
                str(directory / "scores.json"),
                "--scores-out",
                str(directory / "scores.npz"),
            ],
            check=True,
            cwd=ROOT,
        )
        enc, pred, heads, now, meta = load_model(str(model), device="cpu")
        budget = onboard_budget(enc, pred, heads, now, img_res=meta["img_res"])
        return {
            "scores": read(directory / "scores.json"),
            "budget": budget,
            "estimated_gap8_ms": budget["macs_decision"] / (GAP8_GMACS * 1e6),
        }
    if stage == "report":
        from eval.compare_wm_scores import _load, compare

        pairs, comparisons = [], {}
        for seed in config["seeds"]:
            a, b = [
                read(CAMPAIGN / "records" / f"score_{arm}_{seed}.json")["result"]
                for arm in config["arms"]
            ]
            pairs.append(
                {
                    "seed": seed,
                    "baseline": a["scores"],
                    "candidate": b["scores"],
                    "baseline_budget": a["budget"],
                    "candidate_budget": b["budget"],
                }
            )
            score_paths = [
                OUT / f"score_{arm}_{seed}" / "scores.npz" for arm in config["arms"]
            ]
            comparisons[str(seed)] = compare(
                *[_load(p) for p in score_paths], **config["bootstrap"]
            )
            if config.get("kind") == "cf_hard_pool":
                probe = comparisons[str(seed)]["veer"]
                for name, arm in (("baseline", a), ("candidate", b)):
                    scores = arm["scores"]
                    assert probe["n_samples"] == scores["veer_all"][1]
                    assert probe["n_rollouts"] == scores["veer_rollouts"]
                    if probe["n_samples"]:
                        assert np.isclose(
                            probe[f"accuracy_{name}"], scores["veer_all"][0]
                        ), "veer raw sample/aggregate mismatch"
        try:
            decision = verdict(pairs, config)
        except (ValueError, TypeError, KeyError) as exc:
            decision = {"verdict": "INVALID", "reason": str(exc)}
        deltas = {}
        for world in config["worlds"] + ["room", "all"]:
            values = [
                comparisons[str(s)]["worlds"][world]["delta"] for s in config["seeds"]
            ]
            deltas[world] = {
                "paired_deltas": values,
                "mean": float(np.mean(values)) if None not in values else None,
                "range": [min(values), max(values)] if None not in values else None,
            }
        return {
            "decision": decision,
            "paired_auc_summary": deltas,
            "pairs": pairs,
            "comparisons": comparisons,
        }
    raise ValueError(f"unknown stage: {stage}")


def stages(config):
    data = [
        "vision",
        "indoor_train",
        "indoor_holdout",
        "legacy_train",
        "world_balanced_train",
        "holdout",
    ]
    if config.get("kind") == "cf_hard_pool":
        data = ["vision", "training_data", "indoor_holdout", "holdout"]
    fits = [f"train_{arm}_{seed}" for arm, seed in config["order"]]
    scores = [
        f"score_{arm}_{seed}" for seed in config["seeds"] for arm in config["arms"]
    ]
    return data + fits + scores + ["report"]


def completed(stage):
    receipt = CAMPAIGN / "records" / f"{stage}.json"
    if not receipt.exists():
        return False
    record = read(receipt)
    if record["manifest_sha256"] != sha(CAMPAIGN / "manifest.json"):
        raise RuntimeError("receipt belongs to another manifest")
    verify_files(record["files"])
    return True


def run_stage(stage, config):
    check_manifest()
    # Every prior stage must be complete and unchanged before any dependent work.
    for previous in stages(config):
        if previous == stage:
            break
        if not completed(previous):
            raise RuntimeError(f"required earlier stage incomplete: {previous}")
    if completed(stage):
        print(f"VERIFIED-SKIP {stage}", flush=True)
        return
    directory = OUT / stage
    directory.mkdir()  # any orphan outputs stop us before a repeated draw
    started = time.time()
    try:
        result = execute(stage, directory, config)
        check_manifest()
        record = {
            "stage": stage,
            "started_unix": started,
            "elapsed_seconds": time.time() - started,
            "manifest_sha256": sha(CAMPAIGN / "manifest.json"),
            "result": result,
            "files": {
                str(p): sha(p) for p in sorted(directory.iterdir()) if p.is_file()
            },
        }
        write_new(CAMPAIGN / "records" / f"{stage}.json", record)
    except BaseException as exc:
        write_new(
            directory / "failure.json",
            {"error": repr(exc), "elapsed_seconds": time.time() - started},
        )
        raise
    print(f"STAGE-DONE {stage}", flush=True)


def selftest():
    import tempfile
    from copy import deepcopy
    from unittest.mock import patch

    config = read(REGISTRATION)
    scores = {
        "auc_by_world": {w: 0.7 for w in config["worlds"] + ["room"]},
        "now_auc": 0.8,
        "veer_all": [0.8, 30],
    }
    pairs = [
        {
            "seed": seed,
            "baseline": deepcopy(scores),
            "candidate": deepcopy(scores),
            "baseline_budget": {"total_kb": 160.0},
            "candidate_budget": {"total_kb": 160.0},
        }
        for seed in config["seeds"]
    ]
    for pair in pairs:
        pair["candidate"]["auc_by_world"]["moving"] += 0.04
    assert verdict(pairs, config)["verdict"] == "GO"
    bad = deepcopy(pairs)
    bad[1]["candidate"]["auc_by_world"]["room"] -= 0.021
    assert (
        verdict(bad, config)["verdict"] == "NO-GO"
    ), "one broken guard hidden by averaging"
    bad = deepcopy(pairs)
    bad[0]["candidate"]["auc_by_world"]["moving"] -= 0.04
    assert verdict(bad, config)["verdict"] == "NO-GO"
    for invalid in (pairs[:2], pairs + pairs[:1]):
        try:
            verdict(invalid, config)
        except ValueError:
            pass
        else:
            raise AssertionError("partial/duplicate draw set accepted")
    for value in (float("nan"), float("inf")):
        bad = deepcopy(pairs)
        bad[0]["candidate"]["now_auc"] = value
        try:
            verdict(bad, config)
        except ValueError:
            pass
        else:
            raise AssertionError("nonfinite guard accepted")
    cf_config = read(ROOT / "experiments/cf_hard_pool_v1/registration.json")
    cf_pairs = deepcopy(pairs)
    for pair in cf_pairs:
        for arm in (pair["baseline"], pair["candidate"]):
            arm["veer_rollouts"] = 8
            arm["now_label_counts"] = {"positive": 100, "negative": 100}
            arm["label_counts_by_world"] = {
                w: {"positive": 40, "negative": 40}
                for w in cf_config["bars"]["guard_worlds"]
            }
        pair["candidate"]["veer_all"][0] = 0.86
    assert verdict(cf_pairs, cf_config)["verdict"] == "GO"
    bad = deepcopy(cf_pairs)
    bad[1]["candidate"]["auc_by_world"]["room"] -= 0.021
    assert verdict(bad, cf_config)["verdict"] == "NO-GO"
    bad = deepcopy(cf_pairs)
    bad[0]["candidate"]["veer_all"][0] = 0.79
    bad[1]["candidate"]["veer_all"][0] = 1.0
    assert verdict(bad, cf_config)["verdict"] == "NO-GO", "negative seed hidden"
    invalids = [cf_pairs[:2], cf_pairs + cf_pairs[:1]]
    for key, value in (("veer_rollouts", 5), ("veer_all", [0.86, 19])):
        bad = deepcopy(cf_pairs)
        bad[0]["candidate"][key] = value
        invalids.append(bad)
    bad = deepcopy(cf_pairs)
    bad[0]["candidate"]["label_counts_by_world"]["moving"]["negative"] = 0
    invalids.append(bad)
    bad = deepcopy(cf_pairs)
    bad[0]["candidate"]["now_auc"] = float("nan")
    invalids.append(bad)
    for bad in invalids:
        try:
            verdict(bad, cf_config)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid CF evidence accepted")
    assert len(stages(cf_config)) == len(set(stages(cf_config))) == 17
    assert sum(s.startswith("train_") for s in stages(cf_config)) == 6
    assert training_path("legacy_masked", cf_config) == training_path(
        "answerable", cf_config
    )
    with tempfile.TemporaryDirectory(prefix="schedule_layout_selftest_") as tmp:
        path = Path(tmp) / "record.json"
        write_new(path, {"value": np.float32(0.7)})
        files = {str(path): sha(path)}
        verify_files(files)
        try:
            write_new(path, {"replacement": True})
        except FileExistsError:
            pass
        else:
            raise AssertionError("record overwritten")
        path.write_text("changed")
        try:
            verify_files(files)
        except RuntimeError:
            pass
        else:
            raise AssertionError("changed evidence accepted")
        campaign, out = Path(tmp) / "campaign", Path(tmp) / "output"
        campaign.mkdir()
        out.mkdir()
        write_new(campaign / "manifest.json", {"selftest": True})
        with (
            patch(__name__ + ".CAMPAIGN", campaign),
            patch(__name__ + ".OUT", out),
            patch(__name__ + ".check_manifest"),
            patch(__name__ + ".execute") as worker,
        ):

            def produce(stage, directory, config):
                (directory / "evidence.txt").write_text("measured once")
                return {"selftest": stage}

            worker.side_effect = produce
            run_stage("vision", config)
            run_stage("vision", config)
            assert worker.call_count == 1, "completed stage was remeasured"
            (out / "indoor_train").mkdir()
            try:
                run_stage("indoor_train", config)
            except FileExistsError:
                pass
            else:
                raise AssertionError("incomplete stage was silently retried")
            assert worker.call_count == 1
            (out / "vision/evidence.txt").write_text("changed")
            try:
                run_stage("vision", config)
            except RuntimeError:
                pass
            else:
                raise AssertionError("changed stage output was skipped")
            assert worker.call_count == 1
    assert len(stages(config)) == len(set(stages(config))) == 19
    print(
        "SCHEDULE-LAYOUT-STUDY OK: complete draw set, per-seed guards, "
        "finite evidence, immutable records"
    )


def main():
    global CAMPAIGN, OUT, REGISTRATION
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--campaign",
        choices=("schedule_layout_v1", "cf_hard_pool_v1"),
        default="schedule_layout_v1",
    )
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--run", action="store_true")
    mode.add_argument("--stage")
    mode.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    CAMPAIGN = ROOT / "experiments" / args.campaign
    OUT = ROOT / "output" / args.campaign
    REGISTRATION = CAMPAIGN / "registration.json"
    config = read(REGISTRATION)
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "run.lock").open("a") as lock:
        # Workers run under the parent's lock; direct --stage is not an API.
        if args.stage:
            if os.environ.get("SCHEDULE_LAYOUT_PARENT") != str(os.getppid()):
                ap.error("use --run; direct stage execution bypasses the queue lock")
            if args.stage not in stages(config):
                ap.error("stage is not registered")
            run_stage(args.stage, config)
            return
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        manifest = CAMPAIGN / "manifest.json"
        if not manifest.exists():
            frozen = provenance()
            frozen["git_revision"] = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip()
            frozen["started_unix"] = time.time()
            write_new(manifest, frozen)
        check_manifest()
        env = dict(os.environ, SCHEDULE_LAYOUT_PARENT=str(os.getpid()))
        for stage in stages(config):
            with (CAMPAIGN / f"{stage}.log").open("a") as stream:
                print(f"STAGE-START {stage}", flush=True)
                subprocess.run(
                    [
                        sys.executable,
                        "-u",
                        "-m",
                        "scripts.schedule_layout_study",
                        "--campaign",
                        args.campaign,
                        "--stage",
                        stage,
                    ],
                    cwd=ROOT,
                    env=env,
                    stdout=stream,
                    stderr=subprocess.STDOUT,
                    check=True,
                )
        check_manifest()
        print(
            config.get("completion_marker", "SCHEDULE-LAYOUT-STUDY COMPLETE"),
            flush=True,
        )


if __name__ == "__main__":
    main()

"""Fixed executed/CF label diagnostic; --run, --verify, or --selftest.

No pixels, inference, model weights, generated courses or changed targets.
"""

import argparse
import fcntl
import platform
import sys
from pathlib import Path

import numpy as np

from datasets.intervention_labels import HORIZONS, RADII, counterfactual_labels
from eval.eval_dataset_support import load_metadata
from planner.action_set import ACTION_NAMES, ACTION_VECS
from scripts.schedule_layout_study import read, sha, verify_files, write_new
from sim.envs import CTRL_HZ
from world_model.training import _index_samples, _split_rollouts
from world_model.veer_probe import select

ROOT = Path(__file__).resolve().parents[2]
FOLDER = Path(__file__).resolve().parent
OUT = ROOT / "output/executed_cf_agreement_v1"


def identity(config):
    previous = read(ROOT / config["source_folder"] / "manifest.json")
    for key in ("sources", "inputs", "protected"):
        verify_files(previous[key])
    inputs = {str(ROOT / p): h for p, h in config["inputs"].items()}
    verify_files(inputs)
    return {
        "sources": {
            str(FOLDER / n): sha(FOLDER / n)
            for n in ("audit.py", "definition.md", "registration.json")
        },
        "original_sources": previous["sources"],
        "inputs": inputs,
        "protected": previous["protected"],
        "runtime": {
            "python": sys.version,
            "numpy": np.__version__,
            "platform": platform.platform(),
        },
    }


def geometry(data, tolerance):
    """Independent instantaneous-distance reconstruction, no CF routine used."""
    if data["world_names"].tolist() != ["classic", "dense", "moving", "room"]:
        raise ValueError("unexpected dataset world catalog")
    if list(data["horizons"]) != list(HORIZONS):
        raise ValueError("dataset horizon mismatch")
    r_count, length = data["dists"].shape
    if data["pos"].shape != (r_count, length, 3):
        raise ValueError("wrong position dimensions")
    transit = np.flatnonzero(data["world_id"] < 3)
    if (
        not np.isfinite(data["pos"][transit]).all()
        or not np.isfinite(data["dists"][transit]).all()
    ):
        raise ValueError("nonfinite transit observations")
    if (
        not np.isfinite(data["speed"][transit]).all()
        or (data["speed"][transit] <= 0).any()
    ):
        raise ValueError("invalid speed")
    ids = data["act_id"][transit]
    if (
        ids.dtype.kind not in "iu"
        or not np.isin(ids, np.arange(len(ACTION_NAMES))).all()
    ):
        raise ValueError("invalid action id")
    expected = data["speed"][transit, None, None] * ACTION_VECS[ids]
    if not np.allclose(expected, data["actions"][transit], rtol=1e-5, atol=1e-6):
        raise ValueError("action ids do not match physical commands")
    rows = {}
    for wid in range(3):
        rolls = np.flatnonzero(data["world_id"] == wid)
        maximum, worst = 0.0, None
        for r in rolls:
            pil, vel = data["pillars"][r], data["pillar_vel"][r]
            if not np.array_equal(np.isnan(pil[:, 0]), np.isnan(pil[:, 1])):
                raise ValueError("partly padded pillar")
            keep = ~np.isnan(pil[:, 0])
            pil, vel = pil[keep], vel[keep]
            if not np.isfinite(pil).all() or not np.isfinite(vel).all():
                raise ValueError("nonfinite pillar geometry")
            if len(pil):
                moving = (
                    pil[None] + np.arange(length)[:, None, None] / CTRL_HZ * vel[None]
                )
                reconstructed = np.linalg.norm(
                    data["pos"][r, :, None, :2] - moving, axis=-1
                ).min(axis=1)
            else:
                reconstructed = np.full(length, 9.0)
            errors = np.abs(reconstructed - data["dists"][r])
            t = int(errors.argmax())
            if errors[t] > maximum:
                maximum, worst = float(errors[t]), [int(r), t]
        rows[str(data["world_names"][wid])] = {
            "courses": len(rolls),
            "frames": len(rolls) * length,
            "maximum_absolute_error_m": maximum,
            "worst_pair": worst,
            "within_tolerance": maximum <= tolerance,
        }
    return rows


def confusion(executed, cf, visible, rolls):
    executed, cf, visible, rolls = map(np.asarray, (executed, cf, visible, rolls))
    if executed.ndim != 1 or any(
        a.shape != executed.shape for a in (cf, visible, rolls)
    ):
        raise ValueError("aligned label vectors required")
    if any(not np.isin(a, [0, 1]).all() for a in (executed, cf, visible)):
        raise ValueError("binary targets and answerability required")
    if rolls.dtype.kind not in "iu" or (rolls < 0).any():
        raise ValueError("nonnegative integer course identities required")
    result = {}
    for value, name in ((1, "answerable"), (0, "masked")):
        selected = visible == value
        cells = {}
        for e in (0, 1):
            for c in (0, 1):
                use = selected & (executed == e) & (cf == c)
                cells[f"executed{e}_cf{c}"] = {
                    "windows": int(use.sum()),
                    "courses": len(np.unique(rolls[use])),
                    "course_ids": np.unique(rolls[use]).tolist(),
                }
        conflict = selected & (executed != cf)
        total, disagreed = int(selected.sum()), int(conflict.sum())
        assert sum(row["windows"] for row in cells.values()) == total
        result[name] = {
            "windows": total,
            "courses": len(np.unique(rolls[selected])),
            "matrix": cells,
            "disagreement_windows": disagreed,
            "disagreement_courses": len(np.unique(rolls[conflict])),
            "disagreement_rate": disagreed / total if total else None,
        }
    assert sum(row["windows"] for row in result.values()) == len(executed)
    return result


def probe_comparison(data, pairs, cf, visible, cells):
    probe = select(data)
    pp = probe["veer_pairs"]
    left, right = [ACTION_NAMES.index(a) for a in ("veer_left", "veer_right")]
    c_left, c_right = [cf[pp[:, 0], pp[:, 1], a, -1, 0] for a in (left, right)]
    truth_matches = (c_left != c_right) & ((c_left < c_right) == probe["veer_gt_left"])
    answerable = visible[pp[:, 0], pp[:, 1], left].astype(bool) & visible[
        pp[:, 0], pp[:, 1], right
    ].astype(bool)
    rows, intersections = {}, {}
    selected_set = set(map(tuple, pp.tolist()))
    for wid in range(3):
        use = probe["veer_world_id"] == wid
        rows[str(data["world_names"][wid])] = {
            "frames": int(use.sum()),
            "courses": len(np.unique(pp[use, 0])),
            "cf_truth_mismatch_frames": int((use & ~truth_matches).sum()),
            "both_cf_answerable_frames": int((use & answerable).sum()),
        }
    for world, action in cells:
        wid, aid = list(data["world_names"]).index(world), ACTION_NAMES.index(action)
        use = (data["world_id"][pairs[:, 0]] == wid) & (
            data["act_id"][pairs[:, 0], pairs[:, 1]] == aid
        )
        chosen = pairs[use]
        probe_world = pp[probe["veer_world_id"] == wid]
        intersections[f"{world}/{action}"] = {
            "executed_windows": len(chosen),
            "executed_courses": len(np.unique(chosen[:, 0])),
            "shared_frames": len(set(map(tuple, chosen.tolist())) & selected_set),
            "shared_courses": len(set(chosen[:, 0]) & set(probe_world[:, 0])),
        }
    return {"worlds": rows, "domain_intersection": intersections}


def analyze(config):
    if (
        list(HORIZONS) != config["horizons"]
        or CTRL_HZ != config["control_hz"]
        or not np.isclose(RADII[0], config["warn_radius"])
    ):
        raise ValueError("instrument constants differ from registration")
    source = ROOT / config["source_folder"]
    assert read(source / "report.json")["decision"]["verdict"] == "NO-GO"
    loaded = {
        name: load_metadata(ROOT / path) for name, path in config["datasets"].items()
    }
    checks = {
        name: geometry(data, config["clearance_absolute_tolerance_m"])
        for name, data in loaded.items()
    }
    output = {
        "scope": config["scope"],
        "instrument": checks,
        "inputs": {},
        "original_verdict": "NO-GO",
    }
    if not all(
        row["within_tolerance"] for value in checks.values() for row in value.values()
    ):
        return dict(output, status="INSTRUMENT_FAILURE")
    for name, data in loaded.items():
        pairs, labels = _index_samples(data)
        cf, visible = counterfactual_labels(data)
        rr, tt = pairs.T
        aa = data["act_id"][rr, tt]
        # Room IDs name a different action catalog; gather only transit rows.
        transit = data["world_id"][rr] < 3
        cf_selected = np.zeros(len(pairs), dtype=np.uint8)
        vis_selected = np.zeros(len(pairs), dtype=np.uint8)
        cf_selected[transit] = cf[rr[transit], tt[transit], aa[transit], -1, 0]
        vis_selected[transit] = visible[rr[transit], tt[transit], aa[transit]]
        partitions = {}
        if name == "exam":
            n, room = (
                config["exam_transit_courses_per_block"],
                config["exam_room_courses"],
            )
            assert np.array_equal(
                data["study_timing_block"], np.repeat([0, 1, 2], [n, n, room])
            )
            partitions = {
                block: np.flatnonzero(data["study_timing_block"] == i)
                for i, block in enumerate(("approach", "immediate"))
            }
        else:
            saved = read(source / "support" / f"{name}_support.json")
            for seed in config["seeds"]:
                train, _ = _split_rollouts(data, np.random.default_rng(seed))
                previous = sorted(
                    r
                    for w in saved["splits"][str(seed)]["train"]["worlds"].values()
                    for r in w["rollout_ids"]
                )
                assert train == previous, "training memberships changed"
                partitions[f"train_seed{seed}"] = np.asarray(train)
        readings = {}
        for part, rolls in partitions.items():
            selected = np.isin(rr, rolls)
            rows = {}
            for world, action in config["cells"]:
                wid, aid = list(data["world_names"]).index(world), ACTION_NAMES.index(
                    action
                )
                use = selected & (data["world_id"][rr] == wid) & (aa == aid)
                rows[f"{world}/{action}"] = confusion(
                    labels[use, -1, 0], cf_selected[use], vis_selected[use], rr[use]
                )
            readings[part] = rows
        output["inputs"][name] = {
            "partitions": readings,
            "probe": probe_comparison(data, pairs, cf, visible, config["cells"]),
        }
    return dict(output, status="COMPLETE")


def selftest():
    from datasets.combine_rollouts import _synth
    from world_model.veer_probe import fixture

    r = confusion([0, 1, 0, 1], [0, 0, 1, 1], [1, 1, 0, 0], [0, 0, 1, 2])
    assert r["answerable"]["disagreement_rate"] == 0.5
    assert r["answerable"]["disagreement_courses"] == 1
    assert r["masked"]["disagreement_windows"] == 1
    empty = confusion([], [], [], np.array([], dtype=int))
    assert empty["answerable"]["disagreement_rate"] is None
    for values in (([2], [0], [1], [0]), ([0], [0], [3], [0]), ([0], [0], [1], [-1])):
        try:
            confusion(*values)
        except ValueError:
            pass
        else:
            raise AssertionError("malformed targets accepted")
    # A stationary flown path versus a commanded kinematic right veer.
    # Instrument distances agree exactly; supervision can still disagree.
    data = _synth([0, 1, 2], length=40)
    data["world_names"] = np.array(["classic", "dense", "moving", "room"])
    data["pillars"][:] = [0.8, -0.2]
    data["dists"][:] = np.linalg.norm(data["pillars"][0, 0])
    data["act_id"][:] = 3
    data["actions"][:] = ACTION_VECS[3]
    assert all(r["within_tolerance"] for r in geometry(data, 1e-4).values())
    pairs, labels = _index_samples(data)
    cf, vis = counterfactual_labels(data)
    rr, tt = pairs.T
    result = confusion(labels[:, -1, 0], cf[rr, tt, 3, -1, 0], vis[rr, tt, 3], rr)
    assert result["answerable"]["disagreement_windows"] == len(pairs) == 24
    assert result["answerable"]["matrix"]["executed0_cf1"]["courses"] == 3
    data["dists"][0, 0] += 0.01
    assert not geometry(data, 1e-4)["classic"]["within_tolerance"]
    data["pillars"][:] = [0.2, 0.8]
    data["dists"][:] = np.linalg.norm(data["pillars"][0, 0])
    data["act_id"][:] = 2
    data["actions"][:] = ACTION_VECS[2]
    cf, vis = counterfactual_labels(data)
    result = confusion(labels[:, -1, 0], cf[rr, tt, 2, -1, 0], vis[rr, tt, 2], rr)
    assert result["answerable"]["windows"] == 0
    assert result["masked"]["disagreement_windows"] == 24
    data = fixture()
    data["frames"] = np.empty((5, 3, 0, 0, 3), dtype=np.uint8)
    cf, vis = counterfactual_labels(data)
    report = probe_comparison(
        data, np.array([[0, 0], [1, 0]]), cf, vis, [("dense", "veer_right")]
    )
    assert report["worlds"]["classic"]["frames"] == 2
    assert report["worlds"]["dense"]["cf_truth_mismatch_frames"] == 0
    assert report["worlds"]["dense"]["both_cf_answerable_frames"] == 2
    assert report["domain_intersection"]["dense/veer_right"]["shared_frames"] == 0
    print(
        "EXECUTED CF AGREEMENT OK: geometry, conflicting targets, masks, probe, nulls"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--selftest", action="store_true")
    modes.add_argument("--run", action="store_true")
    modes.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return
    config = read(FOLDER / "registration.json")
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "runner.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
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
        print("EXECUTED CF AGREEMENT", result["status"], flush=True)
        if result["status"] != "COMPLETE":
            raise SystemExit(2)


if __name__ == "__main__":
    main()

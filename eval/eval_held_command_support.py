"""Registered repeated-command support audit; no pixels, model calls or new data.

python -m eval.eval_held_command_support --selftest
python -m eval.eval_held_command_support
python -m eval.eval_held_command_support --verify
"""

import argparse
import json
from pathlib import Path

import numpy as np

from datasets.intervention_labels import HORIZONS, window_valid
from datasets.provenance import file_identity
from planner.action_set import ACTION_NAMES, ACTION_VECS
from planner.nav_action_set import NAV_ACTION_NAMES, NAV_ACTION_VECS
from world_model.checkpoint_io import check_destination, publish_checkpoint
from world_model.training import _index_samples

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "experiments/held_command_support_v1"
CATALOGS = {
    name: (ACTION_NAMES, ACTION_VECS) for name in ("classic", "dense", "moving")
}
CATALOGS["room"] = (NAV_ACTION_NAMES, NAV_ACTION_VECS)
FIELDS = ("seg", "actions", "act_id", "speed", "dists", "world_id", "world_names")


def masks(actions, seg, horizon):
    """Use the frozen inclusive endpoint convention for both eligibility rules."""
    actions, seg = np.asarray(actions), np.asarray(seg)
    if (
        actions.ndim != 3
        or actions.shape[-1] != 4
        or actions.dtype.kind not in "fiu"
        or not np.isfinite(actions).all()
        or seg.shape != actions.shape[:2]
        or seg.dtype.kind not in "iu"
        or (seg < 0).any()
        or (seg[:, 1:] < seg[:, :-1]).any()
    ):
        raise ValueError(
            "finite commands and monotonic nonnegative segment IDs required"
        )
    if type(horizon) is not int or not 0 < horizon < seg.shape[1]:
        raise ValueError("horizon must fit inside the rollout")
    command_change = (actions[:, 1:] != actions[:, :-1]).any(axis=-1)
    segment_change = seg[:, 1:] != seg[:, :-1]
    cumulative = np.pad(command_change.cumsum(axis=1), ((0, 0), (1, 0)))
    constant = cumulative[:, horizon:] == cumulative[:, :-horizon]
    original = seg[:, horizon:] == seg[:, :-horizon]
    if (original & ~constant).any():
        raise ValueError("an original accepted window contains changing commands")
    return original, constant, segment_change & ~command_change, command_change


def support(mask, labels):
    rows, _ = np.nonzero(mask)
    positive = labels[mask]
    return {
        "windows": int(mask.sum()),
        "rollouts": int(len(np.unique(rows))),
        "positive": int(positive.sum()),
        "negative": int((~positive).sum()),
        "positive_rollouts": int(len(np.unique(rows[positive]))),
        "negative_rollouts": int(len(np.unique(rows[~positive]))),
    }


def analyze(data, horizon=32, radius=0.7):
    original, constant, repeated, changes = masks(data["actions"], data["seg"], horizon)
    r, length = data["seg"].shape
    names, world_id = np.asarray(data["world_names"]), np.asarray(data["world_id"])
    ids, speed, distances = [
        np.asarray(data[key]) for key in ("act_id", "speed", "dists")
    ]
    if (
        names.ndim != 1
        or names.dtype.kind != "U"
        or not len(names)
        or len(set(names)) != len(names)
        or any(name not in CATALOGS for name in names)
        or world_id.shape != (r,)
        or world_id.dtype.kind not in "iu"
        or (world_id < 0).any()
        or (world_id >= len(names)).any()
        or ids.shape != (r, length)
        or ids.dtype.kind not in "iu"
        or speed.shape != (r,)
        or speed.dtype.kind not in "fiu"
        or not np.isfinite(speed).all()
        or (speed <= 0).any()
        or distances.shape != (r, length)
        or distances.dtype.kind not in "fiu"
        or not np.isfinite(distances).all()
        or not np.isfinite(radius)
        or radius <= 0
    ):
        raise ValueError("invalid corpus world/action/distance metadata")
    labels = (
        np.lib.stride_tricks.sliding_window_view(distances, horizon + 1, axis=1).min(
            axis=-1
        )
        < radius
    )
    choices = {
        "original": original,
        "recovered": constant & ~original,
        "union": constant,
    }

    def describe(selected):
        return {key: support(mask & selected, labels) for key, mask in choices.items()}

    worlds = {}
    for wid, world in enumerate(names):
        rows = world_id == wid
        action_names, vectors = CATALOGS[world]
        action_ids = ids[rows]
        if (action_ids < 0).any() or (action_ids >= len(action_names)).any():
            raise ValueError(f"invalid action IDs for {world}")
        expected = speed[rows, None, None] * vectors[action_ids]
        if not np.allclose(data["actions"][rows], expected, rtol=1e-5, atol=1e-6):
            raise ValueError(f"action IDs disagree with physical commands in {world}")
        worlds[str(world)] = {
            "rollouts": int(rows.sum()),
            "possible_windows": int(rows.sum()) * (length - horizon),
            "same_command_segment_boundaries": int(repeated[rows].sum()),
            "true_command_changes": int(changes[rows].sum()),
            **describe(rows[:, None]),
            "actions": {
                action: describe(rows[:, None] & (ids[:, : length - horizon] == aid))
                for aid, action in enumerate(action_names)
            },
        }
    return {
        "rollouts": r,
        "length": length,
        "horizon": horizon,
        "warn_radius": radius,
        "possible_windows": r * (length - horizon),
        **describe(np.ones_like(original)),
        "worlds": worlds,
    }


def checked(entry):
    path = ROOT / entry["path"]
    if file_identity(path)["sha256"] != entry["sha256"]:
        raise ValueError(f"registered input changed: {entry['path']}")
    return path


def load_metadata(path):
    with np.load(path, allow_pickle=False) as blob:
        data = {key: blob[key] for key in FIELDS}
        if not np.array_equal(blob["horizons"], HORIZONS):
            raise ValueError("corpus horizons differ from the registration")
    return data


def run():
    registration = CAMPAIGN / "registration.json"
    identity = file_identity(registration)
    config = json.loads(registration.read_text())
    if tuple(HORIZONS) != (4, 8, 16, 32) or config["horizon"] != 32:
        raise ValueError("audit requires the registered standard horizons")
    for path, digest in config["reference_sources"].items():
        checked({"path": path, "sha256": digest})
    results = {}
    for item in config["inputs"]:
        data = load_metadata(checked(item["dataset"]))
        row = analyze(data, config["horizon"], config["warn_radius"])
        receipt = json.loads(checked(item["receipt"]).read_text())
        assert item["dataset"]["sha256"] in receipt["files"].values()
        assert set(row["worlds"]) == set(config["worlds"]) == set(receipt["result"])
        for world, reading in row["worlds"].items():
            old = receipt["result"][world]
            assert reading["rollouts"] == old["rollouts"]
            for label in ("positive", "negative"):
                assert reading["original"][label] == old[label], (world, label)
        # Shape-only placeholder for the original index; no pixels are decoded.
        shape = (*data["seg"].shape, 0, 0, 3)
        index, labels = _index_samples(
            dict(data, frames=np.empty(shape, dtype=np.uint8))
        )
        old_mask = masks(data["actions"], data["seg"], config["horizon"])[0]
        np.testing.assert_array_equal(index.reshape(-1, 2), np.argwhere(old_mask))
        old_truth = np.array(
            [
                data["dists"][r, t : t + 33].min() < config["warn_radius"]
                for r, t in index
            ]
        )
        np.testing.assert_array_equal(labels[:, -1, 0], old_truth)
        checked(item["dataset"])
        checked(item["receipt"])
        results[item["name"]] = {"dataset": item["dataset"], **row}
    if file_identity(registration) != identity:
        raise ValueError("registration changed during audit")
    for path, digest in config["reference_sources"].items():
        checked({"path": path, "sha256": digest})
    return {
        "scope": "Retrospective metadata support; no new independent courses, model "
        "inference, resampling, changed index or scientific gate.",
        "registration_sha256": identity["sha256"],
        "inputs": results,
    }


def summary(report):
    lines = [
        "# Repeated-command window support",
        "",
        "Saved metadata only. Original indices, labels and closed NO-GOs "
        "are unchanged.",
        "Recovered windows cross a segment boundary while the commanded four-vector",
        "stays exactly constant over the existing inclusive horizon-32 window.",
        "",
        "| Corpus / world | Original windows | Recovered | Union | "
        "Same-command boundaries |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, data in report["inputs"].items():
        for world, row in data["worlds"].items():
            lines.append(
                f"| {name} / {world} | {row['original']['windows']} | "
                f"{row['recovered']['windows']} | {row['union']['windows']} | "
                f"{row['same_command_segment_boundaries']} |"
            )
    for name, data in report["inputs"].items():
        lines += [
            "",
            f"## {name}: every action",
            "",
            "Positive / negative distinct-course counts are original → union.",
            "Recovered windows can come from courses already represented; counts",
            "overlap across actions/classes and must not be summed "
            "as independent trials.",
            "",
            "| World / action | Recovered + / − windows | Positive courses | "
            "Negative courses |",
            "|---|---:|---:|---:|",
        ]
        for world, row in data["worlds"].items():
            for action, counts in row["actions"].items():
                old, extra, union = [
                    counts[k] for k in ("original", "recovered", "union")
                ]
                lines.append(
                    f"| {world} / {action} | "
                    f"{extra['positive']} / {extra['negative']} | "
                    f"{old['positive_rollouts']} → {union['positive_rollouts']} | "
                    f"{old['negative_rollouts']} → {union['negative_rollouts']} |"
                )
    lines += [
        "",
        "Full original/recovered/union class and course counts: [report](report.json).",
        "No extra samples were admitted to training or evaluation. This establishes",
        "available commanded-intent support, not model quality, rendering, causal",
        "benefit or statistical power. No bootstrap or model-promotion gate follows.",
        "A future recipe must preserve split identity and account for changes in",
        "optimizer-step and CF/now sampling counts. See [registration](definition.md).",
        "",
    ]
    return "\n".join(lines)


def selftest():
    import tempfile

    rng = np.random.default_rng(9)
    seg = np.repeat(np.arange(14), 5)[None, :].repeat(4, axis=0)
    world_names = np.array(list(CATALOGS))
    ids = np.empty_like(seg)
    actions = np.empty((*seg.shape, 4), dtype=np.float32)
    for r, world in enumerate(world_names):
        names, vectors = CATALOGS[world]
        ids[r] = np.repeat(rng.integers(len(names), size=14), 5)
        actions[r] = vectors[ids[r]]
    data = dict(
        seg=seg,
        actions=actions,
        act_id=ids,
        speed=np.ones(4),
        world_names=world_names,
        world_id=np.arange(4),
        dists=rng.uniform(0.2, 1.1, size=seg.shape),
    )
    for horizon in (1, 4, 8, 32):
        old, constant, _, _ = masks(actions, seg, horizon)
        loop_old = np.array(
            [[window_valid(s, t, horizon) for t in range(70 - horizon)] for s in seg]
        )
        loop_constant = np.array(
            [
                [
                    np.array_equal(
                        a[t : t + horizon + 1], np.broadcast_to(a[t], (horizon + 1, 4))
                    )
                    for t in range(70 - horizon)
                ]
                for a in actions
            ]
        )
        np.testing.assert_array_equal(old, loop_old)
        np.testing.assert_array_equal(constant, loop_constant)
        row = analyze(data, horizon)
        assert (
            row["union"]["windows"]
            == row["original"]["windows"] + row["recovered"]["windows"]
        )
        assert (
            sum(w["recovered"]["windows"] for w in row["worlds"].values())
            == row["recovered"]["windows"]
        )
    repeated = np.zeros((1, 6, 4))
    segments = np.array([[0, 0, 0, 1, 1, 1]])
    old, union, boundaries, _ = masks(repeated, segments, 2)
    assert old.tolist() == [[True, False, False, True]]
    assert union.all() and boundaries.sum() == 1
    repeated[0, 3:, 0] = 1
    assert np.array_equal(masks(repeated, segments, 2)[1], old)
    repeated[0, 3:, 0] = np.nextafter(0.0, 1.0)
    assert np.array_equal(
        masks(repeated, segments, 2)[1], old
    ), "equality must be exact"
    fixture = dict(
        seg=np.tile(segments, (3, 1)),
        actions=np.broadcast_to(ACTION_VECS[0], (3, 6, 4)).copy(),
        act_id=np.zeros((3, 6), dtype=int),
        speed=np.ones(3),
        world_id=np.zeros(3, dtype=int),
        world_names=np.array(["classic"]),
        dists=np.array([[0.2] * 6, [0.9] * 6, [0.2, 0.9, 0.9, 0.9, 0.9, 0.2]]),
    )
    counts = analyze(fixture, 2)
    assert counts["original"] == dict(
        windows=6,
        rollouts=3,
        positive=4,
        negative=2,
        positive_rollouts=2,
        negative_rollouts=1,
    )
    assert counts["recovered"] == dict(
        windows=6,
        rollouts=3,
        positive=2,
        negative=4,
        positive_rollouts=1,
        negative_rollouts=2,
    )
    assert counts["union"] == dict(
        windows=12,
        rollouts=3,
        positive=6,
        negative=6,
        positive_rollouts=2,
        negative_rollouts=2,
    )
    assert counts["worlds"]["classic"]["actions"]["veer_left"]["union"]["windows"] == 0
    with tempfile.TemporaryDirectory(prefix="held_command_selftest_") as folder:
        path = Path(folder) / "metadata.npz"
        np.savez(
            path, **fixture, horizons=HORIZONS, frames=np.array([{}], dtype=object)
        )
        loaded = load_metadata(path)  # Reading frames would fail allow_pickle=False.
        assert "frames" not in loaded and analyze(loaded, 2) == counts
    for bad in (seg.astype(float), -seg, np.zeros_like(seg)):
        try:
            masks(actions, bad, 4)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid segment metadata accepted")
    corrupt = dict(data, act_id=np.full_like(ids, 999))
    try:
        analyze(corrupt)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid action catalog accepted")
    print(
        "HELD-COMMAND SUPPORT OK: independent window oracle, boundaries, "
        "exact intent, both catalogs"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return
    paths = [CAMPAIGN / "report.json", CAMPAIGN / "summary.md"]
    if not args.verify:
        for path in paths:
            check_destination(path)
    result = run()
    text = summary(result)
    if args.verify:
        assert json.loads(paths[0].read_text()) == result
        assert paths[1].read_text() == text
        print(
            "HELD-COMMAND SUPPORT VERIFIED: unchanged inputs, original support, "
            "saved counts"
        )
    else:
        for path, payload in zip(
            paths, [json.dumps(result, indent=2, allow_nan=False) + "\n", text]
        ):
            publish_checkpoint(
                path, lambda stream, value=payload: stream.write(value.encode())
            )
        print(
            "HELD-COMMAND SUPPORT COMPLETE: two fixed corpora, "
            "no changed scientific gate"
        )


if __name__ == "__main__":
    main()

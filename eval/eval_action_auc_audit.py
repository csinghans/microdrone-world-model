"""Decompose immutable executed_weight_v1 scores by executed action; no inference.

python -m eval.eval_action_auc_audit --selftest
python -m eval.eval_action_auc_audit
python -m eval.eval_action_auc_audit --verify
"""

import argparse
import io
import json
from pathlib import Path

import numpy as np

from datasets.provenance import file_identity
from eval.compare_wm_scores import _load, _validate
from planner.action_set import ACTION_NAMES, ACTION_VECS
from world_model.auc_decomposition import decompose
from world_model.checkpoint_io import check_destination, publish_checkpoint

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "experiments/action_auc_audit_v1"


def checked(entry):
    path = ROOT / entry["path"]
    if file_identity(path)["sha256"] != entry["sha256"]:
        raise ValueError(f"frozen input changed: {entry['path']}")
    return path


def link_actions(export, data, world):
    pairs = export["pairs"]
    shape = data["act_id"].shape
    if len(shape) != 2 or data["actions"].shape != (*shape, 4):
        raise ValueError("invalid dataset action shapes")
    if data["world_id"].shape != (shape[0],) or data["speed"].shape != (shape[0],):
        raise ValueError("invalid rollout metadata shapes")
    if (
        pairs.ndim != 2
        or pairs.shape[1] != 2
        or not np.issubdtype(pairs.dtype, np.integer)
        or (pairs < 0).any()
        or (pairs[:, 0] >= shape[0]).any()
        or (pairs[:, 1] >= shape[1]).any()
    ):
        raise ValueError("export pairs outside dataset bounds")
    if not np.array_equal(export["world_names"], data["world_names"]):
        raise ValueError("world catalogs differ")
    if not np.array_equal(export["world_id"], data["world_id"][pairs[:, 0]]):
        raise ValueError("export world differs from dataset rollout")
    ids = np.flatnonzero(data["world_names"] == world)
    if len(ids) != 1:
        raise ValueError(f"world missing or duplicated: {world}")
    mask = export["world_id"] == ids[0]
    selected = pairs[mask]
    if not len(selected):
        raise ValueError(f"no saved scores for required world: {world}")
    rolls, times = selected.T
    actions = data["act_id"][rolls, times]
    if (
        not np.issubdtype(actions.dtype, np.integer)
        or (actions < 0).any()
        or (actions >= len(ACTION_NAMES)).any()
    ):
        raise ValueError("invalid transit action ids")
    expected = data["speed"][rolls, None] * ACTION_VECS[actions]
    if not np.allclose(expected, data["actions"][rolls, times], rtol=1e-5, atol=1e-6):
        raise ValueError("action ids do not match physical commands")
    return mask, actions, rolls


def analyze():
    config = json.loads((CAMPAIGN / "registration.json").read_text())
    if config["action_names"] != ACTION_NAMES or config["horizon"] != 32:
        raise ValueError("catalog/horizon differs from frozen diagnostic")
    entries = [config[k] for k in ("dataset", "holdout_receipt", "report_receipt")]
    entries += [m[k] for m in config["models"] for k in ("scores", "receipt")]
    for entry in entries:
        checked(entry)
    with np.load(checked(config["dataset"]), allow_pickle=False) as blob:
        data = {
            k: blob[k]
            for k in ("act_id", "actions", "speed", "world_id", "world_names")
        }
    original = json.loads(checked(config["report_receipt"]).read_text())["result"]
    if original["decision"]["verdict"] != "NO-GO":
        raise ValueError("closed source verdict changed")
    expected_models = {
        (arm, seed) for arm in ("unit", "moving_2p25") for seed in range(3)
    }
    if (
        len(config["models"]) != 6
        or {(m["arm"], m["seed"]) for m in config["models"]} != expected_models
    ):
        raise ValueError("all six original models are required")
    worlds = {name: {"models": [], "paired_deltas": []} for name in config["worlds"]}
    first = None
    for model in config["models"]:
        export = _load(checked(model["scores"]))
        _validate(export if first is None else first, export)
        first = export if first is None else first
        receipt = json.loads(checked(model["receipt"]).read_text())
        if export["metadata"] != receipt["result"]["scores"]:
            raise ValueError("score export differs from original receipt")
        if (
            export["metadata"]["provenance"]["dataset"]["sha256"]
            != config["dataset"]["sha256"]
        ):
            raise ValueError("score export belongs to another dataset")
        if export["metadata"]["training_seed"] != model["seed"]:
            raise ValueError("score export belongs to another training seed")
        for world, row in worlds.items():
            mask, actions, rolls = link_actions(export, data, world)
            result = decompose(
                export["scores"][mask, -1],
                export["labels"][mask, -1],
                actions,
                rolls,
                ACTION_NAMES,
            )
            expected = export["metadata"]["auc_by_world"][world]
            if not np.isclose(
                result["auc"], expected, rtol=0, atol=config["reconstruction_tolerance"]
            ):
                raise ValueError(f"{world}: pooled AUC differs from archived metric")
            row["models"].append(dict(arm=model["arm"], seed=model["seed"], **result))
    for world, row in worlds.items():
        for seed in range(3):
            a, b = [
                next(m for m in row["models"] if (m["seed"], m["arm"]) == (seed, arm))
                for arm in ("unit", "moving_2p25")
            ]
            if a["groups"] != b["groups"] or a["total_pairs"] != b["total_pairs"]:
                raise ValueError("paired action support differs")
            delta = {"seed": seed, "auc": b["auc"] - a["auc"]}
            for part in ("within", "across"):
                if a[part]["share"] != b[part]["share"]:
                    raise ValueError("paired score-comparison mass differs")
                delta[part] = b[part]["contribution"] - a[part]["contribution"]
            expected = original["paired_auc_summary"][world]["paired_deltas"][seed]
            if not np.allclose(
                [delta["auc"], delta["within"] + delta["across"]],
                expected,
                rtol=0,
                atol=config["reconstruction_tolerance"],
            ):
                raise ValueError(
                    "decomposed change differs from original paired change"
                )
            row["paired_deltas"].append(delta)
        row["mean_deltas"] = {
            k: float(np.mean([d[k] for d in row["paired_deltas"]]))
            for k in ("auc", "within", "across")
        }
    for entry in entries:
        checked(entry)
    return {
        "scope": "Retrospective decomposition of fixed saved scores; no inference, "
        "resampling, new gate or causal attribution. Pair products are not "
        "independent samples.",
        "registration": file_identity(CAMPAIGN / "registration.json"),
        "instrument_sha256": {
            path: file_identity(ROOT / path)["sha256"]
            for path in (
                "eval/eval_action_auc_audit.py",
                "eval/compare_wm_scores.py",
                "world_model/auc_decomposition.py",
                "world_model/metrics.py",
                "planner/action_set.py",
            )
        },
        "source_verdict": original["decision"]["verdict"],
        "worlds": worlds,
    }


def summary(report):
    def score(value):
        return "undefined" if value is None else f"{value:.4f}"

    lines = [
        "# Action-pair AUC audit — source study remains NO-GO",
        "",
        "Generated from the six saved `executed_weight_v1` score exports.",
        "No fitting, model inference, new courses, bootstrap or changed verdict.",
        "",
        "An AUC compares positive and negative windows. The matrix groups each",
        "comparison by both windows' executed action categories. Diagonal cells",
        "compare the same category; off-diagonal cells compare different categories.",
        "Both contributions are weighted by their share of all score pairs.",
        "",
        "![Moving AUC decomposition](moving_contributions.png)",
        "",
        "## Comparison support",
        "",
        "| World | Windows | Courses | Positive / negative | Same-action pair share |",
        "|---|---:|---:|---:|---:|",
    ]
    for world, row in report["worlds"].items():
        r = row["models"][0]
        lines.append(
            f"| {world} | {r['samples']} | {r['rollouts']} | "
            f"{r['positive']} / {r['negative']} | {r['within']['share']:.2%} |"
        )
    for world, row in report["worlds"].items():
        lines += [
            "",
            f"## {world}: every paired seed",
            "",
            "Control = unit weight; candidate = moving weight 2.25.",
            "",
            "| Seed | Pooled Δ | Within contribution Δ | Across contribution Δ | "
            "Within AUC control → candidate | Across AUC control → candidate |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        for d in row["paired_deltas"]:
            a, b = [
                next(
                    m
                    for m in row["models"]
                    if (m["seed"], m["arm"]) == (d["seed"], arm)
                )
                for arm in ("unit", "moving_2p25")
            ]
            lines.append(
                f"| {d['seed']} | {d['auc']:+.6f} | {d['within']:+.6f} | "
                f"{d['across']:+.6f} | "
                f"{score(a['within']['auc'])} → {score(b['within']['auc'])} | "
                f"{score(a['across']['auc'])} → {score(b['across']['auc'])} |"
            )
        mean = row["mean_deltas"]
        lines += [
            "",
            f"Three-draw mean: pooled {mean['auc']:+.6f} = within "
            f"{mean['within']:+.6f} + across {mean['across']:+.6f}.",
            "",
            "| Action | Positive / negative windows | Positive / negative courses |",
            "|---|---:|---:|",
        ]
        for name, s in row["models"][0]["groups"].items():
            lines.append(
                f"| {name} | {s['positive']} / {s['negative']} | "
                f"{s['positive_rollouts']} / {s['negative_rollouts']} |"
            )
    lines += [
        "",
        "## Interpretation limits",
        "",
        "The contribution split is an exact accounting identity on this fixed exam.",
        "Within-category comparisons still mix speeds, courses and geometry; across-",
        "category comparisons can contain useful scene information. Neither part alone",
        "establishes action memorization, causal perception, or a flight capability.",
        "Course counts may overlap across actions/classes. Windows and their pair",
        "products are not independent trials; no new confidence interval is claimed.",
        "Empty pair cells have null AUC in the complete [JSON matrices](report.json).",
        "The original failed seed and guards remain NO-GO. No candidate is promoted.",
        "",
    ]
    return "\n".join(lines)


def figure(report):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    moving = report["worlds"]["moving"]
    models, deltas = moving["models"], moving["paired_deltas"]
    fig, (left, right) = plt.subplots(1, 2, figsize=(12, 4.7), layout="constrained")
    within = [m["within"]["contribution"] for m in models]
    across = [m["across"]["contribution"] for m in models]
    x = np.arange(6)
    left.bar(x, within, color="#267c9b", label="Same action category")
    left.bar(x, across, bottom=within, color="#df9f42", label="Different categories")
    left.set_xticks(
        x,
        [
            f"{'Control' if m['arm'] == 'unit' else 'Weight 2.25'}\ns{m['seed']}"
            for m in models
        ],
    )
    left.set(
        ylabel="Contribution to pooled AUC",
        ylim=(0, 1),
        title="Moving: complete AUC accounting",
    )
    left.legend(loc="upper center", frameon=False, fontsize=9)
    x = np.arange(3)
    right.bar(
        x - 0.17,
        [d["within"] for d in deltas],
        0.32,
        color="#267c9b",
        label="Within contribution Δ",
    )
    right.bar(
        x + 0.17,
        [d["across"] for d in deltas],
        0.32,
        color="#df9f42",
        label="Across contribution Δ",
    )
    right.plot(
        x, [d["auc"] for d in deltas], "D", color="#263345", label="Pooled Δ (sum)"
    )
    right.axhline(0, color="#64748b", linewidth=0.8)
    right.set_xticks(x, ["Seed 0", "Seed 1", "Seed 2"])
    right.set(ylabel="Candidate − control", title="Every original paired training draw")
    right.legend(loc="upper left", frameon=False, fontsize=9)
    for axis in (left, right):
        axis.spines[["top", "right"]].set_visible(False)
        axis.grid(axis="y", alpha=0.15)
        axis.set_axisbelow(True)
    fig.suptitle(
        "Stored scores only • fixed exam • source verdict stays NO-GO", fontsize=13
    )
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=180)
    plt.close(fig)
    return buffer.getvalue()


def selftest():
    from copy import deepcopy

    from world_model.auc_decomposition import selftest as math_test

    math_test()
    data = dict(
        act_id=np.array([[0, 1], [2, 3]]),
        speed=np.array([1.0, 2.0]),
        world_id=np.array([0, 1]),
        world_names=np.array(["classic", "moving"]),
    )
    data["actions"] = data["speed"][:, None, None] * ACTION_VECS[data["act_id"]]
    export = dict(
        pairs=np.array([[0, 1], [1, 0]]),
        world_id=np.array([0, 1]),
        world_names=data["world_names"],
    )
    mask, ids, rolls = link_actions(export, data, "moving")
    assert (
        mask.tolist() == [False, True] and ids.tolist() == [2] and rolls.tolist() == [1]
    )
    for key, value in (
        ("pairs", np.array([[0, 1], [1, -1]])),
        ("pairs", np.array([[0.0, 1.0], [1.0, 0.0]])),
        ("world_id", np.array([1, 0])),
    ):
        bad = deepcopy(export)
        bad[key] = value
        try:
            link_actions(bad, data, "moving")
        except ValueError:
            pass
        else:
            raise AssertionError("invalid pair/dataset mapping accepted")
    data["actions"][1, 0, 0] += 1
    try:
        link_actions(export, data, "moving")
    except ValueError:
        pass
    else:
        raise AssertionError("mismatched physical action accepted")
    print("ACTION-AUC-AUDIT OK: pure decomposition and strict action/score alignment")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return
    outputs = [
        CAMPAIGN / name
        for name in ("report.json", "summary.md", "moving_contributions.png")
    ]
    if not args.verify:
        for path in outputs:
            check_destination(path)
    report = analyze()
    text = summary(report)
    if args.verify:
        if (
            json.loads(outputs[0].read_text()) != report
            or outputs[1].read_text() != text
        ):
            raise ValueError(
                "saved diagnostic differs from recomputed fixed-score accounting"
            )
        print(
            "ACTION-AUC VERIFIED: all six exports, action mapping, "
            "original AUCs and deltas"
        )
        return
    payloads = [
        (json.dumps(report, indent=2, allow_nan=False) + "\n").encode(),
        text.encode(),
        figure(report),
    ]
    for path, payload in zip(outputs, payloads):
        publish_checkpoint(path, lambda stream, value=payload: stream.write(value))
    print(
        "ACTION-AUC COMPLETE: saved-score accounting only; source verdict remains NO-GO"
    )


if __name__ == "__main__":
    main()

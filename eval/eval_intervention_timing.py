"""Frozen intervention-timing endpoints; no model inference or corpus generation.

python -m eval.eval_intervention_timing --selftest
The study runner supplies complete, independently scored common-exam exports.
"""

import argparse

import numpy as np

from eval.compare_wm_scores import _validate
from eval.eval_action_auc_audit import link_actions
from planner.action_set import ACTION_NAMES
from world_model.metrics import roc_auc
from world_model.training import _index_samples
from world_model.veer_probe import select


def auc_pair(a, b, labels):
    if not np.isin(labels, [0, 1]).all() or len(np.unique(labels)) != 2:
        raise ValueError("required AUC cell lacks both classes")
    aa, bb = roc_auc(a, labels), roc_auc(b, labels)
    return {"baseline": aa, "candidate": bb, "delta": bb - aa}


def primary_bootstrap(a, b, data, masks, config):
    """Paired course draws shared across actions; preserve timing mixture strata."""
    settings = config["bootstrap"]
    if settings["n_boot"] < 1:
        raise ValueError("positive bootstrap count required")
    blocks = data["study_timing_block"]
    worlds = data["world_id"]
    if blocks.shape != worlds.shape or blocks.dtype.kind not in "iu":
        raise ValueError("invalid timing-block identities")
    strata = []
    for world in sorted({w for w, _ in config["primary_cells"]}):
        wid = list(data["world_names"]).index(world)
        if not np.isin(blocks[worlds == wid], [0, 1]).all():
            raise ValueError("transit exam must have approach/immediate blocks")
        for block in (0, 1):
            ids = np.flatnonzero((worlds == wid) & (blocks == block))
            if len(ids) < 2:
                raise ValueError("fewer than two courses in a bootstrap stratum")
            strata.append(ids)
    rng = np.random.default_rng(settings["seed"])
    rows = []
    for mask in masks.values():
        rows.append(
            (
                a["pairs"][mask, 0],
                a["scores"][mask, -1],
                b["scores"][mask, -1],
                a["labels"][mask, -1],
            )
        )
    deltas = []
    for _ in range(settings["n_boot"]):
        chosen = np.concatenate([rng.choice(s, len(s)) for s in strata])
        counts = np.bincount(chosen, minlength=len(worlds))
        cells = []
        for rolls, sa, sb, labels in rows:
            ix = np.repeat(np.arange(len(rolls)), counts[rolls])
            if len(np.unique(labels[ix])) != 2:
                break
            cells.append(auc_pair(sa[ix], sb[ix], labels[ix])["delta"])
        if len(cells) == len(rows):
            deltas.append(float(np.mean(cells)))
    return {
        "method": "paired_world_and_timing_stratified_whole_course_percentile",
        "scope": "primary macro delta, conditional on this fixed checkpoint pair",
        "n_boot": settings["n_boot"],
        "seed": settings["seed"],
        "stratum_course_counts": [len(s) for s in strata],
        "valid_bootstraps": len(deltas),
        "undefined_bootstraps": settings["n_boot"] - len(deltas),
        "ci95": np.quantile(deltas, [0.025, 0.975]).tolist() if deltas else None,
    }


def readings(a, b, data, config):
    _validate(a, b)
    pairs, labels = _index_samples(data)
    if not np.array_equal(a["pairs"], pairs) or not np.array_equal(
        a["labels"], labels[:, :, 0]
    ):
        raise ValueError("export must cover exactly the complete registered exam")
    probe = select(data)
    for key in ("veer_pairs", "veer_gt_left", "veer_world_id"):
        if not np.array_equal(a[key], probe[key]):
            raise ValueError(f"incomplete geometric probe: {key}")
    y, sa, sb = a["labels"][:, -1], a["scores"][:, -1], b["scores"][:, -1]
    worlds, forward, cells, masks = {}, {}, {}, {}
    for world in config["worlds"] + ["room"]:
        wid = list(data["world_names"]).index(world)
        mask = a["world_id"] == wid
        worlds[world] = auc_pair(sa[mask], sb[mask], y[mask])
        if world == "room":
            continue
        selected, actions, _ = link_actions(a, data, world)
        for action in ["forward"] + [
            name for w, name in config["primary_cells"] if w == world
        ]:
            use = np.zeros(len(y), dtype=bool)
            use[np.flatnonzero(selected)] = actions == ACTION_NAMES.index(action)
            row = auc_pair(sa[use], sb[use], y[use])
            if action == "forward":
                forward[world] = row
            else:
                key = f"{world}/{action}"
                cells[key], masks[key] = row, use
    now_labels = data["dists"] < float(data["danger_r"])
    expected_now = {
        "positive": int(now_labels.sum()),
        "negative": int(now_labels.size - now_labels.sum()),
    }
    for arm in (a, b):
        meta = arm["metadata"]
        if meta["now_label_counts"] != expected_now:
            raise ValueError("now-head support differs from the complete exam")
        if meta["va_rolls"] != list(range(len(data["world_id"]))):
            raise ValueError("metadata does not contain every exam course")
        for world, row in worlds.items():
            key = "baseline" if arm is a else "candidate"
            if not np.isclose(meta["auc_by_world"][world], row[key], atol=1e-12):
                raise ValueError("raw score/aggregate AUC mismatch")
        if not np.isfinite(meta["now_auc"]) or not 0 <= meta["now_auc"] <= 1:
            raise ValueError("invalid now AUC")
    now_a, now_b = a["metadata"]["now_auc"], b["metadata"]["now_auc"]
    veer = {}
    for world in ["all"] + config["worlds"]:
        mask = (
            np.ones(len(a["veer_pairs"]), dtype=bool)
            if world == "all"
            else a["veer_world_id"] == list(data["world_names"]).index(world)
        )
        if not mask.any():
            raise ValueError(f"missing required veer world: {world}")
        aa, bb = [float(arm["veer_correct"][mask].mean()) for arm in (a, b)]
        veer[world] = {
            "baseline": aa,
            "candidate": bb,
            "delta": bb - aa,
            "frames": int(mask.sum()),
            "courses": len(np.unique(a["veer_pairs"][mask, 0])),
        }
    for key, arm in (("baseline", a), ("candidate", b)):
        if not np.isclose(arm["metadata"]["veer_all"][0], veer["all"][key]):
            raise ValueError("raw score/aggregate veer mismatch")
    return {
        "primary_cells": cells,
        "primary_delta": float(np.mean([r["delta"] for r in cells.values()])),
        "primary_baseline": float(np.mean([r["baseline"] for r in cells.values()])),
        "primary_candidate": float(np.mean([r["candidate"] for r in cells.values()])),
        "worlds": worlds,
        "forward": forward,
        "now": {"baseline": now_a, "candidate": now_b, "delta": now_b - now_a},
        "veer": veer,
        "primary_bootstrap": primary_bootstrap(a, b, data, masks, config),
    }


def decision(pairs, config):
    if [p["seed"] for p in pairs] != config["seeds"]:
        raise ValueError("all registered seeds required, exactly once and in order")
    bars, checks, deltas = config["bars"], {}, []
    expected = {
        "primary_cells": {f"{w}/{a}" for w, a in config["primary_cells"]},
        "worlds": set(config["worlds"] + ["room"]),
        "forward": set(config["worlds"]),
        "veer": set(config["worlds"] + ["all"]),
    }
    tolerances = {
        "primary_cells": "primary_cell_each_delta_min",
        "worlds": "world_each_delta_min",
        "forward": "forward_each_delta_min",
        "veer": "veer_each_delta_min",
        "now": "now_each_delta_min",
    }
    for pair in pairs:
        seed, row = pair["seed"], pair["readings"]
        for group, bar in tolerances.items():
            values = {"all": row[group]} if group == "now" else row[group]
            if group != "now" and set(values) != expected[group]:
                raise ValueError(f"incomplete guard group: {group}")
            for name, metric in values.items():
                a, b, delta = [metric[k] for k in ("baseline", "candidate", "delta")]
                if not all(np.isfinite(v) for v in (a, b, delta)):
                    raise ValueError("nonfinite decision metric")
                if not 0 <= a <= 1 or not 0 <= b <= 1 or not np.isclose(delta, b - a):
                    raise ValueError("inconsistent decision metric")
                checks[f"seed{seed}/{group}/{name}"] = delta >= bars[bar]
        delta = float(np.mean([r["delta"] for r in row["primary_cells"].values()]))
        if not np.isclose(row["primary_delta"], delta):
            raise ValueError("inconsistent primary macro")
        deltas.append(delta)
        checks[f"seed{seed}/primary_positive"] = (
            delta > bars["primary_each_delta_min_exclusive"]
        )
        a, b = pair["baseline_bill"], pair["candidate_bill"]
        for bill in (a, b):
            if set(bill) != {"budget", "estimated_gap8_ms"} or not all(
                np.isfinite(v) and v > 0
                for v in [*bill["budget"].values(), bill["estimated_gap8_ms"]]
            ):
                raise ValueError("invalid deployment bill")
        checks[f"seed{seed}/budget"] = (
            a == b
            and b["budget"]["total_kb"] <= bars["budget_kb_max"]
            and b["estimated_gap8_ms"] <= bars["estimated_ms_max"]
        )
    checks["primary_mean"] = float(np.mean(deltas)) >= bars["primary_mean_delta_min"]
    return {
        "verdict": "GO" if all(checks.values()) else "NO-GO",
        "checks": checks,
        "primary_deltas": deltas,
        "primary_mean": float(np.mean(deltas)),
        "primary_range": [min(deltas), max(deltas)],
        "scope": config["interpretation"],
    }


def selftest():
    import copy
    from pathlib import Path

    from scripts.schedule_layout_study import read

    config = read(
        Path(__file__).resolve().parents[1]
        / "experiments/intervention_timing_v1/registration.json"
    )
    metric = {"baseline": 0.6, "candidate": 0.64, "delta": 0.04}
    row = {
        "primary_cells": {f"{w}/{a}": dict(metric) for w, a in config["primary_cells"]},
        "worlds": {w: dict(metric) for w in config["worlds"] + ["room"]},
        "forward": {w: dict(metric) for w in config["worlds"]},
        "veer": {w: dict(metric) for w in config["worlds"] + ["all"]},
        "now": dict(metric),
        "primary_delta": 0.04,
    }
    bill = {"budget": {"total_kb": 140.0}, "estimated_gap8_ms": 7.8}
    pairs = [
        {
            "seed": s,
            "readings": copy.deepcopy(row),
            "baseline_bill": copy.deepcopy(bill),
            "candidate_bill": copy.deepcopy(bill),
        }
        for s in config["seeds"]
    ]
    assert decision(pairs, config)["verdict"] == "GO"
    # Every behavioral guard independently vetoes a superficially good macro.
    for group in ("primary_cells", "worlds", "forward", "veer", "now"):
        keys = [None] if group == "now" else list(row[group])
        for key in keys:
            bad = copy.deepcopy(pairs)
            target = bad[0]["readings"][group]
            target = target if key is None else target[key]
            target.update(candidate=0.4, delta=-0.2)
            bad[0]["readings"]["primary_delta"] = np.mean(
                [v["delta"] for v in bad[0]["readings"]["primary_cells"].values()]
            )
            assert decision(bad, config)["verdict"] == "NO-GO", (group, key)
    for field, value in (("total_kb", 513.0), ("estimated_gap8_ms", 8.1)):
        bad = copy.deepcopy(pairs)
        for name in ("baseline_bill", "candidate_bill"):
            target = bad[0][name]
            target = target["budget"] if field == "total_kb" else target
            target[field] = value
        assert decision(bad, config)["verdict"] == "NO-GO"
    for corrupt in ("seed", "nan", "missing", "macro", "bill"):
        bad = copy.deepcopy(pairs)
        if corrupt == "seed":
            bad[1]["seed"] = 0
        elif corrupt == "nan":
            bad[0]["readings"]["now"]["candidate"] = float("nan")
        elif corrupt == "missing":
            del bad[0]["readings"]["forward"]["moving"]
        elif corrupt == "macro":
            bad[0]["readings"]["primary_delta"] = 0.9
        else:
            bad[0]["baseline_bill"]["estimated_gap8_ms"] = float("nan")
        try:
            decision(bad, config)
        except ValueError:
            pass
        else:
            raise AssertionError(corrupt)
    for labels in (np.zeros(3), np.ones(3), np.array([])):
        try:
            auc_pair(labels, labels, labels)
        except ValueError:
            pass
        else:
            raise AssertionError("undefined AUC used as chance performance")
    assert auc_pair(np.ones(4), np.ones(4), np.array([1, 0, 1, 0]))["delta"] == 0
    # Two worlds × two timing blocks × two courses. Every course contains
    # both labels. All ties versus perfect ranking must give exactly +0.5,
    # including repeated courses, shared action draws and no-window courses.
    data = {
        "world_names": np.array(["dense", "moving"]),
        "world_id": np.repeat([0, 1], 4),
        "study_timing_block": np.tile([0, 0, 1, 1], 2),
    }
    rolls = np.repeat(np.arange(8), 4)
    labels = np.tile([0, 1, 0, 1], 8)
    a = {
        "pairs": np.column_stack([rolls, np.tile(np.arange(4), 8)]),
        "scores": np.ones((32, 1)),
        "labels": labels[:, None],
    }
    b = {"scores": labels[:, None]}
    masks = {
        f"{w}/{action}": (rolls // 4 == wid) & (a["pairs"][:, 1] // 2 == aid)
        for wid, w in enumerate(data["world_names"])
        for aid, action in enumerate(["veer_left", "veer_right"])
    }
    small = copy.deepcopy(config)
    small["bootstrap"] = {"n_boot": 50, "seed": 0}
    result = primary_bootstrap(a, b, data, masks, small)
    assert result["ci95"] == [0.5, 0.5] and result["valid_bootstraps"] == 50
    # Independent pairwise oracle: retain duplicate courses, omit no-window
    # courses only after drawing, and use shared draws across action cells.
    varied = {"scores": b["scores"].copy()}
    varied["scores"][rolls % 3 == 0] = 1 - varied["scores"][rolls % 3 == 0]
    varied_masks = {k: v & (rolls != 0) for k, v in masks.items()}
    result = primary_bootstrap(a, varied, data, varied_masks, small)
    rng, oracle = np.random.default_rng(0), []
    for _ in range(50):
        picked = np.concatenate(
            [rng.choice(s, len(s)) for s in ([0, 1], [2, 3], [4, 5], [6, 7])]
        )
        cells = []
        for mask in varied_masks.values():
            ix = np.concatenate([np.flatnonzero(mask & (rolls == r)) for r in picked])
            y = a["labels"][ix, 0]
            if len(np.unique(y)) != 2:
                break
            scores = varied["scores"][ix, 0]
            pos, neg = scores[y == 1, None], scores[None, y == 0]
            cells.append(float(((pos > neg) + 0.5 * (pos == neg)).mean()) - 0.5)
        if len(cells) == 4:
            oracle.append(np.mean(cells))
    assert result["valid_bootstraps"] == len(oracle)
    assert np.array_equal(result["ci95"], np.quantile(oracle, [0.025, 0.975]))
    for mask in masks.values():
        mask[a["pairs"][:, 1] % 2 == 1] = False
    result = primary_bootstrap(a, b, data, masks, small)
    assert result["ci95"] is None and result["undefined_bootstraps"] == 50
    readings_selftest(small)
    print("INTERVENTION TIMING METRICS OK")


def readings_selftest(config):
    """Exercise complete export/corpus wiring with no pixels, model or artifact."""
    import copy

    from datasets.combine_rollouts import _synth
    from planner.action_set import ACTION_VECS
    from world_model.metrics import AUC_METHOD

    data = _synth(np.repeat(np.arange(4), 6), length=40)
    data["world_names"] = np.array(["classic", "dense", "moving", "room"])
    data["study_timing_block"] = np.tile([0, 1, 0, 1, 0, 1], 4)
    for r in range(24):
        aid = [0, 0, 2, 2, 3, 3][r % 6] if r < 18 else 0
        data["act_id"][r] = aid
        data["actions"][r] = ACTION_VECS[aid]
        data["dists"][r] = 0.1 if r % 2 else 2.0
    data["pillars"][:] = [0.9, 0.2]
    data["pillars"][18:] = np.nan
    pairs, labels = _index_samples(data)
    probe = select(data)
    a = {
        **probe,
        "pairs": pairs,
        "scores": np.full(labels[:, :, 0].shape, 0.5),
        "labels": labels[:, :, 0],
        "world_names": data["world_names"],
        "world_id": data["world_id"][pairs[:, 0]],
        "horizons": data["horizons"],
        "veer_correct": np.zeros(len(probe["veer_pairs"]), dtype=bool),
        "metadata": {
            "split": "independent_holdout_all",
            "auc_method": AUC_METHOD,
            "provenance": {"dataset": {"sha256": "synthetic_timing_selftest"}},
            "va_rolls": list(range(24)),
            "now_auc": 0.5,
            "now_label_counts": {"positive": 480, "negative": 480},
            "auc_by_world": {w: 0.5 for w in data["world_names"]},
            "veer_all": [0.0, len(probe["veer_pairs"])],
        },
    }
    b = copy.deepcopy(a)
    b["scores"] = a["labels"].copy()
    b["veer_correct"][:] = True
    b["metadata"]["auc_by_world"] = {w: 1.0 for w in data["world_names"]}
    b["metadata"]["veer_all"][0] = 1.0
    result = readings(a, b, data, config)
    assert result["primary_delta"] == 0.5
    assert all(v["delta"] == 0.5 for v in result["forward"].values())
    assert all(v["delta"] == 1 for v in result["veer"].values())
    for corrupt in ("subset", "labels", "probe", "now", "aggregate", "action"):
        aa, bb, dd = copy.deepcopy(a), copy.deepcopy(b), copy.deepcopy(data)
        if corrupt == "subset":
            for arm in (aa, bb):
                for key in ("pairs", "scores", "labels", "world_id"):
                    arm[key] = arm[key][:-1]
        elif corrupt == "labels":
            aa["labels"][0, 0] = bb["labels"][0, 0] = 1 - aa["labels"][0, 0]
        elif corrupt == "probe":
            for arm in (aa, bb):
                for key in (
                    "veer_pairs",
                    "veer_correct",
                    "veer_world_id",
                    "veer_gt_left",
                ):
                    arm[key] = arm[key][:-1]
        elif corrupt == "now":
            aa["metadata"]["now_label_counts"]["positive"] -= 1
        elif corrupt == "aggregate":
            bb["metadata"]["auc_by_world"]["moving"] = 0.7
        else:
            dd["actions"][0, 0] = 0
        try:
            readings(aa, bb, dd, config)
        except ValueError:
            pass
        else:
            raise AssertionError(corrupt)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true", required=True)
    parser.parse_args()
    selftest()

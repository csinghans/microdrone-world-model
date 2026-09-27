"""Moving-only timing endpoints, with dense and timing-stratified guards.

python -m eval.eval_moving_timing --selftest
Reuse the complete-exam validation and primary bootstrap without inference.
"""

import argparse
import copy
from pathlib import Path

import numpy as np

from eval.eval_action_auc_audit import link_actions
from eval.eval_intervention_timing import auc_pair
from eval.eval_intervention_timing import decision as base_decision
from eval.eval_intervention_timing import readings as base_readings
from planner.action_set import ACTION_NAMES
from scripts.schedule_layout_study import read


def readings(a, b, data, config):
    result = base_readings(a, b, data, config)
    extra, stratified = {}, {}
    for world, action in config["extra_guard_cells"] + config["primary_cells"]:
        mask, actions, rolls = link_actions(a, data, world)
        selected = np.flatnonzero(mask)[actions == ACTION_NAMES.index(action)]
        labels = a["labels"][selected, -1]
        sa, sb = a["scores"][selected, -1], b["scores"][selected, -1]
        key = f"{world}/{action}"
        if [world, action] in config["extra_guard_cells"]:
            extra[key] = auc_pair(sa, sb, labels)
        else:
            blocks = data["study_timing_block"][
                rolls[actions == ACTION_NAMES.index(action)]
            ]
            for i, block in enumerate(config["stratified_guard_blocks"]):
                use = blocks == i
                stratified[f"{key}/{block}"] = auc_pair(sa[use], sb[use], labels[use])
    return dict(result, extra_guards=extra, stratified_guards=stratified)


def decision(pairs, config):
    result = base_decision(pairs, config)
    groups = {
        "extra_guards": (
            {f"{w}/{a}" for w, a in config["extra_guard_cells"]},
            "extra_cell_each_delta_min",
        ),
        "stratified_guards": (
            {
                f"{w}/{a}/{b}"
                for w, a in config["primary_cells"]
                for b in config["stratified_guard_blocks"]
            },
            "stratified_each_delta_min",
        ),
    }
    for pair in pairs:
        for group, (expected, bar) in groups.items():
            rows = pair["readings"][group]
            if set(rows) != expected:
                raise ValueError(f"missing/extra registered guard: {group}")
            for key, row in rows.items():
                a, b, delta = [row[k] for k in ("baseline", "candidate", "delta")]
                if (
                    not all(np.isfinite(v) for v in (a, b, delta))
                    or not 0 <= a <= 1
                    or not 0 <= b <= 1
                    or not np.isclose(delta, b - a)
                ):
                    raise ValueError("invalid extra guard metric")
                result["checks"][f"seed{pair['seed']}/{group}/{key}"] = (
                    delta >= config["bars"][bar]
                )
    result["verdict"] = "GO" if all(result["checks"].values()) else "NO-GO"
    return result


def selftest():
    from unittest.mock import patch

    from planner.action_set import ACTION_VECS

    config = read(
        Path(__file__).resolve().parents[1]
        / "experiments/moving_timing_v1/registration.json"
    )
    metric = {"baseline": 0.6, "candidate": 0.65, "delta": 0.05}
    row = {
        "primary_cells": {f"{w}/{a}": dict(metric) for w, a in config["primary_cells"]},
        "worlds": {w: dict(metric) for w in config["worlds"] + ["room"]},
        "forward": {w: dict(metric) for w in config["worlds"]},
        "veer": {w: dict(metric) for w in config["worlds"] + ["all"]},
        "now": dict(metric),
        "primary_delta": 0.05,
        "extra_guards": {
            f"{w}/{a}": dict(metric) for w, a in config["extra_guard_cells"]
        },
        "stratified_guards": {
            f"{w}/{a}/{b}": dict(metric)
            for w, a in config["primary_cells"]
            for b in config["stratified_guard_blocks"]
        },
    }
    bill = {"budget": {"total_kb": 140.0}, "estimated_gap8_ms": 7.8}
    pairs = [
        {
            "seed": s,
            "readings": copy.deepcopy(row),
            "baseline_bill": bill,
            "candidate_bill": bill,
        }
        for s in config["seeds"]
    ]
    assert decision(pairs, config)["verdict"] == "GO"
    for group in ("extra_guards", "stratified_guards"):
        for key in row[group]:
            bad = copy.deepcopy(pairs)
            bad[1]["readings"][group][key].update(candidate=0.5, delta=-0.1)
            assert decision(bad, config)["verdict"] == "NO-GO", key
        for mode in ("missing", "nonfinite"):
            bad = copy.deepcopy(pairs)
            key = next(iter(row[group]))
            if mode == "missing":
                del bad[0]["readings"][group][key]
            else:
                bad[0]["readings"][group][key]["delta"] = float("nan")
            try:
                decision(bad, config)
            except ValueError:
                pass
            else:
                raise AssertionError((group, mode))
    # Every synthetic action/block has both classes. The base routine is
    # independently tested; this seam verifies the additional slice wiring.
    combinations = [
        (w, a, block, y)
        for w in (1, 2)
        for a in (2, 3)
        for block in (0, 1)
        for y in (0, 1)
    ]
    worlds, actions, blocks, y = np.asarray(combinations).T
    n = len(y)
    data = {
        "world_names": np.array(["classic", "dense", "moving", "room"]),
        "world_id": worlds,
        "act_id": actions[:, None],
        "actions": ACTION_VECS[actions][:, None],
        "speed": np.ones(n),
        "study_timing_block": blocks,
    }
    a = {
        "pairs": np.column_stack([np.arange(n), np.zeros(n, dtype=int)]),
        "world_names": data["world_names"],
        "world_id": worlds,
        "labels": y[:, None],
        "scores": np.full((n, 1), 0.5),
    }
    b = dict(a, scores=y[:, None])
    with patch(__name__ + ".base_readings", return_value={}):
        extra = readings(a, b, data, config)
    assert len(extra["extra_guards"]) == 2 and len(extra["stratified_guards"]) == 4
    assert all(v["delta"] == 0.5 for rows in extra.values() for v in rows.values())
    print(
        "MOVING TIMING METRICS OK: dense/timing guards, missing/nonfinite, slice wiring"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true", required=True)
    parser.parse_args()
    selftest()

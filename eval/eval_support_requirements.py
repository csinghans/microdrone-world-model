"""Check prospective action/label support requirements before fitting models.

    python -m eval.eval_support_requirements --report support.json \
        --requirements registered.json --data corpus.npz --out fresh.json
    python -m eval.eval_support_requirements --selftest

Exit 0 means the explicit count requirements are satisfied, 10 means
insufficient support, and 2 means an input/configuration error. No default
scientific thresholds, model inference, resampling or training occurs here.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path

from planner.action_set import ACTION_NAMES
from planner.nav_action_set import NAV_ACTION_NAMES
from world_model.checkpoint_io import check_destination, publish_checkpoint

TARGET = "executed_warn_at_32"
COUNTS = ("positive", "negative", "positive_rollouts", "negative_rollouts")
CATALOGS = {world: ACTION_NAMES for world in ("classic", "dense", "moving")}
CATALOGS["room"] = NAV_ACTION_NAMES
SCOPE = (
    "Prospective count requirements only. Windows are correlated; course counts "
    "mean distinct rollout IDs within each class/action and may overlap. Passing "
    "does not establish statistical power, independent courses, rendered vision, "
    "held-out provenance or model performance. Freeze requirements in a new "
    "registration; never apply them as new gates to closed studies."
)


def _object(value, where, keys=None):
    if not isinstance(value, dict) or (keys is not None and set(value) != set(keys)):
        raise ValueError(
            f"{where}: expected object" + (f" with keys {keys}" if keys else "")
        )
    return value


def _count(value, where, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(f"{where}: expected integer >= {minimum}")
    return value


def _contract(document, where):
    _object(document, where)
    if (
        type(document.get("schema_version")) is not int
        or document["schema_version"] != 1
    ):
        raise ValueError(f"{where}: schema_version must be 1")
    if document.get("target") != TARGET:
        raise ValueError(f"{where}: target must be {TARGET}")


def expand_requirements(requirements):
    """All four minima are mandatory and positive; no vacuous/implicit bars."""
    _object(requirements, "requirements", ("schema_version", "target", "checks"))
    _contract(requirements, "requirements")
    checks = requirements["checks"]
    if not isinstance(checks, list) or not checks:
        raise ValueError("requirements.checks: nonempty list required")
    expanded, seen = [], set()
    for i, check in enumerate(checks):
        where = f"checks[{i}]"
        _object(check, where, ("partition", "world", "actions", "minimum"))
        part, world = check["partition"], check["world"]
        if not isinstance(part, str) or not re.fullmatch(
            r"all|splits/(0|[1-9][0-9]*)/(train|val)", part
        ):
            raise ValueError(
                f"{where}: partition must be all or splits/<seed>/train|val"
            )
        if not isinstance(world, str) or world not in CATALOGS:
            raise ValueError(f"{where}: unknown world {world!r}")
        minima = _object(check["minimum"], f"{where}.minimum", COUNTS)
        for key in COUNTS:
            _count(minima[key], f"{where}.minimum.{key}", 1)
        actions = check["actions"]
        if not isinstance(actions, list) or not actions:
            raise ValueError(f"{where}: nonempty actions list required")
        for action in actions:
            if not isinstance(action, str) or action not in CATALOGS[world]:
                raise ValueError(f"{where}: unknown {world} action {action!r}")
            identity = (part, world, action)
            if identity in seen:
                raise ValueError(f"{where}: duplicate requirement {identity}")
            seen.add(identity)
            expanded.append((part, world, action, dict(minima)))
    return expanded


def _label_counts(row, where, windows, rollouts):
    _object(row, where)
    for key in COUNTS:
        _count(row.get(key), f"{where}.{key}")
    if row["positive"] + row["negative"] != windows:
        raise ValueError(f"{where}: positive + negative != windows")
    for label in ("positive", "negative"):
        n, courses = row[label], row[label + "_rollouts"]
        if courses > min(n, rollouts) or (n == 0) != (courses == 0):
            raise ValueError(f"{where}: inconsistent {label} course count")
    defined = row["positive"] > 0 and row["negative"] > 0
    if type(row.get("auc_defined")) is not bool or row["auc_defined"] != defined:
        raise ValueError(f"{where}: inconsistent auc_defined")


def _partition(report, name):
    node = report
    for key in name.split("/"):
        if not isinstance(node, dict) or key not in node:
            raise ValueError(f"report: requested partition {name!r} is absent")
        node = node[key]
    _object(node, name)
    total_rolls = _count(node.get("rollouts"), f"{name}.rollouts")
    total_windows = _count(node.get("valid_windows"), f"{name}.valid_windows")
    worlds = _object(node.get("worlds"), f"{name}.worlds")
    seen, windows_sum = set(), 0
    for world, row in worlds.items():
        where = f"{name}/{world}"
        if world not in CATALOGS:
            raise ValueError(f"{where}: no registered action catalog")
        _object(row, where)
        rolls = _count(row.get("rollouts"), f"{where}.rollouts")
        windows = _count(row.get("valid_windows"), f"{where}.valid_windows")
        ids = row.get("rollout_ids")
        if not isinstance(ids, list):
            raise ValueError(f"{where}: rollout_ids list required")
        for rid in ids:
            _count(rid, f"{where}.rollout_ids")
        if len(ids) != rolls or len(set(ids)) != rolls or seen.intersection(ids):
            raise ValueError(f"{where}: inconsistent/duplicate rollout IDs")
        seen.update(ids)
        actions = _object(row.get("actions"), f"{where}.actions")
        for action, support in actions.items():
            if action not in CATALOGS[world]:
                raise ValueError(f"{where}: unknown action {action!r}")
            _object(support, f"{where}/{action}")
            count = _count(support.get("windows"), f"{where}/{action}.windows")
            _label_counts(support, f"{where}/{action}", count, rolls)
        labels = row.get("labels_at_32")
        _label_counts(labels, f"{where}.labels_at_32", windows, rolls)
        for label in ("positive", "negative"):
            if sum(a[label] for a in actions.values()) != labels[label]:
                raise ValueError(f"{where}: action {label} counts do not reconcile")
            courses = [a[label + "_rollouts"] for a in actions.values()]
            if (
                not max(courses, default=0)
                <= labels[label + "_rollouts"]
                <= sum(courses)
            ):
                raise ValueError(
                    f"{where}: action {label} course counts do not reconcile"
                )
        windows_sum += windows
    if len(seen) != total_rolls or windows_sum != total_windows:
        raise ValueError(f"{name}: world totals do not reconcile")
    return worlds


def check_support(report, requirements):
    """Pure comparison of selected partitions, with strict count validation."""
    expanded = expand_requirements(requirements)
    _contract(report, "report")
    if report.get("horizons") != [4, 8, 16, 32]:
        raise ValueError("report: unsupported horizons")
    names = dict.fromkeys(name for name, _, _, _ in expanded)
    partitions = {name: _partition(report, name) for name in names}
    rows = []
    for part, world, action, minima in expanded:
        worlds = partitions[part]
        source = worlds.get(world, {}).get("actions", {}).get(action)
        observed = {key: source[key] if source else 0 for key in COUNTS}
        missing = None
        if world not in worlds:
            missing = "world_absent"
        elif source is None:
            missing = "action_absent"
        deficits = {
            key: minima[key] - observed[key]
            for key in COUNTS
            if observed[key] < minima[key]
        }
        rows.append(
            dict(
                partition=part,
                world=world,
                action=action,
                minimum=minima,
                observed=observed,
                missing=missing,
                deficits=deficits,
                satisfied=not deficits,
            )
        )
    return {
        "schema_version": 1,
        "target": TARGET,
        "scope": SCOPE,
        "status": "satisfied" if all(r["satisfied"] for r in rows) else "insufficient",
        "checks": rows,
    }


def _digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"{path}: duplicate JSON key {key!r}")
            result[key] = value
        return result

    def nonfinite(value):
        raise ValueError(f"{path}: nonfinite JSON constant {value}")

    return json.loads(
        path.read_text(), object_pairs_hook=unique, parse_constant=nonfinite
    )


def run(report_path, requirements_path, data_path, output_path):
    """Pin file identities and publish a fresh receipt, including insufficiency."""
    check_destination(output_path)
    paths = {
        "report": Path(report_path).resolve(),
        "requirements": Path(requirements_path).resolve(),
        "dataset": Path(data_path).resolve(),
    }
    identities = {
        key: {"path": str(path), "sha256": _digest(path)} for key, path in paths.items()
    }
    root = Path(__file__).resolve().parents[1]
    sources = [
        Path(__file__).resolve(),
        root / "planner/action_set.py",
        root / "planner/nav_action_set.py",
        root / "world_model/checkpoint_io.py",
    ]
    source_hashes = {str(path): _digest(path) for path in sources}
    report, requirements = _read_json(paths["report"]), _read_json(
        paths["requirements"]
    )
    _object(report, "report")
    provenance = _object(report.get("provenance"), "report.provenance")
    dataset = _object(provenance.get("dataset"), "report.provenance.dataset")
    if dataset.get("sha256") != identities["dataset"]["sha256"]:
        raise ValueError("report dataset SHA does not match --data")
    result = check_support(report, requirements)
    result["provenance"] = {
        **identities,
        "report_provenance": provenance,
        "sources": source_hashes,
    }
    for key, path in paths.items():
        if _digest(path) != identities[key]["sha256"]:
            raise ValueError(f"{key} changed during support check")
    if any(_digest(path) != sha for path, sha in source_hashes.items()):
        raise ValueError("checker source changed during support check")
    payload = (json.dumps(result, indent=2, allow_nan=False) + "\n").encode()
    publish_checkpoint(output_path, lambda stream: stream.write(payload))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("report", "requirements", "data", "out"):
        parser.add_argument("--" + name)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        from scripts.support_requirements_selftest import selftest

        selftest()
        return 0
    if not all((args.report, args.requirements, args.data, args.out)):
        parser.error("--report, --requirements, --data and a new --out are required")
    try:
        result = run(args.report, args.requirements, args.data, args.out)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    satisfied = result["status"] == "satisfied"
    failed = sum(not row["satisfied"] for row in result["checks"])
    print(
        f"SUPPORT-REQUIREMENTS {result['status'].upper()}: "
        f"{failed}/{len(result['checks'])} unmet checks; {args.out}"
    )
    return 0 if satisfied else 10


if __name__ == "__main__":
    raise SystemExit(main())

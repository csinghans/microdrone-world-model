"""Paired AUC@32 uncertainty on one independently generated holdout.

    python -m eval.compare_wm_scores --baseline a.npz --candidate b.npz \
        --out experiments/new_audit/comparison.json
    python -m eval.compare_wm_scores --selftest

Inputs come from eval_wm_checkpoint --independent-holdout --scores-out.
Resample whole rollouts, paired across models and stratified by world;
overlapping future windows are not independent experimental units. These
percentile intervals describe test-course uncertainty conditional on two
fixed checkpoints, NOT variation across training draws or a promotion gate.
Sample indices, world catalogs, horizons and optional veer fields are checked
before metric calculation or resampling. The pooled key `all` is reserved.
Without the source corpus these checks cannot establish frame upper bounds,
rendered vision, independent courses or that an export contains the full exam.
"""

import argparse
import json
from pathlib import Path

import numpy as np

from datasets.provenance import reject_training_file
from world_model.metrics import AUC_METHOD, roc_auc


def _load(path):
    with np.load(path, allow_pickle=False) as blob:
        out = {k: blob[k] for k in blob.files if k != "metadata"}
        out["metadata"] = json.loads(str(blob["metadata"]))
    return out


def _indices(value, name, ndim):
    if (
        not isinstance(value, np.ndarray)
        or value.ndim != ndim
        or not np.issubdtype(value.dtype, np.integer)
        or (value < 0).any()
    ):
        raise ValueError(f"{name}: expected {ndim}D nonnegative integer indices")


def _rollout_worlds(pairs, worlds, name):
    mapping = {}
    for rollout in np.unique(pairs[:, 0]):
        ids = np.unique(worlds[pairs[:, 0] == rollout])
        if len(ids) != 1:
            raise ValueError(f"{name}: a rollout belongs to multiple worlds")
        mapping[rollout] = ids[0]
    return mapping


def _validate(a, b):
    for name, arm in (("baseline", a), ("candidate", b)):
        meta = arm["metadata"]
        if meta.get("split") != "independent_holdout_all":
            raise ValueError(f"{name}: requires an explicitly independent holdout")
        if meta.get("auc_method") != AUC_METHOD:
            raise ValueError(f"{name}: incompatible AUC method; export fresh scores")
        reject_training_file(
            meta.get("checkpoint_meta", {}).get("training_dataset_sha256"),
            meta["provenance"]["dataset"]["sha256"],
        )
        scores, labels, pairs = arm["scores"], arm["labels"], arm["pairs"]
        _indices(pairs, f"{name} pairs", 2)
        _indices(arm["world_id"], f"{name} world_id", 1)
        horizons, names = arm["horizons"], arm["world_names"]
        _indices(horizons, f"{name} horizons", 1)
        if (
            len(horizons) == 0
            or (horizons == 0).any()
            or (horizons[1:] <= horizons[:-1]).any()
            or horizons[-1] != 32
        ):
            raise ValueError(f"{name}: horizons must increase strictly and end at 32")
        if (
            not isinstance(names, np.ndarray)
            or names.ndim != 1
            or names.dtype.kind != "U"
            or len(names) == 0
            or any(not n.strip() or n != n.strip() or n == "all" for n in names)
            or len(np.unique(names)) != len(names)
        ):
            raise ValueError(
                f"{name}: world names must be unique nonempty strings, not all"
            )
        if (arm["world_id"] >= len(names)).any():
            raise ValueError(f"{name}: world_id outside world catalog")
        if (
            not isinstance(scores, np.ndarray)
            or not isinstance(labels, np.ndarray)
            or scores.ndim != 2
            or scores.shape != labels.shape
            or scores.shape != (len(pairs), len(arm["horizons"]))
            or pairs.shape != (len(pairs), 2)
            or len(pairs) == 0
            or arm["world_id"].shape != (len(pairs),)
        ):
            raise ValueError(f"{name}: inconsistent sample shapes")
        if (
            scores.dtype.kind not in "biuf"
            or labels.dtype.kind not in "biuf"
            or not np.isfinite(scores).all()
            or not np.isin(labels, [0, 1]).all()
        ):
            raise ValueError(f"{name}: nonfinite scores or nonbinary labels")
        if len(np.unique(pairs, axis=0)) != len(pairs):
            raise ValueError(f"{name}: duplicate (rollout, time) pairs")
        _rollout_worlds(pairs, arm["world_id"], name)
    for key in ("pairs", "labels", "world_id", "world_names", "horizons"):
        if not np.array_equal(a[key], b[key]):
            raise ValueError(f"paired exam mismatch: {key}")
    hashes = [arm["metadata"]["provenance"]["dataset"]["sha256"] for arm in (a, b)]
    if not hashes[0] or hashes[0] != hashes[1]:
        raise ValueError("paired exam mismatch: dataset sha256")
    _validate_veer(a, b)


def _validate_veer(a, b):
    keys = {"veer_pairs", "veer_gt_left", "veer_world_id", "veer_correct"}
    if not (keys.intersection(a) or keys.intersection(b)):
        return
    for name, arm in (("baseline", a), ("candidate", b)):
        if not keys <= arm.keys():
            raise ValueError(f"{name}: incomplete veer sample fields")
        pairs, worlds = arm["veer_pairs"], arm["veer_world_id"]
        _indices(pairs, f"{name} veer_pairs", 2)
        _indices(worlds, f"{name} veer_world_id", 1)
        n = len(pairs)
        if pairs.shape != (n, 2) or len(np.unique(pairs, axis=0)) != n:
            raise ValueError(f"{name}: invalid or duplicate veer pairs")
        for key in ("veer_correct", "veer_gt_left", "veer_world_id"):
            if not isinstance(arm[key], np.ndarray) or arm[key].shape != (n,):
                raise ValueError(f"{name}: inconsistent veer sample shape")
        for key in ("veer_correct", "veer_gt_left"):
            if arm[key].dtype.kind not in "biuf" or not np.isin(arm[key], [0, 1]).all():
                raise ValueError(f"{name}: {key} must be binary")
        if (worlds >= len(arm["world_names"])).any():
            raise ValueError(f"{name}: veer_world_id outside world catalog")
        auc_worlds = _rollout_worlds(arm["pairs"], arm["world_id"], name)
        veer_worlds = _rollout_worlds(pairs, worlds, f"{name} veer")
        for rollout in auc_worlds.keys() & veer_worlds.keys():
            if auc_worlds[rollout] != veer_worlds[rollout]:
                raise ValueError(f"{name}: AUC and veer disagree on rollout world")
    for key in ("veer_pairs", "veer_gt_left", "veer_world_id"):
        if not np.array_equal(a[key], b[key]):
            raise ValueError(f"paired veer exam mismatch: {key}")


def _compare_veer(a, b, n_boot, seed):
    """Conditional accuracy uncertainty on inputs already checked by _validate."""
    pairs, worlds = a["veer_pairs"], a["veer_world_id"]
    n = len(pairs)
    rows = {r: np.flatnonzero(pairs[:, 0] == r) for r in np.unique(pairs[:, 0])}
    out = {"n_samples": n, "n_rollouts": len(rows), "ci95": None}
    if not n:
        return dict(out, delta=None, reason="no eligible veer probe frames")
    correct_a, correct_b = a["veer_correct"].astype(float), b["veer_correct"].astype(
        float
    )
    out.update(
        accuracy_baseline=float(correct_a.mean()),
        accuracy_candidate=float(correct_b.mean()),
        delta=float(correct_b.mean() - correct_a.mean()),
    )
    strata = [np.unique(pairs[worlds == w, 0]) for w in np.unique(worlds)]
    if any(len(s) < 2 for s in strata):
        return dict(out, reason="fewer than two probe rollouts in a world stratum")
    rng, deltas = np.random.default_rng(seed), []
    for _ in range(n_boot):
        picked = np.concatenate([rng.choice(s, size=len(s)) for s in strata])
        ix = np.concatenate([rows[r] for r in picked])
        deltas.append(float((correct_b[ix] - correct_a[ix]).mean()))
    return dict(
        out, ci95=np.quantile(deltas, [0.025, 0.975]).tolist(), valid_bootstraps=n_boot
    )


def compare(a, b, n_boot=2000, seed=0):
    """Report candidate minus baseline AUC; no threshold-based verdict."""
    _validate(a, b)
    if n_boot < 1:
        raise ValueError("n_boot must be positive")
    rng = np.random.default_rng(seed)
    y, sa, sb = a["labels"][:, -1], a["scores"][:, -1], b["scores"][:, -1]
    rolls, worlds = a["pairs"][:, 0], a["world_id"]
    result = {}
    groups = [("all", np.ones(len(y), dtype=bool))]
    for wid in np.unique(worlds):
        names = a["world_names"]
        name = str(names[int(wid)]) if 0 <= wid < len(names) else str(wid)
        groups.append((name, worlds == wid))
    for name, mask in groups:
        selected = np.flatnonzero(mask)
        ids = np.unique(rolls[selected])
        row = {
            "n_samples": int(len(selected)),
            "n_rollouts": int(len(ids)),
            "n_positive": int(y[selected].sum()),
        }
        if len(np.unique(y[selected])) < 2:
            row.update(
                auc_baseline=None,
                auc_candidate=None,
                delta=None,
                ci95=None,
                valid_bootstraps=0,
                reason="single label class",
            )
            result[name] = row
            continue
        aa, bb = roc_auc(sa[selected], y[selected]), roc_auc(sb[selected], y[selected])
        row.update(auc_baseline=aa, auc_candidate=bb, delta=bb - aa)
        by_roll = {r: selected[rolls[selected] == r] for r in ids}
        strata = [
            np.unique(rolls[selected][worlds[selected] == w])
            for w in np.unique(worlds[selected])
        ]
        # One observed course cannot price a world-specific course distribution.
        if any(len(s) < 2 for s in strata):
            row.update(
                ci95=None,
                valid_bootstraps=0,
                reason="fewer than two rollouts in a world stratum",
            )
            result[name] = row
            continue
        deltas = []
        for _ in range(n_boot):
            chosen = np.concatenate([rng.choice(s, size=len(s)) for s in strata])
            ix = np.concatenate([by_roll[r] for r in chosen])
            if len(np.unique(y[ix])) < 2:
                continue  # undefined AUC is not a chance-level measurement
            deltas.append(roc_auc(sb[ix], y[ix]) - roc_auc(sa[ix], y[ix]))
        row.update(
            ci95=np.quantile(deltas, [0.025, 0.975]).tolist() if deltas else None,
            valid_bootstraps=len(deltas),
            undefined_bootstraps=n_boot - len(deltas),
        )
        result[name] = row
    extra = {}
    if "veer_pairs" in a or "veer_pairs" in b:
        if "veer_pairs" not in a or "veer_pairs" not in b:
            raise ValueError("only one model exports veer samples")
        extra["veer"] = _compare_veer(a, b, n_boot, seed)
    return {
        "method": "paired_world_stratified_rollout_percentile_bootstrap",
        "auc_method": AUC_METHOD,
        "seed": seed,
        "n_boot": n_boot,
        "scope": "test-course uncertainty conditional on these fixed checkpoints; "
        "does not estimate training-draw variation or change frozen gates",
        "baseline": a["metadata"],
        "candidate": b["metadata"],
        "worlds": result,
        **extra,
    }


def selftest():
    from copy import deepcopy

    pairs = np.array([(r, t) for r in range(8) for t in range(2)])
    labels = np.tile([0, 1], 8).reshape(-1, 1)
    a = dict(
        pairs=pairs,
        labels=labels,
        scores=1 - labels,
        world_id=np.repeat([0] * 4 + [1] * 4, 2),
        world_names=np.array(["classic", "dense"]),
        horizons=np.array([32]),
        metadata={
            "split": "independent_holdout_all",
            "auc_method": AUC_METHOD,
            "provenance": {"dataset": {"sha256": "synthetic-selftest"}},
        },
    )
    b = deepcopy(a)
    b["scores"] = labels.copy()
    r = compare(a, b, n_boot=40, seed=7)
    assert r == compare(a, b, n_boot=40, seed=7), "bootstrap must be seeded"
    assert r["worlds"]["all"]["delta"] == 1
    assert r["worlds"]["all"]["ci95"] == [1, 1]
    same = compare(a, a, n_boot=40)["worlds"]["all"]
    assert same["delta"] == 0 and same["ci95"] == [0, 0]
    # Duplicating correlated windows inside each course adds no independent
    # evidence. An iid-frame bootstrap would shrink this interval spuriously.
    variable = deepcopy(b)
    reversed_rolls = pairs[:, 0] % 2 == 0
    variable["scores"][reversed_rolls] = 1 - labels[reversed_rolls]
    coarse = compare(a, variable, n_boot=100, seed=5)
    expanded = []
    for arm in (a, variable):
        dense = deepcopy(arm)
        for key in ("pairs", "scores", "labels", "world_id"):
            dense[key] = np.repeat(arm[key], 3, axis=0)
        dense["pairs"][:, 1] = np.tile(np.arange(6), 8)
        expanded.append(dense)
    fine = compare(*expanded, n_boot=100, seed=5)
    for world in coarse["worlds"]:
        assert coarse["worlds"][world]["ci95"] == fine["worlds"][world]["ci95"]
        assert coarse["worlds"][world]["delta"] == fine["worlds"][world]["delta"]
    for key in ("pairs", "labels", "world_id", "horizons"):
        bad = deepcopy(b)
        bad[key] = bad[key] + 1
        try:
            compare(a, bad, n_boot=1)
        except ValueError:
            pass
        else:
            raise AssertionError(f"mismatched {key} accepted")
    bad = deepcopy(b)
    bad["metadata"]["provenance"]["dataset"]["sha256"] = "another-dataset"
    try:
        compare(a, bad, n_boot=1)
    except ValueError:
        pass
    else:
        raise AssertionError("different dataset accepted")
    for side in (0, 1):
        arms = [deepcopy(a), deepcopy(b)]
        arms[side]["metadata"]["checkpoint_meta"] = {
            "training_dataset_sha256": "synthetic-selftest"
        }
        try:
            compare(*arms, n_boot=1)
        except ValueError as exc:
            assert "training dataset" in str(exc)
        else:
            raise AssertionError("known training file accepted as independent exam")
    flat = deepcopy(a)
    flat["labels"][:] = 0
    assert compare(flat, flat, n_boot=10)["worlds"]["all"]["ci95"] is None
    aa, bb = deepcopy(a), deepcopy(a)
    for arm in (aa, bb):
        arm.update(
            veer_pairs=pairs.copy(),
            veer_gt_left=np.zeros(len(pairs), dtype=bool),
            veer_world_id=a["world_id"].copy(),
            veer_correct=np.zeros(len(pairs), dtype=bool),
        )
    bb["veer_correct"][:] = True
    vr = compare(aa, bb, n_boot=20)["veer"]
    assert vr["delta"] == 1 and vr["ci95"] == [1, 1]
    assert vr["n_rollouts"] == 8
    # Doubling frames within each course cannot add independent evidence.
    bb["veer_correct"][pairs[:, 0] % 2 == 0] = False
    coarse_veer = compare(aa, bb, n_boot=40, seed=3)["veer"]
    doubled = []
    for arm in (aa, bb):
        dense = deepcopy(arm)
        for key in ("veer_pairs", "veer_gt_left", "veer_world_id", "veer_correct"):
            dense[key] = np.repeat(arm[key], 2, axis=0)
        dense["veer_pairs"][:, 1] = np.tile(np.arange(4), 8)
        doubled.append(dense)
    assert compare(*doubled, n_boot=40, seed=3)["veer"]["ci95"] == coarse_veer["ci95"]
    _schema_selftest(a)
    print(
        "WM-COMPARISON OK: paired course bootstrap, identity, alignment, undefined AUC"
    )


def _schema_selftest(base):
    from copy import deepcopy
    from unittest.mock import patch

    fields = {
        "pairs": [
            base["pairs"].astype(float) + 0.5,
            -base["pairs"] - 1,
            base["pairs"].astype(bool),
            np.array(0),
        ],
        "world_id": [
            base["world_id"].astype(float) + 0.5,
            -base["world_id"] - 1,
            base["world_id"] + 2,
            base["world_id"][:, None],
        ],
        "world_names": [
            np.array(["same", "same"]),
            np.array(["all", "dense"]),
            np.array(["", "dense"]),
            np.array([" classic", "dense"]),
            np.array([0, 1]),
            np.array([["classic", "dense"]]),
        ],
        "horizons": [
            np.array([32.5]),
            np.array([0, 32]),
            np.array([32, 32]),
            np.array([16, 8, 32], dtype=np.uint16),
            np.array([], dtype=int),
        ],
        "scores": [base["scores"].astype(complex) + 1j],
    }
    valid = deepcopy(base)
    valid.update(
        veer_pairs=base["pairs"].copy(),
        veer_world_id=base["world_id"].copy(),
        veer_gt_left=np.zeros(len(base["pairs"]), dtype=bool),
        veer_correct=np.zeros(len(base["pairs"]), dtype=bool),
    )
    fields.update(
        veer_pairs=[valid["veer_pairs"].astype(float), -valid["veer_pairs"] - 1],
        veer_world_id=[
            valid["veer_world_id"].astype(float) + 0.5,
            valid["veer_world_id"] + 2,
            1 - valid["veer_world_id"],
        ],
        veer_gt_left=[np.full(len(valid["veer_pairs"]), 2)],
        veer_correct=[np.full(len(valid["veer_pairs"]), 0.5)],
    )
    rejected = 0
    for key, values in fields.items():
        for value in values:
            bad = deepcopy(valid)
            bad[key] = value
            for a, b in ((bad, valid), (valid, bad), (bad, bad)):
                with (
                    patch(
                        __name__ + ".roc_auc", side_effect=AssertionError("metric ran")
                    ),
                    patch.object(
                        np.random, "default_rng", side_effect=AssertionError("RNG ran")
                    ),
                ):
                    try:
                        compare(a, b, n_boot=1)
                    except ValueError:
                        rejected += 1
                    else:
                        raise AssertionError(f"invalid {key} accepted")
    for key in ("veer_pairs", "veer_gt_left", "veer_correct", "veer_world_id"):
        bad = deepcopy(valid)
        del bad[key]
        try:
            _validate(bad, valid)
        except ValueError as exc:
            assert "incomplete veer" in str(exc)
        else:
            raise AssertionError(f"partial veer fields accepted: missing {key}")
    empty = deepcopy(valid)
    for key in ("veer_pairs", "veer_gt_left", "veer_correct", "veer_world_id"):
        empty[key] = empty[key][:0]
    assert compare(empty, empty, n_boot=2)["veer"]["n_samples"] == 0
    assert compare(empty, empty, n_boot=2)["veer"]["ci95"] is None
    # Veer can see a course with no held-command AUC windows. Only IDs
    # present in both sample sets have a cross-signal world to reconcile.
    extra = deepcopy(valid)
    extra["veer_pairs"][:, 0] += 100
    _validate(extra, extra)
    print(
        f"SCORE-SCHEMA OK: {rejected} malformed-arm checks before metrics/RNG; "
        "partial/empty/additional-course veer support"
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--baseline")
    ap.add_argument("--candidate")
    ap.add_argument("--out")
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    if not all((args.baseline, args.candidate, args.out)):
        ap.error("--baseline, --candidate and --out are required")
    out = Path(args.out)
    if out.exists():
        ap.error("--out must be new; preserve historical records")
    try:
        report = compare(
            _load(args.baseline), _load(args.candidate), args.n_boot, args.seed
        )
    except ValueError as exc:
        ap.error(str(exc))
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(f"WM-COMPARISON OK: {out}")


if __name__ == "__main__":
    main()

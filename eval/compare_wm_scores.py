"""Paired AUC@32 uncertainty on one independently generated holdout.

    python -m eval.compare_wm_scores --baseline a.npz --candidate b.npz \
        --out experiments/new_audit/comparison.json
    python -m eval.compare_wm_scores --selftest

Inputs come from eval_wm_checkpoint --independent-holdout --scores-out.
Resample whole rollouts, paired across models and stratified by world;
overlapping future windows are not independent experimental units. These
percentile intervals describe test-course uncertainty conditional on two
fixed checkpoints, NOT variation across training draws or a promotion gate.
"""

import argparse
import json
from pathlib import Path

import numpy as np

from world_model.metrics import AUC_METHOD, roc_auc


def _load(path):
    with np.load(path, allow_pickle=False) as blob:
        out = {k: blob[k] for k in blob.files if k != "metadata"}
        out["metadata"] = json.loads(str(blob["metadata"]))
    return out


def _validate(a, b):
    for name, arm in (("baseline", a), ("candidate", b)):
        meta = arm["metadata"]
        if meta.get("split") != "independent_holdout_all":
            raise ValueError(f"{name}: requires an explicitly independent holdout")
        if meta.get("auc_method") != AUC_METHOD:
            raise ValueError(f"{name}: incompatible AUC method; export fresh scores")
        scores, labels, pairs = arm["scores"], arm["labels"], arm["pairs"]
        if (
            scores.ndim != 2
            or scores.shape != labels.shape
            or scores.shape != (len(pairs), len(arm["horizons"]))
            or pairs.shape != (len(pairs), 2)
            or len(pairs) == 0
            or arm["world_id"].shape != (len(pairs),)
        ):
            raise ValueError(f"{name}: inconsistent sample shapes")
        if not np.isfinite(scores).all() or not np.isin(labels, [0, 1]).all():
            raise ValueError(f"{name}: nonfinite scores or nonbinary labels")
        if len(np.unique(pairs, axis=0)) != len(pairs):
            raise ValueError(f"{name}: duplicate (rollout, time) pairs")
        for r in np.unique(pairs[:, 0]):
            if len(np.unique(arm["world_id"][pairs[:, 0] == r])) != 1:
                raise ValueError(f"{name}: a rollout belongs to multiple worlds")
    for key in ("pairs", "labels", "world_id", "world_names", "horizons"):
        if not np.array_equal(a[key], b[key]):
            raise ValueError(f"paired exam mismatch: {key}")
    hashes = [arm["metadata"]["provenance"]["dataset"]["sha256"] for arm in (a, b)]
    if not hashes[0] or hashes[0] != hashes[1]:
        raise ValueError("paired exam mismatch: dataset sha256")
    if int(a["horizons"][-1]) != 32:
        raise ValueError("comparison requires horizon 32 as the final score column")


def _compare_veer(a, b, n_boot, seed):
    """Conditional accuracy uncertainty; correlated probe frames stay together."""
    for key in ("veer_pairs", "veer_gt_left", "veer_world_id"):
        if not np.array_equal(a[key], b[key]):
            raise ValueError(f"paired veer exam mismatch: {key}")
    pairs, worlds = a["veer_pairs"], a["veer_world_id"]
    n = len(pairs)
    if pairs.shape != (n, 2) or len(np.unique(pairs, axis=0)) != n:
        raise ValueError("invalid or duplicate veer pairs")
    if not np.issubdtype(pairs.dtype, np.integer) or (pairs < 0).any():
        raise ValueError("veer pairs must be nonnegative integer indices")
    for arm in (a, b):
        for key in ("veer_correct", "veer_gt_left", "veer_world_id"):
            if arm[key].shape != (n,):
                raise ValueError("inconsistent veer sample shape")
        if not np.isin(arm["veer_correct"], [0, 1]).all():
            raise ValueError("veer correctness must be binary")
    rows = {r: np.flatnonzero(pairs[:, 0] == r) for r in np.unique(pairs[:, 0])}
    if any(len(np.unique(worlds[ix])) != 1 for ix in rows.values()):
        raise ValueError("veer rollout belongs to multiple worlds")
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
    print(
        "WM-COMPARISON OK: paired course bootstrap, identity, alignment, undefined AUC"
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

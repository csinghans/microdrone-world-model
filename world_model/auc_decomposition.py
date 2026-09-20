"""Exact positive/negative group-pair decomposition of AUC; no model required.

python -m world_model.auc_decomposition
"""

import numpy as np

from world_model.metrics import roc_auc


def decompose(scores, labels, groups, rollouts, names):
    scores, labels, groups, rollouts = map(
        np.asarray, (scores, labels, groups, rollouts)
    )
    if scores.ndim != 1 or any(
        a.shape != scores.shape for a in (labels, groups, rollouts)
    ):
        raise ValueError("scores, labels, groups and rollouts must be aligned vectors")
    if not np.isfinite(scores).all() or not np.isin(labels, (0, 1)).all():
        raise ValueError("finite scores and binary labels required")
    if not names or len(set(names)) != len(names):
        raise ValueError("group names must be nonempty and unique")
    for a in (groups, rollouts):
        if not np.issubdtype(a.dtype, np.integer) or (a < 0).any():
            raise ValueError("group and rollout ids must be nonnegative integers")
    if (groups >= len(names)).any():
        raise ValueError("group id outside declared catalog")
    positive, negative = labels == 1, labels == 0
    total = int(positive.sum()) * int(negative.sum())
    support, pairs = {}, []
    masses = {"within": [0, 0.0], "across": [0, 0.0]}
    for i, name in enumerate(names):
        mask = groups == i
        pos, neg = mask & positive, mask & negative
        support[name] = {
            "samples": int(mask.sum()),
            "rollouts": int(len(np.unique(rollouts[mask]))),
            "positive": int(pos.sum()),
            "negative": int(neg.sum()),
            "positive_rollouts": int(len(np.unique(rollouts[pos]))),
            "negative_rollouts": int(len(np.unique(rollouts[neg]))),
        }
        for j, other in enumerate(names):
            nmask = (groups == j) & negative
            npos, nneg = int(pos.sum()), int(nmask.sum())
            count = npos * nneg
            auc = None
            if count:
                auc = roc_auc(
                    np.r_[scores[pos], scores[nmask]],
                    np.r_[np.ones(npos), np.zeros(nneg)],
                )
            weight = count / total if total else None
            wins = auc * count if count else 0.0
            contribution = wins / total if total else None
            part = masses["within" if i == j else "across"]
            part[0] += count
            part[1] += wins
            pairs.append(
                dict(
                    positive_group=name,
                    negative_group=other,
                    positive=npos,
                    negative=nneg,
                    pairs=count,
                    auc=auc,
                    weight=weight,
                    contribution=contribution,
                )
            )
    result = {
        "samples": len(scores),
        "rollouts": int(len(np.unique(rollouts))),
        "positive": int(positive.sum()),
        "negative": int(negative.sum()),
        "total_pairs": total,
        "auc": roc_auc(scores, labels) if total else None,
        "groups": support,
        "pairs": pairs,
    }
    for name, (count, wins) in masses.items():
        result[name] = dict(
            pairs=count,
            share=count / total if total else None,
            auc=wins / count if count else None,
            contribution=wins / total if total else None,
        )
    if total:
        reconstructed = (
            result["within"]["contribution"] + result["across"]["contribution"]
        )
        if not np.isclose(reconstructed, result["auc"], rtol=0, atol=1e-12):
            raise ValueError("pair decomposition failed to reconstruct AUC")
    return result


def selftest():
    rng = np.random.default_rng(0)
    names = ["a", "b", "absent"]
    for _ in range(24):
        scores = rng.integers(0, 4, size=24)
        labels = np.r_[np.ones(9), np.zeros(15)]
        groups = rng.integers(0, 2, size=24)
        rolls = np.arange(24) // 3
        r = decompose(scores, labels, groups, rolls, names)
        positive, negative = scores[labels == 1], scores[labels == 0]
        oracle = (
            (positive[:, None] > negative) + 0.5 * (positive[:, None] == negative)
        ).mean()
        assert r["auc"] == oracle
        assert r["within"]["pairs"] + r["across"]["pairs"] == 9 * 15
        assert r["groups"]["absent"]["samples"] == 0
        for pair in r["pairs"]:
            i, j = names.index(pair["positive_group"]), names.index(
                pair["negative_group"]
            )
            p, n = (
                scores[(groups == i) & (labels == 1)],
                scores[(groups == j) & (labels == 0)],
            )
            if len(p) and len(n):
                expected = ((p[:, None] > n) + 0.5 * (p[:, None] == n)).mean()
                assert pair["auc"] == expected
            else:
                assert pair["auc"] is None and pair["contribution"] == 0.0
        permutation = rng.permutation(24)
        assert (
            decompose(
                scores[permutation],
                labels[permutation],
                groups[permutation],
                rolls[permutation],
                names,
            )
            == r
        )
    # Group-constant scores contain no within-group ranking, yet pooled AUC is .9.
    y = np.r_[1, np.zeros(9), np.ones(9), 0]
    g = np.repeat(np.arange(2), 10)
    r = decompose(g, y, g, np.arange(20), names)
    assert r["auc"] == 0.9 and r["within"]["auc"] == 0.5
    assert np.isclose(r["within"]["share"], 0.18)
    # Single-class and empty inputs have no ranking score; no .5 fallback.
    for y in (np.ones(3), np.zeros(3), np.array([])):
        n = len(y)
        r = decompose(np.zeros(n), y, np.zeros(n, dtype=int), np.arange(n), names)
        assert r["auc"] is None
        assert all(r[k]["auc"] is None for k in ("within", "across"))
    r = decompose([1.0, 0.0], [1, 0], [0, 1], [0, 1], names)
    assert r["within"]["auc"] is None and r["across"]["auc"] == 1.0
    for scores, labels, groups, rolls in (
        ([float("nan"), 0], [1, 0], [0, 1], [0, 1]),
        ([1, 0], [0.5, 0], [0, 1], [0, 1]),
        ([1, 0], [1, 0], [0, 9], [0, 1]),
        ([1, 0], [1, 0], [0.0, 1.0], [0, 1]),
        ([1, 0], [1, 0], [0, 1], [-1, 1]),
        ([1], [1, 0], [0, 1], [0, 1]),
    ):
        try:
            decompose(scores, labels, groups, rolls, names)
        except ValueError:
            pass
        else:
            raise AssertionError("malformed decomposition input accepted")
    print("AUC-DECOMPOSITION OK: pairwise oracle, ties, support, permutations, mixture")


if __name__ == "__main__":
    selftest()

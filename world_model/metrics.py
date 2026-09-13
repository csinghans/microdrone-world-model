"""Pure NumPy research metrics, usable without model or simulator artifacts."""

import numpy as np

AUC_METHOD = "mann_whitney_average_ranks_v2"


def roc_auc(scores: np.ndarray, labels: np.ndarray) -> float:
    """Mann-Whitney AUC with half credit for tied positive/negative scores.

    Labels above/below 0.5 are positive/negative; exactly 0.5 is ignored.
    Preserve the project's 0.5 fallback when either class is absent.
    """
    scores, labels = np.asarray(scores), np.asarray(labels)
    if scores.shape != labels.shape:
        raise ValueError("AUC scores and labels must have matching shapes")
    if not np.isfinite(scores).all() or not np.isfinite(labels).all():
        raise ValueError("AUC scores and labels must be finite")
    pos, neg = scores[labels > 0.5], scores[labels < 0.5]
    if len(pos) == 0 or len(neg) == 0:
        return 0.5
    values = np.concatenate([pos, neg])
    order = values.argsort()
    ordered = values[order]
    starts = np.r_[0, np.flatnonzero(ordered[1:] != ordered[:-1]) + 1]
    ends = np.r_[starts[1:], len(order)]
    ranks = np.empty(len(order), dtype=np.float64)
    # Each equal-score group receives its average one-based rank. Arbitrary
    # distinct ranks make ties depend on sort order (all ties can score 0).
    ranks[order] = np.repeat((starts + ends + 1) / 2, ends - starts)
    r_pos = ranks[: len(pos)].sum()
    return float((r_pos - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def selftest() -> None:
    scores = np.array([0.9, 0.8, 0.2, 0.1])
    labels = np.array([1, 1, 0, 0])
    assert roc_auc(scores, labels) == 1.0, "perfect ranking must score 1"
    assert roc_auc(-scores, labels) == 0.0, "reversed ranking must score 0"
    for y in (labels, np.array([1, 0, 0, 0])):
        assert roc_auc(np.full(len(y), 0.5), y) == 0.5, "all ties must score 0.5"

    def pairwise_oracle(s, y):
        pos, neg = s[y > 0.5, None], s[None, y < 0.5]
        return float(((pos > neg) + 0.5 * (pos == neg)).mean())

    mixed = np.array([0.9, 0.5, 0.5, 0.1])
    expected = pairwise_oracle(mixed, labels)
    assert expected == 0.875
    assert roc_auc(mixed, labels) == expected, "mixed ties must receive half credit"
    rng = np.random.default_rng(0)
    for _ in range(32):
        # Saturated/quantized predictions produce many ties across both classes.
        s = rng.integers(0, 4, size=32)
        y = np.r_[np.ones(11), np.zeros(21)]
        expected = pairwise_oracle(s, y)
        assert roc_auc(s, y) == expected, "rank AUC must match pairwise comparisons"
        order = rng.permutation(len(y))
        assert roc_auc(s[order], y[order]) == expected, "AUC must ignore row order"

    for y in (np.array([]), np.ones(4), np.zeros(4), np.full(4, 0.5)):
        assert roc_auc(np.zeros(len(y)), y) == 0.5, "missing class fallback changed"
    assert roc_auc(np.array([1.0, 0.0, 9.0]), np.array([1.0, 0.0, 0.5])) == 1.0
    for s, y in (
        ([float("nan"), 0], [1, 0]),
        ([1, 0], [float("inf"), 0]),
        ([1], [1, 0]),
    ):
        try:
            roc_auc(np.asarray(s), np.asarray(y))
        except ValueError:
            pass
        else:
            raise AssertionError("malformed AUC input produced a plausible metric")
    print("METRICS OK: tied ranks, pairwise oracle, missing classes, malformed inputs")


if __name__ == "__main__":
    selftest()

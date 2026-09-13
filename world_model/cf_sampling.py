"""Explicit counterfactual hard-pool recipes, with no model/RNG side effects.

    python -m world_model.cf_sampling

legacy_masked preserves the existing zero-masked-vector heuristic.
answerable requires different labels among candidates with answerable labels
at the SAME horizon/ring. A fully masked row has no ranking information.
Neither rule changes the oracle labels or the CF loss's visibility mask.
"""

import numpy as np

CF_HARD_POOLS = ("legacy_masked", "answerable")


def hard_pool_mask(labels, visible, mode="legacy_masked"):
    """Map (..., actions, horizons, rings) labels to a (...) frame mask."""
    if mode not in CF_HARD_POOLS:
        raise ValueError(f"unknown CF hard-pool recipe: {mode}")
    labels, visible = np.asarray(labels), np.asarray(visible)
    if labels.ndim < 4 or visible.shape != labels.shape[:-2]:
        raise ValueError("CF labels/visibility shapes do not align")
    if labels.shape[-3] < 1 or not np.isin(labels, [0, 1]).all():
        raise ValueError("CF labels must be binary with at least one action")
    if not np.isin(visible, [0, 1]).all():
        raise ValueError("CF visibility must be binary")
    if mode == "legacy_masked":
        masked = labels * visible[..., None, None]
        return (masked.max(axis=-3) != masked.min(axis=-3)).any(axis=(-2, -1))
    # Signed sentinels avoid treating an unknown label as safe. Cast uint8
    # labels before introducing -1 (NumPy 2 rejects an out-of-range scalar).
    signed = labels.astype(np.int8, copy=False)
    high = np.where(visible[..., None, None], signed, -1).max(axis=-3)
    low = np.where(visible[..., None, None], signed, 2).min(axis=-3)
    return (high > low).any(axis=(-2, -1))


def selftest():
    rng = np.random.default_rng(117)
    labels = rng.integers(0, 2, (100, 6, 4, 2), dtype=np.uint8)
    visible = rng.integers(0, 2, (100, 6), dtype=np.uint8)
    old = (labels * visible[:, :, None, None]).reshape(100, 6, 8)
    expected = (old.max(axis=1) != old.min(axis=1)).any(axis=1)
    assert np.array_equal(hard_pool_mask(labels, visible), expected)
    candidate = hard_pool_mask(labels, visible, "answerable")
    assert not (candidate & ~expected).any(), "answerable pool must be a subset"
    # Flipping masked labels cannot change the candidate's ranking questions.
    changed = np.where(visible[..., None, None], labels, 1 - labels)
    assert np.array_equal(candidate, hard_pool_mask(changed, visible, "answerable"))
    visible[:] = 1
    assert np.array_equal(
        hard_pool_mask(labels, visible), hard_pool_mask(labels, visible, "answerable")
    )
    labels[:] = 1
    visible[:, 0] = 0
    assert hard_pool_mask(labels, visible).all()
    assert not hard_pool_mask(labels, visible, "answerable").any()
    visible[:] = 0
    assert not hard_pool_mask(labels, visible).any()
    assert not hard_pool_mask(labels, visible, "answerable").any()
    # A difference across horizons alone is not an action-ranking contrast.
    labels[:, :, :2] = 0
    visible[:] = 1
    assert not hard_pool_mask(labels, visible, "answerable").any()
    for args in ((labels, visible, "bad"), (labels, visible[:, :2])):
        try:
            hard_pool_mask(*args)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid recipe/shape accepted")
    print("CF-SAMPLING OK: exact legacy mask, answerable pairs, masked invariance")


if __name__ == "__main__":
    selftest()

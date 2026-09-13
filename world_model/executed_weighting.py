"""Optional moving-world weighting of executed prediction/collision losses.

    python -m world_model.executed_weighting

The normalizer uses only eligible training windows, once before fitting.
Weights change objective allocation, not sample counts or independent data.
"""

import numpy as np


def plan(data, pairs, train_indices, moving_weight=1.0):
    factor = float(moving_weight)
    if not np.isfinite(factor) or factor <= 0:
        raise ValueError("executed moving weight must be finite and positive")
    rolls = pairs[np.asarray(train_indices), 0]
    if not len(rolls):
        raise ValueError("no eligible training windows for executed loss")
    if "world_id" in data:
        names = list(map(str, data.get("world_names", ["classic", "dense", "moving"])))
        ids = np.asarray(data["world_id"])[rolls]
        worlds = np.asarray([names[w] if 0 <= w < len(names) else str(w) for w in ids])
    else:
        worlds = np.full(len(rolls), "unrecorded")
    moving = worlds == "moving"
    if factor != 1.0 and not moving.any():
        raise ValueError(
            "nonunit moving weight requires identified moving train windows"
        )
    raw = np.where(moving, factor, 1.0)
    normalizer = float(raw.mean())
    weights = (raw / normalizer).astype(np.float32)
    if not np.isfinite(weights).all() or not (weights > 0).all():
        raise ValueError("executed weights cannot be represented as positive float32")
    info = {
        "moving_weight": factor,
        "normalizer": normalizer,
        "train_windows": len(rolls),
        "by_world": {
            str(w): {
                "windows": int((worlds == w).sum()),
                "window_share": float((worlds == w).mean()),
                "weight_mass_share": float(raw[worlds == w].sum() / raw.sum()),
            }
            for w in np.unique(worlds)
        },
    }
    return weights, info


def weighted_mean(elementwise, weights=None):
    """Default keeps the exact original mean; weights are already normalized."""
    if weights is None:
        return elementwise.mean()
    if weights.ndim != 1 or len(weights) != len(elementwise):
        raise ValueError("one executed weight required per batch window")
    per_window = elementwise.reshape(len(elementwise), -1).mean(dim=1)
    return (per_window * weights).mean()


def selftest():
    import torch

    data = {"world_id": np.array([0, 1, 0]), "world_names": ["classic", "moving"]}
    pairs = np.array([[0, 0], [0, 1], [1, 0], [2, 0]])
    before = torch.get_rng_state().clone()
    unit, ui = plan(data, pairs, [0, 1, 2], 1.0)
    weights, info = plan(data, pairs, [0, 1, 2], 2.25)
    assert torch.equal(before, torch.get_rng_state()), "planning must not consume RNG"
    assert np.array_equal(unit, np.ones(3, dtype=np.float32))
    assert ui["normalizer"] == 1.0 and np.isclose(weights.mean(), 1.0)
    assert np.isclose(weights[2] / weights[0], 2.25)
    assert info["by_world"]["moving"]["weight_mass_share"] == 2.25 / 4.25
    # Unused validation courses cannot affect the training normalizer.
    data["world_id"][2] = 1
    assert np.array_equal(weights, plan(data, pairs, [0, 1, 2], 2.25)[0])
    x = torch.tensor([[1.0, 4.0], [9.0, 16.0], [25.0, 36.0]], requires_grad=True)
    assert torch.equal(weighted_mean(x), x.mean())
    weighted_mean(x, torch.tensor(weights)).backward()
    expected = torch.tensor(weights)[:, None].expand_as(x) / x.numel()
    torch.testing.assert_close(x.grad, expected, rtol=1e-6, atol=1e-8)
    for factor in (0, -1, float("nan"), float("inf")):
        try:
            plan(data, pairs, [0, 1, 2], factor)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid factor accepted")
    try:
        plan(data, pairs, [0, 1], 2.25)
    except ValueError:
        pass
    else:
        raise AssertionError("unidentified moving training data accepted")
    print(
        "EXECUTED-WEIGHTING OK: unit parity, train-only normalization, gradients, RNG"
    )


if __name__ == "__main__":
    selftest()

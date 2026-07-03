"""Domain-randomization primitives (image space).

Training a perception model on randomized appearance (brightness, noise)
forces it to key on *shape*, not the exact colours of one clean sim render —
so it survives an appearance it never saw. `shift_appearance` is the held-out
counterpart: a FIXED shift that stands in for a camera/lighting the model
never trained on, used to *price* the sim-to-real gap before hardware pays it.

The plant-side randomizations (pillar shape/colour, command latency,
actuation noise) live where they act: `sim.scenarios.spawn_pillars` and the
rollout/env loops, keyed off the same `randomize` flag.
"""

import numpy as np


def jitter(imgs, rng):
    """Per-image random brightness + heavy Gaussian noise (training-time DR).
    The noise range is wide on purpose so it covers the appearance shifts a
    deployed model will actually hit."""
    out = imgs.copy()
    b = rng.uniform(0.5, 1.5, size=(len(out), 1, 1, 1)).astype(np.float32)
    sigma = rng.uniform(0.0, 0.18, size=(len(out), 1, 1, 1)).astype(np.float32)
    out = out * b + rng.standard_normal(out.shape).astype(np.float32) * sigma
    return np.clip(out, 0.0, 1.0).astype(np.float32)


def shift_appearance(imgs, brightness: float = 0.7, noise: float = 0.15, seed: int = 7):
    """A FIXED appearance shift (dimmer + heavily noisier) — stands in for a
    different camera / lighting the model never trained on (a sim-to-real gap)."""
    rng = np.random.default_rng(seed)
    out = imgs * brightness + rng.normal(0, noise, size=imgs.shape).astype(np.float32)
    return np.clip(out, 0.0, 1.0).astype(np.float32)


def selftest() -> None:
    rng = np.random.default_rng(7)
    x = np.full((4, 8, 8, 3), 0.5, dtype=np.float32)
    j = jitter(x, rng)
    s1, s2 = shift_appearance(x), shift_appearance(x)
    assert j.shape == x.shape and j.min() >= 0.0 and j.max() <= 1.0
    assert not np.allclose(j, x), "jitter must actually change the images"
    assert np.allclose(s1, s2), "shift_appearance must be deterministic"
    assert s1.mean() < x.mean(), "the fixed shift dims the scene"
    print("DOMAIN-RAND OK: jitter varies, shift_appearance fixed + dimmer")


if __name__ == "__main__":
    selftest()

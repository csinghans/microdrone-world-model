"""The command vocabulary every layer shares.

Six high-level commands (m/s + yaw-rate), world frame with yaw held at 0, so
body frame == world frame throughout — the honest nano simplification that
keeps dataset actions and planner candidates literally identical. The model
conditions on the *commanded* setpoint, never the measured velocity: a
deployed controller can only ever feed it a command, so that is what it must
learn on.

Every training rollout scales the whole command set by one cruise-speed
factor (SPEED_RANGE). Danger is a function of *how fast you are going*, so
the model must see the same corridor flown timidly and briskly — otherwise a
faster planner would be asking it questions from outside the training
envelope.
"""

import numpy as np

ACTIONS = {
    "forward": (0.80, 0.00, 0.00, 0.0),
    "slow": (0.30, 0.00, 0.00, 0.0),
    "veer_left": (0.50, 0.50, 0.00, 0.0),
    "veer_right": (0.50, -0.50, 0.00, 0.0),
    "climb": (0.40, 0.00, 0.40, 0.0),
    "hover": (0.00, 0.00, 0.00, 0.0),
}
ACTION_NAMES = list(ACTIONS)
ACTION_VECS = np.array([ACTIONS[n] for n in ACTION_NAMES], dtype=np.float32)
FORWARD = ACTION_NAMES.index("forward")
SPEED_RANGE = (0.75, 2.0)  # x base speeds -> 0.6..1.6 m/s cruise
# Per-dim normaliser so every action (at any speed) feeds the network in ~[-1, 1].
A_NORM = np.maximum(np.abs(ACTION_VECS).max(axis=0) * SPEED_RANGE[1], 1e-6).astype(
    np.float32
)


def menu(names=("forward", "slow", "veer_left", "veer_right", "hover")):
    """Planner menu -> action ids. `climb` stays off the default menu: it
    games the planar danger labels (changes the view, not the label)."""
    return [ACTION_NAMES.index(n) for n in names]


def selftest() -> None:
    assert ACTION_VECS.shape == (6, 4) and FORWARD == 0
    assert np.all(np.abs(ACTION_VECS * SPEED_RANGE[1]) / A_NORM <= 1.0 + 1e-6)
    m = menu()
    assert len(m) == 5 and ACTION_NAMES.index("climb") not in m
    print(f"ACTION-SET OK: {len(ACTIONS)} commands, menu {len(m)}, A_NORM {A_NORM[:2]}")


if __name__ == "__main__":
    selftest()

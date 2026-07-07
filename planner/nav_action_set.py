"""The command vocabulary for the Indoor Active Search Track.

A SEPARATE, translational 2D-roaming vocabulary — it does NOT replace
`planner.action_set` (the forward-transit benchmark that every existing
regression guard is trained and scored against). Search needs to visit a
whole room, so it needs to move in -x and pure ±y, which the transit set
cannot express (its veers all carry vx>0, and it has no reverse).

**Yaw is still held at 0 on every command** — body frame == world frame,
exactly as in `action_set.py`. This is deliberate: the world model
conditions on the commanded setpoint under the yaw≡0 assumption, and
adding a yaw-rate command would break that coordinate frame and force a
full model + dataset regeneration. Translation keeps the frame intact.

Caveat, by construction: the shipped world model was trained only on the
forward-biased transit commands, so its collision heads are OUT OF
DISTRIBUTION for reverse / pure strafe. Phase 1a therefore flies these
under a privileged geometric safety filter; Phase 1b retrains the model
on this set before it may serve as the safety layer (see
`docs/TRAINING-A-SKILL.md` and the search_room campaign).

Camera stays locked to +x (no yaw), so this vocabulary suits an
omnidirectional beacon target — the drone need not turn to sense it.
Looking-around (yaw) is deferred to the visual-detection phase, which is
where it is actually needed and where the model retrain is justified.
"""

import numpy as np

# (vx, vy, vz, yaw_rate) world-frame velocity setpoints; yaw_rate ALWAYS 0.
NAV_ACTIONS = {
    "forward": (0.60, 0.00, 0.00, 0.0),  # +x
    "reverse": (-0.60, 0.00, 0.00, 0.0),  # -x (the transit set cannot do this)
    "strafe_left": (0.00, 0.60, 0.00, 0.0),  # +y, no forward bias
    "strafe_right": (0.00, -0.60, 0.00, 0.0),  # -y
    "slow": (0.30, 0.00, 0.00, 0.0),  # slow +x for fine approach near walls
    "hover": (0.00, 0.00, 0.00, 0.0),
}
NAV_ACTION_NAMES = list(NAV_ACTIONS)
NAV_ACTION_VECS = np.array([NAV_ACTIONS[n] for n in NAV_ACTION_NAMES], dtype=np.float32)
FORWARD = NAV_ACTION_NAMES.index("forward")
REVERSE = NAV_ACTION_NAMES.index("reverse")
STRAFE_L = NAV_ACTION_NAMES.index("strafe_left")
STRAFE_R = NAV_ACTION_NAMES.index("strafe_right")
HOVER = NAV_ACTION_NAMES.index("hover")

# roaming is slower than transit cruise — coverage does not need 1.6 m/s,
# and slower flight is safer near walls / cheaper on the seam-free plane
NAV_SPEED_RANGE = (0.5, 1.0)  # base scale -> 0.3..0.6 m/s
A_NORM = np.maximum(
    np.abs(NAV_ACTION_VECS).max(axis=0) * NAV_SPEED_RANGE[1], 1e-6
).astype(np.float32)


def nav_menu(names=("forward", "reverse", "strafe_left", "strafe_right", "hover")):
    """Planner menu -> action ids. `slow` stays off the default menu (a
    fine-approach modifier, not a coverage direction) — the four cardinal
    translations + hover span 2D roaming."""
    return [NAV_ACTION_NAMES.index(n) for n in names]


def selftest() -> None:
    assert NAV_ACTION_VECS.shape == (6, 4)
    # every command is planar and yaw-free — the frame-preserving invariant
    assert np.all(NAV_ACTION_VECS[:, 2] == 0.0), "no vz (planar roaming)"
    assert np.all(NAV_ACTION_VECS[:, 3] == 0.0), "yaw held at 0 (body==world)"
    # the two capabilities the transit set lacks
    assert NAV_ACTIONS["reverse"][0] < 0.0, "reverse moves -x"
    assert (
        NAV_ACTIONS["strafe_left"][0] == 0.0 and NAV_ACTIONS["strafe_left"][1] > 0.0
    ), "strafe is pure +y, no forward bias"
    # 2D coverage is expressible: +x, -x, +y, -y all reachable
    dirs = {tuple(np.sign(NAV_ACTION_VECS[i, :2])) for i in nav_menu()}
    for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        assert d in dirs, f"missing cardinal {d}"
    assert np.all(np.abs(NAV_ACTION_VECS * NAV_SPEED_RANGE[1]) / A_NORM <= 1.0 + 1e-6)
    m = nav_menu()
    assert len(m) == 5 and NAV_ACTION_NAMES.index("slow") not in m
    print(
        f"NAV-ACTION-SET OK: {len(NAV_ACTIONS)} commands, menu {len(m)}, "
        f"4 cardinal translations + hover, yaw==0 preserved"
    )


if __name__ == "__main__":
    selftest()

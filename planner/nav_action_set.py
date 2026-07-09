"""The command vocabulary for the Indoor Active Search Track.

A SEPARATE, translational 2D-roaming vocabulary — it does NOT replace
`planner.action_set` (the forward-transit benchmark that every existing
regression guard is trained and scored against). Search needs to visit a
whole room, so it needs to move in -x and pure ±y, which the transit set
cannot express (its veers all carry vx>0, and it has no reverse).

**The COVERAGE menu (`nav_menu`: cardinals + hover) is yaw-free** — body
frame == world frame, exactly as in `action_set.py`, so search flight keeps
the coordinate frame the collision reasoning relies on. Two scan-only
actions (`yaw_left`/`yaw_right`) turn IN PLACE (zero translation) and are
kept OFF the coverage menu; they exist for the hover-yaw-scan that confirms
a VISUAL target. yaw_v1 Phase 0 measured that the frozen WM latent detects
a target just as well when the camera is yawed (AUC ~0.98 across ±90°), so
turning to LOOK needs no WM retrain — only the detection head. Turning
while TRANSLATING (body-frame vx,vy) + collision under yaw still needs the
WM retrain (deferred, Phase 1b).

Caveat, by construction: the shipped world model was trained only on the
forward-biased transit commands, so its collision heads are OUT OF
DISTRIBUTION for reverse / pure strafe. Search flies these under a
privileged geometric safety filter (beams8); the yaw scan happens at a
hover point (already clear), so it does not touch the collision heads.
"""

import numpy as np

YAW_RATE = 2.5  # rad/s for the look-around scan (yaw_v1); OFF the coverage menu
LIFT_V = 0.60  # m/s for the vertical altitude sweep (alt_v1); OFF the coverage menu

# (vx, vy, vz, yaw_rate) setpoints. The COVERAGE menu (cardinals + hover) is
# still yaw-free AND planar (vz=0) -> body==world holds for search flight. The
# scan/lift actions below turn or lift IN PLACE (zero horizontal translation):
# yaw for the horizontal target scan (yaw_v1), up/down for the multi-altitude
# sweep that finds high/low targets (alt_v1). vz is a clean free DOF (the
# camera stays level), so a level +x view at any altitude needs no WM retrain
# (alt_v1 Phase 0: detection holds across altitude with a retrained head).
NAV_ACTIONS = {
    "forward": (0.60, 0.00, 0.00, 0.0),  # +x
    "reverse": (-0.60, 0.00, 0.00, 0.0),  # -x (the transit set cannot do this)
    "strafe_left": (0.00, 0.60, 0.00, 0.0),  # +y, no forward bias
    "strafe_right": (0.00, -0.60, 0.00, 0.0),  # -y
    "slow": (0.30, 0.00, 0.00, 0.0),  # slow +x for fine approach near walls
    "hover": (0.00, 0.00, 0.00, 0.0),
    "yaw_left": (0.00, 0.00, 0.00, YAW_RATE),  # turn in place +yaw (scan only)
    "yaw_right": (0.00, 0.00, 0.00, -YAW_RATE),  # turn in place -yaw
    "up": (0.00, 0.00, LIFT_V, 0.0),  # rise in place (altitude sweep)
    "down": (0.00, 0.00, -LIFT_V, 0.0),  # descend in place
}
NAV_ACTION_NAMES = list(NAV_ACTIONS)
NAV_ACTION_VECS = np.array([NAV_ACTIONS[n] for n in NAV_ACTION_NAMES], dtype=np.float32)
FORWARD = NAV_ACTION_NAMES.index("forward")
REVERSE = NAV_ACTION_NAMES.index("reverse")
STRAFE_L = NAV_ACTION_NAMES.index("strafe_left")
STRAFE_R = NAV_ACTION_NAMES.index("strafe_right")
HOVER = NAV_ACTION_NAMES.index("hover")
YAW_L = NAV_ACTION_NAMES.index("yaw_left")
YAW_R = NAV_ACTION_NAMES.index("yaw_right")
UP = NAV_ACTION_NAMES.index("up")
DOWN = NAV_ACTION_NAMES.index("down")

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
    assert NAV_ACTION_VECS.shape == (10, 4)
    # the COVERAGE menu (cardinals + hover) is still planar + yaw-free ->
    # body==world holds for search flight; only the scan/lift actions break it.
    assert np.all(NAV_ACTION_VECS[nav_menu(), 2] == 0.0), "coverage menu planar (vz=0)"
    assert np.all(NAV_ACTION_VECS[nav_menu(), 3] == 0.0), "coverage menu yaw-free"
    yaw_ids = [NAV_ACTION_NAMES.index(n) for n in ("yaw_left", "yaw_right")]
    assert np.all(NAV_ACTION_VECS[yaw_ids, 3] != 0.0), "yaw scan actions carry yaw"
    assert np.all(NAV_ACTION_VECS[yaw_ids, :3] == 0.0), "yaw turns in place"
    lift_ids = [NAV_ACTION_NAMES.index(n) for n in ("up", "down")]
    assert np.all(NAV_ACTION_VECS[lift_ids, 2] != 0.0), "lift actions carry vz"
    assert np.all(
        NAV_ACTION_VECS[lift_ids, :2] == 0.0
    ), "lift is vertical in place (no horizontal)"
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

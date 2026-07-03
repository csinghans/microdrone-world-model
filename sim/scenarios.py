"""Course layouts and scoring truths: pillar corridors, danger rings, FOV.

The scenario module owns what the *world* is — where obstacles go and what
counts as dangerous. Pillar positions are used to stage courses and to score
flights; they are never given to a policy (every controller in this repo is
vision-only unless it is explicitly labelled a privileged baseline).

Honest notes that shape everything downstream:
  * Pillars are visual-only (no contact physics), so "danger" is a planar
    distance, measured even when the drone flies straight through — which is
    exactly what makes through-pass labels clean.
  * Two rings, not one: a single ring is a region test, not a risk gradient.
    Once the drone is inside the 0.7 m warn ring, every action's warn label
    is 1 — including the one that leaves — and a planner reading only that
    signal goes blind exactly when it matters (measured: it braked to a
    permanent hover mid-course). The 0.35 m critical ring separates "grazes
    past" from "about to hit" everywhere.
  * The camera sees a wedge. FOV_HALF_DEG keeps a margin inside the sim's
    60 degree render, and the label machinery marks out-of-FOV threats as
    unanswerable from a single frame.
"""

import numpy as np

GOAL_X = 3.0  # finish line (m) — every corridor episode flies START -> here
TMAX = 360  # episode step budget (7.5 s @ 48 Hz)
DANGER_R = 0.7  # planar distance (m) that counts as "dangerously close" soon
CRIT_R = 0.35  # planar distance (m) that counts as "about to hit" (crash + margin)
RADII = (DANGER_R, CRIT_R)  # warn ring + critical ring
COLLISION_R = 0.22  # planar distance (m) that counts as a crash
FOV_HALF_DEG = 28  # camera half-FOV (the sim renders 60 deg; keep a margin)


def spawn_pillars(env, rng, in_path: bool, solo: bool = False, randomize: bool = False):
    """Drop 2-3 visual pillars into a fresh (post-reset) arena and return their
    planar centres. `in_path=True` puts the first one in the forward corridor;
    otherwise all sit off to the sides. `solo=True` places ONLY the in-path
    pillar — the speed sweep uses it to test the anticipation-vs-reaction
    mechanism on a threat both policies can actually see (side-pillar clutter
    probes the FOV limit instead, and is measured separately).
    `randomize=True` draws each pillar's radius, height and colour (vary what
    a real scene would vary anyway). Monocular honesty: radius variation makes
    apparent size an ambiguous distance cue — harder, and real. Bodies are
    wiped by the next env.reset()."""
    import pybullet as p

    pillars = []
    n = 1 if solo else int(rng.integers(2, 4))
    for i in range(n):
        if in_path and i == 0:
            px, py = float(rng.uniform(1.3, 2.0)), float(rng.uniform(-0.2, 0.2))
        else:
            px, py = float(rng.uniform(0.9, 2.6)), float(rng.uniform(0.9, 1.5))
            py *= 1.0 if rng.random() < 0.5 else -1.0
        pillars.append((px, py))
        if randomize:
            radius = float(rng.uniform(0.14, 0.22))
            length = float(rng.uniform(1.0, 1.8))
            base = np.array([0.80, 0.32, 0.22])
            color = list(np.clip(base + rng.uniform(-0.3, 0.3, 3), 0.05, 1.0)) + [1]
        else:
            radius, length, color = 0.18, 1.4, [0.80, 0.32, 0.22, 1]
        vis = p.createVisualShape(
            p.GEOM_CYLINDER,
            radius=radius,
            length=length,
            rgbaColor=color,
            physicsClientId=env.CLIENT,
        )
        p.createMultiBody(
            baseMass=0,
            baseVisualShapeIndex=vis,
            basePosition=[px, py, length / 2],
            physicsClientId=env.CLIENT,
        )
    return pillars


def nearest_planar(pos_xy, pillars) -> float:
    """Planar distance from pos to the closest pillar centre (m)."""
    if not len(pillars):
        return 9.0
    return float(min(np.linalg.norm(np.asarray(pos_xy) - np.array(q)) for q in pillars))


def selftest() -> None:
    rng = np.random.default_rng(7)
    from sim.envs import make_env

    env = make_env()
    env.reset(seed=7)
    solo = spawn_pillars(env, rng, in_path=True, solo=True)
    env.reset(seed=8)
    clutter = spawn_pillars(env, rng, in_path=False, randomize=True)
    env.close()
    assert len(solo) == 1 and 1.3 <= solo[0][0] <= 2.0, "solo pillar off-corridor"
    assert 2 <= len(clutter) <= 3, "clutter count out of range"
    assert nearest_planar((0.0, 0.0), solo) > 1.0, "start position not clear"
    assert nearest_planar((0.0, 0.0), []) == 9.0, "empty layout sentinel broken"
    print(
        f"SCENARIOS OK: solo@{solo[0]}, {len(clutter)} clutter pillars, rings {RADII}"
    )


if __name__ == "__main__":
    selftest()

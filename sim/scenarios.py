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


def _pillar_body(env, px, py, radius=0.18, length=1.4, color=(0.80, 0.32, 0.22, 1)):
    """One visual pillar body; returns the pybullet body id."""
    import pybullet as p

    vis = p.createVisualShape(
        p.GEOM_CYLINDER,
        radius=radius,
        length=length,
        rgbaColor=list(color),
        physicsClientId=env.CLIENT,
    )
    return p.createMultiBody(
        baseMass=0,
        baseVisualShapeIndex=vis,
        basePosition=[px, py, length / 2],
        physicsClientId=env.CLIENT,
    )


def spawn_dense_pillars(env, rng):
    """The v0.2 FOV/memory stress test: 5-7 pillars — TWO forced into the
    flight corridor at staggered depths, the rest tight side clutter on both
    sides (0.55-1.2 m off-axis, inside evasion range). Every evasion from the
    first threat steers toward somewhere the camera has not looked recently;
    a memoryless policy must pay here, and a good memory should not."""
    pillars = []
    for x_lo, x_hi in ((1.0, 1.6), (1.9, 2.5)):  # two in-path threats
        pillars.append(
            (float(rng.uniform(x_lo, x_hi)), float(rng.uniform(-0.25, 0.25)))
        )
    n_side = int(rng.integers(3, 6))
    for i in range(n_side):
        px = float(rng.uniform(0.8, 2.7))
        py = float(rng.uniform(0.55, 1.2)) * (1.0 if i % 2 == 0 else -1.0)
        pillars.append((px, py))
    for px, py in pillars:
        _pillar_body(env, px, py)
    return pillars


class MovingCrosser:
    """The v0.2 timing stress test: one pillar CROSSES the corridor laterally
    while 1-2 static clutter pillars watch. The world model was trained on a
    static world, so its danger labels assume pillars stay put — this
    scenario measures what that assumption costs. Deliberately honest: the
    crosser is visually identical to a static pillar; only motion betrays it.

    `step()` must be called once per control step; `positions()` returns the
    current planar centres (crosser first) for scoring and for any policy
    that is allowed privileged state."""

    def __init__(self, env, rng, n_static: int = 1, cruise: float = 0.8):
        import pybullet as p

        self._p, self.env = p, env
        self.dt = env.CTRL_TIMESTEP
        side = 1.0 if rng.random() < 0.5 else -1.0
        self.x = float(rng.uniform(1.4, 2.3))
        self.y = side * float(rng.uniform(1.2, 1.8))
        # aim the crossing at the drone's arrival: it reaches x at ~x/cruise
        # seconds, so pick vy that brings the crosser to the centreline around
        # then (x0.75-1.25 jitter: sometimes ahead, sometimes behind), clamped
        # to a physically sane band
        t_arrive = self.x / max(cruise, 1e-6)
        vy = abs(self.y) / (t_arrive * float(rng.uniform(0.75, 1.25)))
        self.vy = -side * float(np.clip(vy, 0.2, 0.8))
        self.z = 0.7  # length 1.4 / 2
        self.body = _pillar_body(env, self.x, self.y)
        self.static = []
        for i in range(n_static):
            px = float(rng.uniform(0.9, 2.6))
            py = float(rng.uniform(0.9, 1.5)) * (1.0 if i % 2 == 0 else -1.0)
            _pillar_body(env, px, py)
            self.static.append((px, py))

    def step(self) -> None:
        self.y += self.vy * self.dt
        self._p.resetBasePositionAndOrientation(
            self.body,
            [self.x, self.y, self.z],
            [0, 0, 0, 1],
            physicsClientId=self.env.CLIENT,
        )

    def positions(self):
        return [(self.x, self.y)] + list(self.static)


def selftest() -> None:
    rng = np.random.default_rng(7)
    from sim.envs import make_env

    env = make_env()
    env.reset(seed=7)
    solo = spawn_pillars(env, rng, in_path=True, solo=True)
    env.reset(seed=8)
    clutter = spawn_pillars(env, rng, in_path=False, randomize=True)
    assert len(solo) == 1 and 1.3 <= solo[0][0] <= 2.0, "solo pillar off-corridor"
    assert 2 <= len(clutter) <= 3, "clutter count out of range"
    assert nearest_planar((0.0, 0.0), solo) > 1.0, "start position not clear"
    assert nearest_planar((0.0, 0.0), []) == 9.0, "empty layout sentinel broken"
    env.reset(seed=9)
    dense = spawn_dense_pillars(env, rng)
    assert 5 <= len(dense) <= 7, "dense count out of range"
    assert len([q for q in dense if abs(q[1]) <= 0.25]) >= 2, "need 2 in-path threats"
    env.reset(seed=10)
    mover = MovingCrosser(env, rng)
    y0 = mover.positions()[0][1]
    t_cross = abs(y0) / abs(mover.vy)  # when it reaches the centreline
    t_drone = mover.x / 0.8  # when the drone does (default cruise)
    assert 0.5 <= t_cross / t_drone <= 1.5, "crossing not aimed at the encounter"
    for _ in range(48):  # one second
        mover.step()
    dy = mover.positions()[0][1] - y0
    env.close()
    assert 0.2 <= abs(dy) <= 0.8, f"crosser speed off ({dy:+.2f} m/s)"
    assert abs(y0 + dy) < abs(y0), "crosser must move toward the corridor"
    print(
        f"SCENARIOS OK: solo@{solo[0]}, {len(clutter)} clutter, dense {len(dense)} "
        f"(2 in-path), crosser {dy:+.2f} m/s, rings {RADII}"
    )


if __name__ == "__main__":
    selftest()

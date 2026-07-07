"""The three Phase-1a search strategies — the coverage baselines.

All three share the same beacon-approach behavior (once the abstract
beacon is within sensor range, drive along its bearing — the SGBA
gradient, inverted from homing to seeking), so they are compared purely
on how they SEARCH *before* the beacon is sensed:

  * **RandomWalk** — a momentum random walk (resample a cardinal every
    few decisions). The null baseline: coverage by luck.
  * **WallFollow** — SGBA-style: hug a wall, turning along it when the
    forward rangefinder closes. Minimal-sensing exploration.
  * **Frontier** — maintain a visited-cell memory (the drone's own map)
    and step toward the nearest unvisited free cell. Coverage-greedy.

Perception used: the 4 cardinal rangefinders (`ctx["ranges"]`) and the
beacon sense (`ctx["sense"]`) — plus, for Frontier, the drone's own
position history (a self-map, like the odometry x-progress pin). The
privileged geometric safety filter lives in the runner, not here.
"""

import numpy as np

from planner.nav_action_set import FORWARD, HOVER, REVERSE, STRAFE_L, STRAFE_R

_CARDINALS = (FORWARD, REVERSE, STRAFE_L, STRAFE_R)


def _cardinal(dx, dy) -> int:
    """The nav action whose translation best matches direction (dx, dy)."""
    if abs(dx) >= abs(dy):
        return FORWARD if dx >= 0 else REVERSE
    return STRAFE_L if dy >= 0 else STRAFE_R


class _Base:
    """Shared: approach the beacon once sensed; else defer to _search."""

    def begin(self, scenario) -> None:
        self.bounds = scenario.bounds
        self.cell = scenario.cell
        self.seed = int(scenario.meta.get("seed", 0))

    def decide(self, ctx) -> int:
        s = ctx["sense"]
        if s is not None:
            return _cardinal(np.cos(s["bearing"]), np.sin(s["bearing"]))
        return self._search(ctx)

    def _search(self, ctx) -> int:
        raise NotImplementedError


class RandomWalk(_Base):
    PERSIST = 6  # decisions to hold a heading before resampling

    def begin(self, scenario) -> None:
        super().begin(scenario)
        self.rng = np.random.default_rng(self.seed + 101)
        self._hold, self._act = 0, FORWARD

    def _search(self, ctx) -> int:
        if self._hold <= 0:
            self._act = int(self.rng.choice(_CARDINALS))
            self._hold = self.PERSIST
        self._hold -= 1
        return self._act


class WallFollow(_Base):
    """Hug the wall on the right: go along the current heading until the
    forward rangefinder closes, then turn (deterministic left turn),
    keeping the environment's perimeter swept."""

    CLOSE = 0.6  # turn when something is this close ahead

    _LEFT_TURN = {
        FORWARD: STRAFE_L,
        STRAFE_L: REVERSE,
        REVERSE: STRAFE_R,
        STRAFE_R: FORWARD,
    }
    _AXIS = {FORWARD: "+x", REVERSE: "-x", STRAFE_L: "+y", STRAFE_R: "-y"}

    def begin(self, scenario) -> None:
        super().begin(scenario)
        self._head = FORWARD

    def _search(self, ctx) -> int:
        ahead = ctx["ranges"][self._AXIS[self._head]]
        if ahead < self.CLOSE:  # wall ahead: turn along it
            self._head = self._LEFT_TURN[self._head]
        return self._head


class Frontier(_Base):
    """Coverage-greedy: keep a visited-cell set (own position history),
    step the cardinal toward the nearest unvisited free cell. Recomputes
    the target when reached or every REPLAN decisions."""

    REPLAN = 4

    def begin(self, scenario) -> None:
        super().begin(scenario)
        x0, x1, y0, y1 = self.bounds
        self.nx = max(1, int(round((x1 - x0) / self.cell)))
        self.ny = max(1, int(round((y1 - y0) / self.cell)))
        self.x0, self.y0 = x0, y0
        # free cells (clear of walls/obstacles) as the coverage universe
        self._free = set(
            scenario_free_cells(scenario, self.nx, self.ny, x0, y0, self.cell)
        )
        self._visited = set()
        self._target = None
        self._since = 0

    def _cell(self, pos):
        i = int((pos[0] - self.x0) / self.cell)
        j = int((pos[1] - self.y0) / self.cell)
        return (min(max(i, 0), self.nx - 1), min(max(j, 0), self.ny - 1))

    def _centre(self, c):
        return (self.x0 + (c[0] + 0.5) * self.cell, self.y0 + (c[1] + 0.5) * self.cell)

    def _search(self, ctx) -> int:
        pos = ctx["pos"]
        self._visited.add(self._cell(pos))
        self._since += 1
        frontier = self._free - self._visited
        if not frontier:
            return HOVER  # room covered
        if (
            self._target is None
            or self._target in self._visited
            or self._since >= self.REPLAN
        ):
            here = np.asarray(pos)
            self._target = min(
                frontier, key=lambda c: np.hypot(*(np.asarray(self._centre(c)) - here))
            )
            self._since = 0
        tx, ty = self._centre(self._target)
        return _cardinal(tx - pos[0], ty - pos[1])


def scenario_free_cells(scenario, nx, ny, x0, y0, cell):
    """Indices of grid cells clear enough to occupy (mirrors the
    scenario's coverage denominator, in index space)."""
    from sim.scenarios import COLLISION_R

    out = []
    for i in range(nx):
        for j in range(ny):
            cx, cy = x0 + (i + 0.5) * cell, y0 + (j + 0.5) * cell
            if scenario.clearance((cx, cy)) > COLLISION_R:
                out.append((i, j))
    return out


STRATEGIES = {"random": RandomWalk, "wall_follow": WallFollow, "frontier": Frontier}


def get_strategy(name: str):
    return STRATEGIES[name]()


def selftest() -> None:
    from sim.indoor.rooms import single_room

    sc = single_room(3)
    # cardinal mapping
    assert _cardinal(1, 0) == FORWARD and _cardinal(-1, 0) == REVERSE
    assert _cardinal(0, 1) == STRAFE_L and _cardinal(0, -1) == STRAFE_R
    # beacon approach: all strategies drive toward a sensed bearing
    for name in STRATEGIES:
        pol = get_strategy(name)
        pol.begin(sc)
        # beacon due -y (bearing -pi/2) -> strafe_right
        a = pol.decide(
            {
                "pos": (0.0, 0.0),
                "sense": {"bearing": -np.pi / 2, "range": 1.0},
                "ranges": sc.range_sensors((0.0, 0.0)),
                "step": 0,
            }
        )
        assert a == STRAFE_R, f"{name} should approach a -y beacon via strafe_right"
    # random walk: deterministic per seed, holds a heading
    r = get_strategy("random")
    r.begin(sc)
    ctx = {
        "pos": sc.start_xy,
        "sense": None,
        "ranges": sc.range_sensors(sc.start_xy),
        "step": 0,
    }
    seq = [r.decide(ctx) for _ in range(6)]
    assert len(set(seq)) == 1, "momentum: one heading held for PERSIST decisions"
    # frontier: visits new cells; target is an unvisited free cell
    f = get_strategy("frontier")
    f.begin(sc)
    a = f.decide(
        {
            "pos": sc.start_xy,
            "sense": None,
            "ranges": sc.range_sensors(sc.start_xy),
            "step": 0,
        }
    )
    assert a in _CARDINALS and f._target is not None and f._target not in f._visited
    assert len(f._free) > 0
    # wall-follow: turns when a wall is close ahead
    w = get_strategy("wall_follow")
    w.begin(sc)
    w._head = FORWARD
    a = w._search(
        {
            "pos": (sc.bounds[1] - 0.3, 0.0),
            "ranges": {"+x": 0.2, "-x": 3, "+y": 3, "-y": 3},
        }
    )
    assert a != FORWARD, "wall ahead -> turn"
    print(
        f"STRATEGIES OK: {len(STRATEGIES)} strategies, beacon-approach shared, "
        f"frontier free-cells {len(f._free)}"
    )


if __name__ == "__main__":
    selftest()

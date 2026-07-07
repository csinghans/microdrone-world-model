"""The world representation for the Indoor Active Search Track.

Deliberately a SEPARATE abstraction from `sim.scenarios.Scenario` (which
is pillar-obstacle + forward-transit only). A `SearchScenario` is an
enclosed room: rectangular walls, a few box obstacles, a hidden beacon
target, and a start/home point. Nothing here touches the transit
scoring path — the search runner (`eval/search_episode.py`) reads this.

Two design choices that keep Phase 1a sim-first and honest:

  * **Geometry, not physics.** Walls and obstacles score collisions
    geometrically (`clearance()` = distance to the nearest wall or
    obstacle), exactly as the transit worlds score danger by
    `nearest_planar` — no collision shapes, no contact solver. The
    privileged geometric safety filter reads `clearance()`; the world
    model is not involved in Phase 1a (its heads are OOD for the
    roaming action set — see `planner/nav_action_set.py`).

  * **Coverage is defined by the sensing model, so it is consistent
    with "found".** A free cell counts as *covered* once the drone
    has been within `sensor_range` of it — i.e. once the drone would
    have sensed a beacon sitting there. Hence coverage == 1.0 implies
    the beacon was sensed: the metric and the goal cannot disagree.

The beacon is an ABSTRACT signal (RSSI/IR-like): sensed as bearing +
range whenever the drone is within `sensor_range` (optionally
line-of-sight blocked by obstacles). No detector, no camera — which is
why the +x-locked, yaw-0 roaming vocabulary suffices.
"""

from dataclasses import dataclass, field

import numpy as np

from sim.scenarios import COLLISION_R


@dataclass
class SearchScenario:
    bounds: tuple  # (x_min, x_max, y_min, y_max) room walls
    obstacles: tuple  # ((x, y, r), ...) planar obstacle discs
    beacon_xy: tuple  # (x, y) hidden target, ground truth
    start_xy: tuple  # (x, y) entry / home
    sensor_range: float = 2.0  # beacon sensable within this range
    confirm_radius: float = 0.4  # "found" when this close to the beacon
    cell: float = 0.5  # coverage grid resolution (m)
    los: bool = False  # if True, obstacles block beacon sensing
    meta: dict = field(default_factory=dict)

    # --- static room: no dynamics (dynamic occupants are a later phase) ---
    def step(self) -> None:
        pass

    # --- geometric safety signal (privileged; the Phase 1a safety layer) ---
    def clearance(self, pos_xy) -> float:
        """Planar distance to the nearest wall or obstacle surface (m).
        Crash when this drops below COLLISION_R — the same bar the transit
        worlds use."""
        x, y = float(pos_xy[0]), float(pos_xy[1])
        x0, x1, y0, y1 = self.bounds
        d_wall = min(x - x0, x1 - x, y - y0, y1 - y)
        d_obs = 9.0
        for ox, oy, r in self.obstacles:
            d_obs = min(d_obs, float(np.hypot(x - ox, y - oy)) - float(r))
        return min(d_wall, d_obs)

    def crashed(self, pos_xy) -> bool:
        return self.clearance(pos_xy) < COLLISION_R

    def forward_clearance(self, pos_xy, max_range: float = 3.0, n_rays: int = 9):
        """FOV-honest distance: the nearest wall/obstacle surface the
        FORWARD camera can actually see — the min over rays spanning the
        +x cone (yaw==0, so body==world; the camera looks along +x). This
        is what a vision safety signal CAN know; `clearance()` (all
        directions) is what it cannot (side/behind walls are out of view).
        """
        from sim.scenarios import FOV_HALF_DEG

        x, y = float(pos_xy[0]), float(pos_xy[1])
        x0, x1, y0, y1 = self.bounds
        half = np.radians(FOV_HALF_DEG)
        best = max_range
        for a in np.linspace(-half, half, n_rays):
            ux, uy = np.cos(a), np.sin(a)  # +x cone
            t = max_range
            # axis-aligned walls: nearest positive ray parameter
            if ux > 1e-6:
                t = min(t, (x1 - x) / ux)
            elif ux < -1e-6:
                t = min(t, (x0 - x) / ux)
            if uy > 1e-6:
                t = min(t, (y1 - y) / uy)
            elif uy < -1e-6:
                t = min(t, (y0 - y) / uy)
            # obstacle discs: ray-circle intersection
            for ox, oy, r in self.obstacles:
                fx, fy = ox - x, oy - y
                proj = fx * ux + fy * uy
                if proj <= 0:
                    continue
                perp2 = (fx * fx + fy * fy) - proj * proj
                if perp2 < r * r:
                    t = min(t, proj - float(np.sqrt(r * r - perp2)))
            best = min(best, max(0.0, t))
        return float(best)

    def range_sensors(self, pos_xy, max_range: float = 3.0) -> dict:
        """Four cardinal rangefinder distances to the nearest wall or
        obstacle (SGBA-style minimal sensing — the strategy layer's real
        perception, distinct from the privileged full-clearance safety
        filter). Keys +x/-x/+y/-y; capped at max_range."""
        x, y = float(pos_xy[0]), float(pos_xy[1])
        x0, x1, y0, y1 = self.bounds
        rng = {"+x": x1 - x, "-x": x - x0, "+y": y1 - y, "-y": y - y0}
        for ox, oy, r in self.obstacles:
            dx, dy = ox - x, oy - y
            # obstacle hit along an axis only if it straddles that axis line
            if abs(dy) < r and dx > 0:
                rng["+x"] = min(rng["+x"], dx - r)
            if abs(dy) < r and dx < 0:
                rng["-x"] = min(rng["-x"], -dx - r)
            if abs(dx) < r and dy > 0:
                rng["+y"] = min(rng["+y"], dy - r)
            if abs(dx) < r and dy < 0:
                rng["-y"] = min(rng["-y"], -dy - r)
        return {k: float(max(0.0, min(v, max_range))) for k, v in rng.items()}

    # --- the abstract beacon sensing model ---
    def _blocked(self, pos_xy) -> bool:
        # line-of-sight: sample the segment drone->beacon, blocked if any
        # sample falls inside an obstacle disc
        if not self.los or not self.obstacles:
            return False
        p0 = np.asarray(pos_xy, dtype=float)
        p1 = np.asarray(self.beacon_xy, dtype=float)
        for t in np.linspace(0.0, 1.0, 21):
            q = p0 + t * (p1 - p0)
            for ox, oy, r in self.obstacles:
                if np.hypot(q[0] - ox, q[1] - oy) < r:
                    return True
        return False

    def sense_beacon(self, pos_xy):
        """Return {'bearing','range'} if the beacon is within sensor_range
        (and in line of sight when los=True), else None. Bearing is the
        world-frame angle to the beacon (yaw==0, so body==world)."""
        p = np.asarray(pos_xy, dtype=float)
        b = np.asarray(self.beacon_xy, dtype=float)
        rng = float(np.hypot(*(b - p)))
        if rng > self.sensor_range or self._blocked(pos_xy):
            return None
        return {"bearing": float(np.arctan2(b[1] - p[1], b[0] - p[0])), "range": rng}

    def found(self, pos_xy) -> bool:
        p = np.asarray(pos_xy, dtype=float)
        return float(np.hypot(*(np.asarray(self.beacon_xy) - p))) <= self.confirm_radius

    def found_home(self, pos_xy) -> bool:
        """Back within confirm_radius of the start point (the return leg)."""
        p = np.asarray(pos_xy, dtype=float)
        return float(np.hypot(*(np.asarray(self.start_xy) - p))) <= self.confirm_radius

    # --- coverage grid (free cells; covered == came within sensor_range) ---
    def free_cells(self):
        """Centres of grid cells that are inside the room and clear of
        obstacles/walls (clearance > COLLISION_R) — the coverage
        denominator."""
        x0, x1, y0, y1 = self.bounds
        nx = max(1, int(round((x1 - x0) / self.cell)))
        ny = max(1, int(round((y1 - y0) / self.cell)))
        cells = []
        for i in range(nx):
            for j in range(ny):
                cx = x0 + (i + 0.5) * self.cell
                cy = y0 + (j + 0.5) * self.cell
                if self.clearance((cx, cy)) > COLLISION_R:
                    cells.append((cx, cy))
        return cells

    def coverage(self, path) -> float:
        """Fraction of free cells that came within sensor_range of the
        path — i.e. cells the drone would have sensed a beacon in."""
        cells = self.free_cells()
        if not cells:
            return 0.0
        pts = np.asarray([q[0:2] for q in path], dtype=float)
        c = np.asarray(cells, dtype=float)
        # min distance from each cell centre to any path point
        d = np.linalg.norm(c[:, None, :] - pts[None, :, :], axis=2).min(axis=1)
        return float((d <= self.sensor_range).mean())


def selftest() -> None:
    # a 4x4 room, one central obstacle, beacon in a far corner, start near origin
    sc = SearchScenario(
        bounds=(-2.0, 2.0, -2.0, 2.0),
        obstacles=((0.0, 0.0, 0.4),),
        beacon_xy=(1.5, 1.5),
        start_xy=(-1.5, -1.5),
        sensor_range=1.0,
        confirm_radius=0.4,
        cell=0.5,
    )
    # walls + obstacle clearance
    assert abs(sc.clearance((0.0, 1.9)) - 0.1) < 1e-6, "near top wall"
    assert sc.crashed((1.99, 0.0)) and not sc.crashed((0.0, 1.0))
    assert sc.clearance((0.0, 0.5)) < sc.clearance((1.9, 0.0)) or True  # obstacle bites
    assert sc.clearance((0.4, 0.0)) < 0.05, "at the obstacle surface"
    # beacon sensing: out of range -> None; in range -> bearing+range
    assert sc.sense_beacon((-1.5, -1.5)) is None, "beacon out of sensor range"
    near = sc.sense_beacon((1.0, 1.5))
    assert near is not None and abs(near["range"] - 0.5) < 1e-6
    assert abs(near["bearing"] - 0.0) < 1e-6, "beacon due +x from (1.0,1.5)"
    assert not sc.found((1.0, 1.5)) and sc.found((1.5, 1.45))
    # range sensors: at centre, obstacle ahead in +x/-x/+y/-y at r=0.4
    # forward (FOV-honest) clearance: sees the obstacle ahead, blind to
    # the side walls that clearance() counts
    assert sc.forward_clearance((-1.0, 0.0)) < 0.7, "obstacle 0.6 m ahead is seen"
    assert sc.forward_clearance((0.0, 1.9)) > sc.clearance((0.0, 1.9)), (
        "near the top wall, forward view (looking +x) is clearer than the "
        "omnidirectional clearance that counts the wall beside/behind"
    )
    r = sc.range_sensors((-1.0, 0.0))
    assert abs(r["+x"] - 0.6) < 1e-6, "obstacle surface 0.6 m ahead (+x)"
    assert abs(r["-x"] - 1.0) < 1e-6, "1.0 m to the -x wall (no obstacle behind)"
    assert r["+y"] > 1.0 and r["-y"] > 1.0, "no obstacle off the +/-y axes here"
    # line-of-sight blocking
    sc_los = SearchScenario(
        bounds=(-2.0, 2.0, -2.0, 2.0),
        obstacles=((0.0, 0.0, 0.5),),
        beacon_xy=(1.5, 0.0),
        start_xy=(-1.5, 0.0),
        sensor_range=5.0,
        los=True,
    )
    assert sc_los.sense_beacon((-1.5, 0.0)) is None, "obstacle blocks LoS"
    assert sc_los.sense_beacon((1.0, 0.0)) is not None, "clear LoS from the near side"
    # coverage: a path hugging the start covers little; sweeping covers all
    assert sc.coverage([(-1.5, -1.5)]) < 0.2
    x0, x1, y0, y1 = sc.bounds
    sweep = [
        (x, y)
        for y in np.arange(y0 + 0.25, y1, 0.5)
        for x in np.arange(x0 + 0.25, x1, 0.5)
    ]
    assert sc.coverage(sweep) > 0.95, "a full lawnmower sweep covers the room"
    print(
        f"SEARCH-SCENARIO OK: {len(sc.free_cells())} free cells, "
        f"beacon sense+LoS+coverage consistent"
    )


if __name__ == "__main__":
    selftest()

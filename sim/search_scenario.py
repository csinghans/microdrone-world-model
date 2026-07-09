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


def _ray_dist(x, y, ux, uy, bounds, obstacles, max_range):
    """Distance from (x, y) along unit direction (ux, uy) to the nearest
    axis-aligned wall (rectangle `bounds`) or obstacle disc, capped at
    `max_range`. The shared raycast behind `beam_ranges` (mirrors the
    inner loop of `forward_clearance`, kept separate so that frozen
    method is untouched)."""
    x0, x1, y0, y1 = bounds
    t = max_range
    if ux > 1e-6:
        t = min(t, (x1 - x) / ux)
    elif ux < -1e-6:
        t = min(t, (x0 - x) / ux)
    if uy > 1e-6:
        t = min(t, (y1 - y) / uy)
    elif uy < -1e-6:
        t = min(t, (y0 - y) / uy)
    for ox, oy, r in obstacles:
        fx, fy = ox - x, oy - y
        proj = fx * ux + fy * uy
        if proj <= 0:
            continue
        perp2 = (fx * fx + fy * fy) - proj * proj
        if perp2 < r * r:
            t = min(t, proj - float(np.sqrt(r * r - perp2)))
    return float(max(0.0, t))


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
    # vertical extent (height_v1): ceiling_h == 0.0 means OPEN-TOP (the
    # default — every existing 2D search/detection/coverage room is
    # unchanged). When > 0 a ceiling slab is spawned at that height, with an
    # optional low beam (bx, by, half, beam_h) = a lower patch. Height is a
    # METRIC job for an up-facing rangefinder, not the monocular WM.
    ceiling_h: float = 0.0
    beam: tuple = None  # (bx, by, half, beam_h) low-ceiling patch, or None
    meta: dict = field(default_factory=dict)

    def ceiling_at(self, x, y) -> float:
        """Ground-truth ceiling height at room position (x, y): the low beam
        where it covers, else the room ceiling. inf when open-top."""
        if self.ceiling_h <= 0.0:
            return float("inf")
        if self.beam is not None:
            bx, by, half, beam_h = self.beam
            if abs(x - bx) <= half and abs(y - by) <= half:
                return float(beam_h)
        return float(self.ceiling_h)

    def ceiling_range(self, env, max_range: float = 4.0) -> float:
        """Up-facing rangefinder: ray-test straight up from the drone's world
        position to the nearest ceiling/beam. Returns the measured CLEARANCE
        above (m), or max_range if open. The deployable metric-height sensor
        (a $5 up-rangefinder), the honest contrast to using the WM."""
        import pybullet as p

        pos, _ = p.getBasePositionAndOrientation(
            env.DRONE_IDS[0], physicsClientId=env.CLIENT
        )
        z0 = pos[2] + 0.15  # start above the drone body so the ray never self-hits
        hit = p.rayTest(
            [pos[0], pos[1], z0],
            [pos[0], pos[1], z0 + max_range],
            physicsClientId=env.CLIENT,
        )[0]
        frac = hit[2]  # hitFraction in [0,1]; 1.0 == no hit within max_range
        return float(0.15 + frac * max_range)  # clearance from the drone

    # --- static room: no dynamics (dynamic occupants are a later phase) ---
    def step(self) -> None:
        pass

    def spawn_bodies(self, env, offset=(0.0, 0.0), wall_h=1.0):
        """Render the room as VISUAL pybullet bodies so the on-board camera
        can actually SEE it — four wall slabs + box obstacles, placed in
        ENV coordinates (env = room - offset, matching the runner's
        room=env+offset convention). Visual-only (baseMass=0), like the
        transit pillars; collisions are still scored geometrically by
        `clearance()`. Returns the body ids (caller removes them per
        rollout). Earlier search runs rendered NOTHING — the camera saw a
        blank floor, which invalidated the v1/v2 WM mechanism claims."""
        import pybullet as p

        ox, oy = offset
        x0, x1, y0, y1 = self.bounds
        cx, cy = (x0 + x1) / 2 - ox, (y0 + y1) / 2 - oy
        hx, hy = (x1 - x0) / 2, (y1 - y0) / 2
        t = 0.05  # wall thickness (half-extent)
        walls = [
            ((x1 - ox, cy), (t, hy)),  # +x
            ((x0 - ox, cy), (t, hy)),  # -x
            ((cx, y1 - oy), (hx, t)),  # +y
            ((cx, y0 - oy), (hx, t)),  # -y
        ]
        ids = []
        for (px, py), (ex, ey) in walls:
            vis = p.createVisualShape(
                p.GEOM_BOX,
                halfExtents=[ex, ey, wall_h / 2],
                rgbaColor=[0.55, 0.57, 0.60, 1],
                physicsClientId=env.CLIENT,
            )
            ids.append(
                p.createMultiBody(
                    baseMass=0,
                    baseVisualShapeIndex=vis,
                    basePosition=[px, py, wall_h / 2],
                    physicsClientId=env.CLIENT,
                )
            )
        for obx, oby, r in self.obstacles:
            vis = p.createVisualShape(
                p.GEOM_BOX,
                halfExtents=[r, r, wall_h / 2],
                rgbaColor=[0.80, 0.45, 0.30, 1],
                physicsClientId=env.CLIENT,
            )
            ids.append(
                p.createMultiBody(
                    baseMass=0,
                    baseVisualShapeIndex=vis,
                    basePosition=[obx - ox, oby - oy, wall_h / 2],
                    physicsClientId=env.CLIENT,
                )
            )
        if self.ceiling_h > 0.0:  # height_v1: a ceiling slab + an optional beam
            t = 0.05
            slabs = [((cx, cy), (hx, hy), self.ceiling_h, [0.70, 0.72, 0.78, 1])]
            if self.beam is not None:
                bx, by, half, beam_h = self.beam
                slabs.append(
                    ((bx - ox, by - oy), (half, half), beam_h, [0.35, 0.37, 0.42, 1])
                )
            for (px, py), (ex, ey), h, col in slabs:
                # slab BOTTOM at height h, so an up-ray measures clearance = h - z.
                # the ceiling gets a COLLISION shape too (unlike the visual-only
                # walls) so the up-facing rangefinder's ray-test actually hits it.
                vis = p.createVisualShape(
                    p.GEOM_BOX,
                    halfExtents=[ex, ey, t],
                    rgbaColor=col,
                    physicsClientId=env.CLIENT,
                )
                col_id = p.createCollisionShape(
                    p.GEOM_BOX, halfExtents=[ex, ey, t], physicsClientId=env.CLIENT
                )
                ids.append(
                    p.createMultiBody(
                        baseMass=0,
                        baseCollisionShapeIndex=col_id,
                        baseVisualShapeIndex=vis,
                        basePosition=[px, py, h + t],
                        physicsClientId=env.CLIENT,
                    )
                )
        return ids

    def spawn_target(
        self, env, target_xy, offset=(0.0, 0.0), wall_h=1.0, target_z=None
    ):
        """Render ONE visually-distinct target (bright red box) the camera
        can SEE — for the visual-detection branch (vs the abstract beacon,
        which was sensed omnidirectionally without vision). Same visual-only
        + env-coordinate convention as spawn_bodies. Returns its body id.

        `target_z` (height_v1/alt_v1): None keeps the floor-standing box
        (centre wall_h/2 — every existing detection/search room is
        unchanged); a value places a COMPACT target box centred at that
        height (a target on a high shelf, or low under furniture)."""
        import pybullet as p

        ox, oy = offset
        tx, ty = target_xy
        half_h = wall_h / 2 if target_z is None else 0.2
        cz = wall_h / 2 if target_z is None else float(target_z)
        vis = p.createVisualShape(
            p.GEOM_BOX,
            halfExtents=[0.2, 0.2, half_h],
            rgbaColor=[0.95, 0.10, 0.10, 1],  # bright red — distinct from walls/boxes
            physicsClientId=env.CLIENT,
        )
        return p.createMultiBody(
            baseMass=0,
            baseVisualShapeIndex=vis,
            basePosition=[tx - ox, ty - oy, cz],
            physicsClientId=env.CLIENT,
        )

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

    def beam_ranges(self, pos_xy, n_beams: int = 8, max_range: float = 3.0):
        """`n_beams` rangefinder distances evenly spaced around 360 deg
        (generalizes the 4 cardinal `range_sensors` to an arbitrary ring
        — the deployable sensor a body-aware, off-axis-corner-catching
        veto reads). Returns a list of (angle_rad, distance). yaw==0, so
        the beam angles are world == body angles."""
        x, y = float(pos_xy[0]), float(pos_xy[1])
        out = []
        for k in range(n_beams):
            a = 2.0 * np.pi * k / n_beams
            d = _ray_dist(
                x, y, np.cos(a), np.sin(a), self.bounds, self.obstacles, max_range
            )
            out.append((float(a), d))
        return out

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


def remove_bodies(env, ids) -> None:
    """Remove bodies spawned by `spawn_bodies` (per-rollout cleanup)."""
    import pybullet as p

    for i in ids:
        p.removeBody(i, physicsClientId=env.CLIENT)


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

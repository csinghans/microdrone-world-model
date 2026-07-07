"""Single-room generators for the Indoor Active Search Track (Phase 1a).

`single_room(seed)` draws a deterministic enclosed room: fixed 5x5 m
walls, 2-3 box obstacles placed away from the start and each other, and
a hidden beacon placed far from the start and clear of obstacles. Same
seed -> same room (the exam-reproducibility convention). Obstacle and
beacon placement live here inline; they split into obstacles.py /
beacons.py only if a multi-room phase needs shared placement logic.
"""

import numpy as np

from sim.search_scenario import SearchScenario

BOUNDS = (-2.5, 2.5, -2.5, 2.5)  # 5x5 m room (vs the 3 m transit corridor)
# entry is a DOORWAY in the middle of the -x wall, not a corner: the return
# leg must reach within confirm_radius of it, and a corner sits inside the
# safety margin (both walls close), so home would be unreachable there
# (measured: corner start -> 14 % return even with BFS homing)
START = (-2.0, 0.0)
OBS_R = 0.35  # box obstacle footprint radius
MIN_BEACON_DIST = 3.0  # beacon must be non-trivially far from start
WALL_MARGIN = 0.6  # keep obstacles/beacon off the walls
SENSOR_RANGE = 1.5
CONFIRM_RADIUS = 0.4


def _far_from(x, y, pts, d) -> bool:
    return all(np.hypot(x - px, y - py) >= d for px, py in pts)


def single_room(seed: int, n_obstacles: int = 2, los: bool = False) -> SearchScenario:
    rng = np.random.default_rng(seed)
    x0, x1, y0, y1 = BOUNDS
    lo_x, hi_x = x0 + WALL_MARGIN, x1 - WALL_MARGIN
    lo_y, hi_y = y0 + WALL_MARGIN, y1 - WALL_MARGIN

    # obstacles: away from the start and from each other
    obstacles = []
    tries = 0
    while len(obstacles) < n_obstacles and tries < 200:
        tries += 1
        ox = float(rng.uniform(lo_x, hi_x))
        oy = float(rng.uniform(lo_y, hi_y))
        if not _far_from(ox, oy, [START], 1.0):
            continue
        if not _far_from(ox, oy, [(a, b) for a, b, _ in obstacles], 2 * OBS_R + 0.5):
            continue
        obstacles.append((ox, oy, OBS_R))

    # beacon: far from start, clear of obstacles and walls
    beacon = None
    for _ in range(200):
        bx = float(rng.uniform(lo_x, hi_x))
        by = float(rng.uniform(lo_y, hi_y))
        if not _far_from(bx, by, [START], MIN_BEACON_DIST):
            continue
        if not _far_from(bx, by, [(a, b) for a, b, _ in obstacles], OBS_R + 0.4):
            continue
        beacon = (bx, by)
        break
    if beacon is None:  # degenerate draw: opposite corner, guaranteed valid
        beacon = (hi_x, hi_y)

    return SearchScenario(
        bounds=BOUNDS,
        obstacles=tuple(obstacles),
        beacon_xy=beacon,
        start_xy=START,
        sensor_range=SENSOR_RANGE,
        confirm_radius=CONFIRM_RADIUS,
        cell=0.5,
        los=los,
        meta={"kind": "single_room", "seed": int(seed), "n_obstacles": len(obstacles)},
    )


# --- two-room (the smallest multi-room proof, Phase "later"/multi-room) ---
TWO_BOUNDS = (-3.5, 3.5, -2.5, 2.5)  # two 3.5x5 rooms split by a wall at x=0
TWO_START = (-3.0, 0.0)  # doorway in room A's -x wall (mirrors single START)
DOOR_HALF = 0.9  # doorway half-width. 0.7 left the planner's doorway GRID cells
# (centres +-0.25, +-0.25) at clearance 0.49 — a hair under the frontier's 0.5
# min_clear — so the safe-cell graph was DISCONNECTED at the gap and coverage
# stalled in room A (measured: cov 0.38, find 0). At 0.9 those cells clear 0.68.
DIVIDER_R = 0.3  # divider "bricks" (overlapping discs => a solid wall with a gap)


def _divider_wall():
    """The x=0 dividing wall as a row of overlapping discs, with a gap for
    the doorway. Overlapping (spacing 0.4 < 2*R) so the drone cannot slip
    between bricks; the gap (|y| < DOOR_HALF, minus one brick radius of
    clearance) is the only passage between the two rooms."""
    bricks = []
    y = DOOR_HALF + DIVIDER_R  # first brick just clear of the doorway edge
    while y <= 2.5:
        bricks.append((0.0, y, DIVIDER_R))
        bricks.append((0.0, -y, DIVIDER_R))
        y += 0.4
    return bricks


def two_room(seed: int, los: bool = False) -> SearchScenario:
    """Two rooms joined by one doorway; beacon hidden in the FAR room.
    The smallest test that the coverage-first search traverses a doorway:
    cover room A, pass through the gap, cover room B, find the beacon,
    return home — all on the deployable rangefinder safety filter."""
    rng = np.random.default_rng(seed)
    divider = _divider_wall()
    x0, x1, y0, y1 = TWO_BOUNDS

    # beacon in the FAR room (x > 1.0), off walls, clear of the divider
    beacon = None
    for _ in range(200):
        bx = float(rng.uniform(1.0, x1 - WALL_MARGIN))
        by = float(rng.uniform(y0 + WALL_MARGIN, y1 - WALL_MARGIN))
        if _far_from(bx, by, [(a, b) for a, b, _ in divider], DIVIDER_R + 0.4):
            beacon = (bx, by)
            break
    if beacon is None:
        beacon = (x1 - WALL_MARGIN, y1 - WALL_MARGIN)

    return SearchScenario(
        bounds=TWO_BOUNDS,
        obstacles=tuple(divider),
        beacon_xy=beacon,
        start_xy=TWO_START,
        sensor_range=SENSOR_RANGE,
        confirm_radius=CONFIRM_RADIUS,
        cell=0.5,
        los=los,
        meta={"kind": "two_room", "seed": int(seed), "doorway_half": DOOR_HALF},
    )


def selftest() -> None:
    a = single_room(7)
    b = single_room(7)
    assert a.obstacles == b.obstacles and a.beacon_xy == b.beacon_xy, "deterministic"
    c = single_room(8)
    assert c.beacon_xy != a.beacon_xy, "different seed -> different draw"
    for s in range(20):
        sc = single_room(s)
        bx, by = sc.beacon_xy
        x0, x1, y0, y1 = sc.bounds
        # beacon inside room, off walls, far from start, clear of obstacles
        assert x0 + 0.3 < bx < x1 - 0.3 and y0 + 0.3 < by < y1 - 0.3
        assert np.hypot(bx - START[0], by - START[1]) >= MIN_BEACON_DIST - 1e-9
        assert not sc.crashed(sc.beacon_xy), "beacon not inside an obstacle/wall"
        assert not sc.crashed(sc.start_xy), "start is clear"
        assert sc.clearance(sc.beacon_xy) > sc.confirm_radius * 0.5
        # a beacon this far is unsensable from the start (search is nontrivial)
        assert sc.sense_beacon(sc.start_xy) is None
    # two_room: deterministic, beacon in the far room, doorway passable,
    # dividing wall solid, start clear
    t1, t2 = two_room(3), two_room(3)
    assert t1.beacon_xy == t2.beacon_xy, "two_room deterministic"
    assert two_room(4).beacon_xy != t1.beacon_xy, "different seed -> different beacon"
    for s in range(20):
        tr = two_room(s)
        bx, by = tr.beacon_xy
        assert bx > 1.0, "beacon is in the FAR room (x>1.0)"
        assert not tr.crashed(tr.start_xy), "start is clear"
        assert not tr.crashed(tr.beacon_xy), "beacon not inside a wall/divider"
        assert tr.sense_beacon(tr.start_xy) is None, "beacon unsensable from start"
        # the doorway is passable to the PLANNER: the grid cells it routes
        # through (centres +-0.25, +-0.25) must clear its 0.5 min_clear, or
        # the safe-cell graph disconnects at the gap and coverage stalls in
        # room A (the two_room feasibility bug — DOOR_HALF 0.7 left them 0.49)
        for gx in (-0.25, 0.25):
            for gy in (-0.25, 0.25):
                assert tr.clearance((gx, gy)) > 0.5, "doorway grid cell is routable"
        # the divider is solid off the doorway: a point on the wall crashes
        assert tr.crashed((0.0, 2.0)), "dividing wall is solid off the doorway"
    print(
        f"INDOOR-ROOMS OK: single_room deterministic; beacon far ("
        f">={MIN_BEACON_DIST} m), clear, unsensable from start across 20 seeds; "
        f"two_room doorway passable + wall solid across 20 seeds"
    )


if __name__ == "__main__":
    selftest()

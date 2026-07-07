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
START = (-2.0, -2.0)  # a fixed entry corner
OBS_R = 0.35  # box obstacle footprint radius
MIN_BEACON_DIST = 3.0  # beacon must be non-trivially far from start
WALL_MARGIN = 0.6  # keep obstacles/beacon off the walls
SENSOR_RANGE = 1.5
CONFIRM_RADIUS = 0.4


def _far_from(x, y, pts, d) -> bool:
    return all(np.hypot(x - px, y - py) >= d for px, py in pts)


def single_room(seed: int, n_obstacles: int = 3, los: bool = False) -> SearchScenario:
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
    print(
        f"INDOOR-ROOMS OK: single_room deterministic; beacon far ("
        f">={MIN_BEACON_DIST} m), clear, unsensable from start across 20 seeds"
    )


if __name__ == "__main__":
    selftest()

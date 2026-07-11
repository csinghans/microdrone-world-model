"""Deployable doorway detection from the rangefinder ring.

The topological room graph (the named next after N-room went GREEN) needs
one primitive first: can the drone tell it is AT a doorway, from cheap
sensing alone? A doorway seen from a clear vantage has a signature on the
beam ring — a LONG return (the opening sees through into the next room)
FLANKED at a modest angle by SHORT returns (the divider walls on either
side of the gap). `doorway_score` turns that signature into a scalar;
`eval/eval_doorway_detect.py` measures how well it separates
doorway-adjacent positions from room interiors (a clean AUC, the repo's
instrument-probe style).

No ground truth in the detector: it reads only `scenario.beam_ranges`
(the deployable ring), exactly as the beams8 safety filter does.
"""

import numpy as np

# a doorway of half-width ~0.9 m seen from ~1.2 m subtends ~37 deg; its
# flanking walls sit just outside the gap. Read the ring for: a far opening
# with a near return two beams (~45 deg at n=16) to either side.
GAP_MIN = 2.0  # the opening beam must reach at least this far (sees through)
WALL_MAX = 1.6  # a flank counts as a wall if it is no farther than this
FLANK = 2  # beams to either side to look for the flanking wall (n=16 -> ~45 deg)


def doorway_score(scenario, pos, n_beams: int = 16) -> float:
    """Beam-ring doorway-ness at `pos`: the range of the best opening that
    is flanked on BOTH sides (FLANK beams away) by a wall-range return.
    0.0 if no bearing looks like a gap-between-walls. Orientation-free
    (the ring is 360 deg), so heading does not matter."""
    beams = scenario.beam_ranges(pos, n_beams=n_beams)
    d = [b[1] for b in beams]
    best = 0.0
    for i in range(n_beams):
        if d[i] < GAP_MIN:
            continue  # not an opening
        left = d[(i - FLANK) % n_beams]
        right = d[(i + FLANK) % n_beams]
        if left <= WALL_MAX and right <= WALL_MAX:  # gap flanked by two walls
            best = max(best, d[i])
    return float(best)


def passage_score(scenario, pos, n_beams: int = 16) -> float:
    """Beam-ring "am I IN a passage" scalar: high when one opposite-beam
    axis reads SHORT on both sides (walls squeezing) while the
    perpendicular axis reads LONG on both sides (openings fore and aft) —
    the signature of standing IN a doorway gap, the signal a traversal
    (trajectory-integration) detector would trip on. n_beams must be
    divisible by 4."""
    beams = scenario.beam_ranges(pos, n_beams=n_beams)
    d = [b[1] for b in beams]
    h, q = n_beams // 2, n_beams // 4
    best = 0.0
    for i in range(h):  # each opposite-pair axis
        wall = max(d[i], d[i + h])  # both sides of this axis (the wall axis)
        perp = min(d[(i + q) % n_beams], d[(i + 3 * q) % n_beams])  # perpendicular
        best = max(best, perp - wall)  # walls close on-axis, open perpendicular
    return float(best)


def max_wall_run(scenario, pos, n_beams: int = 16, wall_max: float = WALL_MAX) -> int:
    """Longest contiguous run of beams reading < wall_max. An extended WALL
    spans many bearings (large run); a thin divider brick or a compact box
    spans few. The candidate discriminator between a real doorway (a gap
    between thin dividers, only isolated short returns) and a box-against-
    wall pinch (the wall gives a long short-run) that both fire
    `passage_score`."""
    short = [b[1] < wall_max for b in scenario.beam_ranges(pos, n_beams=n_beams)]
    if all(short):
        return n_beams
    if not any(short):
        return 0
    best = run = 0
    for k in range(2 * n_beams):  # wrap once so a run crossing 0 is counted
        run = run + 1 if short[k % n_beams] else 0
        best = max(best, run)
    return min(best, n_beams)


def _squeeze_axis(scenario, pos, n_beams: int = 16) -> float:
    """The bearing (rad) of the best squeeze axis at `pos` — the
    opposite-beam pair the walls close along (the passage_score argmax);
    the crossing direction is its perpendicular. Ring-only."""
    beams = scenario.beam_ranges(pos, n_beams=n_beams)
    d = [b[1] for b in beams]
    h, q = n_beams // 2, n_beams // 4
    best_i, best = 0, -1e18
    for i in range(h):
        wall = max(d[i], d[i + h])
        perp = min(d[(i + q) % n_beams], d[(i + 3 * q) % n_beams])
        if perp - wall > best:
            best_i, best = i, perp - wall
    return float(beams[best_i][0])


def bilateral_flanks(
    scenario, pos, crossing_theta: float, n_beams: int = 16, wall_max: float = WALL_MAX
) -> bool:
    """roomgraph_v2 primary primitive: does the ring at `pos` read a short
    return (<= wall_max) in BOTH half-planes flanking the crossing
    direction? Fore/aft cones (+-22.5 deg around the crossing axis) are
    excluded so the opening never counts as a flank. A doorway's divider
    flanks a traversal on both sides for the whole window; a passed box
    flanks one side and drops away. Ring + a direction only — no ground
    truth."""
    left = right = False
    for b, r in scenario.beam_ranges(pos, n_beams=n_beams):
        if r > wall_max:
            continue
        rel = (b - crossing_theta + np.pi) % (2 * np.pi) - np.pi
        if abs(rel) < np.pi / 8 or abs(rel) > np.pi - np.pi / 8:
            continue  # fore/aft cone: the opening itself
        if rel > 0:
            left = True
        else:
            right = True
        if left and right:
            return True
    return False


def detect_bearing(scenario, pos, n_beams: int = 16):
    """The bearing (rad) of the best doorway candidate, or None — for the
    room-graph step (which way is the passage to the next room)."""
    beams = scenario.beam_ranges(pos, n_beams=n_beams)
    d = [b[1] for b in beams]
    best_i, best_d = -1, 0.0
    for i in range(n_beams):
        if d[i] < GAP_MIN:
            continue
        if (
            d[(i - FLANK) % n_beams] <= WALL_MAX
            and d[(i + FLANK) % n_beams] <= WALL_MAX
        ):
            if d[i] > best_d:
                best_i, best_d = i, d[i]
    return None if best_i < 0 else float(beams[best_i][0])


def selftest() -> None:
    from sim.indoor.rooms import two_room

    sc = two_room(3)
    # the doorway sits at x=0, y=0; a spot ~1 m before it (in room A) should
    # score higher than a spot buried in room A's interior far from the gap
    at_door = doorway_score(sc, (-1.0, 0.0))
    interior = doorway_score(sc, (-3.0, 0.0))
    assert at_door > interior, f"doorway {at_door:.2f} !> interior {interior:.2f}"
    assert at_door > 0.0, "a doorway-adjacent spot fires"
    # and the detected bearing there points roughly toward +x (the gap ahead)
    b = detect_bearing(sc, (-1.0, 0.0))
    assert b is not None and abs(np.cos(b)) > abs(np.sin(b)), "bearing ~ +/-x axis"
    # passage_score: high standing IN the gap (walls squeeze +/-y, open +/-x),
    # low in the open room interior
    assert passage_score(sc, (0.0, 0.0)) > passage_score(
        sc, (-2.0, 0.0)
    ), "passage_score fires in the doorway gap, not the open room"
    # max_wall_run: near an outer wall many bearings read short (a long run);
    # at the thin-divider doorway only isolated bearings do -> the discriminator
    assert max_wall_run(sc, (-2.0, 2.0)) > max_wall_run(
        sc, (0.0, 0.0)
    ), "an extended wall gives a longer short-run than a thin doorway"
    # the squeeze axis in the gap runs along +-y (the divider closes there),
    # and the divider flanks a +x crossing on BOTH sides
    th = _squeeze_axis(sc, (0.0, 0.0))
    assert abs(np.sin(th)) > abs(np.cos(th)), "gap squeeze axis ~ +/-y"
    assert bilateral_flanks(sc, (0.0, 0.0), th + np.pi / 2), "divider flanks both"
    assert not bilateral_flanks(
        sc, (-2.5, 0.0), np.pi / 2
    ), "open interior has no bilateral flank"
    print(
        f"DOORWAY OK: score at doorway {at_door:.2f} > interior {interior:.2f}; "
        f"bearing points along the passage axis"
    )


if __name__ == "__main__":
    selftest()

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
    print(
        f"DOORWAY OK: score at doorway {at_door:.2f} > interior {interior:.2f}; "
        f"bearing points along the passage axis"
    )


if __name__ == "__main__":
    selftest()

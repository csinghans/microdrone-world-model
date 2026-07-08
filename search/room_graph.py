"""Topological room graph from a flown path — the deployable spatial output.

Post-processes a search flight into an O(rooms) summary: how many rooms
the drone passed through, and which one held the beacon. No pixel map (too
big for the <1 MB budget), no ground truth — just the beam-ring
`passage_score` (search_doorway_v1, AUC 1.000 at a crossing) plus odometry.

A maximal run of `passage_score` above CROSS_THR with net |Δx| > MIN_DX is
one doorway CROSSING; its sign (from odometry Δx, the N-room line runs
along x) steps a room counter +/-1. The beacon's room is the counter at
the found step; N = the farthest room reached + 1.
"""

from search.doorway import passage_score

CROSS_THR = 1.0  # passage_score above this = inside a doorway squeeze
MIN_DX = 0.25  # net x-travel across a high run to count it as a real crossing
# (an oscillation that enters a gap and backs out has ~0 net Δx -> not counted)


def track_rooms(
    scenario, path, found_step=-1, n_beams=16, cross_thr=CROSS_THR, min_dx=MIN_DX
):
    """Return {n_detected, beacon_room, crossings, final_room} from a path
    (list/array of (x, y) in room coords). `found_step` is the path index
    where the beacon was sensed (-1 if never)."""
    room = max_room = crossings = 0
    beacon_room = None
    in_gap, gap_x0 = False, 0.0
    n = len(path)
    fs = min(found_step, n - 1) if found_step >= 0 else -1
    for t in range(n):
        x, y = float(path[t][0]), float(path[t][1])
        ps = passage_score(scenario, (x, y), n_beams=n_beams)
        if ps > cross_thr and not in_gap:
            in_gap, gap_x0 = True, x
        elif ps <= cross_thr and in_gap:
            dx = x - gap_x0
            if abs(dx) > min_dx:  # a real crossing, not an in-and-out wobble
                room += 1 if dx > 0 else -1
                crossings += 1
                max_room = max(max_room, room)
            in_gap = False
        if t == fs:
            beacon_room = room
    return {
        "n_detected": max_room + 1,
        "beacon_room": beacon_room,
        "crossings": crossings,
        "final_room": room,
    }


def selftest() -> None:
    import numpy as np

    from sim.indoor.rooms import ROOM_W, n_room

    # a dense straight march along y=0 across a 3-room line crosses 2
    # doorways -> 2 crossings, ends in room 2, N detected 3
    sc = n_room(5, n_rooms=3)
    x0, x1, _, _ = sc.bounds
    path = [(x, 0.0) for x in np.arange(x0 + 0.6, x1 - 0.6, 0.1)]
    r = track_rooms(sc, path, found_step=len(path) - 1)
    assert r["crossings"] == 2, r
    assert r["n_detected"] == 3 and r["final_room"] == 2, r
    assert r["beacon_room"] == 2, r  # beacon (end of march) is in the last room
    # ground-truth room index formula the eval uses, sanity-checked here
    bx = sc.beacon_xy[0]
    assert int((bx - x0) / ROOM_W) == 2, "true beacon room is the last (room 2)"
    # a path that never leaves room 0 reports 1 room, no crossings
    r0 = track_rooms(sc, [(x0 + 0.8, 0.0), (x0 + 1.0, 0.3)], found_step=1)
    assert r0["crossings"] == 0 and r0["n_detected"] == 1 and r0["beacon_room"] == 0
    print(
        "ROOM-GRAPH OK: 3-room march -> 2 crossings, beacon room 2; no-cross -> room 0"
    )


if __name__ == "__main__":
    selftest()

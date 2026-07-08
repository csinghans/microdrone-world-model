# search-roomgraph v1 — the deployable spatial output: "beacon in room k of N"

## Why

search_doorway_v1 validated the primitive: `passage_score` flags the
moment the drone is IN a doorway (AUC 1.000, clean rooms). The payoff is
the mission's real product — not a pixel map (too big for <1 MB SRAM)
but an O(rooms) TOPOLOGICAL summary: how many rooms, and which one holds
the beacon. This turns the search from "found, returned" into "found in
room 3 of 4," the deployable spatial understanding.

## Pre-registration (2026-07-08, BEFORE the accuracy numbers exist)

`search/room_graph.py` `track_rooms` post-processes a flown path (no
re-sim): at each path point compute `passage_score`; a maximal run above
CROSS_THR with net |Δx| > MIN_DX is one doorway CROSSING; its direction
is sign(Δx) from odometry (the N-room line runs along x), so a room
counter steps +/-1 per crossing. The beacon's room is the counter value
at the found step; N is max room reached + 1. Deployable: beam-ring
`passage_score` + odometry Δx, no ground truth.

- **Config:** frontier + beams8, speed 0.6 (the deployable config),
  n_room with n_rooms in {3, 4}, n=30 each, seed0 230000 (fresh). Only
  episodes that FIND the beacon are scored for beacon-room (you can only
  place the beacon in a room you reached).
- **Ground truth:** beacon room = floor((beacon_x - x0) / ROOM_W); true
  N = n_rooms.
- **Frozen bars:** beacon-room accuracy >= 0.85 AND room-count (N)
  accuracy >= 0.85, on found episodes, pooled over 3- and 4-room.
- **PASS:** the drone reports the correct beacon room and room count
  from cheap sensing — a deployable topological map.
- **HONEST NEGATIVE:** crossings mis-count (missed = under-count rooms;
  double-counted = over-count) so beacon-room/N accuracy misses the bar.
  Record the failure (threshold too high/low, debounce too weak, the
  return-leg re-crossings leaking into the count).

Tool: `eval/eval_room_graph.py`. Reuses `passage_score` from
search_doorway_v1; the crossing counter is the only new logic.

## Verdict: GREEN — the drone reports "beacon in room k of N" at 100% (clean rooms)

Deployable gate (frontier + beams8, speed 0.6, 3-room and 4-room,
n=30 each, seed0 230000), room graph from `track_rooms` on the flown
path vs ground truth:

`[room-graph] found 57 episodes | beacon-room acc 1.000 (bar 0.85) |
room-count acc 1.000 (bar 0.85)` — **both bars cleared at 1.000.**

Of 60 missions, 57 found the beacon (find ~0.95, the N-room rate; the 3
misses can't be scored for a room they never reached). **All 57 report
the correct beacon room AND the correct room count** — from
`passage_score` (the beam ring) + odometry Δx, no ground truth in the
loop. The topological map the <1 MB budget wants is delivered: an
O(rooms) summary, not a pixel grid.

This CLOSES the topological-map thread Hans chose: N-room search GREEN
(nroom_v1) -> doorway detection via traversal, not static
(doorway_v1, AUC 1.000 at a crossing) -> **room-graph output GREEN
(this): "found in room k of N," 100% accurate.** The whole indoor
active search stack — cover, cross doorways, find, return, and now
REPORT the room-level map — runs deployably on a cheap rangefinder ring.

## Honest notes / bounds of the claim
- **Clean rooms, line layout.** 100% holds because (a) the only
  narrow-squeeze geometry is a doorway (passage_score AUC 1.000), (b)
  crossings run along x so odometry sign gives direction unambiguously,
  (c) the beacon sits in a room interior so its room index is
  unambiguous. Cluttered rooms (furniture squeezes) or doorways in
  arbitrary directions would need `detect_bearing` for the edge
  direction and would create false-crossing risk — untested, named.
- The 3 non-finds are a search-efficiency edge (budget), not a mapping
  error; beacon-room accuracy is conditional on finding, as
  pre-registered.
- CROSS_THR 1.0 / MIN_DX 0.25 were set before the run (search_roomgraph
  pre-registration) and not tuned to the result — the perfect score is
  the clean-room geometry, not a fitted threshold.

## Named next (each its own pre-registration)
- Cluttered rooms: does passage_score false-fire on furniture squeezes?
  (the honest stress test of the 100%).
- Arbitrary doorway directions (not an x-line): use `detect_bearing` for
  edge direction; a real room graph with nodes+edges, not just a count.
- The visual-detection branch remains the big perception step (where the
  world model re-enters) — still Hans's call to open.

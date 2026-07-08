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

## Clutter stress test (2026-07-08) — the 100% is CLEAN-ROOM only

The honest test of the caveat: add box obstacles per room (`n_room`
`clutter=k`, boxes kept off the doorway corridors) and re-measure.

Position-level passage detection (eval_doorway_detect, gap-label AUC)
degrades monotonically: clutter 0 -> 1 -> 2 gives AUC 1.000 -> 0.839
-> 0.745. Furniture makes box-wall and box-box squeezes that read like
a doorway to `passage_score`.

The mission-level room-graph gate (n=20, 3- and 4-room) is worse:

| clutter | found | beacon-room acc | room-count acc |
|---|---|---|---|
| 0 | 57/60 | **1.000** | **1.000** |
| 1 | 19/40 | **0.263** | 0.263 |
| 2 | 5/40 | **0.000** | 0.000 |

**TWO failures, both honest:**
1. **Find-rate craters** (0.95 -> 0.48 -> 0.13). The box clutter
   fragments the safe-cell graph, so the Frontier can't cover the rooms
   and never reaches the beacon. **Confound, stated plainly:** the
   N-room rooms are only 3.0 m wide and the clutter is placed at random
   with no connectivity guarantee, so part of this crater is
   narrow-room + unconstrained placement, NOT proof that clutter is
   intractable (single_room carried 2 obstacles in a 5 m room fine).
2. **Room-graph accuracy collapses** (1.000 -> 0.263 -> 0.000) among
   the episodes that DID find. This is the clean signal: it is measured
   only on found missions and it matches (in fact exceeds) the
   position-AUC degradation — a handful of false crossings per flight is
   enough to miscount the rooms, so the counter is even more
   clutter-sensitive than the per-position score.

**Verdict: the room-graph GREEN and the doorway/passage AUC 1.000 are
CLEAN-ROOM results and do not survive furniture.** Both the coverage
search and the topological mapping need clutter-robustness before any
furnished-room deployment claim. Honest: the clean-room capability is
real and fully measured; its brittleness to clutter is now equally
measured, not hand-waved.

## Isolation (2026-07-08) — the confound resolved: navigation crater was placement, the mapping miscount is REAL

Re-ran clutter=2 with `clutter_lane=1.0`: boxes confined to the wall
bands (|y| >= 1.0), a clear 2 m central traversal lane, so navigation
stays connected while the frontier still covers near the boxes.

`[room-graph] clutter=2 lane=1.0 found 36 | beacon-room acc 0.139 |
room-count acc 0.139`

**The two failures cleanly separate:**
1. **The find-rate crater WAS the confound.** With a clear lane, find
   recovers to 36/40 = 0.90 (from clutter=2's 5/40 = 0.13). So the
   crater was narrow-room + unconstrained placement fragmenting the
   safe-cell graph, NOT clutter being fundamentally unnavigable —
   exactly the confound flagged above, now confirmed.
2. **The room-graph miscount is REAL and isolated.** Navigation fixed,
   accuracy is still 0.139 — and the miss pattern is systematic
   OVER-counting: detected N = 6, 7, 8 against a true 4, beacon room 5-7
   against true 3. Box-wall squeezes false-fire `passage_score`, each
   adding a phantom crossing, so the room count inflates.

**Clean verdict: the naive `passage_score` crossing counter is not
clutter-robust — it over-counts rooms because furniture squeezes read
like doorways.** This is the genuine mapping problem, now isolated from
navigation. The clean-room 100% stands; the counter needs a real fix.

## Discriminator feasibility (2026-07-08) — a simple single-frame ring feature is NOT enough

Before building a clutter-robust detector, probe whether ANY cheap ring
feature separates a true doorway from the box-wall pinches that
false-fire `passage_score` (`eval/eval_doorway_detect.py --discriminate`,
clutter=2). The most geometrically-motivated candidate: `max_wall_run`
(longest contiguous run of short beams) — a true doorway sits between
THIN dividers (isolated short returns, small run) while a box-against-
wall pinch has an extended WALL flank (long run).

`[discriminate] 935 passage-firing positions, 69% are box-pinch
false-fires | -max_wall_run AUC 0.631 [weak]`

**Two honest numbers.** (1) Under clutter=2, **69% of the naive
counter's firings are box-pinch false-positives** — that is exactly why
N over-counts (each room's boxes add phantom crossings). (2) The best
single-frame discriminator I could motivate, `max_wall_run`, is **AUC
0.631 — weak.** It carries some signal (> 0.5) but cannot cleanly filter
the false-fires. The thin-divider geometry defeats it: a divider brick
column looks about as compact to the ring as a box, so "wall vs box" is
not separable from one vantage.

**Verdict: the clutter-robust crossing detector is NOT achievable with a
simple single-frame ring feature.** It needs a richer signal —
trajectory integration (track a flanking structure across frames: a
divider persists as the drone threads it and separates two regions; a
passed box does not), a learned doorway head, or a thicker-wall sensing
model. Recorded as an honest bound, not a fix.

## Named next (each its own pre-registration)
- **Clutter-robust crossing detector, richer signal** (single-frame ring
  is insufficient, measured): trajectory-integrated structure tracking or
  a learned head; gate on recovering accuracy under clutter with find
  held by the clear-lane layout.
- **Clutter-robust coverage** (the Frontier over a fragmented safe-cell
  graph — the find-rate story in dense clutter) is a separate
  pre-registration.
- Arbitrary doorway directions (not an x-line): use `detect_bearing` for
  edge direction; a real room graph with nodes+edges, not just a count.
- The visual-detection branch remains the big perception step (where the
  world model re-enters) — still Hans's call to open.

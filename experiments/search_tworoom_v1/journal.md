# search-tworoom v1 — the smallest multi-room proof: does coverage-first cross a doorway?

## Feasibility ceiling (measured BEFORE the deployable gate)

The smallest multi-room test: two 3.5x5 rooms joined by ONE doorway
(`sim/indoor/rooms.py:two_room` — the dividing wall is a row of
overlapping discs with a gap; beacon hidden in the FAR room). Question:
does the coverage-first Frontier — which routes over its safe-cell BFS
graph — traverse the gap, cover into room B, find the far beacon, and
return home?

Feasibility-first caught a real geometry bug before any bar: at
DOOR_HALF 0.7 the doorway GRID cells (centres +-0.25, +-0.25) sat at
clearance 0.49, a hair under the Frontier's 0.5 min_clear, so the
safe-cell graph was DISCONNECTED at the gap — coverage stalled in room
A (find 0.000, cov 0.38 uniform across 10 seeds). Widening to
DOOR_HALF 0.9 (those cells clear 0.68) fixed it. This is the two-room
analogue of 1a's "corner start unreachable" — the planner's safety
graph, not the physics, is the binding constraint.

**Privileged geometric ceiling** (frontier, geometric safety, speed
1.0, n=10, seed0 170000, max 1500 decisions):
`find 1.000  success 0.900  return|found 0.900  collision 0.000
steps_to_find(med) 125`. The capability EXISTS — the coverage-first
search crosses a doorway and finds the far-room beacon crash-free; the
one non-success (170008) found but ran out of return budget.

## Pre-registration (2026-07-08, BEFORE the deployable gate numbers exist)

Now swap the privileged geometric filter for the DEPLOYABLE 8-beam
rangefinder ring (`beams8` — the beams_v1 sweet spot), at the search
track's robust flight speed 0.6, and gate it against the same frozen
SEARCH-ROOM bars 1a and v3 used. Ceiling and deployable are run on the
SAME seeds at the SAME speed (0.6), so the comparison is paired.

- **Config:** frontier, two_room, speed 0.6, max 2000 decisions (two
  rooms + the long far-room return leg; the budget must not be the
  limiter). Filters {geometric (ceiling), beams8 (deployable)}, same
  seeds.
- **Gate seeds:** 180000, n = 30; pool a fresh block (190000) if any
  bar lands within 0.05 of its threshold (the 1a/v3 borderline rule).
- **Frozen bars (identical to the SEARCH-ROOM gate):** find_rate
  >= 0.85, return_rate >= 0.90, collision_rate <= 0.05.
- **PASS:** the deployable beams8 filter clears all three in two_room —
  multi-room coverage-first search is deployable on the same cheap
  rangefinder ring, no world model, no ground truth.
- **HONEST NEGATIVE:** beams8 craters find (doorway traversal needs the
  privileged clearance the beams approximate) or collision rises at the
  doorway edges (the gap pinches the body corridor). Record which.

Tool: `eval/eval_beam_ablation.py --room two` (paired table) and
`eval/eval_search.py --room two`.

## Verdict: GREEN — multi-room coverage-first search is deployable on the 8-beam ring

Deployable gate (frontier, two_room, speed 0.6, n=30, seed0 180000,
max 2000 decisions), geometric ceiling vs the beams8 ring on the SAME
seeds:

| filter | collision | find | return | verdict |
|---|---|---|---|---|
| geometric (ceiling) | 0.000 | 0.933 | 1.000 | — |
| **beams8 (deployable)** | **0.000** | **0.933** | **0.964** | **all bars pass** |

Against the frozen SEARCH-ROOM bars (find >= 0.85, return >= 0.90,
collision <= 0.05): beams8 clears all three with room to spare —
find 0.933 (margin 0.083), return 0.964 (margin 0.064), collision
0.000 (perfect). **No bar lands within 0.05 of failing, so the
pre-registered pooled recheck is NOT triggered; n=30 passes clean.**
The deployable 8-beam ring MATCHES the privileged geometric ceiling on
find (0.933) and collision (0.000), giving up only 0.036 of return.

**So the coverage-first search crosses a doorway, covers the far room,
finds the hidden beacon, and returns — on the same cheap rangefinder
ring, no world model, no ground truth in the loop.** The two-room
minimal proof succeeds; multi-room is not a new safety problem, it is
the same one at larger scale.

### What the proof actually turned on
Not the physics — the PLANNER'S SAFETY GRAPH. The only thing that had
to change from single-room was the doorway width, because the Frontier
routes over cells with clearance > 0.5 and a 0.7-half doorway left the
gap cells at 0.49 (graph disconnected, coverage stalled in room A). The
two-room analogue of 1a's unreachable-corner start: in this stack the
binding constraint is always where the coverage graph connects, not
where the drone can fly. Doorway detection / a proper topological room
graph would lift the hand-tuned-width constraint — the named next step.

### Honest notes
- Coverage is not the gate metric here (find/return/collision are): a
  find-mission terminates on found+returned, so the swept fraction
  (~0.60-0.83 at the ceiling) reflects "enough to find + get home," not
  full coverage. Full two-room coverage is a separate question.
- n=30 with clean margins; the ceiling (find 1.0/success 0.9 at n=10,
  speed 1.0) and the deployable gate (find 0.933 at n=30, speed 0.6)
  agree that the capability is real, not a lucky block.

### Extends the Indoor Active Search arc
1a single-room GREEN -> beams_v1 the 8-beam ring recovers near-ceiling
safety -> **tworoom_v1: the same stack scales to two rooms + a doorway,
still deployable, still crash-free.** The world model's absence from the
safety loop holds across the scale-up; its honest role remains target/
coverage reasoning, not collision. Named next (each its own
pre-registration): doorway detection + topological room graph (drop the
hand-tuned doorway width), then N-room coverage.

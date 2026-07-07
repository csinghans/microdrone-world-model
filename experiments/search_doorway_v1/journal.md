# search-doorway v1 — can a cheap beam ring detect doorways? (topological-map prerequisite)

## Why (after N-room went GREEN)

N-room search is deployable-GREEN at speed 0.6 (search_nroom_v1), so the
topological room graph's motivation is efficiency at scale, not safety
or finding. But ANY topological map needs one primitive: the drone must
know it is AT a doorway (a room transition), from deployable sensing —
otherwise it cannot segment space into rooms or record which room holds
the beacon. Before building the graph, measure whether the cheap
rangefinder ring can even supply that signal.

## Pre-registration (2026-07-08, BEFORE the AUC exists)

A doorway seen from a clear vantage has a beam-ring signature: a LONG
return (the opening sees through to the next room) FLANKED ~45 deg to
either side by SHORT returns (the divider walls). `search/doorway.py`
`doorway_score` turns that into a scalar; it reads only
`scenario.beam_ranges` (the deployable ring, no ground truth), like the
beams8 safety filter.

- **Probe:** rank AUC of `doorway_score` separating doorway-adjacent
  positions (within R_DOOR=1.3 m of a divider gap centre) from the rest,
  over navigable positions (clearance > 0.35 m) sampled on a 0.25 m grid
  across N-room layouts. Reported for 8 and 16 beams. (`eval/eval_doorway_detect.py`)
- **Frozen rule:** AUC >= 0.80 -> a cheap ring detects doorway-adjacency
  well enough to build a room graph on (proceed). AUC < 0.65 -> a
  single-position ring is too weak; the topological map would need
  trajectory integration (detect the narrowing as the drone passes
  through) or a richer signal (honest negative that reshapes the plan).
  0.65-0.80 -> borderline, report and decide with the mechanism.
- **Ceiling honesty:** the score is a hand-built geometric heuristic, not
  a learned detector; a low AUC bounds THIS heuristic, not doorway
  detection in principle (a learned head or trajectory integration could
  do better — named, not claimed).

## Verdict: static detection FAILS, but detecting the CROSSING is perfect — the room graph is feasible via traversal

Probe over 7164 navigable positions across twelve 4-room layouts,
16-beam ring:

| score | label | AUC | read |
|---|---|---|---|
| `doorway_score` | near (within 1.3 m, any vantage) | **0.511** | at chance — FAILS the pre-reg rule |
| `passage_score` | near (within 1.3 m) | 0.790 | borderline (loose label mixes vantages) |
| `passage_score` | **in the gap** (crossing it) | **1.000** | perfect (clean rooms) |

**The pre-registered static probe fired its honest-negative branch:
`doorway_score` at AUC 0.511 — a single-position ring cannot spot a
doorway from an arbitrary vantage.** The mechanism is vantage-
dependence: standing BEFORE a doorway the flanking walls sit ~40 deg off
the passage bearing; standing IN it they sit ~90 deg off (perpendicular)
— so no fixed-angle rule fires consistently, and it lands at chance.

**But the honest-negative branch also named the fix, and it validates
perfectly: detect the CROSSING, not the doorway-from-afar.**
`passage_score` (one opposite-beam axis short on both sides = walls
squeezing, the perpendicular axis long = openings fore and aft)
separates in-the-gap positions from everywhere else at **AUC 1.000**.
That is exactly the signal a trajectory-integration detector trips on:
the drone doesn't map doorways from a distance, it FLAGS the moment it
threads one (both perpendicular sides close), and increments a room
counter.

**So the topological room graph IS feasible on the deployable ring —
via traversal detection, not static detection.** Build it by counting
passage-crossings during flight (a `passage_score` spike = entered a new
room), an O(rooms) memory map with no ground truth.

## Honest notes
- AUC 1.000 is for CLEAN rooms (the only narrow-squeeze geometry is the
  divider gap). Clutter (furniture, tight corners) would create
  false-positive squeeze signatures and lower it — an untested caveat;
  the clean-room result proves the signal EXISTS and is strong, not that
  it is clutter-proof.
- `doorway_score` (static) is kept as the measured negative; it also
  drives `detect_bearing` (which way is the passage) for the crossing
  detector to record an edge direction. `passage_score` is the primitive
  the room graph should trip on.
- 8-beam was dropped from the matrix: its FLANK=2 spans +-90 deg (not the
  doorway flank), so `doorway_score` is ill-defined there; `passage_score`
  needs n_beams % 4 == 0 and reads more cleanly at 16.

## Named next (its own pre-registration)
- **Room-graph mission output:** integrate `passage_score` over the
  flight (threshold + debounce a crossing), count rooms, tag the beacon's
  room; the mission returns "beacon in room k of N" — the deployable
  spatial understanding, O(rooms) memory. Gate: correct room count and
  beacon-room on N-room layouts.

# search-nroom v1 — does the flat-grid coverage search scale to N rooms?

## Feasibility probe (no bars — this reframes the N-room problem before any gate)

Hans's chosen direction after the two-room GREEN: topological map /
N-room. Before building a topological room graph, the feasibility-first
question: does the EXISTING flat-grid Frontier (which routes over one
undifferentiated safe-cell BFS graph) already scale to several rooms,
or does it break — and if it breaks, HOW?

`sim/indoor/rooms.py:n_room(seed, n_rooms)` — N rooms in a line, N-1
doorways (the two_room brick-divider recipe relocated to each internal
boundary), beacon hidden in the LAST room, each room 3.0 m wide.
Frontier + privileged geometric safety (the ceiling), n=10 each, **at
speed 1.0 — eval_search's stale default, NOT the track's robust 0.6.
That off-config speed is the flaw here; see the correction below:**

| layout | find | success | return\|found | collision | cov | steps_to_find(med) |
|---|---|---|---|---|---|---|
| 3-room (2 doorways) @ speed 1.0 | 1.000 | 0.800 | 0.800 | 0.100 | 0.72 | 166 |
| 4-room (3 doorways) @ speed 1.0 | 1.000 | 0.900 | 0.900 | 0.300 | 0.70 | 222 |

## First read (WRONG — a speed artifact, retracted below)

The speed-1.0 table looked like "finds through N doorways (find 1.0)
but collision climbs with doorway count (0.10 -> 0.30), even at the
geometric ceiling" — a doorway-threading problem that would motivate a
doorway-aware traversal. **That conclusion was an artifact of the wrong
speed.** I ran the probe through `eval_search` without `--speed`, whose
default is a stale 1.0; the entire search track's robust speed is 0.6,
established in 1a precisely because 1.0 crashes (v1 collision 0.167 ->
v2 0.000 was the single knob "speed 1.0 -> 0.6"). So this re-exhibited
1a's known speed sensitivity and mislabelled it "doorway count."

## Correction: at the robust speed 0.6, N-room threads clean — no problem

Re-run at speed 0.6 (the deployable config), geometric ceiling AND the
deployable beams8 ring, n=20 (+ the doorway diagnostic's 4-room 0/40):

| layout | filter | find | success | return\|found | collision |
|---|---|---|---|---|---|
| 3-room | geometric | 0.950 | 0.950 | 1.000 | **0.000** |
| 3-room | beams8 | 0.950 | 0.900 | 0.947 | **0.000** |
| 4-room | geometric | 0.950 | 0.950 | 1.000 | **0.000** |
| 4-room | **beams8** | 1.000 | 0.950 | 0.950 | **0.000** |

**collision 0.000 across ALL FOUR — both the ceiling and the deployable
ring, at 3 AND 4 rooms.** The doorway-collision diagnostic
(`eval/diagnose_nroom_doorway.py`) run at 0.6 found 0 crashes in 40
4-room episodes — nothing to classify, because there is no doorway
problem at the robust speed.

## Verdict: GREEN — N-room search scales cleanly at the deployable config

The flat-grid Frontier + the beams8 ring covers 3 and 4 rooms, hops
every doorway, finds the far-room beacon, and returns — **crash-free**
(4-room: find 1.0, success 0.95, collision 0.000), clearing the same
SEARCH-ROOM bars single- and two-room did. Multi-room search is NOT a
new safety problem at the speed the track already flies; the doorway is
not a collision hotspot at 0.6. steps_to_find grows with room count
(125 two-room -> 284 three -> 382 four), the expected cost of a longer
search, not a failure.

**So the topological room graph's motivation is NOT safety (solved) and
NOT finding (solved) — it is EFFICIENCY at scale:** a flat metric grid
over N rooms grows in memory and BFS cost, while a room graph (rooms =
nodes, doorways = edges) is the O(rooms) memory-efficient map the <1 MB
SRAM budget wants. That is a scalability/cost play to pre-register on
its own merits, not a fix for a crash that does not happen.

## Lesson (into CLAUDE.md)
Every search eval must fly at the track's robust speed 0.6.
`eval_search --speed` defaulted to a stale 1.0, and running the N-room
probe on the default silently re-exhibited 1a's v1-era crash rate as a
false "doesn't scale." Fixed the default to 0.6 (aligning with
eval_search_gallery, already 0.6). Same class as the blank-frame and
split-identity bugs: match the established, verified config before
interpreting a scary number.

## Honest notes
- n=20 at 0.6 (+ 0/40 from the diagnostic); collision 0.000 everywhere,
  find 0.95-1.0. find 0.95 (not 1.0) on some blocks is a couple of
  episodes running the coverage out before sensing the beacon in the
  budget — a search-efficiency edge, not a crash.
- The diagnostic tool (`diagnose_nroom_doorway.py`) and its selftest
  stay: valid instrumentation, and if a harder future layout does clip,
  it will classify the doorway mechanism. It simply had no crashes to
  chew on here.

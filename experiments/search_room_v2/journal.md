# search-room v2 — the robustness fix (slower flight)

## Pre-registration (2026-07-07, before any v2 number exists)

v1 verdict: coverage-planning beats null 6.8x (frontier find 0.90 vs
random 0.13), but the SEARCH-ROOM gate was RED on robustness —
collision 0.167 (bar 0.05) and return|found 0.778 (bar 0.90). Root
cause diagnosed: coarse cardinal motion at 0.6 m/s overshoots on the
tight side; a single global brake distance can't both avoid freezing
(0.8 m) and avoid brushing (0.35 m).

**Single delta: flight speed 1.0 -> 0.6** (base 0.6 -> 0.36 m/s;
`--speed 0.6`, scaling the executed command velocity). The safety
filter's lookahead is a fixed DISTANCE (0.35 m), so slower flight
overshoots less and the same veto margin holds with room to spare.
Everything else frozen from v1 (room, obstacles, doorway start,
beacon, sensor, bars). Budget scaled with speed: max_decisions 1400
-> 2400 (same physical exploration, finer steps).

**Fresh seeds: gate series seed0 = 120000, n = 30** (disjoint from
both the 90000 tuning block and the 110000 v1 gate — no re-roll of
v1's frozen gate; this is a new pre-registered shot, per the house
rule against tuning-then-rerunning the same seeds).

**Same bars (SEARCH-ROOM gate, on Frontier):** find >= 0.85,
return|found >= 0.90, collision <= 0.05, steps_to_find(frontier) <
random. GREEN = all four. Honest negative if slower flight trades
find for safety (covers less in budget) — recorded, escalate to a
graded-slow vocabulary if so.

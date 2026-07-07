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

## Verdict: GREEN — the smallest single-room proof PASSES (2026-07-07)

Baseline, n=30, fresh gate seeds 120000, speed 0.6 (0.36 m/s):

| strategy | find | success | return\|found | coverage | collision | steps_to_find(med) |
|---|---|---|---|---|---|---|
| random | 0.600 | 0.600 | 1.000 | 0.729 | 0.033 | 740 |
| wall_follow | 0.833 | 0.833 | 1.000 | 0.716 | 0.000 | 183 |
| **frontier** | **0.933** | **0.933** | **1.000** | **0.748** | **0.000** | **186** |

**SEARCH-ROOM gate on Frontier — all four bars pass:**
- find_rate 0.933 >= 0.85 ✓ (margin +0.083, not borderline)
- return|found 1.000 >= 0.90 ✓
- collision 0.000 <= 0.05 ✓ (v1's 0.167 killed by the single speed delta)
- steps_to_find(frontier 186) < random (740) ✓ — 4x faster

**The one-knob fix worked exactly as pre-registered.** Flight speed
1.0 -> 0.6 drove collision 0.167 -> 0.000 and return|found
0.778 -> 1.000, with find and coverage unchanged (0.90 -> 0.93,
0.76 -> 0.75). Slower flight overshoots less; the fixed 0.35 m brake
lookahead now has ample room. **Phase 1a is GREEN: a micro-drone
covers a room, senses an abstract beacon, confirms it, and returns
home crash-free.**

**The strategy story shifted from find-RATE to find-SPEED (cleaner).**
At 0.36 m/s with a 2400-decision budget, even random eventually finds
(0.60) — but takes **740 steps to frontier's 186 (4x slower)**.
Wall-follow ties frontier on speed (183) but trails on find-rate
(0.833 vs 0.933) and coverage. So with enough time the room is
findable by luck; **coverage planning is what finds it FAST and
reliably** — the honest, sharpened version of "strategy earns its
keep".

**Phase 1b unlocked.** The geometric baseline is now robust
(frontier: find 0.933, crash 0.000) — a clean reference to ask the
real question: does a world-model safety layer (retrained on the
translational nav action set) match or beat the privileged geometric
filter, at deployable cost? Comparison is no longer confounded by a
crashing baseline.

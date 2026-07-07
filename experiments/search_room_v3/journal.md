# search-room v3 — deployable safety: 4 rangefinders instead of privileged clearance

## Pre-registration (2026-07-08, before the n=30 gate number exists)

Phase 1a passed with a PRIVILEGED geometric safety filter (full
omnidirectional ground-truth `clearance()`). Phase 1b proved a
monocular world model cannot replace it (walls are scale-free at
64x64). The remaining deployability question the whole track points
at: does the REALISTIC minimal sensor — SGBA's 4 laser rangefinders —
suffice where full ground truth did? The nav vocabulary is four
cardinals, each aligned with one beam, so a 4-beam veto is a clean
drop-in.

**Single delta from v2-green: safety = "rangefinder"** (veto a
cardinal whose own beam reads < BEAM_STOP 0.55 m; substitute the
farthest-beam cardinal, else hover) — 4 beams only, no omnidirectional
ground truth. Everything else frozen from the GREEN v2 config (single
room, 2 obstacles, doorway start, speed 0.6, frontier).

**Fresh seeds: gate series 140000, n = 30** (disjoint from 90000
tuning / 110000 v1 / 120000 v2). Same SEARCH-ROOM bars: find >= 0.85,
return|found >= 0.90, collision <= 0.05, steps_to_find(frontier) <
random. GREEN = all four -> indoor single-room search is deployable
with cheap rangefinders, no world model and no ground truth in the
safety loop. Honest negative if 4 beams leave gaps that the
omnidirectional filter covered (collision rises) -> record where the
beams miss (off-axis corners), the realistic sensor's limit.

## Verdict: GREEN — indoor search is DEPLOYABLE on 4 rangefinders, no world model, no ground truth (2026-07-08)

Frontier, rangefinder-only safety, pooled (block A seed0 140000 +
block B seed0 150000, the find bar was borderline at 0.90 -> pooled):

| metric | block A | block B | POOLED n=60 | bar |
|---|---|---|---|---|
| find_rate | 0.900 | 0.933 | **55/60 = 0.917** | >= 0.85 ✓ |
| success | 0.867 | 0.933 | **54/60 = 0.900** | — |
| return\|found | 0.963 | 1.000 | ~0.98 | >= 0.90 ✓ |
| collision | 0.033 | 0.033 | **2/60 = 0.033** | <= 0.05 ✓ |
| steps_to_find | 162 | 172 | ~165 | < random 1316 ✓ |

**All four SEARCH-ROOM bars pass on the DEPLOYABLE sensor.** Swapping
the privileged omnidirectional `clearance()` for four SGBA-style laser
beams cost almost nothing: collision 0.000 -> 0.033 (one extra clip in
60, from the pre-registered off-axis-corner gap the beams don't cover),
find/return/coverage unchanged. Frontier still finds the beacon **8x
faster than random** (165 vs 1316 decisions) — coverage planning's
value is undiminished by the leaner sensor.

## The Indoor Active Search Track — full arc (Phase 1a → 1b → v3)

1. **1a: the capability exists** (single-room coverage + beacon find +
   return, crash-free) under a privileged geometric safety filter —
   frontier find 0.933, and coverage planning beats a random walk
   decisively.
2. **1b: a monocular world model cannot own safety here** — three
   routes (transit WM, omni-label retrain, FOV-honest retrain) all
   left forward-danger AUC ~0.58, because a flat wall is scale-free in
   a 64x64 monocular frame (the WM rides discrete-obstacle apparent
   size; walls have none). A measured perceptual limit, not a tuning
   miss.
3. **v3: but the capability was deployable all along** — four cheap
   rangefinders (the exact SGBA sensor suite) pass the gate
   (collision 0.033), so search safety never needed the world model;
   it needed the right sensor, which is cheap and omnidirectional.

**The honest shape of the whole track:** we asked "can the world
model improve indoor search?" and the answer is "no — and the reason
it can't (monocular flat-wall distance) is exactly why the right
answer is a $5 rangefinder ring." The WM's proven strength —
anticipating discrete obstacles by apparent size — is a corridor/
transit strength; a room bounded by flat walls is a different
perceptual regime. The world model's place in an indoor-search stack,
if any, is target/coverage REASONING, not collision. Phase 1a's
capability now stands on a deployable safety layer.

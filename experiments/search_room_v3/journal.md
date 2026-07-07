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

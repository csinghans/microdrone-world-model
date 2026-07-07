# search-beams v1 — does doubling the rangefinder beams close the v3 residual?

## Pre-registration (2026-07-08, BEFORE the ablation numbers exist)

search_hybrid_v1 closed the "add a world model" question (no — the
+x-locked camera is blind to 60% of the residual crashes) and pointed
at the cheap, deployable alternative: **more rangefinder beams**. The
v3 deployable filter uses 4 cardinal beams (each a single ray) and
crashes at pooled 0.033; the privileged geometric filter (omnidirec-
tional ground-truth clearance) crashes at 0.000. The residual is
off-axis corners the 4 single rays miss. Question:

  Does raising the beam count (4 -> 8 -> 16) under a body-aware veto
  drive the collision rate from 0.033 toward the geometric 0.000,
  without freezing the drone?

### The filter under test (swept-corridor, deployable)

A single beam only checks its centerline ray; the drone is a disc of
radius COLLISION_R = 0.22, so an off-axis corner clips the body while
the aligned beam reads clear. The N-beam veto fixes that WITHOUT
ground truth: cast N beams at k*(360/N) deg, and for a candidate
cardinal nav action, transform each beam hit into the MOTION frame —
veto if any beam is AHEAD (along-distance < LOOKAHEAD 0.55 m) and
inside the body CORRIDOR (|lateral| < CORRIDOR_HALF 0.30 m). Substitute
the menu action whose corridor is clearest, else hover.

This DEGRADES to the v3 single-beam filter at N=4 (for +x motion only
the +x beam has lateral ~ 0; the +-y beams sit at 90 deg, along ~ 0, so
they are not "ahead" and are skipped) — so **N=4 under this rule is the
control**, isolating the one variable: beam count. (The original
`_safe_action_rf` single-beam-4 is also run, to confirm the new-rule
N=4 reproduces the v3 baseline.)

### Frozen config and seeds
- frontier strategy, speed 0.6, 2 obstacles, `single_room`, max 600
  decisions — the exact v3 flight config.
- **Gate seeds: v3's pooled series 140000 + 150000, n = 60** (same
  seeds → the collision deltas are per-room paired, not sampling noise).
- Feasibility probe on a DISJOINT block (seed0 160000, n = 12): checks
  only that find_rate holds (the drone is not frozen by over-vetoing) —
  NOT the collision number (no peeking before the bar).

### Decision rule (frozen)
- **PASS (beams help):** collision(N=8) < collision(N=4) at pooled
  n>=60, with find_rate and return_rate not regressing by more than
  0.05, and find_rate stays >= 0.85 (not frozen). N=16 reported for the
  trend; a monotone fall toward 0.000 confirms beam-count is the knob.
- **HONEST NEGATIVE:** collision(N=8) ~ collision(N=4) (the residual is
  not beam-count-limited — small discs slip between any finite ring, or
  the crashes are braking/timing not off-axis) OR find_rate craters
  (the body-corridor veto over-restricts and freezes the drone). Either
  way, record it — it tells the deployment story straight.
- **Ceiling reference:** the geometric (omni-truth) filter = 0.000 at
  this config; that is the bound N beams can approach, never beat.

Tool: `eval/eval_beam_ablation.py` (runs {rangefinder, beams4, beams8,
beams16} on the same seeds, prints the paired table). Filter lives in
`eval/search_episode.py` (`_safe_action_beams`); N-beam raycast in
`sim/search_scenario.py` (`beam_ranges`).

## Verdict: PASS — doubling to 8 beams closes 3/4 of the residual, 16 recovers the geometric ceiling; no world model, no ground truth

Pooled block A (seed0 140000) + block B (seed0 150000), n = 120,
identical rooms across all filters. Collision is exact crash counts;
find is the mean of the two equal-n blocks:

| filter | collision (n=120) | find | note |
|---|---|---|---|
| geometric (omni truth) | 0/120 = **0.000** | 0.892 | the ceiling |
| rangefinder (v3 1-beam) | 4/120 = **0.033** | 0.908 | reproduces v3's published 0.033 |
| beams4 (corridor, N=4) | 4/120 = **0.033** | 0.892 | control — matches the 1-beam pooled |
| **beams8** | 1/120 = **0.008** | 0.884 | **sweet spot** |
| beams16 | 0/120 = **0.000** | 0.842 | ceiling reached, find at the floor |

**The pre-registered rule fires PASS: collision(beams8 0.008) <
collision(beams4 0.033), a ~4x cut, with find 0.884 (>= 0.85) and
return holding (~0.95).** The fall is monotone — 0.033 -> 0.008 ->
0.000 — and beams16 recovers the privileged geometric 0.000 exactly.
**So the v3 residual WAS the between-beam off-axis gap, and it closes
with more of the same $5 sensor** — no vision, no world model, no
ground truth in the safety loop. The corridor-rule N=4 (0.033) landing
on the single-beam rangefinder (0.033) pooled confirms the control is
honest (they diverged at n=60 — 0.067 vs 0.050, one episode — and
converged at n=120).

### The deployment tradeoff, measured
find erodes monotonically with beam count: 0.908 (1-beam) -> 0.892 ->
0.884 -> 0.842 (16). More beams = a wider, more conservative body
corridor = more vetoes = occasionally out of coverage budget.
**8 beams is the recommendation:** near-ceiling safety (one crash in
120) while find stays healthy at 0.884; 16 beams buys the last crash
but pushes find to the 0.85 floor (over-conservative). The knob is
real and its cost is visible.

### Honest notes
- **Block B (150000) is a near-zero-collision block** — even beams4
  crashes 0/60 there, so B cannot show the collision CUT (you can't
  improve on zero); its job was no-regression + the find-erosion trend,
  both confirmed. Block A (140000) carries the discriminating crashes
  (it holds the diagnostic's forward-clip seeds 140023/030/048). The
  per-block auto-read on B prints "no improvement" for exactly this
  reason; the POOLED read is the verdict.
- Small counts (4 -> 1 -> 0 of 120): the TREND (monotone + ceiling
  recovery) and the mechanism (selftest: the 8-beam corridor catches an
  off-axis corner the single +x ray provably misses) carry the claim,
  not any single cell.

### Closes the Indoor Active Search safety arc
1a capability (privileged geometry, 0.000) -> 1b/hybrid the monocular
WM cannot own safety (camera-lock blinds it to 60% of residual) -> v3
4 cheap beams are deployable (0.033) -> **beams-v1: 8 beams recover
most of the ceiling (0.008), 16 all of it (0.000).** The whole safety
story is a cheap omnidirectional rangefinder ring, and the world
model's honest role here is target/coverage reasoning, not collision.

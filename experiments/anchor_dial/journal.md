# anchor-dial — widen the KL ball without paying the chain (the ★★★ tool question)

## Pre-registration (2026-07-07, before any number exists)

conservative_ft K2 proved the anchor DECOUPLES (kl=1.0: chain 93.3 %
zero-corrosion, gap 70→80) and measured its binding radius (mgap
stuck at 43 % — its repair needs more movement than the 1.0-ball
permits). Two crowns are queued behind this dial: the slalom-v2
throne (nine sittings vacant, blocked by mgap guards in every
five-world artifact) and, one recipe later, the dodgeball basin
problem. The dial gets its second and third datapoints here.

**Frozen recipe (single knob per arm, K-series verbatim otherwise):**
prior = `ppo_distill_generalist_BC2.zip`, 450k steps, diet
`slalom3_fixed,gap,moving_gap,classic,solo`, x_progress — identical
to conservative_ft K2 except the anchor argument.

- **K1 — constant kl = 0.3.** Hypothesis: a wider constant ball buys
  mgap's radius. Risk this arm PRICES: the dose curve says naked
  re-optimization kills the chain inside 25k — 0.3 may bleed it.
- **K2 — linear schedule kl 1.0 → 0.1 over 450k** (new machinery:
  `--anchor-end`, per-rollout coefficient update; wiring smoke must
  show the coefficient actually moves before the arm flies). 
  Hypothesis: early tightness protects the chain when re-optimization
  pressure is fiercest (measured: corrosion begins immediately), late
  freedom buys the repair radius.
- K2 runs REGARDLESS of K1's reading (two dial datapoints is the
  point; arms are independent, no conditional release).

**Index cells (the K-series exam, reused verbatim):**
`experiments/conservative_ft/index_cells.json` — slalom3@1.0
(seed0 22000) / gap@1.0 (9000) / mgap@1.0 (9500), n=30, borderline
±0.08 → fresh block POOLED n=60.

**Frozen bars (an arm PASSES iff all three):** chain slalom3@1.0
≥ 0.70 ∧ gap ≥ 0.75 ∧ mgap ≥ 0.70.

**Frozen verdict grid:**
- Any arm passes all three → the dial answers YES; successor (fresh
  pre-registration): the FULL slalom-v2 gate promotion shot with that
  artifact.
- Both arms: chain < 0.70 → the dial trades, never buys — the
  erasure-vs-anchor tension is fundamental at this budget; the DAgger
  argument (re-anchor to teacher) inherits the case.
- Both arms: chain holds but mgap < 0.70 → radius still out of reach
  at 450k; record "dial x budget" as a 2D open problem, no fishing.
- Reference row: kl=1.0 record (93.3/80/43.3) sits in the journal
  table for context; it is a RECORD, not a re-run.

Cost: 2 x 450k FT + 2 x 90-episode exams + one machinery smoke,
sequential background (~2-5 h wall).

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01GGt7SZ3GgNrbrXFrC5UWcn

## Machinery on the record (2026-07-07, pre-flight)

`--anchor-end` shipped: per-rollout linear coefficient drive,
**coefficient only** — the first draft called `set_anchor()` per
rollout, which would have re-frozen the prior to the CURRENT policy
(silently deleting the anchor's meaning) and deepcopied a live grad
graph (loud crash — the crash is what caught the semantic bug).
Wiring smoke: 4096 steps, 1.0 → 0.1 → landed kl_coef 0.5500, the
exact two-rollout expectation. Exam preflight: index_cells command
verified on the kl=1.0 record artifact (slalom3@1.0, n=2 dry).

## Verdict: the dial answers YES — the schedule dominates (2026-07-07)

| cell (bar) | BC2 prior | kl=1.0 record | K1 kl=0.3 | K2 sched 1.0→0.1 |
|---|---|---|---|---|
| slalom3 chain (≥0.70) | 0.933 | 0.933 | 0.833 ✓ | **0.833 ✓** |
| gap (≥0.75) | 0.70 | 0.80 | 0.933 ✓ | **1.000 ✓** |
| mgap (≥0.70) | 0.43 | 0.433 | 0.567 ✗ | **0.800 ✓** |

**K2 (the schedule) passes all three frozen bars** — margins +0.133 /
+0.25 / +0.10, none inside the ±0.08 borderline band, no recheck
owed. Landed coefficient 0.1030 (the designed 0.1, last rollout).

**K1 prices the middle of the dial and is strictly dominated:** at
constant 0.3 the chain pays the SAME ~10-point tax as the schedule
(0.833 both) while buying materially less repair (gap 0.933 < 1.000,
mgap 0.567 < 0.800). Constant coefficients trade on one axis; the
schedule buys on both — early tightness carries the chain through the
period when re-optimization pressure is fiercest (measured in the
dose curve: corrosion begins immediately), late freedom finishes the
repair that the 1.0-ball measurably could not reach.

The tool law, three datapoints in: **naked FT erases, constant
anchors trade, scheduled anchors buy.** The chain's residual ~10-pt
bleed (0.933 → 0.833, still 13 pts above bar) is the price of ANY
late freedom; whether a floor schedule (e.g. 1.0 → 0.3) removes it is
an unopened dial question, recorded not scheduled.

**Frozen-grid consequence:** successor unlocked — the FULL
corridor-slalom-v2 gate promotion shot with `ppo_anchor_sched.zip`
(fresh pre-registration, own campaign). The nine-sitting throne gets
its tenth challenger, this one carrying every guard's diet.

Cost: 2 x 450k FT + 180 exam episodes, ~2.6 h wall, background.

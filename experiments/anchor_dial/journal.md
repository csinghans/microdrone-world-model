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

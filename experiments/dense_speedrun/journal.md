# dense-speedrun — attack the oldest frontier, honestly (P5)

## Pre-registration (2026-07-07, before any number exists)

The dense floor (champion crash 17 % @0.8 m/s, 27 % @1.2 m/s since
v0.3) is the repo's stated open frontier. It has survived grounding
(two λ doses), calibration (C0), and — as of lambda_multiseed — the
retro-read that says the model axis never moved. The standing blame
("FOV physical limit: every evasion steers into unseen space") has
never actually been *isolated* from its rival ("the learner can't use
what the obs contains"). The imitation stack now lets us split them.

**Cells (frozen):** world `dense`, speed factors {1.0, 1.5, 2.0}
(= 0.8/1.2/1.6 m/s), n = 30 per read, seed0 = 7000 (the standing
dense exam seeds). Primary currency: success = reached ∧ ¬crashed;
crash % reported alongside (the frontier's historical currency).
Borderline (±0.08 of any bar) → fresh block, POOLED n = 60.

**Stage 0 — the probe (no training).** Two arms, same cells, same
runner (`run_scenario_episode`), path recorded:
1. **OracleField** — NEW privileged scripted pilot (reads pillar
   layout, greedy lane-clearance side-step, same action set /
   decision cadence). Its number is the arena ceiling, honestly a
   LOWER bound (scripted quality is a confound — but dense is a
   spatial task, where Weave/Dodge scripted ceilings held; the
   timing-task caveat from the door arc does not apply).
2. **Champion** (`ppo_wm_policy_edge_hard_xp.zip` + standing model)
   — measured-only red baseline. Its 1.0/1.5 cells double as an
   instrument replication check against the v0.3 record (crash
   17 %/27 %); a gross mismatch (beyond binomial n=30) = bug hunt
   before any verdict.

**Failure taxonomy (the campaign's real deliverable, mechanical from
path + layout):** each non-success classified as timeout | crash at
in-path-1 (pillar x ∈ [1.0,1.6]) | in-path-2 (x ∈ [1.9,2.5]) | side
clutter (|py| ≥ 0.55); crashes additionally flagged **blind-side** if
they occur within 3 decisions after a veer direction change (the
world's design thesis: evasion steers into unseen space).

**Frozen verdict rules:**
- Per cell, K1 unlocks iff OracleField success ≥ 0.70 there
  (dodgeball convention: bars only where the arena is priced
  flyable). Ceiling < 0.70 at 2.0 = "dynamics/action-set wall at
  speed" — recorded, no training thrown at it.
- **K1 (conditional, `research step` only): BC-distill OracleField**
  (collect on dense, seeds 40000+, disjoint from exams; distill.py
  machinery verbatim). Bars, probe-priced: success ≥ 0.70 × ceiling
  (cell) at pooled n ≥ 60. BC val-accuracy floor 0.80 gates entry to
  the closed-loop exam (chain_distill convention).
- **The mechanism split (why this campaign exists):**
  - BC val < 0.65 with a healthy teacher → the information is NOT in
    the obs — the FOV wall is real, confirmed for the first time at
    the data layer (not by elimination).
  - BC val ≥ 0.80 but closed-loop ≪ ceiling → drift/learner wall —
    the FOV story weakens; the two-leg recipe (on-policy FT) becomes
    the named follow-up.
  - BC flies near ceiling → the floor falls to imitation like the
    slalom wall did; dense stops being a frontier.
- No promotion path in this campaign: the champion stack is
  untouched; any artifact is best-so-far only. Guards not applicable
  (nothing merges into anything).

Cost: probe 180 episodes ≈ 30-60 min background; K1 (if unlocked)
one collect + one BC + two exams ≈ 1-1.5 h.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01GGt7SZ3GgNrbrXFrC5UWcn

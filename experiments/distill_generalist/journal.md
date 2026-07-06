# distill-generalist — one clone, every teacher

## Pre-registration (2026-07-06, before any number exists)

Design, recipe, manipulation floors and the frozen signature live in
the skill docstring (`skills/distill_generalist/skill.py`); the data
recipe is code-frozen in `scripts/distill.py::GENERALIST`.

**Teacher probe, recorded before the pot is mixed:** OracleTrack on
moving_gap@1.0 read **27/30 (0.90)** against the 0.80 teacher floor —
the moving-gap teacher is the scripted tracker, not the champion zip
(fallback unused). All five teachers now carry measured records on
their own worlds.

Order: mix the pot (~870 episodes) → BC → **manipulation gate: pooled
AND per-world val top-1 ≥ 0.80** → `research step --knob 0` (exam,
eval only) → verdict per the frozen signature (crown / support /
refuted). K1 reserve (share x2 re-BC) is step-arbitrated on its frozen
condition: chain held, ≥ 1 guard broken.

Baseline: the chain-distill specialist (chain 96.7 %, gap 93 %, mgap
47 %, cluttered 92 %, sweep 85 %). The pre-stated contrast: RL mixing
erased minority behavior this same day (dodgeball-v2); supervised
mixing has no reward war — whichever way the pot goes, the
interference story sharpens.

**Manipulation gate (2026-07-06): PASSED on every floor.** 46,708
decisions from 869/870 teacher episodes. Pooled val top-1 **0.929**;
per-world: classic 0.909, gap 0.912, moving_gap 0.882, slalom3_fixed
0.970, solo 0.939 — all five over the 0.80 floor. One student fits
five teachers in open loop; the exam decides the closed loop.

## K0 — the five-teacher generalist BC clone (2026-07-06 06:03 UTC)
Hypothesis: supervised multi-task has no gradient war: one student holds five mappings — the chain survives the pot, guards included
Config: experiments/distill_generalist/artifacts/ppo_distill_generalist_BC.zip

| cell | n | crash | success | clearance | custom |
|---|---|---|---|---|---|
| slalom3@1.0 | 30 | 7% | 93% | 0.27 | weaved=0.93 weave_frac=0.97 chain_break_at=2.80 |
| diag:slalom2@1.0 | 30 | 77% | 23% | 0.17 | weaved=0.23 weave_frac=0.83 chain_break_at=1.40 |
| diag:slalom3@1.25 | 30 | 100% | 0% | 0.05 | weaved=0.00 weave_frac=0.70 chain_break_at=1.87 |
| guard:gap@1.0 | 30 | 47% | 53% | 0.25 | transited=0.83 gap_margin=0.14 |
| guard:mgap@1.0 | 30 | 47% | 50% | 0.23 | transited=0.77 gap_margin=0.14 |
| guard:cluttered | 120 | 3% | 97% | 0.55 |  |
| guard:sweep@2.0 | 120 | 2% | 96% | 0.64 |  |
- slalom3@1.0 success>=0.7: 0.93 PASS
- guard:gap@1.0 success>=0.75: 0.53 FAIL
- guard:mgap@1.0 success>=0.7: 0.50 FAIL
- guard:cluttered crash<=0.05: 0.03 PASS (rechecked)
- guard:sweep@2.0 crash<=0.1: 0.03 PASS (rechecked)

**Gate verdict: guard_regression**

### Researcher notes
(unattended run)

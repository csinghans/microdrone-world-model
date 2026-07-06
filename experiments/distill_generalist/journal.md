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

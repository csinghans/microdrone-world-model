# dodgeball — station defense: can vision-only training buy the dodge?

## Pre-registration (2026-07-06, before any campaign number exists)

The feasibility probe removed the arena wall at every speed
(`experiments/dodgeball_feasibility/`: oracle 0.90/0.80/0.80/0.80,
crash ≈ 0 — the body's drift budget binds, not reaction time). Bars are
the frozen formula applied to that table, re-derived by the skill
selftest from the committed json so code and pre-registration cannot
drift: dodge@v0.6 ≥ 0.65, dodge@v1.0/v1.4/v1.8 ≥ 0.55.

**The live question is wall 2 (perception).** The G1 model is
single-frame — from one frame, an approaching ball and a parked pillar
at the same range are the same picture. Its diet's radial closure never
exceeded the drone's own walking pace toward static pillars, and every
hover label it ever saw said "hovering is safe". The ONLY mechanism
that can extract closure from this stack is policy-side: the
12-decision stacked history watching the collision probabilities RAMP
as the ball closes. That mechanism is real (it bought moving-gap and
closing-door) but has never been asked about head-on motion. K1 asks
exactly that, with nothing else in the diet.

**Knobs (frozen):**

- **K0** — the general champion zero-shot. Pre-registered structural 0:
  its repertoire never hovers (every command advances ≥ 0.3 m/s), so it
  exits the box by construction. The flee/crash split is the read.
- **K1** — pure dodgeball diet (all four ball speeds), station reward,
  the standard chassis (x_progress + edge_bias, 900k). The science
  knob: transit guards are expected structural failures for this zip
  (promotion impossible by design); the dodge cells are the point.
- **K2** — CONDITIONAL, played only if K1 reads success ≥ 0.30 on any
  priced cell: transit worlds + all four speeds, same chassis — the
  promotion knob, guards regain meaning. Dilution on 7 worlds is a
  known family (on the record). If K1 < 0.30 everywhere, K2 stays
  sheathed and the campaign closes on the perception verdict.

**Station reward (shipped with this pre-registration):** carried by the
world, not a constructor knob — "balls" in scenario meta flips the
episode objective to survival: no progress term, −0.02/decision, crash
−30 (checked at 48 Hz inside the decision loop — the exam's collision
rule, closure can tunnel a 12 Hz check), box exit truncates (forfeits
the bonus), surviving all 90 decisions pays the SAME +50 the transit
goal pays, with `terminated=True` (SB3 bootstraps γ·V onto truncations
— a truncated survival bonus would double-pay imagined future). Every
transit world's reward is bit-for-bit unchanged.

**Frozen campaign signature.** Support: K1 (or K2) clears the bar on
≥ 1 priced cell — vision-only training CAN buy station defense through
a motion-blind model. Full support: a knob passes its full gate.
Partial: K1 success materially above K0's structural floor but under
every bar — the ramp carries *some* warning; K2's condition arbitrates.
**Refuted:** K1 ≈ K0's floor with training completed — the probability
ramp is not a dodgeable signal, and the campaign closes honestly with
Tier-2 priced as three distinct future knobs: strafe surgery (action
set + labels + heads retrain), model-side motion (predictor-supervised,
NOT dataset-diet — dodgeball worlds are banned from the label oracle,
see the skill docstring mine), or a persistence/memory axis. Guards
judged as always; pooled rechecks per the 2026-07-05 protocol.

**Cost estimate:** K0 evals ~minutes (dodge episodes always run the
full 360 steps — the most expensive cell type in the catalog); K1
900k ≈ 4-6 h; K2 conditional. Runner starts only after the
chain-learning campaign releases the machine (single-runner rule:
gate commits must not race).

## K0 — the general champion, zero-shot on a task it was never asked (2026-07-06 00:06 UTC)
Hypothesis: structural 0, pre-registered: its repertoire never hovers (every command advances >= 0.3 m/s), so it exits the box by construction — the flee/crash split is the diagnostic
Config: output/ppo_wm_policy_edge_hard_xp.zip

| cell | n | crash | success | clearance | custom |
|---|---|---|---|---|---|
| dodge@v0.6 | 30 | 50% | 0% | 0.23 | survived=0.00 in_box=0.00 disp_x=3.01 y_max=1.20 |
| dodge@v1.0 | 30 | 70% | 0% | 0.16 | survived=0.00 in_box=0.00 disp_x=3.01 y_max=1.01 |
| dodge@v1.4 | 30 | 70% | 0% | 0.18 | survived=0.00 in_box=0.00 disp_x=3.01 y_max=0.92 |
| dodge@v1.8 | 30 | 77% | 0% | 0.16 | survived=0.00 in_box=0.00 disp_x=3.01 y_max=0.87 |
| guard:gap@1.0 | 30 | 63% | 37% | 0.18 |  |
| guard:mgap@1.0 | 30 | 67% | 33% | 0.19 |  |
| guard:cluttered | 120 | 3% | 97% | 0.54 |  |
| guard:sweep@2.0 | 120 | 4% | 96% | 0.64 |  |
- dodge@v0.6 success>=0.65: 0.00 FAIL
- dodge@v1.0 success>=0.55: 0.00 FAIL
- dodge@v1.4 success>=0.55: 0.00 FAIL
- dodge@v1.8 success>=0.55: 0.00 FAIL
- guard:gap@1.0 success>=0.75: 0.37 FAIL
- guard:mgap@1.0 success>=0.7: 0.33 FAIL
- guard:cluttered crash<=0.05: 0.03 PASS (rechecked)
- guard:sweep@2.0 crash<=0.1: 0.04 PASS (rechecked)

**Gate verdict: guard_regression**

### Researcher notes
(unattended run)

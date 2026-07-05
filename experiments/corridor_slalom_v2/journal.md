
## K0 — v1's best trained artifact, re-based on the fixed geometry (2026-07-05 13:03 UTC)
Hypothesis: the 'before': expect roughly its v1 reading (<=10 %) — mixed-dx training never phase-locked to one spacing
Config: experiments/corridor_slalom/artifacts/ppo_corridor_slalom_K2.zip

| cell | n | crash | success | clearance | custom |
|---|---|---|---|---|---|
| slalom3@1.0 | 30 | 90% | 0% | 0.12 | weaved=0.00 weave_frac=0.82 chain_break_at=2.10 |
| diag:slalom2@1.0 | 30 | 87% | 10% | 0.14 | weaved=0.10 weave_frac=0.83 chain_break_at=1.50 |
| diag:slalom3@1.25 | 30 | 100% | 0% | 0.11 | weaved=0.00 weave_frac=0.76 chain_break_at=1.80 |
| guard:gap@1.0 | 30 | 3% | 93% | 0.43 | transited=0.93 gap_margin=0.26 |
| guard:mgap@1.0 | 30 | 17% | 83% | 0.30 | transited=0.93 gap_margin=0.16 |
| guard:cluttered | 120 | 2% | 98% | 0.42 |  |
| guard:sweep@2.0 | 60 | 0% | 100% | 0.61 |  |
- slalom3@1.0 success>=0.7: 0.00 FAIL
- guard:gap@1.0 success>=0.75: 0.93 PASS
- guard:mgap@1.0 success>=0.7: 0.83 PASS
- guard:cluttered crash<=0.05: 0.02 PASS (rechecked)
- guard:sweep@2.0 crash<=0.1: 0.00 PASS

**Gate verdict: continue**

### Researcher notes
(unattended run)

## K1 — fresh training on the FIXED spacing (v2-combination diet, 900k) (2026-07-05 13:51 UTC)
Hypothesis: a fixed dx is a learnable rhythm; whether it closes 97-vs-10 is the whole question
Config: {"worlds": ["classic", "classic", "dense", "moving", "gap", "moving_gap", "solo", "slalom3_fixed"], "x_progress": true, "edge_bias": true, "timesteps": 900000}

| cell | n | crash | success | clearance | custom |
|---|---|---|---|---|---|
| slalom3@1.0 | 30 | 97% | 0% | 0.11 | weaved=0.00 weave_frac=0.72 chain_break_at=1.33 |
| diag:slalom2@1.0 | 30 | 80% | 13% | 0.16 | weaved=0.13 weave_frac=0.85 chain_break_at=1.63 |
| diag:slalom3@1.25 | 30 | 93% | 0% | 0.09 | weaved=0.00 weave_frac=0.73 chain_break_at=1.60 |
| guard:gap@1.0 | 30 | 7% | 87% | 0.41 | transited=0.87 gap_margin=0.24 |
| guard:mgap@1.0 | 30 | 43% | 57% | 0.25 | transited=0.80 gap_margin=0.12 |
| guard:cluttered | 120 | 2% | 98% | 0.43 |  |
| guard:sweep@2.0 | 120 | 7% | 93% | 0.49 |  |
- slalom3@1.0 success>=0.7: 0.00 FAIL
- guard:gap@1.0 success>=0.75: 0.87 PASS
- guard:mgap@1.0 success>=0.7: 0.57 FAIL
- guard:cluttered crash<=0.05: 0.03 PASS (rechecked)
- guard:sweep@2.0 crash<=0.1: 0.07 PASS (rechecked)

**Gate verdict: guard_regression**

### Researcher notes
(unattended run)

## K2 — same mixture at 1350k (2026-07-05 15:06 UTC)
Hypothesis: reserve: v1 never tried the budget dial here (it doubled share and broke a guard) — buy convergence, not new variables
Config: {"worlds": ["classic", "classic", "dense", "moving", "gap", "moving_gap", "solo", "slalom3_fixed"], "x_progress": true, "edge_bias": true, "timesteps": 1350000}

| cell | n | crash | success | clearance | custom |
|---|---|---|---|---|---|
| slalom3@1.0 | 30 | 90% | 0% | 0.13 | weaved=0.00 weave_frac=0.82 chain_break_at=2.03 |
| diag:slalom2@1.0 | 30 | 77% | 20% | 0.16 | weaved=0.20 weave_frac=0.85 chain_break_at=1.70 |
| diag:slalom3@1.25 | 30 | 87% | 7% | 0.14 | weaved=0.07 weave_frac=0.72 chain_break_at=1.53 |
| guard:gap@1.0 | 30 | 7% | 93% | 0.42 | transited=1.00 gap_margin=0.25 |
| guard:mgap@1.0 | 30 | 40% | 60% | 0.27 | transited=0.97 gap_margin=0.11 |
| guard:cluttered | 120 | 7% | 93% | 0.37 |  |
| guard:sweep@2.0 | 120 | 13% | 86% | 0.40 |  |
- slalom3@1.0 success>=0.7: 0.00 FAIL
- guard:gap@1.0 success>=0.75: 0.93 PASS
- guard:mgap@1.0 success>=0.7: 0.60 FAIL
- guard:cluttered crash<=0.05: 0.07 FAIL (rechecked)
- guard:sweep@2.0 crash<=0.1: 0.13 FAIL (rechecked)

**Gate verdict: guard_regression**

### Researcher notes
(unattended run)

## Researcher notes — campaign close: the bottleneck is structural (2026-07-05)

**No knob passed the one priced target** (slalom3@1.0: 0/0/0 % across
K0/K1/K2 against a 0.70 bar on a 0.97-ceiling arena). The hypotheses
died informatively:

- K1 (fixed spacing, fresh 900 k) came out WORSE than v1's mixed-dx
  artifact (chain_break 1.33 vs 2.10) and broke the mgap guard — the
  "fixed dx is a learnable rhythm" story is refuted, not undertrained.
- K2 (1350 k) restored K0-level penetration (break 2.03, diag slalom2
  20 %) and still completed nothing, breaking two guards — the budget
  dial refuted here too (and the moving-gap dilution tax, seventh
  sighting).
- Across v1+v2: six trained attempts, per-gate competence every time
  (weave_frac 0.72-0.85), full-chain success ~never (0-3 % on slalom3).

**The structural hypothesis this leaves standing (recorded, not
asserted):** at dx = 0.70 and cruise, the gate period is 0.875 s — but
the world model's longest forecast horizon is k=32 ≈ 0.67 s. While
committing to gate k, gate k+1 sits BEYOND every collision head's
horizon; the camera sees its pillars, the encoder embeds them, and the
policy's observation bottleneck (collision probabilities only — 8
numbers per candidate) throws that visibility away. The oracle chains
because it knows the ladder; the policy cannot chain because its
observation cannot represent "the door after this one". If true, no
diet or budget can fix chaining — only longer-horizon heads (k=48/64)
or a richer observation (latent features alongside the probabilities)
can, and both are model-axis, retraining-class, new-campaign material.
Falsifiable signature pre-stated for that future campaign: horizon
extension should move chain_break_at specifically, before it moves
anything else.

**Verdict: CLOSED, honest negative — and the chaining question is now
priced all the way down:** the arena is flyable (0.97 oracle), the
policies are per-gate competent (0.85 frac), and the missing piece is
architectural, not experiential. Sixth+seventh guard-dilution sightings
recorded. The catalog's first capability that the collision-probability
bottleneck structurally cannot support.

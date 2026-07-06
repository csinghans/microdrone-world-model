# bcft-generalist — the two-leg recipe at five-world scale

## Pre-registration (2026-07-06, before any number exists)

Design, knobs and the frozen signature live in the skill docstring
(`skills/bcft_generalist/skill.py`). Operational order:

1. `distill --finetune <BC2> --steps 450000
   --world slalom3_fixed,gap,moving_gap,classic,solo` →
   `artifacts/ppo_bcft_generalist_FT.zip` (the measured dose, SB3
   defaults, uniform diet — one delta on the gated BC2).
2. `research step skills/bcft_generalist --knob 0` (exam, eval only).
3. K1 reserve (broken-worlds-only FT) is step-arbitrated on its frozen
   condition: chain lost (< 0.70) AND >= 1 broken guard repaired.

The headline risk is the experiment: the slalom arc proved on-policy
RL cannot DISCOVER the chain; K0 asks whether it can KEEP one it was
handed. Full pass = the catalog's first distilled champion.

Baselines: BC2 93.3 / 70 / 43 / 93.3 / 93.3 (chain/gap/mgap/
cluttered/sweep); teachers OracleWeave 0.97, OracleTrack 0.885.

## K0 — BC2 + PPO 450k on the uniform five-world diet (the crown shot) (2026-07-06 07:23 UTC)
Hypothesis: the measured two-leg recipe composed: imitation bought five skills, on-policy RL now repairs the closed-loop drift that share could not — while hopefully KEEPING the chain RL could never discover
Config: experiments/bcft_generalist/artifacts/ppo_bcft_generalist_FT.zip

| cell | n | crash | success | clearance | custom |
|---|---|---|---|---|---|
| slalom3@1.0 | 30 | 100% | 0% | 0.10 | weaved=0.00 weave_frac=0.60 chain_break_at=1.43 |
| diag:slalom2@1.0 | 30 | 57% | 43% | 0.19 | weaved=0.43 weave_frac=0.77 chain_break_at=1.53 |
| diag:slalom3@1.25 | 30 | 100% | 0% | 0.08 | weaved=0.00 weave_frac=0.62 chain_break_at=1.57 |
| guard:gap@1.0 | 30 | 3% | 97% | 0.42 | transited=1.00 gap_margin=0.27 |
| guard:mgap@1.0 | 30 | 10% | 90% | 0.34 | transited=1.00 gap_margin=0.20 |
| guard:cluttered | 120 | 1% | 99% | 0.43 |  |
| guard:sweep@2.0 | 60 | 38% | 62% | 0.28 |  |
- slalom3@1.0 success>=0.7: 0.00 FAIL
- guard:gap@1.0 success>=0.75: 0.97 PASS
- guard:mgap@1.0 success>=0.7: 0.90 PASS
- guard:cluttered crash<=0.05: 0.01 PASS (rechecked)
- guard:sweep@2.0 crash<=0.1: 0.38 FAIL

**Gate verdict: guard_regression**

### Researcher notes
(unattended run)

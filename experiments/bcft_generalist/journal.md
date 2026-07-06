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

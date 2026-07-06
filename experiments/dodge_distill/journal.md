# dodge-distill — does fast-ball information exist in the observation at all?

## Pre-registration (2026-07-06, before any number exists)

Design, the two-layer meter (representation val per speed / closed-loop
cells) and the frozen signature live in the skill docstring
(`skills/dodge_distill/skill.py`); recipe code-frozen in
`scripts/distill.py::DODGE` (200 eps x 4 matched teachers, seeds
51000-54199). Order: pooled BC → per-world val meters (floor 0.80,
fast worlds are THE reading) → `research step --knob 0` → verdict;
K1 (station-reward FT, drift repair) step-gated on "fits but misses".

Teacher records already on the books (feasibility probe, n=30/cell):
0.90 / 0.80 / 0.80 / 0.80. Baselines: v1-K3 47/60/20/13 %.

## K0 — the four-speed OracleDodge clone (pooled BC) (2026-07-06 07:47 UTC)
Hypothesis: per-speed val is the representation meter; the cells are the closed loop — the two layers separate wm48's live suspects
Config: experiments/dodge_distill/artifacts/ppo_dodge_distill_BC.zip

| cell | n | crash | success | clearance | custom |
|---|---|---|---|---|---|
| dodge@v0.6 | 30 | 57% | 33% | 0.26 | survived=0.43 in_box=0.90 disp_x=0.71 y_max=0.67 |
| dodge@v1.0 | 30 | 17% | 37% | 0.32 | survived=0.83 in_box=0.53 disp_x=1.41 y_max=1.13 |
| dodge@v1.4 | 90 | 17% | 60% | 0.34 | survived=0.83 in_box=0.74 disp_x=1.39 y_max=0.90 |
| dodge@v1.8 | 90 | 23% | 49% | 0.29 | survived=0.77 in_box=0.68 disp_x=1.33 y_max=0.97 |
| guard:gap@1.0 | 30 | 7% | 0% | 1.74 |  |
| guard:mgap@1.0 | 30 | 60% | 0% | 0.37 |  |
| guard:cluttered | 120 | 0% | 0% | 1.61 |  |
| guard:sweep@2.0 | 60 | 18% | 2% | 1.00 |  |
- dodge@v0.6 success>=0.65: 0.33 FAIL
- dodge@v1.0 success>=0.55: 0.37 FAIL
- dodge@v1.4 success>=0.55: 0.60 PASS (rechecked)
- dodge@v1.8 success>=0.55: 0.49 FAIL (rechecked)
- guard:gap@1.0 success>=0.75: 0.00 FAIL
- guard:mgap@1.0 success>=0.7: 0.00 FAIL
- guard:cluttered crash<=0.05: 0.00 PASS (rechecked)
- guard:sweep@2.0 crash<=0.1: 0.18 FAIL

**Gate verdict: guard_regression**

### Researcher notes
(unattended run)

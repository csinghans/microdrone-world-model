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

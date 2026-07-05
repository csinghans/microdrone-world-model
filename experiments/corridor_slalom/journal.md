
## K0 — the general champion on the slalom (2026-07-05 11:02 UTC)
Hypothesis: trained to dodge PAST things, never to re-enter for a next gate: expect slalom2 marginal, slalom3 snapping at gate 1-2, or a detour caught by `weaved`
Config: output/ppo_wm_policy_edge_hard_xp.zip

| cell | n | crash | success | clearance | custom |
|---|---|---|---|---|---|
| slalom2@1.0 | 30 | 70% | 0% | 0.18 | weaved=0.00 weave_frac=0.50 chain_break_at=0.57 |
| slalom3@1.0 | 30 | 77% | 0% | 0.13 | weaved=0.00 weave_frac=0.73 chain_break_at=1.53 |
| slalom3@1.5 | 30 | 90% | 0% | 0.11 | weaved=0.00 weave_frac=0.62 chain_break_at=1.20 |
| guard:gap@1.0 | 30 | 63% | 27% | 0.18 | transited=0.37 gap_margin=0.04 |
| guard:mgap@1.0 | 30 | 67% | 23% | 0.19 | transited=0.30 gap_margin=0.06 |
| guard:cluttered | 120 | 3% | 97% | 0.54 |  |
| guard:sweep@2.0 | 120 | 4% | 96% | 0.64 |  |
- slalom2@1.0 success>=0.7: 0.00 FAIL
- slalom3@1.0 success>=0.55: 0.00 FAIL
- slalom3@1.5 success>=0.4: 0.00 FAIL
- guard:gap@1.0 success>=0.75: 0.27 FAIL
- guard:mgap@1.0 success>=0.7: 0.23 FAIL
- guard:cluttered crash<=0.05: 0.03 PASS (rechecked)
- guard:sweep@2.0 crash<=0.1: 0.04 PASS (rechecked)

**Gate verdict: guard_regression**

### Researcher notes
(unattended run)

## K1 — the moving-gap v2 champion — its home skill, chained (2026-07-05 11:03 UTC)
Hypothesis: each fence alone is a solved problem; the second direction reversal is the new thing — expect best zero-shot, degrading on slalom3's third gate
Config: experiments/moving_gap_v2/artifacts/ppo_moving_gap_v2_K3.zip

| cell | n | crash | success | clearance | custom |
|---|---|---|---|---|---|
| slalom2@1.0 | 30 | 93% | 7% | 0.11 | weaved=0.07 weave_frac=0.70 chain_break_at=1.30 |
| slalom3@1.0 | 30 | 97% | 0% | 0.09 | weaved=0.00 weave_frac=0.63 chain_break_at=1.00 |
| slalom3@1.5 | 30 | 100% | 0% | 0.08 | weaved=0.00 weave_frac=0.72 chain_break_at=1.47 |
| guard:gap@1.0 | 30 | 10% | 90% | 0.41 | transited=0.90 gap_margin=0.24 |
| guard:mgap@1.0 | 90 | 19% | 81% | 0.31 | transited=0.98 gap_margin=0.17 |
| guard:cluttered | 120 | 3% | 97% | 0.38 |  |
| guard:sweep@2.0 | 60 | 0% | 100% | 0.54 |  |
- slalom2@1.0 success>=0.7: 0.07 FAIL
- slalom3@1.0 success>=0.55: 0.00 FAIL
- slalom3@1.5 success>=0.4: 0.00 FAIL
- guard:gap@1.0 success>=0.75: 0.90 PASS
- guard:mgap@1.0 success>=0.7: 0.81 PASS (rechecked)
- guard:cluttered crash<=0.05: 0.03 PASS (rechecked)
- guard:sweep@2.0 crash<=0.1: 0.00 PASS

**Gate verdict: continue**

### Researcher notes
(unattended run)

## K2 — slalom3 joins the v2-combination diet (2026-07-05 11:49 UTC)
Hypothesis: the chain becomes a trained behaviour (single variable: the new world in the proven chassis)
Config: {"worlds": ["classic", "classic", "dense", "moving", "gap", "moving_gap", "solo", "slalom3"], "x_progress": true, "edge_bias": true, "timesteps": 900000}

| cell | n | crash | success | clearance | custom |
|---|---|---|---|---|---|
| slalom2@1.0 | 30 | 90% | 10% | 0.14 | weaved=0.10 weave_frac=0.85 chain_break_at=1.43 |
| slalom3@1.0 | 30 | 90% | 3% | 0.12 | weaved=0.03 weave_frac=0.82 chain_break_at=2.17 |
| slalom3@1.5 | 30 | 100% | 0% | 0.11 | weaved=0.00 weave_frac=0.73 chain_break_at=1.53 |
| guard:gap@1.0 | 30 | 3% | 93% | 0.43 | transited=0.93 gap_margin=0.26 |
| guard:mgap@1.0 | 30 | 17% | 83% | 0.30 | transited=0.93 gap_margin=0.16 |
| guard:cluttered | 120 | 2% | 98% | 0.42 |  |
| guard:sweep@2.0 | 60 | 0% | 100% | 0.61 |  |
- slalom2@1.0 success>=0.7: 0.10 FAIL
- slalom3@1.0 success>=0.55: 0.03 FAIL
- slalom3@1.5 success>=0.4: 0.00 FAIL
- guard:gap@1.0 success>=0.75: 0.93 PASS
- guard:mgap@1.0 success>=0.7: 0.83 PASS
- guard:cluttered crash<=0.05: 0.02 PASS (rechecked)
- guard:sweep@2.0 crash<=0.1: 0.00 PASS

**Gate verdict: continue**

### Researcher notes
(unattended run)

## K3 — double slalom share (2026-07-05 12:37 UTC)
Hypothesis: played only if K2 trends right but undershoots: rhythm needs reps, not new variables
Config: {"worlds": ["classic", "classic", "dense", "moving", "gap", "moving_gap", "solo", "slalom3", "slalom3"], "x_progress": true, "edge_bias": true, "timesteps": 900000}

| cell | n | crash | success | clearance | custom |
|---|---|---|---|---|---|
| slalom2@1.0 | 30 | 70% | 3% | 0.14 | weaved=0.03 weave_frac=0.58 chain_break_at=0.87 |
| slalom3@1.0 | 30 | 67% | 0% | 0.18 | weaved=0.00 weave_frac=0.68 chain_break_at=1.07 |
| slalom3@1.5 | 30 | 60% | 0% | 0.19 | weaved=0.00 weave_frac=0.64 chain_break_at=1.00 |
| guard:gap@1.0 | 30 | 3% | 97% | 0.44 | transited=1.00 gap_margin=0.27 |
| guard:mgap@1.0 | 30 | 47% | 53% | 0.24 | transited=0.73 gap_margin=0.11 |
| guard:cluttered | 120 | 1% | 99% | 0.50 |  |
| guard:sweep@2.0 | 60 | 0% | 100% | 0.51 |  |
- slalom2@1.0 success>=0.7: 0.03 FAIL
- slalom3@1.0 success>=0.55: 0.00 FAIL
- slalom3@1.5 success>=0.4: 0.00 FAIL
- guard:gap@1.0 success>=0.75: 0.97 PASS
- guard:mgap@1.0 success>=0.7: 0.53 FAIL
- guard:cluttered crash<=0.05: 0.01 PASS (rechecked)
- guard:sweep@2.0 crash<=0.1: 0.00 PASS

**Gate verdict: guard_regression**

### Researcher notes
(unattended run)

## Researcher notes — campaign close: an honest across-the-board negative (2026-07-05)

**No knob passed any target** (best: K2's slalom2 at 10 % vs the 70 %
bar). The question "does evasion chain?" got a sharp answer anyway:
**not at this spacing — the first reversal is the wall.**

- Zero-shot, the mgap champion (K1) threads gate 1 and dies at gate 2
  (chain_break_at ≈ 1.0-1.3, weave_frac 0.63-0.72): the *reversal
  itself* kills, not its repetition. My frozen hypothesis said the
  third gate would be the new thing — wrong; the second was.
- Training helps and saturates far under the bars: K2 pushes
  penetration to chain_break_at 2.17 and weave_frac 0.85, yet joint
  success stays ≤10 % with crash-dominated failures right after gate 1
  — per-gate competence multiplied by a correlated transition failure.
- K3 (double share) made everything worse AND broke the mgap guard
  (53 % vs ≥70 %): the over-specialization/dilution tax, sixth sighting
  of the family.
- Guards elsewhere stayed green, and this was the **pooling protocol's
  first production campaign**: cluttered and sweep@2.0 judged at pooled
  n=120, mgap at n=90 — no re-rolled verdicts.

**Design accountability, recorded:** the pre-registration's own math
flagged the swing (0.56-0.74 m per 0.7-0.8 m of corridor) as
edge-of-authority and bet that real dynamics would be kinder. The bet
lost. What is measured is "beyond this recipe's reach", not "physically
impossible" — the arena's ceiling was never probed, because no scripted
optimal-path feasibility check was pre-registered. That is the lesson
this campaign exports: **calibrate the exam before grading students** —
future arena designs should pre-register a scripted/oracle feasibility
probe that establishes the physical ceiling before any bar is frozen
(the arena-side twin of the sweep2_noise instrument lesson).

**Verdict: CLOSED, honest negative.** The chaining question stays open
pending a slalom v2 with a feasibility-first design (probe the ceiling,
set dx/speed so the ceiling sits ≥90 %, then re-ask). Seeded to the
ideas ledger.

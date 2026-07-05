
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

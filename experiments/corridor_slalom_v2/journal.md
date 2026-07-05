
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

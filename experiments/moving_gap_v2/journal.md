
## K0 — the v1 best (KD1), re-measured on v2's cells (2026-07-05 01:41 UTC)
Hypothesis: one measurement basis for the whole campaign; expected: targets pass, sweep@2.0 lands near its confirmed 17 %
Config: experiments/moving_gap/artifacts/ppo_moving_gap_KD1.zip

| cell | n | crash | success | clearance | custom |
|---|---|---|---|---|---|
| mgap@1.0 | 30 | 20% | 80% | 0.34 | transited=0.97 gap_margin=0.18 |
| mgap@1.5 | 30 | 20% | 80% | 0.35 | transited=0.97 gap_margin=0.19 |
| guard:gap@1.0 | 30 | 0% | 100% | 0.42 | transited=1.00 gap_margin=0.24 |
| guard:cluttered | 60 | 0% | 98% | 0.43 |  |
| guard:sweep@1.0 | 30 | 3% | 97% | 0.43 |  |
| guard:sweep@1.5 | 30 | 0% | 100% | 0.39 |  |
| guard:sweep@2.0 | 60 | 22% | 73% | 0.32 |  |
- mgap@1.0 success>=0.75: 0.80 PASS (rechecked)
- mgap@1.5 success>=0.6: 0.80 PASS
- guard:gap@1.0 success>=0.75: 1.00 PASS
- guard:cluttered crash<=0.05: 0.00 PASS (rechecked)
- guard:sweep@1.0 crash<=0.05: 0.03 PASS (rechecked)
- guard:sweep@1.5 crash<=0.1: 0.00 PASS
- guard:sweep@2.0 crash<=0.1: 0.22 FAIL

**Gate verdict: guard_regression**

### Researcher notes
(unattended run)

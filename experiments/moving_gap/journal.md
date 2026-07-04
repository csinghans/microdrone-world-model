
## K0 — the gap-flight champion, zero-shot on the sliding fence (2026-07-04 23:03 UTC)
Hypothesis: expected honest failure: its diet never moved a fence — the static-future assumption misses by vy x approach-time
Config: experiments/gap_flight/artifacts/ppo_gap_flight_KD1.zip

| cell | n | crash | success | clearance | custom |
|---|---|---|---|---|---|
| mgap@1.0 | 30 | 33% | 67% | 0.27 | transited=0.80 gap_margin=0.13 |
| mgap@1.5 | 30 | 13% | 87% | 0.33 | transited=0.93 gap_margin=0.20 |
| guard:gap@1.0 | 30 | 13% | 87% | 0.39 | transited=0.90 gap_margin=0.24 |
| guard:cluttered | 60 | 0% | 100% | 0.55 |  |
| guard:sweep@1.0 | 30 | 0% | 100% | 0.62 |  |
| guard:sweep@1.5 | 30 | 0% | 100% | 0.62 |  |
| guard:sweep@2.0 | 30 | 10% | 88% | 0.50 |  |
- mgap@1.0 success>=0.75: 0.67 FAIL
- mgap@1.5 success>=0.6: 0.87 PASS (rechecked)
- guard:gap@1.0 success>=0.75: 0.87 PASS
- guard:cluttered crash<=0.05: 0.00 PASS (rechecked)
- guard:sweep@1.0 crash<=0.05: 0.00 PASS (rechecked)
- guard:sweep@1.5 crash<=0.1: 0.00 PASS (rechecked)
- guard:sweep@2.0 crash<=0.1: 0.10 PASS (rechecked)

**Gate verdict: continue**

### Researcher notes
(unattended run)

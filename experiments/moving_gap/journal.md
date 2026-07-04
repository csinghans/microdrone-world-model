
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

## K1 — moving_gap joins the gap champion's diet, at KD1's budget (2026-07-04 23:28 UTC)
Hypothesis: five worlds dilute harder than the four that already needed 1.5x (the KD1 lesson) — schedule 450k from the start
Config: {"worlds": ["classic", "dense", "moving", "gap", "moving_gap"], "x_progress": true, "edge_bias": true, "timesteps": 450000}

| cell | n | crash | success | clearance | custom |
|---|---|---|---|---|---|
| mgap@1.0 | 30 | 17% | 83% | 0.30 | transited=1.00 gap_margin=0.16 |
| mgap@1.5 | 30 | 17% | 83% | 0.35 | transited=1.00 gap_margin=0.21 |
| guard:gap@1.0 | 30 | 0% | 100% | 0.43 | transited=1.00 gap_margin=0.27 |
| guard:cluttered | 60 | 10% | 90% | 0.41 |  |
| guard:sweep@1.0 | 30 | 3% | 97% | 0.43 |  |
| guard:sweep@1.5 | 30 | 8% | 92% | 0.36 |  |
| guard:sweep@2.0 | 30 | 27% | 70% | 0.29 |  |
- mgap@1.0 success>=0.75: 0.83 PASS
- mgap@1.5 success>=0.6: 0.83 PASS
- guard:gap@1.0 success>=0.75: 1.00 PASS
- guard:cluttered crash<=0.05: 0.10 FAIL (rechecked)
- guard:sweep@1.0 crash<=0.05: 0.03 PASS (rechecked)
- guard:sweep@1.5 crash<=0.1: 0.08 PASS (rechecked)
- guard:sweep@2.0 crash<=0.1: 0.27 FAIL

**Gate verdict: guard_regression**

### Researcher notes
(unattended run)

## K2 — moving_gap double share (2026-07-04 23:52 UTC)
Hypothesis: if K1 undertrains the timing cell, double its episode share
Config: {"worlds": ["classic", "dense", "moving", "gap", "moving_gap", "moving_gap"], "x_progress": true, "edge_bias": true, "timesteps": 450000}

| cell | n | crash | success | clearance | custom |
|---|---|---|---|---|---|
| mgap@1.0 | 30 | 25% | 75% | 0.33 | transited=0.98 gap_margin=0.17 |
| mgap@1.5 | 30 | 7% | 93% | 0.39 | transited=1.00 gap_margin=0.22 |
| guard:gap@1.0 | 30 | 3% | 97% | 0.40 | transited=0.97 gap_margin=0.23 |
| guard:cluttered | 60 | 22% | 78% | 0.31 |  |
| guard:sweep@1.0 | 30 | 27% | 73% | 0.30 |  |
| guard:sweep@1.5 | 30 | 3% | 93% | 0.44 |  |
| guard:sweep@2.0 | 30 | 22% | 72% | 0.28 |  |
- mgap@1.0 success>=0.75: 0.75 PASS (rechecked)
- mgap@1.5 success>=0.6: 0.93 PASS
- guard:gap@1.0 success>=0.75: 0.97 PASS
- guard:cluttered crash<=0.05: 0.22 FAIL
- guard:sweep@1.0 crash<=0.05: 0.27 FAIL
- guard:sweep@1.5 crash<=0.1: 0.03 PASS (rechecked)
- guard:sweep@2.0 crash<=0.1: 0.22 FAIL (rechecked)

**Gate verdict: guard_regression**

### Researcher notes
(unattended run)

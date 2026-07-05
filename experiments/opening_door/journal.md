
## K0 — the reactive baseline on a door that isn't open yet (2026-07-05 06:42 UTC)
Hypothesis: reaction has no concept of 'soon': expect pinched (charges the slit) or froze (dodges along the wall all episode)
Config: builtin:reactive

| cell | n | crash | success | clearance | custom |
|---|---|---|---|---|---|
| odoor@1.0 | 30 | 83% | 17% | 0.15 | threaded=0.17 pinched=0.83 froze=0.00 door_margin=0.02 wait_time=0.07 |
| odoor@1.5 | 30 | 100% | 0% | 0.07 | threaded=0.00 pinched=1.00 froze=0.00 door_margin=0.00 wait_time=0.00 |
| guard:gap@1.0 | 30 | 17% | 83% | 0.31 | transited=1.00 gap_margin=0.19 |
| guard:mgap@1.0 | 30 | 23% | 75% | 0.32 | transited=0.92 gap_margin=0.22 |
| guard:cluttered | 60 | 3% | 97% | 0.52 |  |
| guard:sweep@2.0 | 60 | 48% | 52% | 0.23 |  |
- odoor@1.0 success>=0.6: 0.17 FAIL
- odoor@1.5 success>=0.5: 0.00 FAIL
- guard:gap@1.0 success>=0.75: 0.83 PASS (rechecked)
- guard:mgap@1.0 success>=0.7: 0.75 PASS (rechecked)
- guard:cluttered crash<=0.05: 0.03 PASS (rechecked)
- guard:sweep@2.0 crash<=0.1: 0.48 FAIL

**Gate verdict: guard_regression**

### Researcher notes
(unattended run)

## K1 — the hand latent-MPC (2026-07-05 06:42 UTC)
Hypothesis: 0.7 s of anticipation sometimes covers the wait window: expect partial success at short waits, collapse at long ones
Config: builtin:wm_mpc

| cell | n | crash | success | clearance | custom |
|---|---|---|---|---|---|
| odoor@1.0 | 30 | 60% | 40% | 0.16 | threaded=0.40 pinched=0.60 froze=0.00 door_margin=0.07 wait_time=0.31 |
| odoor@1.5 | 30 | 100% | 0% | 0.10 | threaded=0.00 pinched=1.00 froze=0.00 door_margin=0.00 wait_time=0.00 |
| guard:gap@1.0 | 30 | 60% | 40% | 0.19 | transited=0.87 gap_margin=0.15 |
| guard:mgap@1.0 | 30 | 57% | 43% | 0.21 | transited=0.83 gap_margin=0.14 |
| guard:cluttered | 60 | 37% | 63% | 0.36 |  |
| guard:sweep@2.0 | 60 | 20% | 80% | 0.51 |  |
- odoor@1.0 success>=0.6: 0.40 FAIL
- odoor@1.5 success>=0.5: 0.00 FAIL
- guard:gap@1.0 success>=0.75: 0.40 FAIL
- guard:mgap@1.0 success>=0.7: 0.43 FAIL
- guard:cluttered crash<=0.05: 0.37 FAIL
- guard:sweep@2.0 crash<=0.1: 0.20 FAIL

**Gate verdict: guard_regression**

### Researcher notes
(unattended run)

## K2 — the moving-gap v2 champion — does WHERE-timing buy WHEN-timing? (2026-07-05 06:43 UTC)
Hypothesis: the duel's headline: it aims at where a gap will be; waiting for a gap to exist was never in its diet — expect best-of-zero-shot but under bar
Config: experiments/moving_gap_v2/artifacts/ppo_moving_gap_v2_K3.zip

| cell | n | crash | success | clearance | custom |
|---|---|---|---|---|---|
| odoor@1.0 | 30 | 40% | 60% | 0.27 | threaded=0.60 pinched=0.40 froze=0.00 door_margin=0.18 wait_time=0.66 |
| odoor@1.5 | 30 | 67% | 33% | 0.20 | threaded=0.33 pinched=0.67 froze=0.00 door_margin=0.08 wait_time=0.20 |
| guard:gap@1.0 | 30 | 10% | 90% | 0.41 | transited=0.90 gap_margin=0.24 |
| guard:mgap@1.0 | 30 | 15% | 85% | 0.32 | transited=0.98 gap_margin=0.17 |
| guard:cluttered | 60 | 5% | 95% | 0.38 |  |
| guard:sweep@2.0 | 60 | 0% | 100% | 0.54 |  |
- odoor@1.0 success>=0.6: 0.60 PASS (rechecked)
- odoor@1.5 success>=0.5: 0.33 FAIL
- guard:gap@1.0 success>=0.75: 0.90 PASS
- guard:mgap@1.0 success>=0.7: 0.85 PASS (rechecked)
- guard:cluttered crash<=0.05: 0.05 PASS (rechecked)
- guard:sweep@2.0 crash<=0.1: 0.00 PASS

**Gate verdict: continue**

### Researcher notes
(unattended run)

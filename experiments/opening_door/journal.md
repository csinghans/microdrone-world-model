
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

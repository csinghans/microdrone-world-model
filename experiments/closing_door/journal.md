
## K0 — the reactive baseline (privileged direction) on the door (2026-07-05 05:10 UTC)
Hypothesis: distance-triggered: expected to freeze at the fence or commit on stale width and get pinched — it can only lose on timing, which is exactly what the arena prices
Config: builtin:reactive

| cell | n | crash | success | clearance | custom |
|---|---|---|---|---|---|
| door@1.0 | 30 | 17% | 83% | 0.32 | threaded=0.83 pinched=0.17 froze=0.00 door_margin=0.22 |
| door@1.5 | 30 | 60% | 40% | 0.18 | threaded=0.40 pinched=0.60 froze=0.00 door_margin=0.12 |
| guard:gap@1.0 | 30 | 17% | 83% | 0.31 | transited=1.00 gap_margin=0.19 |
| guard:mgap@1.0 | 30 | 23% | 75% | 0.32 | transited=0.92 gap_margin=0.22 |
| guard:cluttered | 60 | 3% | 97% | 0.52 |  |
| guard:sweep@2.0 | 60 | 48% | 52% | 0.23 |  |
- door@1.0 success>=0.7: 0.83 PASS (rechecked)
- door@1.5 success>=0.55: 0.40 FAIL
- guard:gap@1.0 success>=0.75: 0.83 PASS (rechecked)
- guard:mgap@1.0 success>=0.7: 0.75 PASS (rechecked)
- guard:cluttered crash<=0.05: 0.03 PASS (rechecked)
- guard:sweep@2.0 crash<=0.1: 0.48 FAIL

**Gate verdict: guard_regression**

### Researcher notes
(unattended run)

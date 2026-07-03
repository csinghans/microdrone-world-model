
## K0 — the v0.3 champion, zero-shot on the gap (2026-07-03 10:34 UTC)
Hypothesis: expected honest failure: it was never asked to fly toward saturated warn rings
Config: output/ppo_wm_policy_edge_hard_xp.zip

| cell | n | crash | success | clearance | custom |
|---|---|---|---|---|---|
| gap@1.0 | 30 | 63% | 27% | 0.18 | transited=0.37 gap_margin=0.04 |
| gap@1.5 | 30 | 63% | 23% | 0.20 | transited=0.40 gap_margin=0.06 |
| guard:cluttered | 60 | 3% | 0% | 0.54 |  |
| guard:sweep@1.0 | 30 | 0% | 0% | 0.68 |  |
| guard:sweep@1.5 | 30 | 0% | 0% | 0.68 |  |
| guard:sweep@2.0 | 30 | 2% | 0% | 0.65 |  |
- gap@1.0 success>=0.85: 0.27 FAIL
- gap@1.5 success>=0.7: 0.23 FAIL
- guard:cluttered crash<=0.05: 0.03 PASS (rechecked)
- guard:sweep@1.0 crash<=0.05: 0.00 PASS (rechecked)
- guard:sweep@1.5 crash<=0.1: 0.00 PASS
- guard:sweep@2.0 crash<=0.1: 0.02 PASS (rechecked)

**Gate verdict: continue**

### Researcher notes
The pre-registered failure arrived, but with a more interesting shape than
predicted: no hover-collapse (reached 100 % in both cells — the KR-shaping
trigger is NOT met). The champion *charges* the fence: 63 % of runs clip a
pillar on the way through, and the 37 % that find the opening scrape it
with a 0.04 m margin — consistent with warn-ring saturation drowning the
gap's location while the crit heads (which do see it) never learned to
steer this geometry. Guards all green: the failure is specific to the new
skill, not a regression. This is a data problem, exactly what K1 tests:
put the fence in the training diet and let the crit-ring gradient teach
the transit. Proceeding to K1 as scheduled.

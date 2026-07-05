
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

## K1 — classic x2 on the KD1 chassis (2026-07-05 02:26 UTC)
Hypothesis: share starvation: classic fell from the champion diet's 25 % to 20 %; restoring it to 33 % should heal its fast band with it
Config: {"worlds": ["classic", "classic", "dense", "moving", "gap", "moving_gap"], "x_progress": true, "edge_bias": true, "timesteps": 900000}

| cell | n | crash | success | clearance | custom |
|---|---|---|---|---|---|
| mgap@1.0 | 30 | 33% | 67% | 0.26 | transited=0.90 gap_margin=0.12 |
| mgap@1.5 | 30 | 23% | 77% | 0.31 | transited=0.93 gap_margin=0.15 |
| guard:gap@1.0 | 30 | 7% | 93% | 0.43 | transited=0.93 gap_margin=0.27 |
| guard:cluttered | 60 | 2% | 98% | 0.44 |  |
| guard:sweep@1.0 | 30 | 0% | 100% | 0.46 |  |
| guard:sweep@1.5 | 30 | 0% | 100% | 0.49 |  |
| guard:sweep@2.0 | 60 | 0% | 100% | 0.38 |  |
- mgap@1.0 success>=0.75: 0.67 FAIL
- mgap@1.5 success>=0.6: 0.77 PASS
- guard:gap@1.0 success>=0.75: 0.93 PASS
- guard:cluttered crash<=0.05: 0.02 PASS (rechecked)
- guard:sweep@1.0 crash<=0.05: 0.00 PASS (rechecked)
- guard:sweep@1.5 crash<=0.1: 0.00 PASS
- guard:sweep@2.0 crash<=0.1: 0.00 PASS (rechecked)

**Gate verdict: continue**

### Researcher notes
(unattended run)

## K2 — an explicit solo world on the KD1 chassis (2026-07-05 03:11 UTC)
Hypothesis: the bleeding cell is fast+solo geometry; edge-bias already over-samples fast, so a solo world aims it at the wound
Config: {"worlds": ["classic", "dense", "moving", "gap", "moving_gap", "solo"], "x_progress": true, "edge_bias": true, "timesteps": 900000}

| cell | n | crash | success | clearance | custom |
|---|---|---|---|---|---|
| mgap@1.0 | 30 | 47% | 53% | 0.25 | transited=0.80 gap_margin=0.11 |
| mgap@1.5 | 30 | 10% | 90% | 0.34 | transited=0.97 gap_margin=0.20 |
| guard:gap@1.0 | 30 | 10% | 90% | 0.40 | transited=0.90 gap_margin=0.25 |
| guard:cluttered | 60 | 0% | 100% | 0.54 |  |
| guard:sweep@1.0 | 30 | 0% | 98% | 0.64 |  |
| guard:sweep@1.5 | 30 | 2% | 98% | 0.50 |  |
| guard:sweep@2.0 | 60 | 3% | 95% | 0.45 |  |
- mgap@1.0 success>=0.75: 0.53 FAIL
- mgap@1.5 success>=0.6: 0.90 PASS
- guard:gap@1.0 success>=0.75: 0.90 PASS
- guard:cluttered crash<=0.05: 0.00 PASS (rechecked)
- guard:sweep@1.0 crash<=0.05: 0.00 PASS (rechecked)
- guard:sweep@1.5 crash<=0.1: 0.02 PASS (rechecked)
- guard:sweep@2.0 crash<=0.1: 0.03 PASS (rechecked)

**Gate verdict: continue**

### Researcher notes
(unattended run)

## K3 — classic x2 + solo (the combination) (2026-07-05 03:58 UTC)
Hypothesis: played only if K1/K2 each move the fast cell without clearing it; the mgap-share dilution risk is priced by v1's target headroom
Config: {"worlds": ["classic", "classic", "dense", "moving", "gap", "moving_gap", "solo"], "x_progress": true, "edge_bias": true, "timesteps": 900000}

| cell | n | crash | success | clearance | custom |
|---|---|---|---|---|---|
| mgap@1.0 | 30 | 15% | 85% | 0.32 | transited=0.98 gap_margin=0.17 |
| mgap@1.5 | 30 | 7% | 93% | 0.35 | transited=1.00 gap_margin=0.20 |
| guard:gap@1.0 | 30 | 10% | 90% | 0.41 | transited=0.90 gap_margin=0.24 |
| guard:cluttered | 60 | 5% | 95% | 0.38 |  |
| guard:sweep@1.0 | 30 | 0% | 100% | 0.38 |  |
| guard:sweep@1.5 | 30 | 0% | 100% | 0.46 |  |
| guard:sweep@2.0 | 60 | 0% | 100% | 0.54 |  |
- mgap@1.0 success>=0.75: 0.85 PASS (rechecked)
- mgap@1.5 success>=0.6: 0.93 PASS
- guard:gap@1.0 success>=0.75: 0.90 PASS
- guard:cluttered crash<=0.05: 0.05 PASS (rechecked)
- guard:sweep@1.0 crash<=0.05: 0.00 PASS (rechecked)
- guard:sweep@1.5 crash<=0.1: 0.00 PASS
- guard:sweep@2.0 crash<=0.1: 0.00 PASS

**Gate verdict: passed**

### Researcher notes
(unattended run)

## Researcher notes — the campaign verdict (2026-07-05)

**PASSED at K3 — the moving-gap catalog entry has its champion:**
`artifacts/ppo_moving_gap_v2_K3.zip` (classic×2 + solo + the five-world
KD1 chassis, 900 k). All seven criteria green, including the cell that
closed v1: **sweep@2.0 at 0 % (n=60)**, clearance 0.54 m — from v1's
confirmed 17 %.

The instructive part is that *both* shape hypotheses were half right:

- K1 (classic×2) healed every guard — and starved the skill
  (mgap@1.0 67 %). K2 (solo world) healed every guard — and starved it
  worse (53 %). Each fix alone pays for home turf with the very
  training share the new skill needed.
- K3's combination passed everything at once, and its pre-registered
  risk (mgap diluted to ~14 % of episodes) did not materialize —
  mgap@1.0 read 73 % at n=30 and **85 % at the n=60 recheck**, well
  clear of the 75 % bar. A broader base diet apparently costs the
  timing skill less than either narrow supplement did; why is not
  measured here and stays a hypothesis.
- v1's KD1 re-measured as K0 reproduced its close-out signature
  (fast-solo guard regression) on v2's n=60 cell — the two campaigns
  agree across the version boundary.

Sixth sighting of the refrain, now with the constructive corollary:
the hole moves when you patch one band — and it *closes* when the diet
is broad enough to hold every band at once. Budget alone couldn't do
it (v1); shape alone couldn't either (K1/K2); shape × both axes did.

**Catalog promotion:** moving-gap joins gap-flight as a passed skill
(2/2 campaigns to a green gate via the autonomous runner + one
researcher deviation each). The *general* champion is untouched — this
campaign never measured dense/moving cells, so no claim crosses that
line without its own line-up eval.

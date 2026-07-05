
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

## K3 — door_open joins the v2-combination diet (2026-07-05 07:33 UTC)
Hypothesis: PPO must discover hold-then-thread (hover is in the action set; it has just never been the winning move at a fence)
Config: {"worlds": ["classic", "classic", "dense", "moving", "gap", "moving_gap", "solo", "opening_door"], "x_progress": true, "edge_bias": true, "timesteps": 900000}

| cell | n | crash | success | clearance | custom |
|---|---|---|---|---|---|
| odoor@1.0 | 30 | 30% | 70% | 0.32 | threaded=0.70 pinched=0.30 froze=0.00 door_margin=0.21 wait_time=0.76 |
| odoor@1.5 | 30 | 40% | 60% | 0.28 | threaded=0.60 pinched=0.40 froze=0.00 door_margin=0.15 wait_time=0.57 |
| guard:gap@1.0 | 30 | 7% | 93% | 0.42 | transited=0.93 gap_margin=0.26 |
| guard:mgap@1.0 | 30 | 28% | 72% | 0.29 | transited=0.93 gap_margin=0.15 |
| guard:cluttered | 60 | 0% | 100% | 0.53 |  |
| guard:sweep@2.0 | 60 | 13% | 87% | 0.52 |  |
- odoor@1.0 success>=0.6: 0.70 PASS
- odoor@1.5 success>=0.5: 0.60 PASS
- guard:gap@1.0 success>=0.75: 0.93 PASS
- guard:mgap@1.0 success>=0.7: 0.72 PASS (rechecked)
- guard:cluttered crash<=0.05: 0.00 PASS (rechecked)
- guard:sweep@2.0 crash<=0.1: 0.13 FAIL (rechecked)

**Gate verdict: guard_regression**

### Researcher notes
(unattended run)

## Researcher notes — campaign close: capability yes, promotion no (2026-07-05)

**The capability is real and the instrument saw it form.** `wait_time`
climbed the anticipation spectrum exactly as designed — reactive 0.07 s
(charges the shut door, 83-100 % pinched), hand MPC 0.31 s, the mgap
champion 0.66 s (and a zero-shot PASS of the @1.0 bar at its n=60
recheck: WHERE-timing partially buys WHEN-timing — better than the
frozen hypothesis predicted), and K3's trained policy 0.76/0.57 s with
**both targets passing (70 % / 60 %)**: PPO discovered hold-then-thread,
confirming K3's hypothesis.

**No promotion**: guard:sweep@2.0 confirmed 13 % vs ≤10 % at n=60 —
the perennial cell, whose measured history now reads 27/22/8/17/0/13
across two campaigns and six contexts. v1 proved budget does not
control it (non-monotone); v2 proved mixture *shape* can hold it at
0 % — and this campaign shows each newly added timing world re-taxes it
a few points. A further deviation here, before that cell's sampling
distribution is characterized, would be fishing. The backlog's
"sweep@2.0 noise characterization" (docs/RESEARCH-IDEAS.md) is hereby
promoted from a ★★ idea to the *prerequisite* for ever adjudicating
this guard again.

**Two findings beyond the bars:**

- **froze = 0.00 in every cell of every knob — in BOTH door arenas.**
  Eight arena-cells of evidence that freezing is not a natural failure
  mode of this action set: policies charge, they do not hesitate. The
  hesitation-vs-commitment axis is real, but its failure mass sits
  entirely on the commitment side.
- **The harness class caught mid-campaign is fixed at the schema layer:**
  K3's first launch died on a diet world (`solo`) registered only by
  another skill's module — exit 1, gate unrecorded, textbook harness
  error (rerun unchanged after the tool fix). `_validate` now resolves
  every knob's diet worlds at load; closing-door's identical latent
  mine (its never-played K4) was defused by the same commit.

**Dogfood verdict (this campaign doubled as the onboarding stack's
first live exercise):** idea consumed from the backlog as written;
scaffolded by `new_skill`; operator mode executed K0-K2 and the
authorized K3 with fixed-format reports and stopped at exactly the two
designed seams (training-knob authorization, harness error). The lane
works.

## Promotion gate — pre-registered before it flies (2026-07-05)

Authorized by the maintainer following the sweep2_noise calibration.
One shot, no retries: the K3 artifact
(`artifacts/ppo_opening_door_K3.zip`, sha 1cfdcebac9a325d7) flies every
v1 cell at **n=200** (CI half-width ≈ ±3.2 pt at p≈0.06 — inside the
inheritance table's resolution) on the fresh, never-used seed block
20000, judged with the skill's own predicates
(`eval_policy_cells --skill opening-door`). Bars are v1's, verbatim:

| cell | bar |
|---|---|
| odoor@1.0 success | ≥ 0.60 |
| odoor@1.5 success | ≥ 0.50 |
| guard:gap@1.0 success | ≥ 0.75 |
| guard:mgap@1.0 success | ≥ 0.70 |
| guard:cluttered crash | ≤ 0.05 |
| guard:sweep@2.0 crash | ≤ 0.10 |

All six pass → K3 is the opening-door champion. Any bar fails → the
title stays open and THIS measurement is final (no further shots at
n=200; a failed promotion is an honest negative like any other). The
campaign's original gate verdict remains on the record either way —
this gate exists because a strictly stronger instrument became
available, not because we disliked the old verdict.

(appended when the numbers land)


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

## K1 — the hand latent-MPC on the door (2026-07-05 05:10 UTC)
Hypothesis: expected to decline at the saturated warn wall (the gap-flight K0 signature) — anticipating but margin-bound
Config: builtin:wm_mpc

| cell | n | crash | success | clearance | custom |
|---|---|---|---|---|---|
| door@1.0 | 30 | 63% | 33% | 0.17 | threaded=0.33 pinched=0.63 froze=0.00 door_margin=0.08 |
| door@1.5 | 30 | 80% | 17% | 0.15 | threaded=0.17 pinched=0.80 froze=0.00 door_margin=0.04 |
| guard:gap@1.0 | 30 | 60% | 40% | 0.19 | transited=0.87 gap_margin=0.15 |
| guard:mgap@1.0 | 30 | 57% | 43% | 0.21 | transited=0.83 gap_margin=0.14 |
| guard:cluttered | 60 | 37% | 63% | 0.36 |  |
| guard:sweep@2.0 | 60 | 20% | 80% | 0.51 |  |
- door@1.0 success>=0.7: 0.33 FAIL
- door@1.5 success>=0.55: 0.17 FAIL
- guard:gap@1.0 success>=0.75: 0.40 FAIL
- guard:mgap@1.0 success>=0.7: 0.43 FAIL
- guard:cluttered crash<=0.05: 0.37 FAIL
- guard:sweep@2.0 crash<=0.1: 0.20 FAIL

**Gate verdict: guard_regression**

### Researcher notes
(unattended run)

## K2 — the general champion (edge_hard_xp), zero-shot (2026-07-05 05:11 UTC)
Hypothesis: never dieted on fences; expected to hard-charge like gap K0
Config: output/ppo_wm_policy_edge_hard_xp.zip

| cell | n | crash | success | clearance | custom |
|---|---|---|---|---|---|
| door@1.0 | 30 | 23% | 10% | 0.33 | threaded=0.10 pinched=0.23 froze=0.00 door_margin=0.01 |
| door@1.5 | 30 | 20% | 0% | 0.29 | threaded=0.00 pinched=0.20 froze=0.00 door_margin=0.00 |
| guard:gap@1.0 | 30 | 63% | 27% | 0.18 | transited=0.37 gap_margin=0.04 |
| guard:mgap@1.0 | 30 | 67% | 23% | 0.19 | transited=0.30 gap_margin=0.06 |
| guard:cluttered | 60 | 3% | 97% | 0.54 |  |
| guard:sweep@2.0 | 60 | 2% | 98% | 0.65 |  |
- door@1.0 success>=0.7: 0.10 FAIL
- door@1.5 success>=0.55: 0.00 FAIL
- guard:gap@1.0 success>=0.75: 0.27 FAIL
- guard:mgap@1.0 success>=0.7: 0.23 FAIL
- guard:cluttered crash<=0.05: 0.03 PASS (rechecked)
- guard:sweep@2.0 crash<=0.1: 0.02 PASS (rechecked)

**Gate verdict: guard_regression**

### Researcher notes
(unattended run)

## K3 — the moving-gap v2 champion, zero-shot (2026-07-05 05:12 UTC)
Hypothesis: the best predictive contender on paper: gap-trained and motion-trained — but it has never seen an aperture *shrink*
Config: experiments/moving_gap_v2/artifacts/ppo_moving_gap_v2_K3.zip

| cell | n | crash | success | clearance | custom |
|---|---|---|---|---|---|
| door@1.0 | 30 | 7% | 93% | 0.32 | threaded=0.93 pinched=0.07 froze=0.00 door_margin=0.17 |
| door@1.5 | 30 | 13% | 87% | 0.34 | threaded=0.87 pinched=0.13 froze=0.00 door_margin=0.18 |
| guard:gap@1.0 | 30 | 10% | 90% | 0.41 | transited=0.90 gap_margin=0.24 |
| guard:mgap@1.0 | 30 | 15% | 85% | 0.32 | transited=0.98 gap_margin=0.17 |
| guard:cluttered | 60 | 5% | 95% | 0.38 |  |
| guard:sweep@2.0 | 60 | 0% | 100% | 0.54 |  |
- door@1.0 success>=0.7: 0.93 PASS
- door@1.5 success>=0.55: 0.87 PASS
- guard:gap@1.0 success>=0.75: 0.90 PASS
- guard:mgap@1.0 success>=0.7: 0.85 PASS (rechecked)
- guard:cluttered crash<=0.05: 0.05 PASS (rechecked)
- guard:sweep@2.0 crash<=0.1: 0.00 PASS

**Gate verdict: passed**

### Researcher notes
(unattended run)

## Researcher notes — the duel verdict (2026-07-05)

**PASSED at K3, zero-shot — K4 (training) never needed to run.** The
moving-gap v2 champion cleared every bar on an aperture it never
trained on: door 93 % / 87 % threaded, all guards green (fast-solo 0 %
at n=60). The v2 broad diet bought out-of-distribution *timing*
generalization — a shrinking door is neither a static gap nor a sliding
one, and the policy threads it anyway. The closing-door catalog entry's
champion is therefore a cross-skill zip: `ppo_moving_gap_v2_K3.zip`.

**The duel table (the campaign's product):**

| contender | door@1.0 threaded | door@1.5 threaded | signature |
|---|---|---|---|
| K0 reactive (privileged) | 83 % | **40 %** (60 % pinched) | fine at cruise, dies with speed — the distance-budget cliff, live (also 48 % crash on fast-solo) |
| K1 hand latent-MPC | 33 % | 17 % (63-80 % pinched) | charges and gets crushed everywhere (broken-margins era, measured again) |
| K2 general champion | 10 % | 0 % | **detours around the fence** (reaches without threading) — no door concept in its diet |
| K3 mgap v2 champion | **93 %** | **87 %** | commits earliest on the overlay; threads with 0.17-0.18 m margin |

**Pre-registered hypothesis audit (two wrong, one half-wrong, one
right — recorded, not buried):**

- "reactive freezes or gets pinched" — HALF WRONG: it never froze
  (froze = 0.00 in every cell for every contender; the fence never
  froze anyone). At cruise it *threaded 83 %* — with privileged
  direction and a still-open ~0.8 m aperture, wiggling through
  reactively works. The separation is at **speed**, exactly where the
  distance-budget physics says it must be.
- "hand MPC declines at the saturated warn wall" — WRONG: it committed
  and got pinched (63-80 %). The gap-flight K0 signature did not
  transfer to this model+margin combination.
- "general champion hard-charges" — WRONG: it goes *around* (its
  home-turf evasion generalizes to treating the whole fence as one
  obstacle). `transited` catches the detour honestly: reached ≠ success.
- "mgap champion best zero-shot" — RIGHT, and stronger than predicted:
  it didn't just lead the duel, it cleared the whole gate.

**One instrument note:** the `froze` metric never fired — worth keeping
(its zero is informative: this arena punishes commitment errors, not
hesitation), but future duel arenas that want to price hesitation need
a scenario where waiting is tempting (e.g. an *opening* door).

Figures: `duel_outcomes.png` (the four-bar verdict), 
`duel_trajectories.png` (same seed 9800, all four paths; K3 commits
earliest — anticipation visible to the naked eye).

### Addendum (2026-07-05): per-seed timelines

`duel_timeline_door_10.png` / `duel_timeline_door_15.png` (from the new
`eval_duel_plots --timelines`): the outcome grid shows which courses
kill whom; the crossing-time strip shows each contender's commit-time
distribution. Note: timelines re-fly the cells for per-episode data —
they are a diagnostic view, not the gate record.

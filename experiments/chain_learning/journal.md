# chain-learning — the slalom wall, attacked on the RL side

## Pre-registration (2026-07-06, before any number exists)

The horizon campaign (`experiments/horizon/journal.md`) closed the
model axis: with the arena flyable (oracle 0.97) and per-gate
competence learnable, the chain has now survived **diet** (v1/v2),
**budget** (1350k), **fixed rhythm** (v2 K1) and **observation
horizon** (k=48 = 1.0 s > the 0.875 s gate period). The suspect list
is RL-side: credit assignment (success is distal), exploration (chains
sampled at 0-3 % — too rare to reinforce), reward structure
(progress+crash is indifferent to setup positioning).

**Design: a 2x2 factorial** on the shared 900k chassis
(x_progress + edge_bias, the v2-combination diet), pinned against
corridor-slalom-v2 K1 — the already-gated "neither" cell:

| cell | gate reward | graded diet | knob |
|---|---|---|---|
| neither | – | – | v2 K1 (gated 2026-07-05) |
| reward | gate_bonus=8.0 | – | **K1** |
| diet | – | +slalom2_fixed | **K2** |
| both | gate_bonus=8.0 | +slalom2_fixed | **K3** (unconditional — the factorial is only complete with it) |

Mechanism shipped for K1/K3: `WMPolicyEnv(gate_bonus=)` pays 8.0 once
per fence threaded, judged by `gate_bonus_hits` — a pure function that
mirrors `slalom_metrics` inequality-for-inequality (same
(w+2·PILLAR_R)/2 band, same first-crossing interpolation; any first
crossing spends the fence, so detours cannot circle back for the
money). `gate_bonus=0.0` (every existing recipe) is bit-identical to
the old env. Legality under the no-hand-tuned-danger-weights rule:
this is task-structure reward (the category of the existing +50 goal /
-30 crash / 25x progress constants), computed from privileged sim
geometry at training time only — it changes what we ask for, not what
the drone sees. Magnitude frozen at 8.0 (≈ half the 17.5 inter-gate
progress payout; 3 gates = 24 < the goal's 50, so finishing still
dominates). One value, no sweep: if 8.0 fails, the knob fails.

**Frozen campaign signature.** Support: any knob moves slalom3@1.0
`chain_break_at` ≥ 2.5 (mean, n=30). Full support: success ≥ 0.70
(the probe-priced bar, unchanged). **Refuted:** all three knobs land
chain_break_at < 2.5 with success < 0.10 and the trainings completing
— then reward- and diet-altitude RL fixes are eliminated too, and the
remaining suspects escalate to algorithm-class surgery (policy memory,
n_steps/GAE, algorithm swap) as a separate future campaign. A
frac-up-break-flat reading on K1/K3 is *not* support — it means the
bonus inflated attempts without buying chains (reward hacking is
contained by judging only the unchanged exam bars).

**Baselines (already gated, same exam cells, seed0 22000):**

| stack | success | weave_frac | chain_break_at |
|---|---|---|---|
| v2 K0 (v1 best zip) | 0.00 | 0.82 | 2.10 |
| v2 K1 (900k chassis = this campaign's control) | 0.00 | 0.72 | 1.33 |
| v2 K2 (1350k) | 0.00 | 0.82 | 2.03 |
| h48 (k=48 stack) | 0.03 | 0.62 | 1.47 |

diag:slalom2@1.0 baselines: success 0.10 / 0.13 / 0.20 / 0.10,
chain_break 1.50 / 1.63 / 1.70 / 1.13 (same order). For K2/K3,
diag:slalom2 becomes an in-diet read (its world is in their training
mix) — expected to rise; the science cell stays slalom3@1.0.

**Honest confound, K2:** +slalom2_fixed also raises total slalom share
(2/9 vs 1/8). v1's share-doubling knob got worse and broke a guard, so
a K2 win reads as gradation-not-share only weakly; K3 and the
diag:slalom2 trajectory help separate.

**Guards:** the standard catalog block, pooled rechecks per the
2026-07-05 protocol. Dilution expectation on the record: 8-world diets
have broken guard:mgap three times (v2 K1 85→57-70 % family, h48); a
recurrence blocks promotion as always but does not touch the science
signature.

**Cost estimate:** 3 × 900k ≈ 3 × 4-6 h training + exams ≈ 15-20 h
unattended (`scripts.research run`, gate commits per knob).

**Manipulation check (harness verification, not a measurement,
2026-07-06):** a scripted bang-bang driver with privileged fences and a
0.05 m plane lead, inside the real training env
(`WMPolicyEnv(worlds=("slalom3_fixed",), gate_bonus=8.0)`): the bonus
fired on 3 decisions across 6 episodes — the env receives the fences
from scenario meta, `gate_bonus_hits` pays on threading, and the reward
sees it. Wiring proven before any training spend; the pure-function ↔
exam-metric agreement is soul-asserted in the skill selftest (CI).

## K1 — per-gate task reward (gate_bonus=8.0) on the v2-K1 recipe (2026-07-05 22:17 UTC)
Hypothesis: if distal credit is the wall, proximal gate pay concentrates advantage on rare chains and chain_break_at moves first
Config: {"worlds": ["classic", "classic", "dense", "moving", "gap", "moving_gap", "solo", "slalom3_fixed"], "gate_bonus": 8.0, "x_progress": true, "edge_bias": true, "timesteps": 900000}

| cell | n | crash | success | clearance | custom |
|---|---|---|---|---|---|
| slalom3@1.0 | 30 | 70% | 7% | 0.15 | weaved=0.07 weave_frac=0.78 chain_break_at=1.73 |
| diag:slalom2@1.0 | 30 | 77% | 13% | 0.16 | weaved=0.13 weave_frac=0.75 chain_break_at=1.50 |
| diag:slalom3@1.25 | 30 | 83% | 3% | 0.13 | weaved=0.03 weave_frac=0.72 chain_break_at=1.47 |
| guard:gap@1.0 | 30 | 7% | 93% | 0.44 | transited=0.93 gap_margin=0.26 |
| guard:mgap@1.0 | 90 | 32% | 67% | 0.25 | transited=0.91 gap_margin=0.10 |
| guard:cluttered | 120 | 2% | 98% | 0.52 |  |
| guard:sweep@2.0 | 120 | 3% | 97% | 0.53 |  |
- slalom3@1.0 success>=0.7: 0.07 FAIL
- guard:gap@1.0 success>=0.75: 0.93 PASS
- guard:mgap@1.0 success>=0.7: 0.67 FAIL (rechecked)
- guard:cluttered crash<=0.05: 0.03 PASS (rechecked)
- guard:sweep@2.0 crash<=0.1: 0.03 PASS (rechecked)

**Gate verdict: guard_regression**

### Researcher notes
(unattended run)

## K2 — graded diet: slalom2_fixed added to the v2-K1 recipe (2026-07-05 23:09 UTC)
Hypothesis: 2-gate chains succeed often enough to reinforce; the reversal should transfer (share confound stated in the pre-registration)
Config: {"worlds": ["classic", "classic", "dense", "moving", "gap", "moving_gap", "solo", "slalom2_fixed", "slalom3_fixed"], "x_progress": true, "edge_bias": true, "timesteps": 900000}

| cell | n | crash | success | clearance | custom |
|---|---|---|---|---|---|
| slalom3@1.0 | 30 | 93% | 0% | 0.10 | weaved=0.00 weave_frac=0.80 chain_break_at=1.97 |
| diag:slalom2@1.0 | 30 | 87% | 10% | 0.16 | weaved=0.10 weave_frac=0.80 chain_break_at=1.60 |
| diag:slalom3@1.25 | 30 | 93% | 0% | 0.11 | weaved=0.00 weave_frac=0.80 chain_break_at=1.90 |
| guard:gap@1.0 | 30 | 10% | 83% | 0.38 | transited=0.83 gap_margin=0.21 |
| guard:mgap@1.0 | 90 | 27% | 72% | 0.29 | transited=0.94 gap_margin=0.14 |
| guard:cluttered | 120 | 5% | 95% | 0.39 |  |
| guard:sweep@2.0 | 120 | 10% | 89% | 0.40 |  |
- slalom3@1.0 success>=0.7: 0.00 FAIL
- guard:gap@1.0 success>=0.75: 0.83 PASS
- guard:mgap@1.0 success>=0.7: 0.72 PASS (rechecked)
- guard:cluttered crash<=0.05: 0.05 PASS (rechecked)
- guard:sweep@2.0 crash<=0.1: 0.10 PASS (rechecked)

**Gate verdict: continue**

### Researcher notes
(unattended run)

## K3 — both: gate reward + graded diet (the interaction cell) (2026-07-06 00:02 UTC)
Hypothesis: played unconditionally — the factorial is only complete with it; a K3-only win means the axes help jointly, not alone
Config: {"worlds": ["classic", "classic", "dense", "moving", "gap", "moving_gap", "solo", "slalom2_fixed", "slalom3_fixed"], "gate_bonus": 8.0, "x_progress": true, "edge_bias": true, "timesteps": 900000}

| cell | n | crash | success | clearance | custom |
|---|---|---|---|---|---|
| slalom3@1.0 | 30 | 97% | 0% | 0.11 | weaved=0.00 weave_frac=0.73 chain_break_at=1.80 |
| diag:slalom2@1.0 | 30 | 67% | 20% | 0.19 | weaved=0.20 weave_frac=0.75 chain_break_at=1.50 |
| diag:slalom3@1.25 | 30 | 97% | 0% | 0.10 | weaved=0.00 weave_frac=0.81 chain_break_at=2.00 |
| guard:gap@1.0 | 30 | 10% | 83% | 0.40 | transited=0.87 gap_margin=0.24 |
| guard:mgap@1.0 | 30 | 13% | 87% | 0.32 | transited=0.97 gap_margin=0.17 |
| guard:cluttered | 120 | 4% | 96% | 0.42 |  |
| guard:sweep@2.0 | 120 | 2% | 98% | 0.49 |  |
- slalom3@1.0 success>=0.7: 0.00 FAIL
- guard:gap@1.0 success>=0.75: 0.83 PASS
- guard:mgap@1.0 success>=0.7: 0.87 PASS
- guard:cluttered crash<=0.05: 0.04 PASS (rechecked)
- guard:sweep@2.0 crash<=0.1: 0.02 PASS (rechecked)

**Gate verdict: continue**

### Researcher notes
(unattended run)

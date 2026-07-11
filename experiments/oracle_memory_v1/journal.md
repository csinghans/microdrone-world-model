# oracle_memory_v1 — is MEMORY the dense frontier's binding constraint?

**Opened:** 2026-07-12 · **Owner:** Hans · **Source:** docs/REVIEW-2026-07.md
(C5 Phase-0 — "the gate before the gate"; the quarter's strategic probe)

## The question

The dense transit frontier (crash 17–27 %, `docs/ROADMAP.md` open item
2) has survived metric grounding, calibration fixes, and every policy
knob. The review's thesis says the remaining axis is TIME: the
champion's residual deaths at speed are FOV-edge side clutter — 13/14
at ×2.0 (`experiments/dense_speedrun/`) — things that **slid out of
view**. The proposed cure (temporal_wm_v1: a model-side GRU at 5–10×
data) is the horizon's one WM retrain and its most expensive campaign.
Before a single epoch: **if a drone with PERFECT memory of what it has
seen cannot beat the frontier, memory is not the binding constraint and
the retrain dies for free.** This is the house oracle move
(slalom_feasibility, wm48's kinematics oracle) applied to the most
expensive question on the board.

## Re-opening context (stated, since a GRU negative exists)

v0.2's model-side GRU was an honest negative (dense AUC 0.82→0.74 — "it
helped exactly where memory wasn't the constraint"), and the house rule
demands a mechanism argument to re-approach: (a) that judge was
single-seed model-axis AUC, an instrument later measured to spread
~0.5; (b) the failure signature now in hand (FOV-edge deaths) is
exactly out-of-frame information; (c) this probe judges at FLIGHT
level. The probe itself retrains nothing — it PRICES the information.

## Protocol (frozen before any number)

**Arms, identical seeds:** the transit champion policy
(`ppo_wm_policy_edge_hard_xp` on the champion WM — the frontier's
holder) vs the SAME policy wrapped in a privileged out-of-FOV memory
veto. Dense world, speed factor 1.5 (1.2 m/s — the 27 % frontier cell),
**n = 200 per arm**, `run_hard_episode`'s existing privileged hook
(`policy.pillars`, the same one the reactive baseline uses).

**The oracle wrapper (exact rule, frozen):** track every pillar that
has EVER been inside the camera cone (±28°, range ≤ 3.0 m) — "seen".
After the base policy decides, if any SEEN pillar is currently OUTSIDE
the cone, within 1.0 m, and the chosen action's planar velocity points
within ±35° of it → substitute the non-hover menu action whose
direction maximizes the minimum angle to all such threats. No hover
substitutions (stop-observe measured dead stops as OOD for continuous
champions); one-decision substitutions only; the base policy is
otherwise untouched. Interventions per flight are RECORDED — a no-fire
probe would be vacuous and is interpreted as such, not as a negative.

**Honest asymmetry, stated:** this veto is ONE crude use of perfect
memory — a PASS is strong evidence memory helps (even a crude
controller cashed it); a FAIL kills the cheap route and the named
justification, but a cleverer oracle controller could in principle be
proposed under a fresh registration. The review's framing stands: no
oracle win → no retrain.

## Pre-registered bars

| read | consequence |
|---|---|
| **Δcrash ≤ −0.05** (wrapped − base, pooled n=200/arm) | **memory IS binding** → releases the full temporal_wm_v1 pre-registration for the owner's GO/NO-GO (the retrain itself stays owner-gated) |
| Δcrash > −0.05 with a non-trivial intervention rate | **memory is NOT the binding constraint at this frontier** — temporal_wm_v1 dies before an epoch; the dense frontier's last named road becomes conditional recalibration |
| intervention rate ≈ 0 | probe vacuous by construction — recorded, redesign needed (not a negative) |

Guards: reached-rate must not collapse (wrapped ≥ base − 0.05); the
substitution must never be hover (asserted in the tool).

## Results (2026-07-12 — `eval_oracle_memory --probe`, probe_results.json)

| arm | crash | reached | min_clear | interventions/flight |
|---|---|---|---|---|
| champion (base) | 0.455 | 0.980 | — | — |
| champion + perfect memory | 0.420 | 0.985 | — | 3.4 |
| **Δcrash** | **−0.035** (bar ≤ −0.050) | guard ✓ | | non-vacuous ✓ |

Stable through the run (−0.045 at n=180, −0.035 at n=200). Honest note
on levels: this fresh seed block flies the cell at base 0.455, above
the historical 27–33 % — dense cells are measured to be seed-set
sensitive (`experiments/moving_gap/`'s lesson); the probe's PAIRED
same-seed Δ is the read, not the level.

## Verdict — memory is NOT the binding constraint; the retrain dies free

Perfect memory of every pillar ever seen, actively cashed 3.4 times per
flight by a steering veto, recovers **3.5 points of a 45.5 % crash
rate** — under the pre-registered 5-point release bar. Per the frozen
consequence table: **temporal_wm_v1 dies before a single epoch.** The
horizon's one planned WM retrain — the review's most expensive
campaign — is killed by a forty-minute probe.

Mechanism refinement the probe buys: the FOV-edge death signature
(13/14 at ×2.0) LOOKED memory-shaped, but knowing where the unseen
pillar is barely helps — in dense geometry at speed the failure is
closer to "no kinematically comfortable escape exists by the time any
signal fires" and "the evade itself creates the next conflict". That
re-points the dense frontier's last named road, conditional
recalibration (`docs/RESEARCH-IDEAS.md` deep water), and honestly
prices everything else: a temporal WM might still buy detection
elsewhere, but not THIS wall.

Asymmetry honored: a cleverer oracle controller could be proposed under
a fresh registration (this veto is one crude cashing of the
information); until someone pays that, the no-oracle-win → no-retrain
rule stands.

**The day's convergence, for the record:** person_pose_v1 disarmed the
pitch retrain; this probe kills the temporal retrain. The 12-month
program's two most expensive steps both died to cheap pre-registered
probes inside one day — the review's cheap-path discipline doing
exactly what it was written to do.

## Status

- [x] Pre-registration committed (this file, before any number)
- [x] Oracle wrapper + probe tool + selftest
- [x] n=200×2 read → **Δcrash −0.035 < bar; memory NOT binding;
      temporal_wm_v1 KILLED before an epoch; conditional recalibration
      is the dense frontier's last named road**

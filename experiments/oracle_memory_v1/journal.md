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

## Status

- [x] Pre-registration committed (this file, before any number)
- [ ] Oracle wrapper + probe tool + selftest
- [ ] n=200×2 read → the quarter's verdict

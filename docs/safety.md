# Safety

## Boundary

This project is for safety-focused autonomous navigation, collision
avoidance, education, and research. It does not support weaponization,
surveillance abuse, or evasion of safety/legal constraints. Contributions in
those directions are declined regardless of technical merit.

## Why a collision-avoidance repo talks about safety at all

The models here decide where a flying object goes. In simulation that risk
is zero; the moment the v0.6 hardware bridge lands, it is not. The rule is
that the safety envelope ships *before* the first free flight, not after
the first incident.

## The failsafe list (required for any flight demo)

| Guard | Sim status | Hardware requirement |
|---|---|---|
| Geofence | `planner.safety_filter` soft box (own odometry) | Hard box + altitude ceiling, enforced below the AI layer |
| Vertical envelope | vz commanded for altitude/floor search (`planner.nav_action_set` up/down) | Floor bound + capped descent rate near the ground, enforced below the AI layer — the near-surface / ground-effect regime is a sim-to-real unknown (`docs/sim_to_real.md`, lowfly_v1), so hardware must bound it independently |
| Imminent-collision backstop | `planner.safety_filter.imminent` | Same head, on-board, cannot be overridden by the policy |
| Manual override | `planner.authority` — the Level-3 assistance layer: pilot toggle to AUTO granted in ≤1 decision; a handback DURING danger is latched, granted after 12 clear decisions; imminent veto substitutes on the trigger decision (guardian_* rows) | RC/app kill-switch takes the link at any moment, BELOW the AI layer — the human kill stays above this whole machine |
| Emergency land | n/a | One command, spiral-descend, no AI in the loop |
| Low-battery behaviour | n/a | Land-now threshold with hysteresis, logged |
| Log replay | episode dicts (`eval.eval_closed_loop.run_episode`) | Full-flight black box, replayable against the sim |
| Field-test checklist | n/a | GO/NO-GO gate walked before every session |

Since 2026-07-12 the sim-gateable rows are EXECUTABLE — one
deterministic scenario each, asserted green:
`python -m eval.safety_selftest --all` (geofence steered into the
fence, forced-forward imminent veto, vertical envelope, capped-rate
emergency land, budget-return choreography, bit-exact log replay;
since the assisted chapter, four guardian rows: same-decision veto,
same-decision toggle-to-AUTO, the danger-latched handback, and the
geofence flown against a fence-seeking PILOT). The suite flies in
`scripts/gate.py`'s quick layer, so every whole-system scorecard
re-certifies it; the RC kill-switch and the GO/NO-GO checklist stay
honestly in the hardware column.

## Sensor requirements (measured in sim, priced axis by axis)

The beams8 safety ring's tolerance envelope, priced by delegating
proxies that perturb exactly what the safety filter reads while the
judge, the planner context and the beacon stay clean:

| axis | safe pocket | knee (collision crosses 0.05) | ledger |
|---|---|---|---|
| range noise σ | ≤ 0.05 m | σ = 0.10 | `experiments/beam_noise_v1/` |
| missed returns (read "far") | ≤ 5 % | p = 0.10 | `experiments/beam_noise_v1/` |
| report latency @ 0.6 m/s | ≲ 500 ms (~31 cm of stale geometry) | ~1 s | `experiments/beam_latency_v1/` (control-band caveat in the ledger) |

A VL53-class multiranger (σ < 5 cm, report latency in the tens of
milliseconds) sits an order of magnitude inside every pocket; the
binding axis for part selection is missed returns. Under every
perturbation find/return never moved — the ring feeds only the safety
veto, so these axes price SAFETY, not mission performance.

## Design principle

The safety filter wraps *every* policy — scripted, MPC, learned — behind the
same interface, so no future "smarter" policy can bypass it. Learned
components propose; the envelope disposes. The assisted chapter extends the
sentence: the pilot proposes, the envelope disposes — whether the pilot is
silicon or human. Within the assistance layer, safety holds the stick (a
mid-danger handback is latched, the AEB that will not release the brake
mid-event); above the layer, the human's hardware kill remains absolute.

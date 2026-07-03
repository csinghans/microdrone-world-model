# Safety

## Boundary

This project is for safety-focused autonomous navigation, collision
avoidance, education, and research. It does not support weaponization,
surveillance abuse, or evasion of safety/legal constraints. Contributions in
those directions are declined regardless of technical merit.

## Why a collision-avoidance repo talks about safety at all

The models here decide where a flying object goes. In simulation that risk
is zero; the moment the v0.4 hardware bridge lands, it is not. The rule is
that the safety envelope ships *before* the first free flight, not after
the first incident.

## The failsafe list (required for any flight demo)

| Guard | Sim status | Hardware requirement |
|---|---|---|
| Geofence | `planner.safety_filter` soft box (own odometry) | Hard box + altitude ceiling, enforced below the AI layer |
| Imminent-collision backstop | `planner.safety_filter.imminent` | Same head, on-board, cannot be overridden by the policy |
| Manual override | n/a | RC/app kill-switch takes the link at any moment |
| Emergency land | n/a | One command, spiral-descend, no AI in the loop |
| Low-battery behaviour | n/a | Land-now threshold with hysteresis, logged |
| Log replay | episode dicts (`eval.eval_closed_loop.run_episode`) | Full-flight black box, replayable against the sim |
| Field-test checklist | n/a | GO/NO-GO gate walked before every session |

## Design principle

The safety filter wraps *every* policy — scripted, MPC, learned — behind the
same interface, so no future "smarter" policy can bypass it. Learned
components propose; the envelope disposes.

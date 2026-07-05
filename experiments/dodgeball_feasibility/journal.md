# dodgeball feasibility — can this body afford station defense at all?

## Pre-registration (2026-07-06, frozen before any episode flies)

**Why.** Hans asked whether the drone can hover in place and dodge
objects thrown head-on at it. Honest audit: nothing in the catalog has
ever asked for this — no head-on movers in any diet, no station-keeping
objective anywhere, and the action set has no strafe and no backward
(veers are (0.5, ±0.5)). Before any bar exists, the arena lesson from
the slalom arc applies verbatim: price the physical ceiling with a
scripted oracle using the SAME action set, or the campaign post-mortem
cannot separate walls.

**The arithmetic that sized the arena** (derived, not tuned):

- A dodge must buy ~0.40 m of lateral miss (ball r 0.18 + COLLISION_R
  0.22); at veer slope 1.0 that costs ~0.40-0.45 m of forward drift,
  and no command ever brings x back.
- 3 aimed arrivals × 0.45 m + slack ≈ **1.9 m box budget** (station
  box x ∈ [−0.3, +1.9], |y| ≤ 1.2 — comfortably short of GOAL_X 3.0,
  so fleeing forward also ends the episode early and fails the
  full-length clause).
- Arrival times {4.0, 5.2, 6.4} s ± 0.25: the slowest ball (0.6 m/s,
  flight 3.67 s from 2.2 m) still launches at t > 0, and launch time =
  arrival − flight time per speed — **arrivals are equalized across
  the ball-speed axis; warning time is what varies, never threat
  count.** (First drafts with 4-5 arrivals from t=1.5 s were killed by
  this same arithmetic: negative launch times for slow balls and a
  budget the box could not hold. The geometry was fixed BEFORE flying,
  which is the whole point of deriving it.)

**Probe design** (`eval/eval_dodge_ceiling.py`, selftested): OracleDodge
holds station, differentiates live privileged snapshots into per-ball
velocities (teleport-alias clip at 1.5× nominal), and veers away from
the projected pass side ONLY when the projected miss < 0.45 m —
thrift is mandatory, every needless veer burns box budget. Grid:
ball_speed ∈ {0.6, 1.0, 1.4, 1.8} m/s at drone factor 1.0, n = 30
seeds per cell, seed0 31000. Judged by the skill's own
`dodge_success` (survive all 360 steps, never leave the box).

**Frozen selection formula** (the slalom-v2 formula, verbatim): cells
with oracle ceiling ≥ 0.55 get a campaign bar of **ceiling − 0.25**;
cells under 0.55 fly as measured-only diagnostics (no bar, recorded
never judged). No other rule may be invented after the table exists.

**The three walls, named now.** This probe removes exactly one:
1. **Arena** — is hover-veer-hover defense affordable under this body's
   drift arithmetic? (the probe's question)
2. **Perception** — the G1 model is single-frame and its diet's radial
   closure never exceeded drone-walking speeds toward static pillars;
   hover labels were learned in worlds where hovering is always safe.
   A head-on ball at 1.4-1.8 m/s asks the heads about motion they
   cannot represent from one frame. The policy-side 12-decision stacked
   history watching the probability ramp is the mechanism that could
   still extract closure — that IS the campaign's experiment.
3. **Policy/learning** — whatever the campaign's knobs measure after
   walls 1-2 are priced.

A high ceiling with a later learned-policy failure is therefore an
honest split verdict (perception or learning), not a design bug — the
slalom-v1 mistake ("could not separate arena from policy") upgraded to
a three-way separation, stated before any number exists.

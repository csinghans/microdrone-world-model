# search-room v1 — the smallest single-room proof (Phase 1a)

## Pre-registration (2026-07-07, before any gate number exists)

The first milestone of the Indoor Active Search Track (see
`docs/TRAINING-A-SKILL.md` sibling and the plan): can a micro-drone,
flying a translational 2D roaming vocabulary under a PRIVILEGED
geometric safety filter (Phase 1a isolates search strategy from
perception — the world model enters in Phase 1b), cover a single
enclosed room, sense an ABSTRACT beacon, and return home? And does a
coverage-planning strategy beat the null baseline?

**Frozen arena** (`sim/indoor/rooms.single_room`): 5x5 m walls, 2 box
obstacles (r 0.35), entry doorway mid -x wall at (-2, 0), hidden
beacon >= 3 m from start and clear of obstacles, sensor_range 1.5 m,
confirm_radius 0.4 m, coverage cell 0.5 m. Beacon sensed as
bearing+range within sensor_range (no detector — the abstract-beacon
ruling).

**Frozen seeds:** gate series seed0 = 110000, n = 30 (DISJOINT from
the 90000 tuning seeds used to debug the mechanics). max_decisions
1400. Borderline +/-0.08 -> one fresh block POOLED.

**Feasibility ceiling (measured before freezing, feasibility-first):**
the privileged Frontier explorer (BFS coverage planning + geometric
safety) on tuning seeds 90000-90007 scored find 1.00 / success 1.00 /
collision 0.00, coverage 0.70. The room is coverable, the beacon
findable, home reachable — bars are legitimate.

**Frozen bars — the SEARCH-ROOM gate (judged on the Frontier
strategy):**
- find_rate >= 0.85 (senses + confirms the beacon)
- return_rate | found >= 0.90 (gets home after finding)
- collision_rate <= 0.05 (the safety layer holds)
- steps_to_find(frontier) < steps_to_find(random) — coverage planning
  must beat the null walk (the strategy earns its keep)

**Baselines, same seeds:** random (momentum walk) / wall_follow
(SGBA-style) / frontier (BFS coverage). All three share the privileged
geometric safety filter and the SGBA beacon-approach once sensed, so
they differ ONLY in how they search before sensing.

**Verdict rule:** GREEN if Frontier clears all four bars. The honest
negative worth recording: if random finds as fast as frontier, the
room is too small for strategy to matter (shrink the sensor or grow
the room). Guards: the transit avoidance benchmark is structurally
isolated (own action set / scenario / runner) — a regression there
would be a bug, not a result; one existing skill gate is re-flown to
confirm zero cross-effect.

Cost: 3 strategies x 30 episodes, privileged safety, no training,
background.

## Verdict: strategy-beats-null SUPPORTED; the gate is RED on robustness (2026-07-07)

Baseline, n=30, gate seeds 110000 (disjoint from the 90000 tuning block):

| strategy | find | success | return\|found | coverage | collision | steps_to_find(med) |
|---|---|---|---|---|---|---|
| random | 0.133 | 0.067 | 0.500 | 0.503 | 0.533 | 168 |
| wall_follow | 0.800 | 0.667 | 0.833 | 0.731 | 0.333 | 105 |
| **frontier** | **0.900** | 0.700 | 0.778 | **0.762** | 0.167 | 121 |

**The core hypothesis SUPPORTED, decisively:** coverage-planning
frontier finds the beacon **0.90 vs random's 0.13** — a 6.8x lift —
and leads on coverage (0.76) and safety (collision 0.17 vs random
0.53). Wall-follow is a strong middle (find 0.80) and marginally
faster to first sight (105 vs 121 steps — it hugs the perimeter where
several beacons sit) but covers less and crashes twice as often. The
strategy layer earns its keep: **which way you search dominates the
outcome**, exactly the thing Phase 1a set out to measure.

**The SEARCH-ROOM gate is RED — on robustness, not search:**
- find_rate 0.90 >= 0.85 ✓ (borderline +0.05, moot below)
- steps_to_find(frontier 121) < random (168) ✓
- **return_rate|found 0.778 < 0.90 ✗**
- **collision_rate 0.167 > 0.05 ✗ (the hard fail)**

**The n=8 feasibility ceiling was a FRIENDLY BLOCK.** On the tuning
seeds the privileged Frontier read find 1.0 / success 1.0 /
collision 0.0; the fresh n=30 gate reads 0.90 / 0.70 / 0.167. This is
the repo's own recurring lesson (graduation must be judged at high n,
not a friendly first block — cf. the integration-suite n=30 promotion
that fell at n=100) re-applied to a new track. The mechanics were
tuned against the 8 friendly seeds and the gate caught the overfit.
Recorded, not re-rolled.

**Where the crashes come from (diagnostic):** a single global
`BRAKE_DIST` cannot both avoid freezing (0.8 m stalled the drone) and
avoid brushing (0.35 m lets ~1-in-6 episodes clip a corner) — the
coarse cardinal motion at 0.6 m/s overshoots on the tight side. The
homing return also stalls ~22 % (BFS routes exist but the same
brush-or-freeze tension bites on the way home).

**Named successor (fresh pre-registration, fresh seeds — NOT a
re-tune of this gate): search_room_v2.** Hypothesis: a GRADED safety
filter — command `slow` (already in the nav vocabulary, off the
coverage menu) when clearance is marginal, and veto only when a crash
is imminent — drives collision under 0.05 without the freeze, because
it decouples "slow down near obstacles" from "stop exploring". Phase
1b (world-model safety layer) waits behind v2: comparing WM-assisted
vs a geometric baseline that itself crashes 17 % would confound the
WM's contribution with the geometric filter's weakness.

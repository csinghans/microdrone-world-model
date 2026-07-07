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

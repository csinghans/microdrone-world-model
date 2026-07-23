# Roadmap

The living version: what shipped (with verdicts, including the negative
ones), what is open, and what it would take to unfreeze the parked items.
Every claim links to a journal or a changelog entry — this file contains
no numbers that a script cannot reproduce.

An external review of the whole program, with a sequenced 12-month
research plan (advisory — it moves no bars): [REVIEW-2026-07.md](REVIEW-2026-07.md).

## Shipped

| version | one line | verdict |
|---|---|---|
| v0.1 | the port — Lesson 29's stack as a clean package, reproduced from scratch twice | mechanisms held on every draw; point numbers published as ranges |
| v0.2 | harder worlds, three axes (motion-aware labels / model-side GRU / hard-diet policy) | two wins, one honest negative (the GRU helped exactly where memory wasn't the constraint) |
| v0.3 | the dense hole — odometry map pin + edge diet | dense 37-50 % → 17-27 %; one scalar and a diet beat architecture, third confirmation |
| v0.4 | the research loop becomes a program (registry, skill plugins, gate runner, `/research` charter) | first autonomous campaign (gap-flight) self-ran to PASS: 27 % → 87-90 % |
| v0.5 | metric grounding — the perfect-4D-GS upper bound | **split verdict**: detection +0.07..+0.24 dense AUC (M1), flight 17 % → 37 % dense crash (M2). A better detector is not a better flight, fourth confirmation |
| post-v0.5 | two mechanism campaigns (`grounding_mechanism`, `head_calibration`) | warn-ring miscalibration measured (D0); temperature fix falsified — the miscalibration is context-conditional (C0); the dense-AUC instrument itself flagged (~0.5 seed spread) |

Full gate-by-gate numbers: `experiments/*/journal.md`, `CHANGELOG.md`.

## Recently closed

- **assist_v1 + assist_v2 (the Level-3 chapter opens, and every rung
  gets a price): two recorded negatives, one measured law.** The
  authority ladder shipped and certified in one commit-arc (pilot
  personas, WM guardian, paired-seed runner, keyboard cockpit, four
  safety rows, +0.0 KB budget); the full-ladder probe was NO-GO (WM
  arms add crashes where the same-ladder oracle prevents 7 with 0
  added), and the veto-only ablation on identical seeds split the
  blame: half the harm is the takeover rung handing a privileged pilot
  to a worse vision-only autopilot, the rest is the veto itself, whose
  price scales with speed. The law the chapter banks: **a guardian is
  only as good as its eyes in context and the pilot it swaps in.**
  Full arcs: `experiments/assist_v1/`, `experiments/assist_v2/`; track
  section below.
- **opening-door (price hesitation): champion promoted at n=200.** The
  fourth skill and the onboarding stack's first live exercise (backlog
  idea → `new_skill` scaffold → operator-mode campaign). Its title arc
  is the repo's measurement discipline in miniature: campaign gate
  failed as written (a replacement-era recheck drew the one bad seed
  block in ten) → the `sweep2_noise` calibration priced the cell as
  honest binomial → rechecks now **pool, never replace** → one
  pre-registered n=200 shot passed all six bars (fast-solo 5.0 %,
  independently confirming the calibration's 5.7 %). Also exported:
  `wait_time` climbs the anticipation spectrum (0.07→0.76 s), and
  froze=0 across both door arenas — this action set fails by
  commitment, never hesitation. Catalog: 4/4 skills with champions.
- **closing-door (the duel): PASSED at K3, zero-shot.** The third
  skill is a benchmark first: a converging aperture judged at the
  crossing instant, four contenders on identical seeds. The reactive
  baseline lives at cruise and dies at speed (83 % → 40 %); the
  moving-gap v2 champion threads a door it never trained on (93/87 %,
  all guards green) — no training knob needed, the catalog's first
  cross-skill champion. Figures in `experiments/closing_door/`.
- **moving-gap, v1 → v2: PASSED.** The sliding-fence skill (success
  judged at the crossing instant). v1 ran K0→KD1 autonomously and
  closed "capability yes, promotion no": targets passed everywhere,
  but a fast-solo guard (17 % vs ≤10 %, n=60) resisted both share
  re-weighting and 2× budget (non-monotone response — more budget
  would have been fishing). v2 attacked the **mixture shape** as v1's
  verdict prescribed: classic×2 healed all guards but starved the
  skill; an explicit solo world did the same, worse; their
  **combination passed all seven bars** (mgap 85/93 %, old skill 90 %,
  fast-solo cell 0 % at n=60). Champion:
  `experiments/moving_gap_v2/artifacts/ppo_moving_gap_v2_K3.zip` —
  flies with the G1 world model. Catalog: 2/2 skills passed through
  the autonomous runner. Full arcs: `experiments/moving_gap*/journal.md`.

## Open, in order of pull

1. **The skill catalog.** Each new flight capability is a plugin +
   pre-registered campaign the runner executes end-to-end. Next
   candidates after moving-gap: dense-speedrun (fly the dense world
   fast — deliberately collides with the known frontier),
   corridor-slalom (sustained weaving), narrow-moving-gap (compose the
   hard ends of both axes).
2. **The dense frontier, 17-27 %.** What we now *know it is not*
   (measured, so nobody re-digs these): not fixable by metric grounding
   at λ∈{0.1, 0.5} (v0.5 M2), not a global calibration error
   (head_calibration C0 — the warn heads over-report *conditionally*,
   in dense geometry specifically). What remains is retraining-class:
   conditional recalibration (needs a context signal the flying drone
   actually has), representation work, or memory at a data scale the
   GRU never got. Any attempt must respect the instrument lesson below.
3. **Instrument discipline.** Single-seed per-world val AUC spreads
   ~0.5 on the dense slice (five same-draw trainings: 0.47..0.99).
   Model-axis gates therefore need ≥3-seed means, bigger stratified val
   slices, or must skip straight to flight gates. The probe toolkit is
   in `eval/`: `eval_wm_checkpoint` (model axis, 4-decimal),
   `eval_policy_cells` (policy axis, pre-registered JSON cells),
   `eval_head_calibration` (probability-landscape diagnostics),
   `calibrate_heads` (temperature baking, AUC-invariant by construction).
4. **The hardware bridge (still parked — but its gate is GREEN).**
   Two stages, honestly labelled (`hardware/README.md`): Tello
   (off-board AI, the perception gap) → Crazyflie 2.1+ + AI-deck
   (GAP8, the on-board story the whole budget discipline points at).
   Status 2026-07-07: the original unfreeze criteria are MET (six
   bilingual articles in `writing/`; the Flight-TDD deployment gate —
   ≥ 0.70 over 100 random 3-stage courses — passed at 72/100 with
   committed videos of record), and v0.6.0 shipped as the imitation
   turn instead. Hardware remains parked by explicit standing
   instruction; unfreezing is the owner's call, not a schedule's.
   The shopping list is priced and ready; nothing here blocks on it.

Shipped since this roadmap's last revision (see `CHANGELOG.md` for
the gate-by-gate record): the imitation turn (v0.6.0 — five skills
become one pilot, the deployment gate opens), the instrument-honesty
era (the λ multi-seed retro-read, the dense-speedrun map), and the
corridor-slalom-v2 crown (eleventh sitting, anchored-schedule
fine-tune + edge-biased diet).

## The Indoor Active Search Track (new, 2026-07-07)

The repo's next direction — from proactive avoidance to a task-driven
autonomy: cover an unknown indoor room, find an abstract beacon,
return home. A SEPARATE track (its own translational nav action set,
search scenario, mission runner, and strategies) sharing the world
model and research gate but structurally isolated from the transit
benchmark. Phasing (`experiments/search_room_v*`,
`docs/TRAINING-A-SKILL.md` for the method):

**What the world model is FOR (the track's through-line, measured).** The
track put the WM to three indoor jobs and gated each honestly:

| job | WM result | who wins |
|---|---|---|
| collision safety | flat walls scale-free, blind to side/behind | cheap 4-8 rangefinder ring (v3, beams_v1) |
| coverage (where to go) | HURTS under clutter vs a grid | geometric Frontier / grid policy (coverage_v1) |
| **detection (is a target in view)** | **AUC 0.94, target-specific, no retrain** | **the world model** (vision_v1) |

The WM is a SEEING instrument: it loses the spatial jobs (safety, coverage)
to cheap geometry, but perception/detection is its home. The track's
recurring binding constraint was the **yaw=0 +x camera-lock** (kept to
protect the WM's body==world frame): it blinded the WM to 60% of collisions
(search_hybrid_v1) AND capped visual search (the +x cone only glimpses a
target as it sweeps past — vision_v1 flight). **v0.8 lifted it for
perception, cheaply (yaw_v1 below): detection turned out to be
yaw-INVARIANT, so "turn to find" and vertical search cost a retrained head,
not a WM retrain.** Only flight-*while*-turning avoidance (body≠world) still
awaits the WM retrain — and indoor avoidance is the beams8 ring's job, not
the WM's, so that step is no longer on the deployment path.

**v0.8 — indoor search goes vertical, and one WM learns two modes.** The
constraint fell and the search grew a dimension; full numbers in the
CHANGELOG (0.8.0) and `experiments/{yaw,alt,height,lowfly,unified_wm,slalom_stopobserve}_v1/`:

- **yaw_v1 — the camera-lock broken, GREEN.** Frozen-latent detection is
  yaw-invariant (pooled AUC 0.977, no decay with heading); a retrained head
  reads yaw-swept frames at AUC 0.982. Hover-yaw-scan flight gate PASSES
  (correct 0.70, false-alarm 0.10, collision 0.00, return 1.00) vs the
  +x-lock baseline's FA 0.95 / miss 0.40 — a ~10-line VelCommander yaw
  integrator, zero WM retrain.
- **alt_v1 — vertical search, GREEN after a head retrain.** Fly to the
  target's height and look level (vz, a clean DOF, not pitch). Level
  detection is strong high (1.6–2.0 m AUC 0.98–0.99), weak near the floor
  (0.4 m 0.663); a multi-height-frame head recovers the low regime (0.4 m
  0.66→0.90, near-floor z=0.15 m 0.83). A multi-height scan lifts find-rate
  0.50→1.00 — high cabinet (2.0 m) 0.00→1.00 and under-bed (0.3 m) 0.17→1.00,
  both outside a single level FOV. Zero WM retrain.
- **height_v1 — height is geometry, not the WM.** An upward rangefinder
  reads ceiling clearance at MAE 0.0 cm (8 rooms / 326 points) and maps a low
  beam (0.62 vs 1.63 m). Same division of labor as beams8: WM wins
  perception, cheap geometry wins metric/spatial.
- **lowfly_v1 — floor-hugging flight is clean in sim; the limit is
  sim-to-real.** Settled hover and descent hold to z=0.15 m (<0.5 mm drift,
  <1 cm overshoot, no floor contact) — the DSL PID compensates the modeled
  ground effect. The honest remaining limit is near-surface aero the sim does
  not model, not control.
- **unified_wm_v1 + flight_mode — one embedded pair, two modes.** One WM on
  transit+indoor beats the champion on every WM-owned job (transit AUC@32
  0.896→0.931, crash 40%→21%, false-evasion 100%→6%; indoor detection
  0.940→0.978) but overwriting the champion breaks the distilled zoo (slalom
  80%→0%). So it ships ALONGSIDE via a start-of-mission flight-mode selector
  (`planner/flight_mode.py`; `scripts.fly --mode`), two WMs resident at
  ~163 KB int8, one running per mode. slalom_stopobserve_v1 measured the
  swap-robustness levers (wrapper fails, stop-aware 0→25%, two-WM data-aug
  0→75% but rebalances).

- **Phase 1a — the smallest single-room proof: GREEN.** A micro-drone
  covers a 5×5 room, senses an abstract beacon (bearing+range, no
  detector), confirms it and returns home crash-free. Frontier
  (BFS coverage planning) clears the SEARCH-ROOM gate at n=30:
  find 0.933 / success 0.933 / collision 0.000 / return 1.000, and
  finds the beacon **4× faster than a random walk** (186 vs 740
  decisions). Feasibility-first caught (and the fresh-seed gate
  confirmed) that a naive safety filter and an n=8 friendly ceiling
  were overfit — the robust configuration is slow flight (0.36 m/s)
  under a braking-distance geometric safety filter. Trajectory:
  `docs/figures/search_room_trajectory.png`.
- **Phase 1b — does the world model help? YES for forward collision
  (after a setup correction).** First pass (v1/v2) read a negative —
  transit WM forward AUC ~0.48, and a retrain did not fix it — and
  wrongly blamed a "monocular flat-wall is scale-free" perceptual
  limit. **That was a rendering bug:** `SearchScenario` spawned no
  pybullet bodies, so the camera saw a blank floor; the WM scored at
  chance because there was nothing in the image. With the room
  actually RENDERED (`spawn_bodies`: wall slabs + box obstacles), the
  **transit WM transfers out of the box — forward AUC 0.814 at n=12,
  zero retraining** — the pillar-trained collision head reads box-walls
  fine. The v1/v2 negative and its mechanism story are RETRACTED
  (`experiments/search_wm_v3/`; v1/v2 kept with correction notes). So
  the WM CAN own vision-based forward danger; side/behind stays the
  rangefinders' omnidirectional job.
- **Hybrid safety layer (WM-forward + rangefinder-side)? NOT worth
  building — add beams, not a world model.** A collision-forensics
  diagnostic (`experiments/search_hybrid_v1/`, 200 episodes) classified
  the v3 residual crashes: of 10 first-contact failures, a WM-forward
  warn could prevent only **4 (40%)** — forward corners just off the
  single +x beam but inside the +-28 deg cone. The other 60% are blind
  to a +x-locked camera by construction: 3 strafe/reverse (camera
  orthogonal to motion) and 3 forward corners past +-28 deg. The cheap
  fix covers all ten — **more rangefinder beams** (8/angled), no vision
  stack in the safety loop. The channel-limit theme, sharpened: the
  yaw=0 camera-lock that keeps the WM VALID is what hides most of the
  crashes from it. The WM's honest role here is target/coverage
  reasoning, not collision.
- **Beam-count ablation (search_beams_v1): PASS — 8 beams close 3/4 of
  the residual, 16 recover the geometric ceiling.** A body-aware
  swept-corridor veto over an N-beam ring, pooled n=120 on the v3
  seeds: collision **0.033 (4 beams) -> 0.008 (8) -> 0.000 (16)**,
  monotone, with 16 beams matching the privileged geometric filter's
  0.000. The residual WAS the between-beam off-axis gap — it closes
  with more of the same cheap sensor, no vision/WM/ground-truth. Cost:
  find_rate erodes monotonically (0.908 -> 0.884 -> 0.842) as the
  corridor veto turns conservative; **8 beams is the deployment sweet
  spot** (one crash in 120, find 0.884). This CLOSES the Indoor Active
  Search safety arc: the whole story is a cheap omnidirectional
  rangefinder ring (`experiments/search_beams_v1/`).
- **Two-room (search_tworoom_v1): GREEN — the smallest multi-room
  proof.** Two rooms joined by one doorway, beacon hidden in the far
  room. The deployable beams8 ring clears all three SEARCH-ROOM bars at
  n=30 (find 0.933, return 0.964, collision 0.000), matching the
  geometric ceiling (find 0.933 / collision 0.000) — the coverage-first
  search crosses the doorway, covers the far room, finds the beacon,
  returns, still no world model or ground truth. Feasibility-first
  caught the real constraint: not the physics but the PLANNER'S SAFETY
  GRAPH — a 0.7-half doorway left the gap's grid cells at clearance 0.49
  (below the 0.5 min_clear), disconnecting the graph and stalling
  coverage in room A; widening to 0.9 fixed it (the two-room analogue of
  1a's unreachable-corner start). Named next: doorway detection +
  topological room graph (drop the hand-tuned width), then N-room
  (`experiments/search_tworoom_v1/`). Trajectory (god view of a
  deployable beams8 run, doorway traversal visible):
  `docs/figures/search_tworoom_trajectory.png`.
- **N-room (search_nroom_v1): GREEN — multi-room scales cleanly at the
  deployable config.** N rooms in a line (N-1 doorways, beacon in the
  last room). At the robust speed 0.6, the deployable beams8 ring covers
  3 AND 4 rooms, hops every doorway, finds the far beacon, and returns
  crash-free (4-room: find 1.0, success 0.95, **collision 0.000**);
  geometric ceiling identical (0.000). A first read at eval_search's
  stale default speed 1.0 looked like "collision rises with doorway
  count (0.10 -> 0.30)" — RETRACTED: that re-exhibited 1a's known
  speed sensitivity (v1 0.167 -> v2 0.000 was the "1.0 -> 0.6" knob),
  not a doorway problem. So the topological room graph's motivation is
  neither safety nor finding (both solved) but EFFICIENCY at scale
  (an O(rooms) memory-efficient map for the <1 MB budget) — a
  scalability play to pre-register on its own merits. Lesson: every
  search eval must fly at 0.6; the stale 1.0 default is fixed
  (`experiments/search_nroom_v1/`).
- **Doorway detection (search_doorway_v1): static FAILS, crossing is
  perfect — the room graph is feasible via traversal.** The topological
  map's one prerequisite: can the cheap ring tell the drone it is at a
  doorway? A static single-position heuristic (`doorway_score`, a far
  opening flanked by near walls) lands at chance (AUC 0.511) — the
  signature is vantage-dependent (flanks ~40 deg off before the gap,
  ~90 deg in it), so no fixed rule fires. But detecting the CROSSING
  (`passage_score`: one beam axis short both sides = walls squeezing,
  the perpendicular axis long = openings fore/aft) separates
  in-the-gap positions at **AUC 1.000** (clean rooms). So the drone maps
  doorways by FLAGGING the traversal, not spotting them from afar — an
  O(rooms) deployable room graph built by counting passage-crossings, no
  ground truth. Named next: the room-graph mission output ("beacon in
  room k of N"). Caveat: 1.000 is clean-room; clutter would lower it
  (`experiments/search_doorway_v1/`).
- **Room graph (search_roomgraph_v1): GREEN — "beacon in room k of N" at
  100%.** The deployable spatial output. `track_rooms` post-processes a
  flight: a `passage_score` spike (debounced, net |Δx| > 0.25) is a
  doorway crossing, its sign from odometry steps a room counter; the
  beacon's room is the counter at the found step, N is the farthest room
  reached + 1. Gate (beams8, speed 0.6, 3- and 4-room, 57 found of 60):
  **beacon-room accuracy 1.000 and room-count accuracy 1.000** (bars
  0.85), from the beam ring + odometry, no ground truth — an O(rooms)
  topological map, not a pixel grid. Closes the topological thread:
  N-room GREEN -> doorway-by-traversal -> room-level report. **But
  CLEAN-ROOM only, now measured:** a clutter stress test (box obstacles
  per room) breaks both legs — find-rate craters 0.95 -> 0.48 -> 0.13
  (clutter fragments the safe-cell graph; partly a narrow-room/placement
  confound) and room-graph accuracy collapses 1.000 -> 0.263 -> 0.000
  among found missions (box squeezes false-fire `passage_score`).
  **Isolation (clear-lane clutter, boxes against walls) resolves the
  confound:** find recovers to 0.90 (the crater was narrow-room +
  placement, not clutter-fundamental), but room-graph accuracy stays
  0.139 — systematic OVER-counting (detected N 6-8 vs true 4) as
  furniture squeezes add phantom crossings. So the naive crossing
  counter is genuinely not clutter-robust; the clean-room 100% stands.
  Named next: a clutter-robust crossing detector (discriminate a doorway
  — two large open regions — from a box-wall pinch; gate on recovering
  accuracy under clutter) (`experiments/search_roomgraph_v1/`).
- **WM-driven coverage (coverage_v1): HONEST NEGATIVE — the world model
  does not buy coverage.** The owner's direction ("use the WM to
  completely cover the space, THEN visual detection") built the first
  WM-DRIVEN task: an RL-on-WM-latent coverage policy (293-d obs = 40 WM
  collision probs over nav actions + an egocentric covered/occupancy
  grid), safety on beams8, dense coverage-delta reward. Pre-registered
  3-arm gate (Frontier ceiling / WM policy / grid-only ablation, clean +
  clutter, bars frozen from the Frontier ceiling); all three fail: WM
  clean 0.689 < Frontier 0.774 (A); no learned arm beats Frontier's
  clutter 0.395 — cluttered coverage is reachability-bound under safe
  flight, not a planning gap (B); WM clutter 0.324 < grid-only 0.379 —
  **the WM HURTS clutter coverage** (probs OOD for reverse/strafe,
  scale-free for walls) (C). It helps CLEAN modestly (grid 0.582 -> WM
  0.689) but never reaches Frontier and reverses to a hurt under clutter.
  Consistent with the arc — the WM lost to rangefinders for safety and
  now to geometry/grid for coverage; a monocular threat-channel world
  model is not the indoor spatial instrument. Deployable coverage =
  geometric Frontier or a grid-only policy, no WM
  (`experiments/coverage_v1/`).
- **Visual detection (vision_v1): the WM's latent SEES targets, but the
  +x camera-lock caps the flight search.** After coverage's negative, the
  opposite probe: the shipped WM latent linearly detects "target in +x
  FOV" at AUC 0.94 (> a color pixel baseline) — perception IS the WM's
  home. A small detection head on the frozen latent is target-SPECIFIC
  (fresh-room AUC 0.925, obstacle false-alarm 0.105 — red target vs orange
  obstacles), no retrain. BUT the end-to-end flight (Frontier sweep +
  detector "found") FAILS: a single-frame trigger compounds the 0.105
  per-frame false-alarm into 0.95 per-flight; a consecutive-firing
  debounce cuts that to 0.35 but trades it for 0.40 MISS (the +x cone only
  glimpses the target as it sweeps past — too few consecutive frames to
  confirm). The binding constraint is the yaw=0 camera-lock (kept to
  protect the WM frame): the drone cannot turn to face/confirm a target.
  Same lock that blinded the WM to 60% of collisions (hybrid). Named next
  (the deferred big step): add yaw + retrain the WM on the turning
  vocabulary — the owner's call (`experiments/vision_v1/`).
- **v3 (search_room) — the deployability capstone: GREEN.** Swapping the privileged
  omnidirectional clearance for four SGBA-style rangefinder beams
  passes the SEARCH-ROOM gate at pooled n=60 (find 0.917, collision
  0.033, return ~0.98, 8× faster than random). **Indoor single-room
  search is deployable with a $5 rangefinder ring — no world model,
  no ground truth in the safety loop.** The full arc: 1a the
  capability exists (privileged geometry) → 1b the monocular WM can't
  own safety (flat walls are scale-free) → v3 it never needed to; the
  right sensor is cheap and omnidirectional (`experiments/search_room_v3/`).
- **Later (each its own pre-registration):** the multi-room MINIMAL
  proof is done (two_room GREEN above) — next is doorway detection + a
  topological room graph to drop the hand-tuned doorway width and scale
  to N rooms; a visual-detection branch (widen the observation channel —
  the big perception step, where the world model re-enters); static-
  person SAR framing with safety bounds.

## The Assisted Flight Track (Level 3) (new, 2026-07-23)

Transit and indoor search fly Level-4 — the AI holds the stick end to
end. This track puts a PILOT in the loop (a human at a keyboard, or a
seeded synthetic stand-in) and spends the repo's wedge on someone else's
intent: the world model watches every command ("and if THIS command is
held?") and an authority ladder intervenes. The automotive analogy is
deliberate: the previous chapters were the self-driving car; this one is
driver assistance.

- **The ladder** (`planner/authority.py`): PILOT → OVERRIDE → AUTO.
  The absolute imminent backstop + geofence fire a same-decision
  momentary substitution (~0.5 s commit); the relative margin only
  accumulates escalation evidence (3-of-5) — it never grabs a human's
  stick on a single decision. Toggle TO auto is instant; a handback
  DURING danger is latched and granted after 12 clear decisions.
  Mechanics certified: four guardian rows in `eval/safety_selftest.py`
  (same-decision veto/toggle, gated handback, geofence-vs-pilot, flown);
  budget +0.0 KB weights, the deployed decision path IS the MPC's own
  sweep. `python -m scripts.fly --mode assisted`; the keyboard cockpit
  is `python -m scripts.fly_assisted --gui`.
- **The instrument**: three frozen pilot personas (reaction delay /
  fat-thumb / distraction / deadband over an OracleField core), a
  paired-seed protocol (same pilot, same course, bare vs guarded — the
  unassisted arm reproduced BIT-FOR-BIT across two campaigns), and a
  privileged oracle guardian that prices what perfect eyes could buy.
- **assist_v1 (full ladder): NO-GO.** Both WM arms add crashes (pooled
  added 18-20 of 40 on the primary cells vs the frozen added==0 guard)
  while the same-ladder oracle prevents 7 with 0 added and 333-880 ms
  of lead. dense@1.5 is the kinematic floor seen from the assistance
  side (the oracle cannot halve a 0.80 pilot crash rate). Margin sweeps
  refute the cheap-threshold rescue (`experiments/assist_v1/`).
- **assist_v2 (veto-only ablation, same seeds): the rungs are priced.**
  The takeover rung owns ~half the harm (added 64 → 29); the naked
  veto's price scales with speed (near break-even at 0.8 m/s, prevented
  9 / added 24 at 1.2 m/s — a 0.5 s hold displaces ~0.6 m mid-thread);
  and perfect eyes FLIP the ladder's sign (full-ladder oracle beats
  veto-only oracle in dense@1.0). **The chapter's measured law: a
  guardian is only as good as (a) its eyes in context and (b) the pilot
  it swaps in** (`experiments/assist_v2/`).
- **assist_v3 (the certified takeover, same seeds): the law at cell
  granularity.** Swapping the AUTO rung to the transit champion cuts
  classic harm monotonically (weak-takeover ladder 22-30 → no ladder
  14 → champion ladder 11) but the sacred added==0 stays unmet; the
  per-cell sign follows the pilot-vs-relief differential exactly
  (dense@1.5/novice, pilot 0.80 vs champion 0.45: the chapter's first
  genuinely helped hard cell, dcrash -0.200, lead 1479 ms;
  dense@1.5/average, 0.25 vs 0.45: taxed +0.200). Assistance pays for
  pilots worse than the relief artifact in context, and taxes the
  rest (`experiments/assist_v3/`).
- **assist_v4 (the hard-veto operating point): the cheap-knob era
  closes.** The trigger dose-response (imm_thr 0.5/0.7/0.9, identical
  seeds) shows the veto can be made QUIET, not ACCURATE: harm falls
  29 → 21 → 9 but never reaches 0 (dense saturation crosses any
  threshold) while prevention falls with comparable elasticity
  (16 → 9 → 6) — no separating region on the ROC
  (`experiments/assist_v4/`).
- **Standing verdict (final for this WM generation):** four campaigns,
  four honest negatives, every cheap knob priced on one paired seed
  set — ladder shape, takeover rung, trigger threshold. The ladder is
  mechanically sound and ships (mode, cockpit, instrument set, the
  law with its price list); NO WM-triggered intervention clears the
  added==0 sacred guard. The road is REPRESENTATION — eyes that do
  not saturate in clutter — exactly the quarterly-class road v0.14
  named for the autonomy chapter; the two chapters now wait on the
  same wall. Recurring pocket signature (reported, never barred):
  help pays only for the worst pilot in the worst place
  (dense@1.5/novice, three independent appearances).

## How we work

House rules: `CLAUDE.md` (one knob per run, frozen bars, sacred guards,
honest negatives, harness-error ≠ measurement). Agent-driven campaigns:
`.claude/commands/research.md`. Writing: `writing/` (bilingual, every
number traceable). The precedent that binds all of it: bars and
interpretive rules are committed *before* the numbers exist.

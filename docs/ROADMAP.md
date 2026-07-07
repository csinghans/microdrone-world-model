# Roadmap

The living version: what shipped (with verdicts, including the negative
ones), what is open, and what it would take to unfreeze the parked items.
Every claim links to a journal or a changelog entry — this file contains
no numbers that a script cannot reproduce.

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
  (`experiments/search_tworoom_v1/`).
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

## How we work

House rules: `CLAUDE.md` (one knob per run, frozen bars, sacred guards,
honest negatives, harness-error ≠ measurement). Agent-driven campaigns:
`.claude/commands/research.md`. Writing: `writing/` (bilingual, every
number traceable). The precedent that binds all of it: bars and
interpretive rules are committed *before* the numbers exist.

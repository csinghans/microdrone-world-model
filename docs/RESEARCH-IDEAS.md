# Research ideas — a graded backlog anyone can pick up

## The queue (priority order, set 2026-07-06)

- ~~P0 — dodgeball-v2~~ CLOSED 2026-07-06, refuted (world-identifiability
  diagnosis; see the entry below).
- ~~P1 — wm48-defense~~ CLOSED 2026-07-06, refuted: v1.8 crash 80 % vs
  77 % — 0.34 s of extra theoretical warning removed zero collisions,
  and the slow cells regressed (weaker draw overall). Kinematics
  exonerated by the oracle; **the fast-ball wall is signal quality at
  range** (`experiments/wm48_defense/journal.md`). Sharper long-horizon
  supervision = model-training class, fresh pre-registration if played.
- ~~P2 — chain-distill~~ **CLOSED 2026-07-06, FULL SUPPORT — the chain
  fell.** slalom3@1.0 = 96.7 % vs the five-elimination 0-6.7 % band
  (chain_break 2.90, teacher ceiling 0.97, unseen courses; first bar
  pass in seven sittings of that exam). Obs sufficient (open-loop val
  0.965) + body sufficient (oracle 97 %) + five axes eliminated ⇒ the
  LEARNER was the wall, and copying removes it
  (`experiments/chain_distill/journal.md`). No promotion (moving
  guard 47 %); cruise specialist. Distillation machinery now standing:
  `scripts/distill.py`.
- ~~distill-generalist~~ CLOSED 2026-07-06, SUPPORT twice-confirmed:
  the chain held the five-teacher pot at 93.3 % both knobs; crown one
  world short (gap 70 % a recheck-margin under bar; mgap 43-50 % —
  share measured to NOT be its lever). Supervised interference is a
  localized tax where RL interference was a confiscation
  (`experiments/distill_generalist/journal.md`).
- ~~surpass-the-teacher~~ CLOSED 2026-07-06, SUPPORT: teacher 0.885 /
  BC 0.585 / **BC+PPO-450k 0.880** at n=200 — the fine-tune repaired
  the 30-point closed-loop drift tax (crash 41→11.5 %) and TIED the
  teacher (no crossing; ~88-89 % may be the body's practical band
  there — unpriced hypothesis). Context: beats the pure-RL champion
  (88 vs 82, different seed set). Division of labor measured:
  **imitation buys the skill, on-policy RL buys the robustness**
  (`experiments/surpass_teacher/journal.md`).
- ~~BC+FT-generalist~~ CLOSED 2026-07-06, REFUTED — and the export is
  **the fine-tune safety law, measured three ways** (+ a fourth from
  dodge-distill K1): FT repairs exactly its own diet (surpass-teacher:
  +29.5 single-world), corrodes everything outside it (bcft K1: sweep
  98 % crash on untouched worlds), corrodes RL-unlearnable skills even
  inside it (bcft K0: chain 93→0 with slalom IN the diet), and can be
  biased by a strong-but-imperfect prior into a basin WORSE than
  from-scratch (dodge-distill K1: fled the box under the same tick
  economy K3 used to hold it). Safe iff the diet covers everything you
  care about AND all of it is RL-learnable. Since extended to six
  clauses — (5) anchor pressure is mass-weighted; (6) anchors defend
  against drift, not reward — and the slalom-v2 crown landed at the
  ELEVENTH sitting via the schedule anchor
  (`experiments/slalom_v2_promotion/journal.md`,
  `experiments/dodge_crown/journal.md`).
- ~~OracleDodge distillation~~ CLOSED 2026-07-06, SUPPORT —
  **dodge@v1.8 = 60 % over its bar, the catalog's only fast-cell
  pass** (crash 80→23 vs RL). Representation verdict instrument-
  audited: dodge-decision (non-hover) accuracy 0.898 at both fast
  speeds — the information was in the observation all along; wm48's
  range-quality suspect acquitted at this level. The curve INVERTS
  (fast cells easiest for imitation: brief threats convert decision
  accuracy directly; slow balls accumulate closed-loop drift)
  (`experiments/dodge_distill/journal.md`).
- ~~KL-anchored / short-dose fine-tuning~~ CLOSED 2026-07-06, refuted
  by rule / amended by data (`experiments/conservative_ft/`): the dose
  axis has NO window (the chain dies inside 25k steps while repair
  completes — corrosion outruns repair), but the KL anchor at 1.0
  **decoupled for real** — chain held at zero corrosion while gap
  repaired past its bar; mgap's deeper drift needs more movement than
  the 1.0-ball permits. Exports: `AnchoredPPO` (vendored 2.9.0,
  pinned) and the anchored zip — the catalog's best five-world
  artifact (93.3/80/43 on chain/gap/mgap).
- **The roads to a distilled champion — ALL PLAYED (2026-07-07), one
  crown, one file at rest.** Scoreboard form, one line per road:
  - *coefficient schedule* → **CROWNED** (slalom-v2, eleventh
    sitting: schedules buy what constants trade).
  - *per-world (per-group) coefficients* → defense WORKS (ball
    success monotone in the ball coefficient, 0→0.2-0.4→0.33-0.55 —
    the sixth clause has a countermeasure) but the pin strictly
    dominates the floor: **station-keeping and slow-ball repair live
    on the same states**; per-group anchoring cannot split them.
  - *the fidelity (volume) road* → refuted at its own checkpoint
    (200→600 v06 demos bought BC v0.6 0.267→0.433, sub-linear;
    log-fit says ~1400 eps ≈ 0.56, bar-level BC needs ~2500 eps
    ≈ 8 h — priced, owner's call).
  - *DAgger teacher-anchor* → kill condition fired by its letter
    (v0.6 tied the pin EXACTLY, 21/60 both); honest margins recorded
    (crashes fell 5x, v1.8 crossed its bar, mgap first green).

  **The dodge file rests with every named road priced** — five
  mechanism directions plus the volume curve's own arithmetic.
  Re-opening requires the 2500-episode shot or a NEW idea (stronger
  slow-ball teacher, curriculum, action-set change)
  (`experiments/dodge_crown/journal.md`).
- ~~dispatch (six-class)~~ CLOSED 2026-07-06 at its own phase-1 meter
  (`experiments/dispatch/journal.md`): moving_gap 0.80 and
  opening_door 0.667 under the frozen 0.85 identification floor —
  opening_door's identity is temporally hidden (median stable ID at
  decision 34; it opens as a sealed wall), and the confusable set is
  the single-fence family, the THIRD independent sighting of that
  boundary. Machinery stands: `planner/dispatch.py` (hysteresis,
  hover-biased default, frozen experts, union-exam runner).
- ~~dispatch-v2 (four-class)~~ CLOSED 2026-07-06, REFUTED — **the
  hover-lock, caught by trace**: perfect open-loop meters (1.00 on
  every world) collapsed in the closed loop because the hover-biased
  default generates stationary streams that ARE the dodgeball class's
  signature — the classifier confirms the default forever (door/gap
  traces: dodgeball 90/90, zero escapes; door@1.0 read 0 % success /
  0 % crash — it never went anywhere). The law, measured at TWO levels
  in one day (BC's 30-point drift tax at the policy level, the
  hover-lock at the meta-decision level): **a learned component whose
  inputs are shaped by its own outputs must be trained — and metered —
  in its own closed loop** (`experiments/dispatch/journal.md`).
- ~~dispatch-v3 (close the loop)~~ CLOSED 2026-07-06 at its meter — and
  it WORKED for its target: v2's hover-lock victims all freed (fence
  family + slalom escape in 2 decisions inside the dispatcher's own
  loop). The residue is one world and one sentence: classic reads
  0.067 (14/15 never-stable) because **a static sparse scene viewed
  from a stationary drone is a constant stream, and constant-over-
  sparse IS dodgeball's pre-launch signature — world identity needs
  probing motion** (`experiments/dispatch/journal.md`).
- ~~dispatch-v4 (probe gait)~~ CLOSED 2026-07-06, REFUTED — and the
  zero-effect shape found the real wall: classic unchanged to the
  digit (0.067) because **the parallax never reaches the classifier**
  — its input is the per-action collision probabilities, a threat
  summary that reports "nothing" outside 0.67 s regardless of
  viewpoint motion. The observation bottleneck, one level up: you
  cannot identify a world through a channel built to report only
  imminent danger (`experiments/dispatch/journal.md`).
- ~~dispatch-v5 (latent tap)~~ CLOSED 2026-07-06, refuted — the raw z
  is a NOISIER substrate than the probability summary (classic 0.0,
  slalom 0.067). The dispatch arc closes at five priced eliminations;
  cold-start world ID is the recorded open problem — and the
  integration layer reframed the battlefield (mid-course = moving-
  viewpoint ID).
- **THE INTEGRATION LAYER (flight TDD) is live** — `sim/composite.py`
  + `eval/eval_integration.py` + `docs/TDD-FLIGHT.md`; deployment gate
  ≥ 0.70 @ n=100 random 3-stage courses; baseline of record: slalom
  clone **33/100** with the privileged specialist relay at only 13 % —
  **the seam tax** (mid-flight entry states halve every expert's stage
  rate; 57/67 failures at seams). Videos of record appear on first
  pass (`experiments/integration_v1/journal.md`).
- ~~hot-start distillation~~ CLOSED 2026-07-06/07 (course-level BC buys
  nothing: filtered 0.333 = unfiltered 0.367 = clone 0.330 — every BC
  pays the closed-loop tax and students at best tie teachers, so the
  0.50-0.56 relay capped the pot; `experiments/hot_start/journal.md`).
- ~~odoor-v2/v3~~ CLOSED 2026-07-07, **FULL SUPPORT — the student
  surpasses the teacher**: BC 0.367 → BC+FT **0.96 @ n=100** (teacher
  ceiling 0.90, old champion 0.70-0.74). The weakest integration unit
  is now the strongest; the two-leg ledger completes (mgap tie 0.880,
  odoor surpass 0.960): imitation buys the skill shape, on-policy RL
  buys the timing (`experiments/odoor_v2/journal.md`).
- **integration-FT ★★★ (the gate shot)** — the two-leg recipe at
  course level: WMPolicyEnv gains a course mode (goal/tmax from the
  "stages" meta; per-stage obs reset + stage-local x, matching the
  exam's StageLocal semantics), then FT a course-BC prior on random
  composite courses — the diet IS the exam, squarely in FT's measured
  safe zone. Unit inventory now supports it: native mean ≈ 0.92 →
  product 0.77 > the 0.70 gate; the ONLY remaining deficit is the
  seam tax (measured conditional 0.51 vs the 0.888 needed).
- **DAgger, course-level** (distinct from the PLAYED dodge
  teacher-anchor, which died on its own kill condition): re-anchor a
  course/integration student to its relay teacher. The mechanism
  debate is written (`experiments/dodge_crown/journal.md`, K4); a
  course-level application would need its own pre-registration and
  its own kill condition.
- ~~P3 — chain-algorithm campaign~~ RESHAPED by chain-distill: the
  chaining question is ANSWERED (imitation chains at 96.7 %); an
  RL-algorithm campaign against that wall is now academic. Reopen
  only with a question distillation cannot touch.
- ~~P4 — the λ multi-seed replication~~ CLOSED 2026-07-07 (below):
  NOT RESOLVABLE at every power measured; the debt paid, the probe's
  split-identity leak found and hardened along the way.
- ~~P5 — dense-speedrun~~ CLOSED 2026-07-07 at stage 0 (below): the
  map was the deliverable; the scripted ceiling refuted twice.
- **P6 — trigger-based infra & deep water:** world_model knobs in the
  runner (wire when a SECOND hand-queued model-axis campaign appears
  after wm48-defense), predictor-side grounding, conditional
  calibration.

Each entry: difficulty, expected cost, a hypothesis sketch (falsifiable
— being wrong is a finding), the conventions to reuse, and what "done"
looks like. Claim one by opening a campaign branch/PR whose skill
docstring carries the pre-registration. Newcomers: do the
[ONBOARDING](ONBOARDING.md) hour first; ★ ideas are deliberately sized
as first campaigns.

## The Indoor Active Search Track (v0.7–v0.8) — a separate arc, ledgered

A task-driven track (cover an unknown room, find an abstract beacon, return)
structurally isolated from the transit benchmark; full gate-by-gate writeups
in `docs/ROADMAP.md` and `experiments/search_*`. Through-line: the WM is a
SEEING instrument — it loses the spatial jobs to cheap geometry, owns
perception. The closed ledger:

- ~~single-/multi-room search~~ CLOSED (v0.7) GREEN — Frontier coverage + the
  beams8 rangefinder ring find a beacon and return crash-free across 1, 2, N
  rooms at the robust speed 0.6; deployable with a ~$5 sensor ring, no WM, no
  ground truth (`experiments/search_{room_v3,tworoom_v1,nroom_v1}`).
- ~~WM for indoor collision safety~~ CLOSED (v0.7) NEGATIVE — flat walls are
  scale-free; the fix is more rangefinder beams (8 close 3/4 of the residual,
  16 hit the geometric 0.000), not a vision stack in the safety loop
  (`experiments/search_{hybrid,beams}_v1`).
- ~~WM-driven coverage~~ CLOSED (v0.7) HONEST NEGATIVE — an RL-on-WM-latent
  coverage policy HURTS under clutter vs a plain grid; deployable coverage is
  geometric Frontier/grid, no WM (`experiments/coverage_v1`).
- ~~topological room graph~~ CLOSED (v0.7) GREEN clean-room — "beacon in room
  k of N" at 100 % from beam-ring passage-crossings + odometry, no ground
  truth; NOT clutter-robust (over-counts) — a clutter-robust crossing
  detector is the recorded open sub-item
  (`experiments/search_{doorway,roomgraph}_v1`).
- ~~visual detection~~ CLOSED (v0.7) — the WM latent SEES targets (AUC 0.94,
  target-specific, no retrain) but the yaw=0 +x camera-lock capped the flight
  search to glimpses; named the yaw step (`experiments/vision_v1`).
- ~~yaw — break the camera-lock~~ CLOSED (v0.8) GREEN — detection is
  yaw-INVARIANT (pooled AUC 0.977), so "turn to find" cost a retrained head,
  not a WM retrain; hover-yaw-scan flight gate PASS (correct 0.70, FA 0.10,
  collision 0.00) (`experiments/yaw_v1`).
- ~~vertical / multi-altitude search~~ CLOSED (v0.8) GREEN — fly to a target's
  height (vz, a clean DOF, not pitch) and look level: find-rate 0.50→1.00,
  catching high-cabinet (2.0 m) + under-bed (0.3 m); height is cheap geometry
  (up-rangefinder MAE 0.0 cm) (`experiments/{alt,height}_v1`).
- ~~floor-hugging flight~~ CLOSED (v0.8) — clean in sim (the PID compensates
  the modeled ground effect, hover + descent to z=0.15 m); the honest limit is
  the sim-to-real near-surface aero gap, not control (`experiments/lowfly_v1`).
- ~~one WM for two modes~~ CLOSED (v0.8) — a unified WM beats the champion on
  every WM-owned job but overwriting it breaks the distilled zoo, so it ships
  ALONGSIDE via a flight-mode selector; swap-robustness levers measured
  (wrapper fails, stop-aware 0→25 %, two-WM data-aug 0→75 %)
  (`experiments/{unified_wm,slalom_stopobserve}_v1`).
- **OPEN (deferred, owner's call) — flight-WHILE-turning avoidance
  (body≠world), then collapsed/rubble 3D search.** Everything above lifted the
  camera-lock for PERCEPTION with no WM retrain. Avoiding obstacles *while*
  yawing (body frame ≠ world frame) would need a WM retrain on the turning
  vocabulary — but indoor avoidance is the beams8 ring's job, so this is off
  the deployment path. The larger deferred step is a real pitch-view WM
  retrain for collapsed/rubble 3D search (a new sim + multi-pose training).

## ★ good first campaigns

### ~~opening-door (price hesitation)~~ — DONE 2026-07-05
Consumed as written (`skills/opening_door`,
`experiments/opening_door/journal.md`): capability yes (70/60 % with
visible waiting — PPO discovered hold-then-thread; the mgap champion
even cleared @1.0 zero-shot), promotion no (the perennial fast-solo
guard, 13 % vs ≤10 % at n=60). Two exported findings: froze = 0 across
*both* door arenas (policies charge, they don't hesitate), and the
sweep@2.0 characterization below is now the **prerequisite** for ever
adjudicating that guard again.

### ~~sweep@2.0 noise characterization~~ — DONE 2026-07-05
Consumed (`experiments/sweep2_noise/journal.md`): the cell is **honest
binomial** (dispersion 1.12, bootstrap p 0.25) — its historical chaos
was plain sampling noise at inadequate n (±8.3 pt at n=30, ±5.9 at
n=60). Inheritance: the per-n CI table; bars on this cell judged at
pooled n ≥ 200 or with explicit margins; and a pending protocol
proposal — **rechecks should pool, not replace** (the study caught the
replacement-style recheck re-rolling an opening-door PASS into the one
bad block in ten). The opening-door K3 title question now has a
legitimate path: a fresh pre-registered promotion gate at pooled n ≥ 200.

### ~~corridor-slalom-v2 throne~~ — CROWNED 2026-07-07 (eleventh sitting)
`ppo_anchor_sched_edge.zip`: BC2 prior + 450k anchored-schedule FT
(kl 1.0→0.1) + edge_bias. Pooled chain 84/120 = 0.700 EXACT, four
guards green with margins (sweep@2.0 crash 0.05, clearance 0.62 m).
The crown recipe, one line: BC shape + mass-weighted anchored repair
+ slice-aware diet. Full arc: `experiments/slalom_v2_promotion/`,
`experiments/anchor_dial/`. FT-safety law fifth clause measured both
ways en route (thin slice 3%→31.7% corrosion; mass restored → 5%).

### ~~corridor-slalom (sustained weaving)~~ — CLOSED 2026-07-05, honest negative
No knob passed any target (best 10 % vs a 70 % bar): **the first
reversal is the wall** — the mgap champion dies at gate two zero-shot,
training pushes penetration (chain_break 2.17, weave_frac 0.85) but
joint success stays ≤10 %, and the double-share knob broke the mgap
guard. Exported lesson: pre-register a **scripted feasibility probe**
that prices an arena's physical ceiling BEFORE freezing bars (the
arena-side twin of the instrument lesson). The chaining question stays
open — see slalom v2 below.

### ~~slalom v2, feasibility-first~~ — CLOSED 2026-07-05, honest negative (structural)
The probe worked exactly as designed (`experiments/slalom_feasibility/`:
oracle ceiling 0.97 at v1's own spacing — v1's cruise verdict
re-attributed to capability, its speed bars to the arena), and the v2
campaign then failed its one priced target three ways
(`experiments/corridor_slalom_v2/`): fixed-spacing and budget
hypotheses both refuted, per-gate competence every time, full chains
~never. **Left standing: the observation-bottleneck hypothesis** — gate
period 0.875 s > the k=32 horizon (0.67 s); the camera sees gate k+1,
the collision-probability observation cannot represent it. See the
horizon campaign below.

### ~~the horizon campaign~~ — CLOSED 2026-07-06, hypothesis REFUTED
The signature fired on the refutation branch
(`experiments/horizon/journal.md`): a k=48 stack (1.0 s > the 0.875 s
gate period, observation widened to 10 probs/candidate) left
chain_break_at inside the k=32 baseline band with success ~0.
**Observability was not the wall.** The slalom arc is now fully priced:
arena flyable (0.97), per-gate competence learnable, and the chain
survives diet, budget, fixed rhythm AND observation horizon. Live
suspects moved off the model axis entirely — see below.

### ~~the chain-learning campaign~~ — CLOSED 2026-07-06, REFUTED (the fifth elimination)
The 2x2 factorial (per-gate reward x graded diet, pinned on v2 K1)
left the whole grid inside the baseline chain_break band
(`experiments/chain_learning/journal.md`): proximal gate pay, easier
chains in the diet, and their combination all move nothing. Secondary
finding worth stealing: the axes compose on GUARDS — K3 flew a 9-world
diet all-green where K1 alone broke mgap (dilution's ninth sighting).
The slalom arc now counts five eliminations: diet, budget, rhythm,
horizon, reward/credit-at-this-altitude.

### the chain-algorithm campaign (algorithm-class, deep water) ★★★
What survives five eliminations is the algorithm itself. Candidate
knobs, one per gate, each needing its own pre-registered signature:
**policy memory** (RecurrentPPO — the repo's LSTM lost 5x on transit
tasks, but chaining is the first task where a reversal must be *held
across* a gate; the old negatives don't price this shape), **PPO's
n_steps/GAE horizon** (the advantage window vs the ~2.6 s chain), or
an **algorithm swap**. Exam: slalom-v2 verbatim, sixth time. The bar
for opening this: argue in the pre-registration why the chosen knob's
mechanism differs from all five eliminated ones.

### ~~duel timelines (tooling, no training)~~ — DONE 2026-07-05
Consumed: `eval_duel_plots --timelines` renders, per duel cell, an
outcome grid (which courses kill whom) + a crossing-time strip (when
each contender commits, coloured by how it ended). Applied to BOTH door
campaigns' journals; in the opening-door figures, K3's wait is a
visible rightward shift and hard-course clustering (seeds ~14-17) is
legible. Renderer is pure and selftested; timelines re-fly cells for
per-episode data (diagnostic view, not the gate record).

## ★★ real campaigns

### ~~dodgeball — station defense~~ — CLOSED 2026-07-06, SUPPORT (crown vacant)
The catalog's first non-transit arena closed with all three walls
removed by their own instruments (`experiments/dodgeball/journal.md`):
arena by the oracle probe (0.80-0.90), **perception by K1** (survival
100/93/60/43 % vs the champion's flee-and-crash — the stacked history
reading a motion-blind model's probability ramp IS a dodgeable signal;
crash gradient tracks the 0.7 + v·0.67 m warning arithmetic), and
**objective by the K3 deviation** (dense in-box tick: in_box 0 → 0.8,
dodge@v1.0 **60 % over its priced 0.55 bar**). No promotion — transit
guards fail structurally for the pure-diet specialist, as
pre-registered. Also on the record: K2 ran in breach of its own
release condition (orchestration lesson now in CLAUDE.md).

### dodgeball v2 — the guard-clean defender ★★
The untested union: mixed diet WITH the station tick (K2-without-tick
erased the station; K3-without-mixing holds it). Chase a policy that
transits AND defends — guards regain meaning, promotion becomes
possible. If the fast cells (v1.4/v1.8) are attacked instead, the
priced crutch is WM48 (the horizon campaign's artifact — its transit
refutation says nothing about defense warning time). Fresh
pre-registration required; the v1 bars stay frozen.

### dense-speedrun (attack the known frontier, honestly)

**CLOSED 2026-07-07 at stage 0 — the map was the deliverable.** The
scripted "ceiling" was refuted by the incumbent champion itself
(0.733 vs 0.367 @x1.5, 0.433 vs 0.100 @x2.0 — speed management is a
learned skill scripts lack; the slalom lesson's dual). Mechanism map:
cruise is essentially closed (0.833 vs 0.867, side-clutter deaths
only); at speed the champion clears in-path threats at every factor
and dies on FOV-EDGE side clutter (13/14 @x2.0). Stage 0b (slow-capable
oracle) refuted the instrument a second time — slow-interleave ≈ plain
script everywhere (0.367 = 0.367 @x1.5): speed management is a TIMING
skill, the door-arc law again. No valid speed ceiling exists; headroom
unknown. Sole successor (unscheduled): champion-as-teacher two-leg,
bars priced against the existence numbers + margin
(`experiments/dense_speedrun/journal.md`).

*(Original framing, kept for the record: fly dense at factors
1.5-2.0, pre-register modest bars, expect an honest partial — the
value is the failure's shape. Delivered exactly that.)*

### the λ multi-seed replication (instrument discipline, practiced)

**CLOSED 2026-07-07 — NOT RESOLVABLE, and the debt is paid.** Three
arms × three seeds on one frozen draw: arm means separate by 0.112
against a pooled within-arm sd of 0.189 (control alone spans
0.75→1.00 on identical data). No λ effect readable at this power; the
M1 model-axis PASS does not survive the powered control (retro-read
recorded in `experiments/lambda_multiseed/journal.md`). Single-seed
model-layer AUC is weather — now measured, not asserted. Escalation PLAYED
(2026-07-07): the n=8 run exposed a probe split-identity leak (every
non-s0 read was graded on the s0 split — train/val overlap), the
instrument was hardened (ckpts store their seed; probe refuses
mismatches), and on clean reads the stabilizer hypothesis DISSOLVES
(variance ratio 0.96; it was born of a leaked number). n=3 verdict
and the M1 retro-read conclusion survive re-derivation. The λ file
is closed at every power measured.

*(Original framing, kept for the record: publish the distribution,
not the best run. Delivered — twice, the second time on a repaired
instrument.)*

## ★★★ deep water

### predictor-side grounding (the N3 reserve, never played)
v0.5's mechanism story says the *frame-level* aux debased the warn
surface conditionally. Supervise polar occupancy from the *predicted
future* latents (ẑ_k vs time-extrapolated grids) instead — aligns the
aux with what the heads actually read. Needs training.py surgery +
fresh pre-registration; judge at flight gates only (model-layer AUC is
a weak instrument — see above). *Done:* the M1/M2 pair rerun with the
new aux placement.

### world_model knobs in the runner
`train_knob` currently rejects `kind="world_model"` — campaigns tune
policies only. Wire WM training (with `--out` + the model-swap protocol
from the M2 journal) into the runner so model-axis campaigns stop being
hand-run. *Done:* research --selftest covers a dry WM knob; one real
campaign uses it.

### conditional calibration
The heads over-report in dense geometry specifically while sitting
under-confident globally (head_calibration C0). A per-context correction
needs a context signal the flying drone actually has (its own stacked
history? the x-progress pin?). Retraining-class; pre-register against
the M2 flight bars. *Done:* dense crash parity with the champion, warn
ECE halved, or an honest negative closing this road too.

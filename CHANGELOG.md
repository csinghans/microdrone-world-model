# Changelog

## Unreleased — the friendly research environment, exercised to a crown

- **Onboarding stack** (docs + tools + charter, all verified on a fresh
  env AND on CI's artifact-less runners): ONBOARDING/GLOSSARY/
  RESEARCH-IDEAS/START-HERE.zh-TW/CONTRIBUTING; `research doctor` (the
  preflight with a cost estimate) and `status --json` (one parseable
  object, next-knob hint); `scripts/new_skill` (conventions pre-filled,
  green as generated); the champions release + `fetch_champions`
  (sha256-pinned); the operator charter — a prescriptive lane for
  weaker agents with fixed-format gate reports and hard boundaries.
- **opening-door** (fourth skill, consumed straight from the backlog by
  the new stack, operator-mode executed): capability at K3 (71/74 % at
  n=200, wait_time 0.76 s — PPO discovered hold-then-thread; the mgap
  champion cleared @1.0 zero-shot), plus two exported findings
  (froze=0 across both door arenas; the WHERE→WHEN generalization).
- **sweep2_noise calibration**: the thrice-litigated fast-solo cell is
  honest binomial (dispersion 1.12); its historical 27/22/8/17/0/13 was
  sampling noise at inadequate n — and the study caught the
  replacement-era recheck re-rolling a passing read into the one bad
  block in ten. **Protocol upgraded: rechecks pool, never replace**
  (prospective; older journals keep their era's numbers).
- **The promotion-gate pattern**: when a strictly stronger instrument
  appears, the legitimate path is one pre-registered high-n shot — not
  a verdict rewrite. opening-door K3 passed all six bars at n=200
  (fast-solo 5.0 %, independently confirming the calibration's 5.7 %)
  and is the opening-door champion. Catalog: 4/4 skills crowned.
- Schema hardening: knob training diets' worlds are validated at load
  (a diet referencing another skill's world crashed a campaign
  mid-launch once — the whole class now dies with a friendly message);
  `eval_policy_cells --skill` judges with a skill's own predicates.

## Unreleased — the closing-door duel (third skill; the benchmark that is also a capability)

- **closing-door PASSED at K3, zero-shot** (`skills/closing_door`,
  figures + gate-by-gate numbers in `experiments/closing_door/`): the
  reactive-vs-predictive duel arena — the gap fence's edge pillars
  converge at 0.25-0.45 m/s, the aperture is aimed to be flyable at an
  on-time arrival and fully shut within the episode, and success is
  judged **at the crossing instant**. Four contenders flew the same
  cells and seeds (the runner grew a `builtin:` route for the non-zip
  baselines): the privileged reactive threads 83 % at cruise and
  collapses to 40 % at speed — the distance-budget cliff, live; the
  hand latent-MPC commits-and-dies (63-80 % pinched); the general
  champion detours around the whole fence (`transited` catches
  reached-without-threading); and **the moving-gap v2 champion clears
  every bar on an aperture it never trained on** (93/87 % threaded,
  all guards green) — the broad v2 diet bought out-of-distribution
  timing generalization, so the training knob never ran and the door's
  champion is a cross-skill zip. Hypothesis audit recorded honestly:
  two wrong, one half-wrong, one right; nobody froze (an *opening*
  door would price hesitation — future-arena note).
  `eval/eval_duel_plots.py` renders the outcome bars + a same-seed
  trajectory overlay where the champion's earliest commit makes
  anticipation visible to the naked eye. Catalog: 3/3 skills passed.

## Unreleased — moving-gap v2: PASSED (the diet's shape closes what budget couldn't)

- **moving-gap-v2 PASSED at K3** (`skills/moving_gap_v2`,
  `experiments/moving_gap_v2/journal.md`): the mixture-shape campaign
  v1's verdict called for. Both hypotheses proved half right — classic×2
  healed every home-turf guard and starved the skill (mgap@1.0 67 %);
  an explicit solo world healed every guard and starved it worse
  (53 %); their **combination passed all seven bars at once**: mgap
  **85 %** (n=60 recheck) / 93 %, static gap 90 %, cluttered at-bar
  5 %, sweeps 0/0/0 — with v1's killer cell, fast-solo sweep@2.0, at
  **0 % (n=60, clearance 0.54 m)** from a confirmed 17 %. The
  pre-registered dilution risk (mgap at ~14 % of episodes) never
  materialized. Sixth sighting of the house refrain, with the
  constructive corollary: budget alone failed (v1), each shape alone
  failed, **shape across both axes closed the hole**. The skill catalog
  stands at 2/2 campaigns passed through the autonomous runner (one
  researcher deviation each); the general champion is explicitly
  untouched — dense/moving cells were never measured here.

## Unreleased — the second skill campaign (moving-gap, closed: capability yes, promotion no)

- **moving-gap** (`skills/moving_gap`): transit a *sliding* fence's gap,
  success judged at the crossing instant — the first skill whose success
  predicate is a statement about time, and the first with a cross-skill
  regression guard (the specialist must keep static gap ≥ 75 %). The
  autonomous runner took it K0→K3 unattended, then a pre-rationaled
  KD1 (K1's mixture, 900 k) closed the arc: **targets passed at every
  trained knob** (best gate 82/97 % success, 98-100 % transit; even the
  zero-shot gap champion partially tracks a sliding fence for free by
  re-deciding every 5 steps, failing only at low speed — the timing
  story's exact prediction), and the dilution tax healed everywhere
  except one cell: **sweep@2.0 confirmed 17 % at n=60** (bar ≤ 10 %),
  with a *non-monotone* budget response (27/22/8/17 across 450-900 k) —
  so the campaign closed rather than fish with more budget. Fifth
  sighting of the refrain: the hole moved, this time from clutter to
  speed. No promotion; the mixture-shape attack (explicit fast-solo
  share) is future skill-v2 material with fresh bars and more n on the
  noisy fast cell.
- `docs/ROADMAP.md`: the living roadmap — shipped verdicts including
  the negatives, the dense frontier's measured "not-this" map, the
  instrument discipline, and v0.6 hardware behind explicit unfreeze
  criteria.
- **The weekly train-smoke ran for the first time ever** (manual
  dispatch) and paid for itself three times: the recalibrated model
  smokes passed on CI, and three born-broken steps surfaced and got
  honest fixes — `WMPolicyEnv` now rides `load_or_train` (artifact-less
  runners), the research runner grew a *dry-only* zero-shot stand-in
  (real campaigns still fail loudly on a missing champion), and the
  demo's anticipating seat now belongs to the measured champion stack
  (the hand MPC it used to assert had been broken by G1's recalibration
  since v0.2 — the story asserts were silently red on every machine).
  Auto-trained stand-ins are provenance-stamped
  (`meta["autotrained_tiny"]`) so behavioral selftests can scope
  themselves to wiring, honestly. Weekly job: green.

## Unreleased — the calibration falsification (head_calibration campaign, closed)

- **C0: FAILED — and the failure sharpened the mechanism.** Temperature
  recalibration (`eval/calibrate_heads.py`, in CI: one T per
  horizon×ring fitted on the train rollouts' FOV-masked oracle labels,
  baked into the head weights so AUC is invariant *by construction*)
  fitted **T < 1 on every head of both models** — the natural-
  distribution fit wants the heads *sharper*, refuting the c_hard-
  oversampling origin story — and made the target metric worse
  (calibrated-grounded dense warn ECE 0.1225 → 0.1318) while improving
  every non-dense slice. D0's warn inflation is therefore
  **context-conditional, not a global logit scale**: the heads
  over-report specifically in dense geometry while sitting slightly
  under-confident overall. One scalar cannot express that; every
  remaining fix is retraining-class. C1/C2 stayed closed per the frozen
  schedule — the deterministic knob failed before the 2.5 h flight gate
  spent anything.
- The grounding arc, complete: detection win (M1) → flight loss (M2) →
  mechanism candidate (D0) → cheapest fix falsified (C0). The champion
  stack stands; dense 17-27 % keeps its crown as the open frontier.

## Unreleased — the mechanism hunt (grounding_mechanism campaign, closed)

- **D0, the product:** the v0.5 flight loss has a measured mechanism
  candidate. The new landscape probe (`eval/eval_head_calibration.py`,
  in CI) compared the champion and grounded checkpoints on identical
  held-out frames: grounding left candidate contrast and richness intact
  (saturation *dropped*) and **mis-calibrated the warn ring upward** —
  dense warn ECE 0.0702 → 0.1225 (1.75×), warn mean P inflated on every
  world. Better ordered, numerically crying wolf: exactly the surface a
  raw-probability policy would misread. Measured on frozen checkpoints;
  no training noise in the claim.
- **N1 (λ=0.1): FAILED as gated** — and N1b (a pre-rationaled seed-1
  characterization run, gate verdict unaffected) reframed the failure:
  same knob, dense AUC@32 0.4705 (seed 0) vs 0.9504 (seed 1). Five
  same-draw trainings span dense 0.47..0.99 — **single-seed per-world
  val AUC is a weak instrument** (~5-6 dense val rollouts), too noisy to
  gate λ variants. Future model-axis gates need ≥3-seed means, bigger
  stratified val slices, or flight gates directly. (M1's two-seed mean
  cleared its bar by +0.105 — beyond this noise; M2's flight verdict
  never leaned on the model-layer number. v0.5's conclusions stand.)
- N2/N3 stayed closed per the frozen schedule. The actionable thread
  left open: attack *calibration directly* (temperature/Platt on the
  heads, zero retraining, judged at the flight gate).
- `scripts.train` grows `--ground-lambda`; second bilingual article
  (why predicting pixels is the wrong target) in `writing/`.

## 0.5.0 — 2026-07-05 (the metric-grounding split verdict)

- **M1 (model axis): PASSED.** A train-only grounding aux — a 5×3
  FOV-honest polar occupancy grid read off the privileged layout, i.e.
  the *perfect-reconstruction upper bound* of an offline 4D-GS pipeline —
  against a same-draw control at 96-rollout hard-mix scale: dense AUC@32
  0.7511 → 0.8175/0.9948 (seed 0/1; the pre-registered borderline rule
  fired and the two-seed mean 0.9062 clears the bar by +0.105), every
  slice up, now-AUC +0.13, veer doubled, deploy budget unmoved (the aux
  head is dropped at deploy; +1.0 KB train-only).
- **M2 (policy axis): FAILED.** The unchanged champion recipe retrained
  on the grounded model flies dense *worse*: 17 % → **36.7 %** @0.8,
  27 % → **48.3 %** @1.2 (n=60 fresh-seed recheck; the n=30 read of
  26.7 % was a friendly seed set), moving@0.8 guard broke at n=60
  (23.3 % vs ≤18 %); home turf spotless (sweep 0 % everywhere,
  cluttered 0 %). Fourth and sharpest confirmation of the refrain:
  **a better detector is not a better flight — even through a full
  policy retrain.** The champion stack stays G1 + edge_hard_xp.
- New gate probes, both in CI: `eval/eval_wm_checkpoint.py` (4-decimal
  model-axis probe; selftest asserts probe == training val exactly) and
  `eval/eval_policy_cells.py` (one zip × a pre-registered JSON cell
  list, flown by the research runner's own `run_cell`).
- Training smoke asserts recalibrated to what smoke scale can promise —
  the shipped v0.4.0 static smoke failed its old MSE bars
  deterministically (val Δ at 20 classic rollouts is draw-dominated);
  the latent-regression claim moved to the full-scale gates, where the
  M1 control re-verified it (MSE@32 1.304 < no-op 1.733).
- `scripts.train` grows `--ground`, `--out`, `--seed`; `writing/` opens
  with the first bilingual article (why micro-drones need tiny world
  models); FUNDING.yml (by Hans).

## 0.4.0 — 2026-07-04 (the research loop becomes a program)

- **First autonomous campaign: gap-flight, PASSED (knob 3 of 4).**
  K0 zero-shot champion: 27 % success — the pre-registered honest failure
  (it charges the fence; warn rings saturate in-gap and the crit heads had
  never steered the geometry). K1 (one diet share of the fence): targets
  smashed (92 %/83 %) but fast-solo guard broke (13 %). KD1 (deviation with
  written rationale — same mixture, 1.5x budget): **87 %/90 % success,
  transit 95-100 %, ~0.22 m margin, all guards green**. The loop exercised
  every clause it was built with: frozen bars, seven n=60 rechecks, a
  scheduled-knob skip, a deviation knob, and a harness-error recovery.
  Full numbers: experiments/gap_flight/journal.md.

- **Scenario registry** (`sim/scenario_registry.py`): worlds register once
  (builtins keep ids 0/1/2 forever; datasets self-describe via a
  `world_names` array), replacing five hardcoded dispatch sites. The
  refactor is regression-proven: the dataset selftest's numbers are
  bit-identical before and after.
- **Flight-skill plugins** (`skills/`): a skill declares scenarios, frozen
  targets + guards, a knob schedule, and a trajectory-level success
  predicate. First skill: **gap-flight**.
- **The autonomous gate runner** (`scripts/research.py`) + the `/research`
  command: one command per campaign; per-gate journal/results/commit; the
  borderline-recheck rule built in. The discipline that produced
  v0.2/v0.3 (single knob, pre-registered bars, honest negatives) is now
  executable.

## 0.3.0 — 2026-07-04 (the dense hole, closed by a map pin and a diet)

- **H1 (the odometry map pin):** one knob on top of the v0.2 champion —
  each observation step carries the drone's own corridor progress
  (x/GOAL_X, pure odometry), the anchor that lets the stacked history be
  spatially registered. Result: **dense 37 % → 17 %** @0.8 and
  **50 % → 33 %** @1.2 (both pre-registered targets beaten), moving@0.8
  33 % → 13 % (clearance 0.61 m), home sweep a perfect 0/0/0/0/10 %,
  cluttered 0 %, fast single-pillar 8 % → 2 %. The bill, confirmed real at
  n=60 (18 % vs 38 %): **moving@1.2 regressed** — the pin buys a spatial
  prior that a fast crosser violates. Same refrain as every diet knob:
  patch the band you point at, watch the hole move — but this trade closes
  four cells and opens one.
- **H2 (the pin + the edge diet — the champion):** one more knob,
  `--edge-bias` on top of H1, so training sees more fast episodes including
  fast crossers. The moved hole closes: **moving@1.2 37 % → 7 %**
  (clearance 0.72 m) — and nothing else pays: dense 17 % / **27 %** (the
  @1.2 cell improved again), moving@0.8 13 %, home sweep 0/0/0/0/**3 %**,
  cluttered 3 %, fast 3-8 % (two seed-sets disagree within noise).
  `hard + x-progress + edge-bias` is the v0.3 champion, best-or-near-best
  in every measured cell.
- **The campaign, one line:** v0.2's open frontier (dense 37-50 %) ends at
  **17-27 %**, with moving at 13/7 % — closed by one odometry scalar and a
  data diet, not by architecture. Third confirmation of the house refrain.

## 0.2.0 — 2026-07-04

Harder worlds, attacked on all three axes — each gate measured, two wins
and one honest negative:

- **G3 (policy axis — the win):** the stacked PPO retrained on the
  hard-world diet (same 300 k budget, G1's static motion-taught model,
  chosen by measurement) is best-or-tied in every cell: moving@0.8 crash
  **83 % → 33 %** vs the v0.2 baseline (clearance 0.39 m, best), moving@1.2
  **40 % → 20 %** (best vision-only), dense 37/50 % (best, still the open
  frontier), cluttered **0 %** (beats even the privileged-direction
  reactive's 2 %), fast single-pillar 8 %. Home-turf cost: a few points in
  the sweep mid-band (0/3/7/10/13 %), endpoint improved (23 → 13 %).
- Remaining open, stated plainly: **dense clutter** (best ≈ 37-50 % — the
  FOV/memory hole survives both the GRU and the diet; v0.3 material) and
  the hand MPC's fixed margins (broken by every model recalibration —
  three strikes; the learned policy is the answer, and now it is measured
  as such).

- **G2 (model-side GRU), honest negative result:** the first smoke caught a
  real bug (memory silently replacing the residual base — fixed: memory
  conditions, the residual stays frame-based, and the fix proves itself at
  scale with true long-horizon gain, MSE@32 1.31 vs no-op 1.94). But the
  pre-registered criterion failed: per-world AUC@32 went classic 0.86→0.95,
  dense 0.82→**0.74**, moving 0.88→**0.84** — the memory helped exactly
  where memory was not the constraint and hurt both hard slices; veer 0.80.
  Same verdict as the policy-side LSTM chapters, one level down: at this
  budget and data scale, elegance hasn't paid its way. The v3 code path
  stays (measured infrastructure, +24 KB, budget 161.7 KB); the deployed
  model for step ③ is G1's static motion-taught checkpoint, chosen by
  measurement.

- **G1 (motion-aware labels + hard-mix data, world model retrained):**
  per-world AUC@32 classic/dense/moving = 0.86/0.82/0.88 — the oracle fix
  lands (moving is now *detectable*: moving@0.8 wm crash 83 % → 47 %, and
  the privileged-direction reactive with the motion-taught danger-now head
  drops to 3 % at moving@1.2). But the recalibrated probabilities broke the
  hand MPC's fixed margins on classic/dense (sweep 30/33/23/3/17 %,
  dense up to 90 %) — the third measured instance of the same refrain: a
  better detector is not a better flight through hand-tuned margins. Dense
  remains a memory problem, as pre-registered. Consequences: step ② (GRU)
  attacks dense/FOV; step ③ (policy retrain on the new model) is now
  *required*, not optional — the decision layer must re-fit the new
  probability landscape.

- License changed from MIT to Apache-2.0 (patent grant; provenance kept in
  NOTICE).
- v0.2 opens with harder worlds: `spawn_dense_pillars` (5-7 pillars, two
  forced in-path) and `MovingCrosser` (a pillar crossing the corridor, its
  speed *aimed* at the encounter — an unaimed crosser misses on most seeds
  and measures nothing), plus `eval_hard_worlds`.
- **v0.2 baseline, measured before any model change** (30 seeds/cell,
  crash rate, zero-shot static-trained stack):

  | world @ cruise | reactive | hand MPC | learned |
  |---|---|---|---|
  | dense @ 0.8 m/s | 30 % | 50 % | 33 % |
  | dense @ 1.2 m/s | 70 % | 63 % | 50 % |
  | moving @ 0.8 m/s | 83 % | 83 % | 77 % |
  | moving @ 1.2 m/s | 37 % | 33 % | 40 % |

  Verdicts the v0.2 model work must answer: the home-turf crown does not
  transfer (the learned policy's 0 % becomes 33-77 %); nobody handles an
  aimed crosser at matched speed (the static-future assumption fails all
  three policies, including the privileged-direction baseline); and at
  1.2 m/s the moving world *inverts* — outrunning the crosser beats
  dodging it, an emergent "speed as evasion" the labels never taught.

## 0.1.0 — 2026-07-04

The port: the validated world-model stack from
[nanodrone-ai Lesson 29](https://github.com/csinghans/nanodrone-ai/tree/main/lessons/29_world_model)
re-homed as a clean research package.

- `world_model/` — bearing-aware encoder, multi-horizon residual predictor,
  dual-ring collision heads + danger-now head, JEPA losses (EMA target,
  variance guard), the training loop and the veer-ranking probe.
- `planner/` — the shared action set, the hand latent-MPC + reactive
  baseline, the learned-policy family (stacked / LSTM / edge-biased /
  curriculum) and a first-cut safety filter.
- `sim/` — the 48 Hz Crazyflie-class env + PID velocity commander, pillar
  scenarios and scoring rings, appearance-randomization primitives.
- `datasets/` — intervention rollout generation and the counterfactual
  label oracle with FOV honesty masks.
- `eval/` — the timing schematic, the cluttered closed-loop scoreboard, the
  speed sweep, the robustness pricing, and the embedded budget/latency bill.
- Everything keeps the `--selftest` / `XXX OK` convention; sys.path hacks
  from the course layout are gone (proper package imports, `pip install -e .`).
- PPO/RecurrentPPO training now seeded (`seed0`) for reproducibility.
- **Benchmark reproduced from scratch, twice** (64- and 96-rollout draws):
  mechanisms held on every draw (veer-ranking 1.00 x3, budget 137.3 KB
  exact, reactive speed collapse, zero false positives, robust-retrain
  buy-back); point numbers published as honest run-to-run ranges (AUC@32
  0.85–0.96, hand-MPC cluttered tail 9–16 %, learned-policy sweep 0–30 %
  per band — the course's all-zero was a strong-model draw). See the
  two-tier table in the README.

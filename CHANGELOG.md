# Changelog

## Unreleased

- **terminal_commit_v1: the distillation arm is REFUTED at its bars —
  and the refusal is worth the price.** The thread-commit oracle's
  skill would not clone cleanly into a vision-only student: two
  teachers (razor threshold, then hysteresis) both capped the
  terminal-region fit near 0.86, and the confusion diagnostic
  localized why — direction confusion 1/104 (the student knows WHERE)
  while 92 % of errors crowd the commit-timing boundary that no
  visual estimate resolves (±2 cm on a moving slot); hysteresis made
  the ORACLE fly better (+8) but the labels history-dependent, i.e.
  worse. Flying anyway (instrument re-registered on the record,
  flight bars untouched), the student captured HALF the oracle's
  gain — mgap seam 17.2 % → 11.1 % pooled vs the frozen ≤ 8 % — so
  the arm does not graduate and ships nothing; the pre-authorized
  slalom re-DAgger is held unspent (its object mooted; the coupling
  guard's trips sit within noise of the TRUE baseline, and the
  guard-anchor lesson — freeze from pooled rates, not one exam's
  draw — is recorded for the second time). Named successor:
  RL-from-success on the terminal window, which needs outcomes, not
  consistent labels — handed the exact target, an oracle warm-start
  option, and the priced ~4 % ceiling. Tools: SeamProbe target/
  thread-commit/hysteresis modes, `scripts/build_mgap_commit.py`;
  ledger: `experiments/terminal_commit_v1/journal.md`.

- **integration_k6_v1: the chain doubled — 6 stages fly at 0.500, and
  the investigation executed six suspects without convicting one.**
  The owner's question ("3 stages → 6, what's the rate?") is answered
  and under-runs the conditional^k prediction (0.55–0.65); the
  dissection finds the depth tax concentrated in moving_gap, and the
  campaign then eliminates, by pre-registered probe or intervention:
  entry pose (recentered — pose tightened, deaths unmoved),
  rendezvous displacement (the composite lazy-steps; the theory was
  shot by its own instrument), open bypass, entry conditions,
  upstream-composition selection, and the controller's time
  accumulators (reset at every boundary — gradient stands). What IS
  established: every moving-gap death is a failure to align by
  crossing time (×2.52, a razor median split: 29.8 % vs 0.0 %), and
  the position gradient predates k=6 entirely — 10.7 % → 26.7 %
  across positions 1→2 in every k=3 gate record on disk (n=271). The
  cause stands as an honest open, recorded, not narrated over; the
  k=3 gate of record is untouched. The reopened trajectory analysis
  then NAILED the kill mechanism — broke pilots track the moving slot
  fine and turn the WRONG WAY in the terminal second (0.90 wrong-way
  share) — and a privileged thread-commit oracle settled causality:
  **the turn is the pilot's MISTAKE, not a surrender** (forced
  commitment erases mgap deaths 27 % → 4.2 % deep and lifts the
  composite 0.500 → 0.610: one second of one stage type is worth +11).
  The terminal-commit TRAINING arm is priced, aimed, and owner-gated.
  Tools: `--k`, `--recenter`, `--ctrl-reset`, `--thread-commit`
  (privileged, labelled) on the integration suite, `eval_pose_walk.py`,
  `eval_gap_phase.py --analyze`; ledger:
  `experiments/integration_k6_v1/`.

## 0.11.0 — 2026-07-13 (the int8 close: parity flown, recipes adopted, sensors priced — and the Feynman rule)

- **The Feynman rule, in the articles and on the site.** Every article
  (all ten, bilingual) now opens with a boxed plain-language "simple
  version" — a few sentences and one everyday analogy before any
  number (the cyclist's running guess, the batter's swing, the
  instructor who never drifts, the guard who looks again…);
  `writing/README` records the convention: if we can't say it that
  simply, we don't understand it yet. The landing page gains an
  `#articles` section — ten cards, each summarized by its simple
  version, linking to the locale's full text. `docs/safety.md` gains
  the measured sensor-requirements table.

- **The measured int8 configs are ADOPTED: `artifacts.lock.json` gains
  a `quantized` section (owner's call, 2026-07-13).** Two deployment
  configs, no new binaries — each is derived at load by fake-quantizing
  the pinned float WM with its recorded recipe: `quantized.transit`
  (int8pc + seam split + int16 predictor activations + the
  quantile-matched trigger thresholds, exact values from
  `k2m_results.json`) and `quantized.indoor_search` (int8pc +
  regime-complete calibration + shipped heads, zero refits — Q1's
  per-head refit recipe is superseded; its qlat artifacts retire).
  Governance wiring: `flight_mode --verify` gains a quantized-section
  consistency layer (runs in the scorecard's quick layer), and
  `eval_int8_parity --selftest` pins the lock entries to the committed
  campaign records — the lock is a pointer, never a second source.

- **beam_latency_v1: the sensor spec line's last axis is priced — a
  beams8-safe ToF ring needs σ < 5 cm, missed-returns < 5 % (P1), and
  now report latency ≲ 500 ms at 0.6 m/s.** A delegating FIFO proxy
  (readings keep their old positions — the report lags the aircraft)
  delayed exactly what the safety filter reads; pooled n=60/arm:
  collisions flat to d4 (~517 ms, ~31 cm of stale geometry) and 0.100
  at d8 (~1033 ms) — real multiranger-class rings report in tens of
  milliseconds, an order of magnitude inside the pocket, so latency is
  the least binding axis. Find/return never moved under any delay (the
  ring feeds only the safety veto — P1's flat-find signature,
  reconfirmed). Ledger honesty carried in full: the pre-registered
  instrument band fired on a block draw (control find 0.767/0.783 vs a
  0.80 band frozen from P1's single-block 0.833), the bare-runner
  exoneration cleared the harness bit-exactly, and the footnote ships
  with the caveat plus an instrument lesson — freeze instrument bands
  from pooled priors, not one block's draw. Tool:
  `eval/eval_beam_latency.py`; ledger:
  `experiments/beam_latency_v1/journal.md`.

- **low_head_int8_v1: the int8 story's last red cell closes — and the
  recipe gets SIMPLER.** The near-floor head's quantization hostility
  (−0.044 shipped, −0.114 after refit) was regime ABSENCE, not regime
  hardness: the calibration corpus contained no near-floor frames, and
  the mechanism meter shows 2/4 encoder leaves clipping that regime
  (worst +8.1 %). Appending 256 train-block near-floor frames
  (calibration is monotone — added frames only widen ranges) recovers
  ALL THREE heads AS SHIPPED (yaw +0.0001 / low −0.0086 / person
  +0.0059, B1/B2 guards green), and the flight read lands it: **B5 on
  the zero-refit stack flies 0.80 correct / 0.00 FA — the best B5 on
  record, beating both the float gate (0.70/0.10) and the refit
  recipe (0.75/0.10).** The measured alternative recipe: int8pc +
  regime-complete calibration + shipped heads, zero per-head refits —
  "calibrate on every regime you fly, and the crutches delete
  themselves." Ledger honesty: K1's pre-registered guard REFUTED the
  knob as written (the person-REFIT row broke — a configuration the
  simpler recipe no longer contains); the letter-verdict stands on
  file beside the flight PASS, and adopting the new recipe
  (lock/packaging) is the owner's call. Tool:
  `eval_int8_parity --low-calib / --low-calib-b5`; ledger:
  `experiments/low_head_int8_v1/journal.md`.

- **transit_margin_v1: the quantized transit trigger reaches
  closed-loop PARITY — Q1's "likeliest cheap win" was real, on the
  second-cheapest arm.** The knob was closed-form (no search):
  transplant the float trigger's operating quantiles onto each
  quantized arm's own (edge, imminent) trace distribution. Two deaths,
  two mechanisms: the split arm's refit was a NO-OP (its quantiles
  already sat on the float constants — its +0.083 crash excess is
  distributional, K1c's ReLU-remix mechanism measured a second way);
  the p16 arm's +0.02/+0.01 threshold shift collapsed false-evasion
  from the all-or-nothing 1.000 to exactly the float 0.0556, went
  borderline on crash (+0.048), and the house pooled recheck landed it:
  **pooled n=126 Δcrash +0.0159 (bar +0.030), FE 0.0556 (bar 0.10) →
  PARITY.** The measured transit int8 recipe: int8pc weights +
  split-scale at the z‖action seam + int16 predictor activations +
  quantile-matched thresholds (0.4204/0.5123, a deployment config that
  must ship with the artifact — owner-gated packaging). With the indoor
  recipe already green, every closed-loop gate in the system now has a
  measured quantized configuration that passes. Tool:
  `eval_int8_parity --k2-margin / --k2-recheck`; ledger:
  `experiments/transit_margin_v1/journal.md`.

- **Article #10 published in-repo:** *Per-Frame Recall Is a Lie:
  Detection as Sequential Evidence* (bilingual,
  `writing/10-per-frame-recall-is-a-lie/`) — the two-way lie (missions
  find at 0.93 on 0.5–0.76 per-frame recall; the stationary bench's
  0.9818 collapses to 0.8888 on in-flight frames with the operating
  point broken, not the ranking), the CUSUM-SPRT duel refuted both
  directions (FA 0.85/0.60 vs confirm-k's 0.25/0.10), and the horizon
  law — bounded lookback beats accumulation optimality — unified with
  article 8's trigger symmetry: choose who may fire over how much
  history, and you have chosen which error explodes.

## 0.10.0 — 2026-07-13 (the seam turn: the gate rises to 79 and the mechanism gets a name)

- **Article #9 published in-repo:** *The Seam Tax: The Teacher Always
  Drives Home* (bilingual, `writing/09-the-seam-tax/`) — the 72→79
  story end to end: the failure map (86 % seam deaths, ×8 at slalom
  hand-offs), the refuted obvious fix and why it never could have
  worked ("the teacher always drives home" — covariate shift, with
  the per-decision numbers), two rounds of DAgger landing the 79
  record, and the three laws the cure taught: lineup-as-ABI (+ the
  ordering law), exam draws vs true rates, and fidelity-as-meter
  (raised twice, flight refused twice). The planned
  sequential-evidence article moves to slot #10.

- **transit_gate_v3: the road past 80, probed honestly and CLOSED at
  the 79 record (owner's call) — with two findings worth more than
  the points.** The cheap knives died fast and cleanly: swapping the
  solo moving_gap champion into the lineup is SWAP-NULL (0.818 vs the
  generalist's 0.828 at seams; the champion itself degrades 10.5 pts
  from cold to seam — moving_gap's wall is the task, random-phase
  entries, not the pilot), and dagger-weighted BC (w=3) is refuted at
  graduation (88/120; held-out student-manifold fidelity ROSE while
  flight fell — unweighted DAgger aggregation was already at the
  flight optimum). Banked: (1) **the lineup-coupling law** — swapping
  any upstream pilot re-opens downstream seams (slalom 17.2 % →
  43.8 % behind a swapped moving_gap; DAgger adaptation binds to the
  upstream exit-state distribution; ordering law: fix upstreams
  first, re-adapt downstream last); (2) **the true-rate table** —
  cross-block pooling shows the DAgger ladder's real, monotone effect
  (slalom seam 34.6 → 24.5 → 17.2 %) and that the exam's 9.5 % read
  was a ~1.3σ friendly draw (true composite ~0.775–0.78; the 79
  record stands by protocol, planning uses truth). Exam hygiene held:
  the 110000 exam never fired this campaign. The RL-class arms
  (slalom RL-from-success, mgap phase training + its re-DAgger
  surcharge) stay priced and parked. Ledger:
  `experiments/transit_gate_v3/journal.md`.

- **transit_gate_v2: the integration gate rises 72 → 79 (PASS ≥ 0.78,
  all conditional guards held) — and the seam finally has a mechanism.**
  The campaign in five measured moves: (1) failure map — 86 % of the
  record's failures are SEAM failures, slalom seam 26 % vs cold 3 %;
  (2) K1, deployment-matched teacher collection: REFUTED, the seam did
  not move a millimetre; (3) R1, the seam-fidelity probe: the clone
  leaves its teacher 3× as often on seam-visited states (0.9523 cold vs
  0.8573 seam; 0.6667 on breaking stages) and K1's diet never
  transferred — **covariate shift, measured** (teacher-flown
  trajectories relax onto the teacher's manifold; the student's own
  compounding errors create the states that kill it); (4) R2, DAgger
  round 1 (student flies, the oracle labels counterfactually): slalom
  seam 30 % → 21.4 %, formal 0.73 — progress, not pass; (5) R3, DAgger
  round 2 (aggregate): slalom conditional 0.814 → **0.917**, seam
  failures 12/40 → **4/42 (9.5 %)**, formal **0.79 = PASS**. The ladder
  was pre-frozen to end at round 2 — no R4. **Promoted 2026-07-12
  (owner's call): the R3 clone takes the HYBRID slalom slot, the gate
  of record re-anchors to `r3_formal_n100.json` (79/100), and the
  scorecard/README carry the new number with full lineage.**
  Instrument dividend: the probe reproduced the 72/100 exam per-seed at
  1.000 after the full environment rebuild — behavioural bit-stability
  across the toolchain swap, measured. Tools:
  `eval/eval_seam_fidelity.py` (probe hook + mirror ObsBuilder + weave
  counterfactuals), `scripts/build_bigpot_v2.py` (--dagger-npz,
  --base-cache); ledger: `experiments/transit_gate_v2/journal.md`.

## 0.9.0 — 2026-07-12 (the review turn: a second gate, one scorecard, int8 priced honestly)

- **Find-a-person (person_v1): GREEN — the WM latent reads a person's
  SHAPE, and the mission finds one at 0.933.** Frozen-latent probe:
  person-vs-box 0.944 (colour) / **0.806 shape-only** (person painted
  box-orange; above the 0.75 diagnostic bar, so it is not a colour cue).
  Widening the capsule to a real shoulder width (r 0.15→0.25) lifts the
  head to AUC 0.918 — but recall did not convert to find-rate until the
  SEARCH CHOREOGRAPHY changed: a yaw-corrected FOV label fix plus
  sense → approach (translate to ≤0.9 m, never spin in place) →
  face-and-confirm (2-hit) lifts find **3/7 → 14/15 = 0.933**, return
  14/15. Honest bounds: an upright capsule proxy, stationary-imaging
  probes + scan compounding; multi-pose / half-buried realism is the
  named stress test (`experiments/person_v1/`).
- **CI is manual-trigger only** (`workflow_dispatch` with an opt-in
  `train_smoke` input): no more auto-runs on push/PR/schedule — run it
  from the Actions tab or `gh workflow run CI` (owner request).
- **External review + 12-month research program (2026-07-11, advisory).**
  `docs/REVIEW-2026-07.md` (+ zh-TW): verified-state table, live
  hazards, assumption-debt and bound-space registers, the
  glimpses→evidence thesis, sequenced campaigns with pre-registration
  sketches, the owner-gate calendar. It moves no bars; ROADMAP.md and
  RESEARCH-IDEAS.md carry pointers.
- **Head governance (review item G1): the deployed detection heads are
  lock-pinned with their WM binding.** `target_head_{yaw,low,person}.pt`
  (all trained on the frozen unified-WM latent) enter
  `artifacts.lock.json` with a `wm` field naming the latent they ride —
  a head is only valid with its WM — and are uploaded to the champions
  release, so `fetch_champions` restores a COMPLETE flying system
  (8 assets, `--check` green). `planner/flight_mode.py` binds heads per
  mode; `--verify` cross-checks lock consistency (CI-safe) + on-disk
  shas, and the selftest refuses a head bound to the wrong WM.
  `alt`/`alt_os` stay journal-side, superseded by `low` on the deployed
  path.
- **The speed-1.0 trap, closed at the API layer (review item I1).**
  `eval_search.suite()` and `run_search_episode` still defaulted to
  speed 1.0 + the privileged "geometric" filter — any programmatic
  caller silently inherited the v1-era crash config. Both now share the
  track constants `ROBUST_SPEED` / `DEPLOY_SAFETY`
  (`eval/search_episode.py`), the eval_search selftest asserts
  CLI == API == runner defaults, and every suite prints its config
  header. The privileged filter is explicit-only.
- **int8_parity_v1 (review item Q1): the first quantized forward pass —
  the indoor int8 recipe is measured GREEN, the transit trigger is not.**
  A fake-quant harness shaped like the GAP8 NNTool SQ8 flow, bars frozen
  before numbers. Models pass (unified worst-world ΔAUC −0.007,
  detection −0.004; the champion's moving −0.016 is real and
  calibration-insensitive). Flight splits by trigger type: the transit
  margin-max WMPolicy FAILS under PTQ with the mechanism fully mapped
  (rank ✓ → probabilities ✓, T≈1 → per-candidate differentials ✗, the
  z‖action shared scale, fixed by a split quant node → threshold-mass ✗,
  any-trigger amplification; stays float pending a margin re-tune/QAT).
  The indoor confirm-k stack fails by MISS instead (FA better than
  float), and **refit heads on the quantized latents recover it: the
  yaw-scan gate flies 0.75/0.10/0.00/1.00 on the fully quantized stack,
  ≥ the float record**. Monochrome arm measured (transit collapses
  0.93→0.71; detection holds 0.98→0.95). Residual: the near-floor head
  (−0.114 after refit). Recipe: int8pc weights + two-track calibration +
  seam quant node + head refits. Tool: `eval/eval_int8_parity.py`;
  ledger: `experiments/int8_parity_v1/journal.md`.
- **Article #8 published in-repo:** *From Sim Toward Crazyflie: The
  Embedded Budget* (bilingual, `writing/08-the-embedded-budget/`) — the
  budget-as-constitution story, the latent-as-ABI lesson (slalom 80→0),
  the parity campaign's mechanism chain, the trigger-symmetry law, the
  monochrome numbers, and the measured int8 recipe. #9 planned:
  detection as sequential evidence.
- **detect_inflight_v1 (review item C1): the stationary-imaging debt is
  PRICED.** Per-frame detection on frames harvested DURING flight
  (behaviour-preserving trace hooks on both search runners): pooled
  n=40 in-flight AUC **0.8888** vs the stationary 0.9818 — and the
  operating point breaks, not the ranking (recall@0.65 collapses
  0.758→0.182; scores shift down). Deployed missions are insulated
  (the shipped yaw-scan detects while hovering); any future
  cruise-detection design retrains heads on moving frames or reads the
  score STREAM as evidence (C2 — its 10542-frame labelled replay corpus
  was recorded by this campaign). `experiments/detect_inflight_v1/`.
- **roomgraph_v2 P0: the bilateral-flank window feature is REFUTED
  (0.486 — below the single-frame 0.631); the windowing direction is
  not (window-mean −max_wall_run 0.631→0.735).** Clutter makes
  bilateral short returns ubiquitous; the honest bound stands and the
  room graph stays clean-room-only until a fresh registration pays for
  a learned head over windowed ring features.
  `experiments/roomgraph_v2/`.
- **indoor_gate_v1: the indoor track's deployment gate opens GREEN at
  91/100.** Four mission families at their unit configs (single-room /
  multi-room / vertical / person; speed 0.6 + beams8 hardcoded),
  feasibility-first (ceiling probe n=20/family → weighted 0.855, bars
  frozen from the probe), then the formal n=100 weight-split read on
  fresh seeds: **composite 0.910 ≥ 0.80, ZERO collision missions in
  100** (and zero in the 80-probe too). M3 is the first FLOWN
  search-then-vertical-scan number (0.750 formal — misses are the
  frontier, never safety). Tool: `eval/eval_indoor_gate.py`
  (--probe/--gate); M4 rides `demo_person.record(snapshots=False)` with
  collision counting. `experiments/indoor_gate_v1/`.

## 0.8.0 — 2026-07-09 (indoor search goes vertical — and one WM learns two flight modes)

The indoor active-search track's binding constraint fell, and the search
grew a third dimension. Every job below cost a head + a few lines of
commander glue — **zero world-model retraining** — because the frozen
latent is a function of the IMAGE: a target ahead in the body FOV is
detectable at any heading and (with a retrained head) almost any altitude.

- **The +x camera-lock, broken (yaw_v1): "turn to find" is free for the
  frozen WM.** The recurring binding constraint of the whole indoor track —
  a yaw=0 forward camera that could only glimpse a target sweeping past —
  falls with no WM retrain. Frozen-latent detection is yaw-INVARIANT (pooled
  AUC **0.977**, per-bin 0.938–1.000, no decay with heading); a head
  retrained on yaw-swept frames reads them at AUC **0.982** (obstacle-FA
  0.021). The hover-yaw-scan flight gate PASSES: correct-find **0.70**,
  false-alarm **0.10**, collision **0.00**, return **1.00** — versus the
  +x-lock baseline's FA 0.95 / miss 0.40. Cost: a ~10-line VelCommander yaw
  integrator + off-menu yaw actions. Flight-IN-yaw avoidance (body≠world)
  stays deferred to a Phase 1b WM retrain — indoor avoidance is the beams8
  ring's job, not the WM's (`experiments/yaw_v1/`).
- **Vertical search: fly to the target's height and look level (alt_v1) —
  high cabinet AND under-bed, zero WM retrain.** Use vertical lift (vz, a
  clean free DOF — the camera stays level) not pitch (which couples to
  translation and is WM-OOD). Frozen-latent level detection is strong high
  (1.6–2.0 m AUC 0.98–0.99) but weak near the floor (0.4 m AUC 0.663); a head
  retrained on multi-height frames recovers the low regime (0.4 m
  **0.66→0.90**, all heights 0.86–0.96; near-floor z=0.15 m AUC **0.83**).
  Capability gate: a multi-height scan lifts find-rate **0.50→1.00** —
  under-bed (0.3 m) 0.17→1.00, high-cabinet (2.0 m, geometrically outside a
  level FOV at cruise height) 0.00→1.00. Sim additions all default-off
  (target height, vary_height rooms, up/down lift actions, down-rangefinder)
  (`experiments/alt_v1/`).
- **Indoor height sensing is geometry, not the WM (height_v1).** An upward
  rangefinder (a modeled up-ToF against a collision-shaped ceiling) measures
  ceiling height at MAE **0.0 cm** over 8 rooms / 326 points, and maps a low
  beam (0.62 m under-beam clearance vs 1.63 m open) — the same division of
  labor as beams8 for avoidance: the WM wins perception, cheap geometry wins
  metric/spatial. (Recognizing vertical STRUCTURE from the image would need a
  real pitch-view WM retrain — a bigger step than yaw, deferred)
  (`experiments/height_v1/`).
- **Floor-hugging flight is clean IN SIM; the real limit is sim-to-real
  (lowfly_v1).** With detection holding to z=0.15 m, the open question was
  flight: settled hover 1.0→0.15 m drifts **<0.5 mm** with no floor-sink, and
  the descend-into-ground-effect transient overshoots **<1 cm** / settles
  <2 cm with no bounce — the DSL PID compensates the MODELED ground effect.
  So the sim reveals no floor-hugging control problem; the honest limit is
  the sim-to-real near-surface aerodynamics (prop-wash recirculation,
  turbulence, clutter) this sim does not model (`experiments/lowfly_v1/`).
- **One 512 KB WM can hold transit AND indoor — and wins every job it owns
  (unified_wm_v1).** A WM trained on the union of transit + indoor rollouts
  beats the pinned champion on transit collision-prediction (held-out AUC@32
  0.896→**0.931**; closed-loop crash **40%→21%**, false-evasion **100%→6%**,
  min-clear 0.35→0.39 m, 100% reach; crash ≤ champion at every 0.8–1.6 m/s
  sweep point, reach trading only at 1.4/1.6 m/s) and on indoor detection
  (0.940→**0.978**), with one honest regression OFF the deployed path (indoor
  forward-collision AUC 0.814→0.674 — a signal the beams8 ring owns anyway).
  But OVERWRITING the pinned champion breaks the distilled skill zoo (slalom
  80%→0%, gap/moving-gap/door −5..−30%; the encoder shift compounds over long
  chains), so the unified WM ships as a SEPARATE artifact.
- **Two flight modes, one embedded pair resident (flight_mode).**
  `planner/flight_mode.py` binds each mission at start to its own stack —
  `transit` = pinned champion WM + skill policy, `indoor_search` = unified WM
  + Frontier + beams8 — two WMs resident at ~163 KB int8 (32% of the 512 KB
  budget), only one running per mode (`scripts.fly --mode`). Ship alongside,
  not over the champion (whose sha is untouched).
- **Surviving the encoder swap, measured three ways (slalom_stopobserve_v1).**
  Whether a swap-broken skill can be RETRAINED to tolerate the unified WM: a
  post-hoc hover wrapper on the continuous champion is a double negative
  (80%→10%/0%; hover is itself OOD), stop-aware retraining recovers slalom
  **0%→25%**, and two-WM encoder data-augmentation is the strongest lever at
  **0%→75%** — but it rebalances (champion 80%→35%) rather than lifting both.
- **⚠ Instrument correction (affects λ-campaign numbers published in
  0.7.0's notes; conclusions survive, arithmetic corrected).** The
  model-axis probe graded every non-seed-0 checkpoint on the seed-0
  rollout split — those "val" reads overlapped the models' train
  sets (leakage). Clean re-probes reproduce the historical M1/N1
  numbers BIT-EXACT (l05_s1 0.9948, l01_s1 0.9504): training was
  deterministic all along and the "seed-adjacent nondeterminism"
  note is retracted. Re-derived clean: the n=3 verdict stands (NOT
  RESOLVABLE); the "λ0.5 stabilizes" hypothesis dissolves (it was
  born of a leaked read — clean n=8 variance ratio 0.96); the M1
  retro-read's conclusion SURVIVES strengthened (clean powered
  control 0.804 ± 0.15 vs λ0.5 0.769 ± 0.16 at n=8 —
  indistinguishable; M1's grounded pair were the λ-arm's luckiest
  draws). Hardening: checkpoints store their training seed; the
  probe reads it, refuses contradictions, warns on legacy ckpts.

## 0.7.0 — 2026-07-07 (the anchor dial: one throne taken, the safety law grows to six clauses)

- **λ multi-seed (the v0.5 instrument debt, PAID): NOT RESOLVABLE.**
  Three arms × three seeds on one frozen draw: arm means separate by
  0.112 against a pooled within-arm sd of 0.189 (the CONTROL arm alone
  spans 0.75→1.00 on identical data). Single-seed model-layer AUC is
  weather — now measured, not asserted. **The retro-read: v0.5's M1
  model-axis PASS does not survive a powered control** (its control
  seed was that arm's worst draw; the powered control mean 0.917
  absorbs the grounded mean 0.9062) *[0.917 was a leaked read — see
  the split-identity correction above; clean value 0.804, conclusion
  unchanged]* — the M1→M2 paradox dissolves:
  there was likely no model-axis gain to cash. Era verdicts stand as
  written; the reading is prospective.
- **dense-speedrun closed at stage 0 (zero training): the map was the
  deliverable.** The scripted "ceiling" was refuted by the incumbent
  champion itself (0.733 vs 0.367 @1.2 m/s; 0.433 vs 0.100 @1.6) and
  a slow-capable script was refuted again (0.367 = 0.367) — **speed
  management is a timing skill; the door-arc law extends to scripts
  that merely slow.** Mechanism map rewritten: cruise is closed;
  at speed the champion clears every in-path threat and dies on
  FOV-edge side clutter (13/14 crashes). The repo records an honest
  instrument gap: no valid speed ceiling exists.
- **anchor-dial (the ★★★ tool question): the schedule buys what
  constants trade.** kl 1.0→0.1 over 450k passes all three index bars
  (chain 0.833 / gap 1.000 / mgap 0.800) while constant 0.3 is
  strictly dominated. Machinery: `--anchor-end` (coefficient-only per
  rollout — the first draft's per-rollout `set_anchor` would have
  silently re-frozen the prior to the current policy; a deepcopy
  crash caught the semantic bug).
- **The FT-safety law's fifth clause, measured both ways:** anchor
  protection is MASS-WEIGHTED. The tenth promotion sitting died on a
  guard no training exam had measured (sweep@2.0: prior 3 % crash →
  31.7 % after anchored FT — the fast-solo slice carries ~4 % of
  rollout mass, and thin slices corrode almost as if naked). One
  knob later (`--ft-edge-bias`, EDGE_P 0.5) the slice's mass rose
  ~6x and the corrosion vanished: 31.7 % → 5.0 %, clearance 0.62 m.
- **👑 corridor-slalom-v2 CROWNED — eleventh sitting.**
  `ppo_anchor_sched_edge.zip` (BC2 prior + 450k anchored-schedule FT
  + edge_bias): chain pooled **84/120 = 0.700 at exact equality**,
  all four guards green with margins — the first artifact in eleven
  sittings across five RL knob families, two fine-tune eras and one
  distillation wall to hold the target AND every guard. The crown
  recipe, one line: **BC shape + mass-weighted anchored repair +
  slice-aware diet.** Honesty on the record: zero chain margin.
- **The dodge throne, priced from five directions (campaign closed,
  throne unclaimed).** The crown pot is strong (pooled val 0.92-0.93;
  fast-ball meter 0.957; the pot BC holds station at 0.267-0.700 —
  v1.8 above the pure clone), and then: (K1) the schedule-anchored FT
  erased station-keeping to 0.000 at every ball speed while
  station_tick paid for the box — **anchors defend against drift, not
  against reward** (the sixth clause); (K2) per-GROUP anchoring
  (`--anchor-ball-end`, tag-aligned buffer sampling) DEFENDS it —
  ball success is monotone in the ball coefficient (0 → 0.2-0.4 →
  0.33-0.55) — but the pin strictly dominates the floor: freedom on
  ball states buys erosion, and **station and repair live on the same
  states**; (K3) the fidelity road is refuted at its own checkpoint
  (tripling slow-ball demos bought BC v0.6 only 0.267→0.433,
  sub-linear) — plus one harness violation quarantined on the record
  (a newline-separated queue ran past a tripped NO-GO; queues now
  must be &&-chained); (K4) **DAgger-anchor** (shadow-teacher CE on
  ball rows, `--anchor-dagger-ball`) ties the pin EXACTLY on the
  frozen headline (v0.6 0.350 = 0.350, 21/60 both) — priced dead by
  its own kill condition, with honest margins recorded (v0.6 crashes
  fell 5x, v1.8 crossed its bar, mgap green for the first time).
  Sole surviving road: a ~1400-episode slow-ball volume
  re-registration. `ppo_dodge_K2a_pin` stands as the best
  station-holding generalist.
- Article #6 shipped (`writing/06-the-integration-climb/`, EN+繁中):
  unit-green is not integration-green — the climb to the deployment
  gate. New standing instrument: `eval_dense_probe` (gap-tracker
  oracles + mechanical failure taxonomy + blind-side flag, in CI).
  House rule added after six red pushes: repo-wide lint before push.

## 0.6.0 — 2026-07-07 (the imitation turn: five skills become one pilot, and the pilot passes its flight exam)

Seven campaign records, newest first — the imitation-era headline,
then the six campaigns that led into it.

- **The slalom wall falls to imitation** (chain_distill →
  distill_generalist): 25 RL sittings scored 0.00-0.067 on slalom3@1.0;
  a behavior clone of the privileged weave oracle scored 0.967, and a
  five-world "big pot" clone (one policy, all skills) holds 0.933. RL
  learnability and skill difficulty are different axes — imitation
  transfers what reward search cannot find.
- **The fine-tune safety law** (conservative_ft, bcft_generalist,
  chain_learning K-series; four datapoints): fine-tuning repairs skills
  inside its training diet, corrodes skills outside it, and erases
  RL-unlearnable skills even *inside* it (the chain died at every dose,
  25k-450k). Only a KL anchor to the prior decouples repair from
  corrosion (AnchoredPPO: vendored SB3 2.9.0 train() + kl·KL(prior‖π)).
- **Two-leg recipe — BC then on-policy FT** (surpass_teacher, odoor_v2):
  the clone buys skill shape, fine-tune buys timing. moving_gap
  0.585→0.880 (ties its RL champion); opening_door 0.367→0.96 at n=100,
  **surpassing its 0.90 teacher** — first surpass on the books.
- **Dispatch arc closed as an honest negative** (dispatch v1-v5): world
  classification from cheap onboard observation fails five ways
  (family confusion, closed-loop self-feeding, stationary-observer
  assumption, channel review, raw-latent noise). Cold-start world ID at
  hover is an open problem; the machinery (planner/dispatch.py) stays.
- **Flight TDD: the integration layer** (sim/composite.py,
  eval/eval_integration.py, docs/TDD-FLIGHT.md): unit tests = skill
  cells with frozen bars (already standing); integration = random
  3-stage composite courses drawn from the five-skill pool; deployment
  gate frozen at **≥0.70 success @ n=100** with videos of record
  (FPV + god-view GIFs + stamp) regenerated on every passing suite.
- **The climb to the gate** (integration_v1 → integration_ft): red
  baseline 0.33 (best single artifact) → anchored course-FT 0.39 →
  flight-plan hybrid 0.55 → +hot-start slalom specialist 0.62 →
  +big-pot specialist (43,488 decisions, val 0.9634) = **0.72 — GATE
  OPEN**. Winning lineup: gate-bonus course-FT generalist for four
  stages + big-pot slalom specialist, joined by flight-plan handoffs
  (per-stage dispatch on course composition — ruled deployment-legal,
  like waypoints). Laws priced along the way: the seam tax (mid-flight
  entry halves RL specialists), fidelity compounding (chain success ≈
  per-decision fidelity^40), and the closed-loop law's third
  application (hot-start collection must filter to cleared segments).
- **Results made visible**: eval/eval_results_figures.py (gate charts
  from every results.json + curated arc charts incl. the climb),
  eval/eval_skill_gallery.py (trajectory portraits), README results
  section, docs/media videos of record.
- Protocol upgrades: graduation judged at pooled n≥60 (an n=30
  friendly block promoted a 0.39 lineup once); conditional-knob
  discipline extended to composite courses.

### the friendly research environment, exercised to a crown

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

### the closing-door duel (third skill; the benchmark that is also a capability)

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

### moving-gap v2: PASSED (the diet's shape closes what budget couldn't)

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

### the second skill campaign (moving-gap, closed: capability yes, promotion no)

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

### the calibration falsification (head_calibration campaign, closed)

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

### the mechanism hunt (grounding_mechanism campaign, closed)

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

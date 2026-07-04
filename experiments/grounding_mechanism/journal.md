# grounding_mechanism — the v0.5 follow-up campaign journal

## Hypothesis (pre-registered 2026-07-05, before any gate ran)

v0.5 closed on a split verdict: metric grounding at λ=0.5 buys detection
(dense AUC@32 +0.07..+0.24 vs a same-draw control) and loses flights
(dense crash 17 % → 37 % @0.8 under the unchanged champion recipe). The
recorded mechanism hypothesis: **the policy consumes the heads' raw
probability surfaces, not their rankings, and grounding recalibrated the
surfaces' shape.** This campaign (a) *measures* that shape difference
directly, then (b) tests whether a gentler grounding (λ=0.1) keeps a
useful detection gain without the flight loss.

Everything reuses the v0.5 measurement basis: the same 96-rollout
hard-mix draw (`--worlds hard --rollouts 96 --len 120 --seed 0`), the
same control checkpoint (`../metric_grounding/artifacts/wm_m1_control.pth`),
the same policy cell spec and bars (`../metric_grounding/m2_cells.json`).

## The knob schedule

**D0 — the landscape diagnostic (no training).** New probe
`eval/eval_head_calibration.py`: per world, on the seed-0 val rollouts,
for G1-champion vs grounded-s0 — candidate **contrast** (per-frame std of
P across the 6 speed-scaled commands), **saturation** (fraction of pairs
pinned past 0.95/0.05), **ECE** vs the FOV-masked counterfactual oracle,
and **mean P**, for the warn and crit rings at k=32.

D0 is diagnostic — no bars. The interpretive rules are frozen HERE,
before the numbers exist:

- **Contrast-compression story**: grounded dense contrast < 0.7× the
  champion's → the policy lost option separation; the λ knob (N1) is the
  indicated remedy, and N1's landscape guard (below) is denominated in
  contrast.
- **Saturation story**: grounded dense saturation > 1.5× champion → the
  surface pinned to the rails; λ knob indicated, guard denominated in
  saturation.
- **Miscalibration story**: grounded dense ECE > 1.5× champion (with
  contrast/saturation roughly unchanged) → the numbers stopped being
  probabilities; λ knob still first, N3 (predictor-side grounding)
  becomes a plausible reserve.
- **Null result**: no metric moves past those thresholds in dense → the
  landscape hypothesis is *unsupported*; N1 still runs (cheapest knob),
  but if N2 then fails too, the campaign records "mechanism
  unidentified" — honestly, without a story.

The one D0 metric that separates the checkpoints most (relative to the
champion's value, in dense) is recorded at the D0 gate and becomes N1's
**landscape guard metric**. N1's bars are frozen at the D0 gate — after
D0's numbers, before N1 trains.

**N1 — the λ=0.1 model.** One knob vs M1's grounded arm: `--ground
--ground-lambda 0.1` (new CLI plumbing, default 0.5 = the M1 value),
same draw, same 80 epochs, seed 0, same control. Bars frozen at the D0
gate; the pre-committed skeleton:

| kind | bar |
|---|---|
| target | dense AUC@32 ≥ control + 0.03 |
| guard | every world-slice AUC@32 ≥ control − 0.03 |
| guard | now-AUC ≥ control − 0.03; deploy budget unchanged |
| guard | landscape: N1's dense <D0-metric> strictly closer to the champion's than grounded-s0's is |
| manipulation | gnd-AUC ≥ 0.70 (λ=0.1 reads the grid weaker; the check is "knob installed", chance is far below) |

Borderline: winning delta within ±0.02 of its bar → seed-1 repeat, judge
on the mean (the M1 rule).

**N2 — the flight gate (runs only if N1 passes).** The unchanged champion
recipe on the N1 model; `experiments/metric_grounding/m2_cells.json`
verbatim; the M2 bars verbatim (dense@0.8 ≤ 12 % **or** dense@1.2
≤ 20 %; guards moving ≤ 18/12 %, cluttered ≤ 5 %, sweep ≤ 5/5/5/10/10 %;
±0.08 → n=60 fresh-seed recheck).

**N3 — reserve**, may be played only if (a) D0's evidence specifically
implicates the *future* surface (crit-ring or ECE story) AND (b) N2
fails: grounding supervised through the predictor's forecast latents
(time-extrapolated grids on ẑ_k) instead of the frame latent. Needs its
own written rationale before launch.

Budget: D0 + N1 (one WM train) + N2 (one policy train + cells + rechecks)
+ reserve N3. Honest negatives get recorded, not retried into passing.

---

## Gates

(appended per gate; numbers only from rerunnable commands)

### D0 — the landscape diagnostic — story selected: **miscalibration** (2026-07-05)

`python -m eval.eval_head_calibration --ckpt-a output/world_model_g1.pth
--ckpt-b experiments/metric_grounding/artifacts/wm_m1_ground.pth
--out experiments/grounding_mechanism/d0_landscape.json` (M1 draw,
seed-0 val rollouts; full table in the json).

| dense, k=32 | champion | grounded s0 | ratio | frozen rule | verdict |
|---|---|---|---|---|---|
| contrast (warn) | 0.1482 | 0.1446 | 0.98× | < 0.7× ? | not supported |
| saturation (warn) | 0.605 | 0.540 | 0.89× | > 1.5× ? | not supported |
| **ECE (warn)** | **0.0702** | **0.1225** | **1.75×** | > 1.5× ? | **SUPPORTED** |
| mean P (warn) | 0.679 | 0.742 | +0.063 | — | context |

Corroboration outside dense: moving warn ECE 0.1345 → 0.2012 (1.50×),
moving crit 0.0541 → 0.0864 (1.60×), mean P inflated on every warn
slice (+0.02..+0.07). Counter-evidence honestly noted: dense *crit* ECE
improved (0.0841 → 0.0676) — the critical ring got better-calibrated
while the warn ring drifted; saturation *dropped* everywhere (the
surfaces got richer, not flatter).

**Reading (per the pre-registered rules, no post-hoc story):** the
miscalibration story is selected — grounding made the warn surface
systematically *over-report* danger (better ordered, numerically
inflated). A policy consuming raw probabilities sees a world that cries
wolf; in dense (mean warn P 0.74) the usable range above the inflated
floor is thin. λ knob (N1) first; N3 (predictor-side grounding) is now
a *plausible* reserve per the rules.

**N1 bars — frozen now, before N1 trains.** The landscape guard metric
is the biggest separator: **dense warn ECE** (champion 0.0702,
grounded-s0 0.1225, gap 0.0523).

| kind | bar |
|---|---|
| target | dense AUC@32 ≥ control (0.7511) + 0.03 → **≥ 0.7811** |
| guard | every world-slice AUC@32 ≥ control − 0.03 (classic ≥ 0.8089, dense ≥ 0.7211, moving ≥ 0.8090) |
| guard | now-AUC ≥ 0.6919; deploy int8 identical (81.3 KB) |
| guard | landscape: N1 dense warn ECE strictly closer to 0.0702 than 0.1225 is → \|ECE − 0.0702\| < 0.0523 |
| manipulation | gnd-AUC ≥ 0.70 |

Borderline: winning delta within ±0.02 → seed-1 repeat, judge on the
mean. Command: `scripts.train --epochs 80 --ground --ground-lambda 0.1
--out experiments/grounding_mechanism/artifacts/wm_n1_l01.pth` on the
unchanged M1 draw.

### N1 — λ=0.1 — **FAILED** (2026-07-05)

Probe: `eval_wm_checkpoint --ckpt .../wm_n1_l01.pth` (train print and
probe agree; landscape in `n1_landscape.json`).

| bar | measured | verdict |
|---|---|---|
| target dense AUC@32 ≥ 0.7811 | **0.4705** | **FAIL** (0.31 from bar — not borderline) |
| guard dense slice ≥ 0.7211 | 0.4705 | **FAIL** |
| guard classic ≥ 0.8089 / moving ≥ 0.8090 | 0.8984 / 0.8189 | pass |
| guard now-AUC ≥ 0.6919; budget | 0.8354; 81.3 KB | pass |
| guard landscape \|ECE − 0.0702\| < 0.0523 | 0.1209 → 0.0507 | pass (barely) |
| manipulation gnd-AUC ≥ 0.70 | 0.90 | pass |

The failure shape was not on the menu: everything global is healthy
(overall AUC@32 0.8177, veer widened 0.9286, MSE@32 1.152 < no-op 2.114)
and the **dense slice alone collapsed below chance** — on the same val
rollouts where the same-draw control scored 0.7511 and the λ=0.5 arms
scored 0.8175/0.9948. λ is measured as *not a smooth dial*: 0.5 buys
detection and loses flights; 0.1 loses the detection outright.

Per the frozen schedule, N2 runs only on an N1 pass → **N2 does not
run**. N3's precondition requires an N2 failure → **N3 stays closed**.

**Deviation N1b — written before it runs, gate verdict unaffected.**
Rationale: four same-draw trainings have now produced dense AUC@32 of
0.7511 / 0.8175 / 0.9948 / 0.4705 — a 0.53-wide spread on the slice
every campaign verdict cares about. N1b repeats the λ=0.1 knob at
seed 1 *as a characterization run, not a gate retry*: N1's FAIL stands
as recorded regardless of N1b's number. What N1b decides is the
finding's wording — "λ=0.1 collapses dense" (if it repeats low) vs
"single-seed dense AUC at this scale is dominated by training noise"
(if it lands high) — two very different lessons for every future
campaign's bar design. Command: same knob, `--seed 1`, out
`wm_n1_l01_s1.pth`.

### N1b — the characterization run — verdict: **the instrument, not the knob** (2026-07-05)

Same knob (λ=0.1), seed 1: dense AUC@32 = **0.9504** (probe, its own
seed-1 val split; classic 0.8968, moving 0.8355, now-AUC 0.7967, veer
widened 0.9683, gnd-AUC 0.82, MSE@32 2.628 < no-op 4.403 — everything
healthy). Seed 0 read 0.4705 on the same knob.

Per the pre-written wording rule, the finding is the second one:
**single-seed dense AUC at this scale is dominated by training noise.**
Five same-draw trainings now span dense AUC@32 = 0.4705 .. 0.9948
(control 0.7511; λ0.5 0.8175/0.9948; λ0.1 0.4705/0.9504) — a ~0.5-wide
lottery. The val slice holds only ~5-6 dense rollouts; per-world AUC on
it is rollout-correlated and tiny-n. The model-layer instrument lacks
the resolution to gate λ variants at all.

## Campaign verdict: CLOSED (2026-07-05)

- **D0 (the product):** the M2 flight loss has a measured mechanism
  candidate — grounding at λ=0.5 leaves ranking and richness intact and
  *mis-calibrates the warn ring upward* (dense warn ECE 1.75×, mean P
  inflated on every warn slice): the policy's observation currency was
  debased even as its ordering improved. Measured on frozen
  checkpoints — no training noise in this claim.
- **N1: FAILED as gated** (seed-0 dense 0.4705 vs bar 0.7811). N1b
  reframes the failure: the gate was honest, but the *instrument* it
  used (single-seed per-world val AUC) cannot resolve the question.
  N2/N3 stay closed per the frozen schedule.
- **The lesson that outlives the campaign:** dense-slice model-layer
  AUC is a weak instrument (~0.5 seed spread); flight gates (n=30/60
  crash rates with recheck) and frozen-checkpoint landscape probes are
  the reliable ones. Future model-axis campaigns must gate on ≥3-seed
  means, bigger stratified val slices, or skip straight to flight.
  (Retroactive humility: M1's two-seed mean passed its bar by +0.105 —
  comfortably beyond this noise, and M2's flight verdict never depended
  on the model-layer number. The M-campaign's conclusions stand.)
- λ remains unmeasurable as a dial at current resolution; the
  miscalibration mechanism (D0) is the actionable thread — a future
  campaign could attack *calibration directly* (e.g. temperature/Platt
  recalibration of the heads, measured at the flight gate), which costs
  no retraining at all.

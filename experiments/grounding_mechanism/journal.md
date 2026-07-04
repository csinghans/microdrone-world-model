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

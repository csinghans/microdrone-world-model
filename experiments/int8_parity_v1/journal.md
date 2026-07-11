# int8_parity_v1 — does the embedded story survive quantization?

**Opened:** 2026-07-11 · **Owner:** Hans · **Source:** docs/REVIEW-2026-07.md (Q1)

## The question

Every budget number in this repo (137.3 KB, ~163 KB two-WM, ~8 ms) is int8
*accounting* — `n_params / 1024` arithmetic (`eval/eval_latency_budget.py`,
`docs/embedded_budget.md`). No quantized forward pass has ever produced a
gate number. If int8 costs accuracy, the whole embedded narrative has a
hole; if it doesn't, writing/#8 gets its missing centerpiece. Pure sim,
zero training, zero WM risk (all arms run on copies; sacred artifacts
untouched).

## Hypothesis (falsifiable)

Post-training int8 fake-quant (per-channel conv weights / per-tensor linear
weights, per-tensor asymmetric activations — the GAP8 NNTool SQ8 shape)
holds every deployed gate within pre-registered parity bars. Falsified if
any bar below fails on the headline arm.

## Arms

| arm | what | role |
|---|---|---|
| `float` | shipped fp32 models, same loops | baseline of record (same run, same seeds — MPS/two-tier rule) |
| `int8pc` | per-channel convs + per-tensor linears, int8 asymmetric activations | **headline — bars sit here** |
| `int8pt` | per-tensor weights everywhere | pessimistic bound (informational) |
| `gray` | float model, luminance-only input (Y replicated ×3) | prices the AI-deck monochrome-camera gap (informational) |
| `gray+int8pc` | both | combined embedded reality (informational) |

Quantization model (honesty list up front): weights symmetric int8 (127),
activations asymmetric uint8 via min/max calibration at every Conv2d/Linear
input; bias stays float (int32 on-device — negligible); ReLU/pool/flatten
run float between quantized leaves (pool rounding not modeled); terminal
logits are NOT output-quantized (sigmoid/rank metrics are monotone-invariant;
tie effects land in the closed-loop arm instead). NOT validated in sim:
PULP-NN rounding/saturation exactness, Autotiler tiling/DMA + real latency
(0.5 GMAC/s stays a stated assumption), NNTool's actual per-layer choices.

**Calibration:** 1024 frames (+ paired actions) sampled seed-fixed from
`output/combined.npz` — the unified WM's own two-track training union. It
contains NO rendered-target imagery (deployment-realistic: heads came
post-hoc); if detection parity fails, "add target frames to calibration"
is a named K1 knob, one change at a time.

## Gates & pre-registered bars (frozen before any number)

Models under test: the two lock-pinned WMs (champion `world_model.pth` for
transit; unified `world_model_unified.pth` for transit + indoor detection)
plus the three locked heads (yaw/low/person) in later phases.

| id | gate (the exact shipped read) | bar (int8pc vs same-run float) |
|---|---|---|
| B1 | transit per-world AUC@32, held-out `transit_eval_holdout.npz`, split seed 0 (`eval_wm_checkpoint.evaluate` loop) — both WMs | worst per-world ΔAUC ≥ −0.010 |
| B2 | indoor detection linear-probe AUC, fixed grid n_rooms=6 seed0=600000 (`eval_target_probe`), unified WM, identical frames across arms | ΔAUC ≥ −0.015 |
| B3 | locked-head AUCs (yaw / low / person) on their own harvests, identical frames across arms | each ΔAUC ≥ −0.015 |
| B4 | transit closed-loop WM-arm, n=60 seed0=1000 (`eval_closed_loop.evaluate` components seam), unified WM | Δcrash ≤ +3 pts AND inside the float arm's 95% binomial CI; false-evasion Δ ≤ +5 pts |
| B5 | yaw-scan visual search flight gate, n=20 (`run_yaw_scan_search`), unified WM + yaw head int8pc | the yaw_v1 bars verbatim: correct ≥ 0.70, FA ≤ 0.20, collision ≤ 0.05, return ≥ 0.80 |

Phasing: **K0 (this sitting)** = B1 + B2 + per-layer SNR + gray arms
(inference-only). **K1** = B3 (head harvests). **K2** = B4 + B5 (flight,
background queue). Bars for ALL phases are frozen now.

## Pre-registered diagnostics & decision rules

- **Per-layer SNR:** quantize ONE leaf at a time (weights + its input
  activation), SNR of the final warn logits vs float over the calibration
  batch — names the hostile layer before anyone guesses.
- B1/B2 fail → K1 knob: calibration 1024→2048 or percentile clipping (one
  knob). Still failing + SNR names the projection/pool seam → per-channel
  there is not available in SQ8 → record as an architecture finding.
- SNR names the predictor's residual accumulation → int16-activation
  predictor arm (NNTool 16-bit option) — flag as a BRIDGE question, not a
  sim fix.
- B3 fails → retrain that head on the QUANTIZED latent (seconds, a new
  lock entry per G1 rules) — heads are cheap, the WM is not.
- B4/B5 fail with B1–B3 green → thresholds are calibrated to float
  probability shapes; temperature re-bake on quantized logits
  (`calibrate_heads` exists, AUC-invariant) is the named knob.

## Kill criteria

None — every outcome is a finding: parity green = the embedded budget's
missing measurement lands (writing/#8 centerpiece); parity red = the
hostile layer gets named, the fix is priced, and the 512 KB story gains
its first honest asterisk.

## K0 results (2026-07-11 — `eval_int8_parity --k0`, k0_results.json)

**Instrument check first:** the float arm reproduces unified_wm_v1's
published per-world numbers bit-close (champion 0.6572/0.9335/0.9314,
unified 0.8211/0.9177/0.9557 — the gate table's 0.657/0.933/0.931 and
0.821/0.918/0.956), and the batched-encode-vs-collector assert held
(<1e-4). Same loop, same split, cpu.

**B1 — transit per-world AUC@32 (bar: worst ΔAUC ≥ −0.010, int8pc):**

| WM | world | float | int8pc | Δ | int8pt | gray |
|---|---|---|---|---|---|---|
| champion | classic | 0.6572 | 0.6716 | +0.014 | 0.6727 | 0.4175 |
| champion | dense | 0.9335 | 0.9454 | +0.012 | 0.9450 | 0.8169 |
| champion | **moving** | 0.9314 | 0.9152 | **−0.016 ✗** | 0.9116 | 0.8270 |
| champion | auc32 | 0.8963 | 0.8935 | −0.003 | 0.8912 | 0.5917 |
| unified | classic | 0.8211 | 0.8146 | −0.007 ✓ | 0.8030 | 0.6968 |
| unified | dense | 0.9177 | 0.9541 | +0.036 ✓ | 0.9527 | 0.4447 |
| unified | moving | 0.9557 | 0.9537 | −0.002 ✓ | 0.9559 | 0.8545 |
| unified | auc32 | 0.9314 | 0.9246 | −0.007 | 0.9244 | 0.7148 |

**Verdict: unified PASSES B1** (worst world −0.007); **champion FAILS
B1 on moving (−0.016)** — as pre-registered, this releases the K1
calibration knob (1024→2048 / percentile clipping), one change at a
time. Note the champion's classic/dense actually IMPROVE under
quantization (noise-as-perturbation on its weak slices); the overall
auc32 Δ is −0.003 — the failure is one world's margin, not a collapse.

**B2 — indoor detection probe (bar: ΔAUC ≥ −0.015):** float 0.9779 →
int8pc **0.9738 (Δ −0.004) ✓ PASS**; int8pt 0.9759; gray 0.9528;
gray+int8pc 0.9418.

**SNR names the hostile layer: `pred.trunk.0` at 22.5 dB** (next-worst
`enc.proj.1` 29.3; everything else 37–166 dB). Mechanism reading: the
trunk's input is the CONCAT of z (64-d latent) and a (4-d action) —
one per-tensor activation scale must span both distributions, so the
narrower branch eats the quantization noise. A split-scale quant at the
concat seam (two quant nodes before concat — SQ8-legal) is the named
mechanism-level candidate; the pre-registered K1 knob (wider/percentile
calibration) is played first.

**The monochrome arm (informational, now measured):** transit collision
prediction COLLAPSES on luminance-only input — champion auc32
0.8963→**0.5917** (classic 0.4175, below chance), unified
0.9314→**0.7148** (dense 0.4447, below chance) — while indoor detection
mostly holds (0.9779→0.9528, −0.025). The AI-deck's stock camera is
monochrome: as-is, the transit WM's collision channel would be badly
degraded on that sensor; the detection story survives. Honest caveat:
the sim's palette (orange boxes, coloured pillars vs grey walls) may
overstate colour reliance vs real-world texture; still, the bridge
needs either a colour sensor or a gray-trained WM (retrain-class) —
this number goes straight into writing/#8 and the bridge-readiness
ledger. (gray+int8pc tracks gray: quantization is not the binding
constraint there.)

## B4 results (2026-07-11 — `eval_int8_parity --closed-loop`, b4_results.json)

**FAIL — and the failure's shape is the finding.** Unified WM, n=60,
identical seeds, WMPolicy closed loop:

| arm | crash | min_clear | false-evasion | reached | lead_ms |
|---|---|---|---|---|---|
| float | 0.214 | 0.387 | 0.056 | 1.000 | 216 |
| int8pc | **0.357** | 0.318 | **1.000** | 1.000 | 313 |

Δcrash **+0.143** (bar ≤ +0.030, float CI ±0.124) → **B4 FAIL**. The
float arm again reproduces the published closed-loop record (21% / ~6%
— unified_wm_v1), so the instrument is sound.

**Mechanism: rank survives, calibration does not.** B1 showed the
quantized model's AUC intact (−0.007) — the ORDERING of dangers is
preserved. But false-evasion pegged at 100% and the trigger fires
~100 ms earlier: quantization (SNR already named `pred.trunk.0`, the
z‖action concat seam) shifts the warn heads' PROBABILITY VALUES upward,
and `WMPolicy`'s thresholds (relative warn-margin 0.4 + absolute crit
backstop) were calibrated to the float probability landscape. Every
clear-path flight now trips a needless evade; in-path, spurious early
evasions push the drone into worse geometry (min_clear 0.39→0.32) and
crash rises 14 pts. The house refrain, one level down: **a
rank-preserving detector is not the same aircraft** — AUC parity (B1)
does not imply flight parity (B4).

Pre-registered decision rule fires: with B1(unified)/B2 green and B4
red, the named knob is a **temperature re-bake on the QUANTIZED logits**
(`eval/calibrate_heads.py` exists and is AUC-invariant by construction)
— refit T so the quantized probability landscape matches what the
thresholds expect, then re-fly B4. One knob, one run. (The champion's
B1 calibration knob — 1024→2048 / percentile — remains a separate,
independently released knob.)

## K1 pre-registration (2026-07-11, before the knob runs)

Two released knobs, one change each, choices argued before numbers:

- **K1a — percentile activation calibration (champion B1 re-read).** Of
  the pre-registered pair "1024→2048 OR percentile clipping", percentile
  is the mechanism-consistent pick: min/max calibration is hostage to
  the single largest outlier (a WIDER sample can only widen ranges and
  coarsen resolution — 2048 would likely make it worse, not better);
  the moving world's motion streaks are exactly where outlier
  activations live. Rule: per calibration batch, take the 0.1/99.9
  percentiles of the input; run lo/hi over batch percentiles. Read: B1
  champion, arms float + int8pc@p99.9, same everything else. Bar
  unchanged (worst world ΔAUC ≥ −0.010).
- **K1b — temperature re-bake on the QUANTIZED logits (B4 re-fly).**
  `calibrate_heads`' own recipe, applied to the quantized graph: fit one
  T per (horizon, ring) by masked BCE on the cf-oracle candidate labels
  over TRAIN rollouts of the combined union (rooms auto-drop out — their
  vis mask is 0 by the cf-loss room fix, so the fit lives on the transit
  frames the closed loop actually flies); wrap the quantized cheads in a
  logits/T scale (algebraically = bake w/T, b/T; on GAP8 it folds into
  the output dequant scale, zero extra compute). No percentile knob here
  — K1b isolates the temperature change on top of the recorded int8pc
  arm. Read: B4, n=60, identical seeds; Δ judged against the recorded
  same-tool float arm (same seeds/device/loop — noted, not re-flown).
  Bar unchanged (Δcrash ≤ +3 pts AND inside float CI; plus
  false-evasion must return to single digits for the mechanism story to
  count as CONFIRMED).

## Status

- [x] Pre-registration committed (this file, before any number)
- [x] K0: B1 + B2 + SNR + gray — **unified int8pc parity GREEN (B1 ✓ B2 ✓);
      champion B1 FAIL on moving (−0.016) → K1 calibration knob released;
      hostile layer named (pred.trunk.0, concat seam); monochrome gap
      measured (transit collapses, detection holds)**
- [x] K2a: B4 closed-loop — **FAIL (Δcrash +0.143, false-evasion 0.056→1.000):
      quantization preserves rank (B1 ✓) but shifts probability values;
      thresholds are float-calibrated → temperature-re-bake knob released**
- [x] K1 pre-registered (percentile pick argued; temperature recipe fixed)
- [x] K1a: **the calibration road is closed, both ways.** Percentile
      p99.9 made it WORSE (moving −0.028, dense −0.020 — the tails carry
      signal; my outlier hypothesis was wrong for this model, measured),
      and 2048-sample min/max reproduced K0 to the third decimal
      (moving −0.0161 vs −0.0162 — as mechanism-predicted, a wider
      min/max sample can only widen). **The champion's B1-moving −0.016
      is a real, calibration-insensitive int8 cost.** The unified WM
      loses only −0.002 on the same world → one more measured argument
      that the unified WM is the embedded-path artifact (it already wins
      every WM-owned job in float). (k1a_results.json, k1a2_results.json)
- [ ] K1b run: TempScale(quantized cheads) → B4 re-fly (in flight)
- [ ] B3 heads; B5 yaw-scan flight (after the temperature story settles)
- [ ] Verdict

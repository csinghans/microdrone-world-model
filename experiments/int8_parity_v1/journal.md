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
- [x] K1b: **temperature REFUTED as the fix — and it sharpens the
      mechanism.** The fitted T are all ≈1.0 (0.87–1.10 across
      horizons/rings, 40 fit rollouts): on the natural candidate-label
      distribution the quantized logits are NOT globally inflated. Yet
      the re-flown B4 is unchanged (crash 0.381, false-evasion 1.000).
      So the earlier story ("quantization shifts probability values
      upward") is wrong as stated — measured. Refined mechanism:
      `WMPolicy`'s trigger reads the RELATIVE warn-margin BETWEEN
      candidate actions; quantization noise at the z‖action concat seam
      (`pred.trunk.0`, 22.5 dB) is uncorrelated across candidates, and
      margins AMPLIFY uncorrelated noise — in clear scenes the trigger
      sees spurious "this action is far safer" spreads everywhere. A
      global temperature cannot remove between-candidate noise.
      (k1b_results.json)

## K1c pre-registration (before the run)

The K0-named mechanism candidate, now first in line: **split-scale
activation quantization at the concat seam** — quantize z (64-d) and a
(4-d) with SEPARATE calibrated ranges before the trunk Linear (two quant
nodes before concat; SQ8-legal, zero extra weights). Prediction on
record: `pred.trunk.0` SNR rises well above 22.5 dB, and if the
between-candidate-noise mechanism is right, B4's false-evasion falls
away from 1.000. Reads: (1) single-leaf SNR with split, (2) B4 re-fly
with full int8pc + split at the seam (identical seeds; float reference
= recorded arm). Bar unchanged. If B4 still fails at high SNR, the
pre-registered fallback is the int16-activation predictor arm — flagged
as a BRIDGE question, not a sim fix.

- [x] K1c block 1: **the mechanism is CONFIRMED — and it is finer than
      predicted.** Split-scale at the seam left the single-leaf SNR
      unmoved (22.5 → 22.7 dB) yet the flight RECOVERED: false-evasion
      **1.000 → 0.0556 (exactly the float value)**, min_clear
      0.318 → 0.411 (above float's 0.387), crash 0.357 → 0.262. The two
      reads together pin it: z's quantization noise is COMMON-MODE
      across candidates (same z feeds every candidate — it cancels in
      margins, and it dominates the absolute-error SNR), while the
      killer was the 4 ACTION dims sharing a scale sized by the 64-d
      latent's range (~25 effective levels on [−1,1] → the differences
      BETWEEN candidate actions were quantization-randomized). Splitting
      gives actions their own 255-level scale; candidate
      distinguishability returns; margins mean something again.
      **Instrument lesson: the SNR probe measures absolute logit error
      and is blind to the differential (between-candidate) error the
      deployed trigger actually reads.**
      Bar arithmetic: false-evasion single-digit ✓ (mechanism clause);
      Δcrash +0.048 vs the +0.030 clause — a 2-crashes-in-42 miss inside
      the float arm's ±0.124 CI = **borderline as written**. The house
      recheck rule applies: pool, never replace — block 2 at fresh seeds
      (seed0=2000, float + int8pc+split, n=60), pooled Δ decides.
      (k1c_results.json)
- [x] K1c block 2 + pooled verdict: **B4 FAILS as written, and honestly.**
      Block 2 (seed0=2000): float crash 0.1905 / FE 0.000; int8pc+split
      crash 0.3095 / FE 0.0556. Pooled n=84 in-path: float **17/84 =
      0.202**, split **24/84 = 0.286**, Δ **+0.083** vs the +0.030
      clause (inside the ±0.086 float CI, but the clause binds — the
      recheck moved the estimate AWAY from the bar). The split fixes the
      false-evasion catastrophe in both blocks (mechanism CONFIRMED
      twice; a small residual 0.056 remains), but a real crash cost
      survives: z's noise is only common-mode BEFORE the trunk's ReLU —
      the nonlinearity re-mixes it differentially in exactly the
      dangerous-geometry states where margins decide evade direction.
      (b4_block2_results.json)

## K1d pre-registration (the last named fallback, before the run)

**int16 activations on the predictor path** — the pre-registered bridge
option (NNTool has a 16-bit activation mode; weights stay int8). Applied
to every `pred.*` leaf: activation step shrinks 256×, so the
differential noise the trunk's ReLU re-mixes should drop below margin
relevance while the encoder stays fully int8 (its noise is common-mode
up to z). Prediction on record: B4 crash returns to the float band
(pooled Δ ≤ +0.030) with false-evasion staying single-digit. Read: B4 at
seed0=1000 (float re-flown same-run), pool with block 2 if borderline.
If it fails too, B4 closes as an honest negative: quantized WMPolicy
flight needs QAT or a margin re-tune — a future campaign, priced beyond
Q1's PTQ scope, and writing/#8 reports the parity table with that
asterisk.

- [x] K1d: **crash clause PASSES exactly (Δ +0.000 — 9/42, bit-equal to
      float; min_clear 0.408 above float), but false-evasion flips BACK
      to 1.000** (K1c's split-only arm had it at 0.056). The int16
      predictor activations shift the z_hat values feeding the (still
      8-bit) cheads; the clear-run margin distribution moves back across
      the trigger threshold. (k1d_results.json)

## B4 verdict — FAIL, with the mechanism fully mapped

Four PTQ arms, each fixing one clause and breaking another:

| arm | crash Δ (bar +0.030) | false-evasion (float 0.056) |
|---|---|---|
| int8pc | +0.143 ✗ | 1.000 ✗ |
| int8pc + T (K1b) | +0.167 ✗ | 1.000 ✗ (T≈1: not a calibration offset) |
| int8pc + split (K1c) | +0.083 pooled ✗ | **0.056 ✓** (mechanism confirmed 2×) |
| int8pc + split + p16 (K1d) | **+0.000 ✓** | 1.000 ✗ |

The meta-finding: **false-evasion is an ANY-over-the-run statistic** —
one spurious margin among ~300 decisions flips a whole flight, so
per-decision noise that is irrelevant to AUC (B1 green throughout) gets
amplified to 0↔1 swings by the trigger's max-statistics. Under PTQ, the
relative-margin trigger is knife-edge: every point fix (temperature,
split scales, 16-bit acts) reshuffles WHICH clause fails. The honest
close: **PTQ alone does not buy closed-loop flight parity for a
margin-triggered WMPolicy.** The named legitimate re-openings (fresh
pre-registration required): re-fit the trigger's MARGIN_WM/backstop on
the QUANTIZED probability landscape (a decision-layer analogue of
temperature — the likeliest cheap win), or QAT. Both priced beyond this
campaign's PTQ scope. Deployment note for writing/#8: the models
quantize (B1/B2 green); the CONTROLLER's thresholds are float-tuned —
"a rank-preserving detector is not the same aircraft" now has its
mechanism chain: rank ✓ → probabilities ✓ (T≈1) → per-candidate
differentials ✗ (action scale, fixed by split) → threshold-adjacent
margin mass ✗ (any-trigger amplification, open).

- [x] B3: **all three heads FAIL as shipped** — yaw 0.9818→0.9652
      (−0.017), low 0.8692→0.8247 (−0.044), person 0.8932→0.8691
      (−0.024) vs the −0.015 bar. The contrast with B2 (linear probe
      RETRAINED per arm on the quantized latents: −0.004) names the
      mechanism: the shipped heads were trained on FLOAT latents and
      suffer a double shift (their own weight quantization + reading a
      latent distribution they never saw). The quantized latent itself
      still carries the signal — B2 proved it. (k2_results.json)
- [x] B5: **FAIL at correct 0.40 (bar 0.70) — but by MISS (0.55), not
      false alarm: FA 0.05 is BETTER than the float gate's 0.10;
      collision 0.00, return 0.90.** The symmetric finding of the
      campaign, now measured across both tracks: the transit margin-max
      trigger AMPLIFIES quantization noise into false positives
      (B4/false-evasion 1.000); the indoor confirm-k temporal filter
      SUPPRESSES false positives (FA better than float) but amplifies
      recall loss into misses (per-frame scores shift down vs the
      float-tuned thr=0.65, and demanding k consecutive hits compounds
      the deficit). Max-statistics amplify noise; consensus statistics
      amplify signal loss. (k2_results.json)

## K2c pre-registration — the heads knob (the rule fires as written)

The original decision table: "B3 fails → retrain that head on the
QUANTIZED latent (seconds)." One knob: refit each head (same
DetectionHead recipe, same train blocks) on the QUANTIZED encoder's
latents, then quantize the refit head — the full int8 stack, trained
where it lives. Reads: B3 re-scored (same fresh blocks, bar unchanged);
B5 re-flown with the refit yaw head (bars unchanged). Prediction on
record: B3 recovers to within −0.015 of the FLOAT stack (B2's −0.004
says the information survives), and B5's miss rate falls back toward
the float gate. Refit heads land in experiments/int8_parity_v1/artifacts/
(NOT the lock — deploying them is a G1-rules owner decision).

- [ ] K2c run: refit heads on quantized latents → B3 + B5 re-read
- [ ] Final verdict + writing/#8 handoff

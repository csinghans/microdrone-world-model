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

## Status

- [x] Pre-registration committed (this file, before any number)
- [ ] K0: B1 + B2 + SNR + gray
- [ ] K1: B3 heads
- [ ] K2: B4 closed-loop + B5 yaw-scan flight
- [ ] Verdict

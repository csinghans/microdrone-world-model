# low_head_int8_v1 — the last red cell: the near-floor head under int8

**Opened:** 2026-07-13 · **Prior:** `experiments/int8_parity_v1/` (Q1,
closed). B3's verdict left ONE residual: the low/near-floor head drops
−0.044 as shipped and −0.114 after the otherwise-winning K2c refit —
"grazing views are genuinely quantization-hostile." Q1's own
calibration docstring names the suspect: the activation calibration
corpus (`combined.npz`, the two-track training union) contains **no
rendered-target imagery and no near-floor frames** — the low head's
whole operating regime (z_cam 0.15–0.35 m, targets on the floor plane)
is outside the distribution that set every activation range.

## Hypothesis (K1, one knob)

Grazing-view frames produce activation statistics the calibrated
[lo, hi] ranges never saw; clipping destroys regime-specific signal in
the quantized latents — which also explains why the refit made things
WORSE (a head fit on degraded train latents learns the degradation,
which does not transfer across blocks). **The knob: add a low-regime
track to the calibration batch** — 256 frames from the low head's own
TRAIN collection (seed block 600000; the 610000 test block stays
untouched), paired with actions sampled seed-fixed from the standard
corpus (the predictor path needs actions; grazing frames carry none).
The standard 1024-frame sample is UNCHANGED — min/max calibration is
monotone in its data, so added frames can only WIDEN ranges: no new
clipping anywhere, and the guard risk is coarser steps for the
standard regime, which the guards below price.

## Reads and bars (frozen; all offline, no flights)

- **Primary (B3 low row, same float reference 0.8692):** with the
  augmented calibration, PASS iff the shipped head's Δ ≥ −0.015 OR the
  refit head's Δ ≥ −0.015 (the standing B3 bar, either configuration).
- **Guards (a calibration change is global):** yaw and person REFIT
  rows stay ≥ −0.015 (their passing configuration); B1 unified int8pc
  worst-world Δ ≥ −0.010 (K0's bar); B2 detection Δ ≥ −0.010.
- **Mechanism meter (declared, not barred):** the fraction of
  low-regime activations falling outside the OLD calibrated ranges
  (should be materially nonzero — the clipping the hypothesis needs)
  vs outside the NEW ranges (should be ~0).

REFUTED = neither configuration clears the bar with the regime in the
corpus → the low residual is not (mainly) a calibration-coverage
artifact; the named next suspects (fresh registration each) are
regime-specific percentile calibration or 16-bit encoder activations
for the low regime, and the residual stays honest in the meantime.

**Machinery (defaults bit-identical):** `_calib_batch` gains
`low_n=0` (0 = today's batch, byte-identical); `b3_heads`/guard reads
accept the augmented batch; `--low-calib` runs the whole read set.

## Status

- [x] Pre-registration (this file, before any number)
- [ ] K1: augmented calibration → B3 low (shipped + refit) + guards +
      mechanism meter → verdict

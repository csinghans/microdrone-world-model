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

## K1 results (2026-07-13 — lowcal_results.json)

**Mechanism meter: CONFIRMED** — 2 of 4 encoder leaves see low-regime
activations outside the standard ranges (worst excursion +8.1 %): the
clipping the hypothesis needed was real.

| head | shipped Δ (old calib) | refit Δ (old calib) | **shipped Δ (aug calib)** | refit Δ (aug calib) |
|---|---|---|---|---|
| yaw | −0.017 | +0.001 | **+0.0001 ✓** | −0.0009 ✓ |
| **low** | −0.044 | −0.114 | **−0.0086 ✓** | −0.0171 ✗ |
| person | −0.024 | +0.025 | **+0.0059 ✓** | −0.0238 ✗ |

Guards: B1 unified worst-world −0.0027 ✓, B2 +0.0000 ✓.

**Verdict: REFUTED as written** — the frozen guard demanded the
yaw/person REFIT rows hold (their Q1-era passing configuration), and
person-refit reads −0.0238. The bar binds; no re-litigation.

**What the table actually shows (recorded in full):** the primary
hypothesis over-delivered — with the near-floor track in the corpus,
**all three heads pass AS SHIPPED**, and the refit crutch (invented to
compensate calibration damage) now HURTS where the damage is gone
(person-refit overfits healthier quantized train latents that the
float-trained head generalizes past). The letter of the guard broke on
a row nobody would deploy; the configuration everyone would deploy —
shipped heads, regime-complete calibration — passes every offline bar
measured here, and simplifies the int8 recipe by deleting the
per-head refit step entirely.

## K2 (pre-registered before the run) — the one unread number: flight

The offline table cannot certify a recipe change; Q1's B5 flight gate
can. **K2: re-fly B5 (the yaw_v1 flight gate on the fully quantized
indoor stack) with the AUGMENTED calibration and the SHIPPED yaw head
(no refit).** Bars: B5's standing absolutes, unchanged — correct
≥ 0.70, FA ≤ 0.20, collision ≤ 0.05, return ≥ 0.80 (float record
0.70/0.10/0.00/1.00; Q1's refit-head B5 read 0.75/0.10/0.00/1.00).
- PASS ⇒ the candidate int8 indoor recipe simplifies to **int8pc +
  regime-complete calibration, shipped heads, zero refits** — recorded
  as the measured alternative to the Q1 recipe; adopting it (lock/
  packaging) stays the owner's call.
- FAIL ⇒ the flight layer disagrees with the offline table; the Q1
  recipe (refits) stands and this campaign closes as an honest
  negative with the offline observation on file.

**Machinery:** `b5_yaw_scan` gains `calib=None` (default = today's
path, byte-identical); CLI `--low-calib-b5`.

## K2 results (2026-07-13 — lowcal_b5_results.json) — PASS, best B5 on record

**correct 0.80 / FA 0.00 / miss 0.20 / collision 0.00 / return 0.95**
— every standing bar passed (0.70/0.20/0.05/0.80), and the zero-refit
stack beats both the float record (0.70/0.10) and Q1's refit-head B5
(0.75/0.10) on correct-find AND false alarms. Honest note: return
0.95 vs the float record's 1.00 — one return miss, inside the
standing absolute bar.

## Campaign verdict — the last red cell closes, and the recipe gets simpler

The low head's quantization hostility was never about the regime
being hard; it was about the regime being ABSENT from the calibration
corpus (meter: 2/4 encoder leaves clipping, worst +8.1 %). With the
regime present, **the measured int8 indoor recipe simplifies to:
int8pc weights + regime-complete calibration (two-track union + 256
near-floor frames) + SHIPPED heads — zero per-head refits** — and it
flies better than the refit recipe it replaces. The embedded lesson,
one line: **calibrate on every regime you fly, and the crutches
delete themselves.** K1's letter-verdict (REFUTED on the person-refit
guard row) stands on the record beside this: the guard broke on a
configuration the simpler recipe no longer contains.

Adoption (lock/packaging of the calibration recipe + retiring the
qlat refit artifacts) is the owner's call — not done here. Q1's
recipe remains the recipe of record until then.

## Status

- [x] Pre-registration (this file, before any number)
- [x] K1: **REFUTED as written** (person-refit guard −0.0238), with
      the over-delivery recorded: all three heads pass AS SHIPPED
      under regime-complete calibration; meter confirms the clipping
- [x] K2 pre-registered (this section, before its number)
- [x] K2: **PASS — 0.80/0.00/0.00/0.95, the best B5 on record; the
      zero-refit recipe is measured end to end. Adoption = owner.**

# stability_v2 — the revised band [1.0, 8.0]: dead where THIS recipe lives

Opened 2026-08-31, from stability_v1's K0 NO-GO (same-day): the ceiling at
4.0 bought stability (z-std max 1.74) but re-equilibrated the whole latent
space onto the lower hinge (std med 2.66 -> 1.00, latent energy halved) and
the apex's moving ranking paid 0.054 — a clean causal read, since seed-0
training is bit-deterministic on this harness. The design rule survived;
the reference set did not: **the ceiling must be dead at the recipe's OWN
healthy operating point** (96d128 @ 80 ep: std max 6.44), not merely at
other recipes' (64-res champions <= 2.53).

This is the registered revision, not a retry: stability_v1's frozen clause
("a revised band is a NEW pre-registration") is being exercised, with the
band chosen by the corrected rule BEFORE any new number exists.

## Pre-registration (committed before any number)

### The knob (single)

`VAR_HI = 4.0 -> 8.0` (`world_model/losses.py`). 8.0 clears the recipe's
measured healthy maximum (6.44) with margin and sits below the measured
explosion (12.05, med 4.21). `VAR_LO = 1.0`, `LAMBDA_VAR`, call site, diet,
seed, batch, D, strips — all unchanged from stability_v1 / perception_v2.

### Arms

- **K0' — 80 epochs, band [1, 8]** (the control, now with a REGISTERED
  falsifiable prediction): if the ceiling is truly dead along the entire
  80-epoch trajectory, seed-0 bit-determinism should reproduce the
  perception_v2 apex — checked by sha256 against
  `52df88a35e135f561574168189c0ba56ee32b21b107e8cb94c3c3755f21609f3`
  (`experiments/perception_v2/artifacts/wm_96d128.pth`). Bit-identity makes
  "the band is dead where it claims to be" an empirical claim. If shas
  differ but bars pass, the ceiling touched the trajectory somewhere —
  recorded, still a pass on the bars.
  `python -m scripts.train --epochs 80 --batch 64 --seed 0 --latent-d 128
  --data output/combined_96.npz
  --out experiments/stability_v2/artifacts/wm_96d128_g3.pth`
- **K1' — 160 epochs, band [1, 8]** (the e160 acceptance rerun — the
  campaign's actual question). Same command, `--epochs 160`,
  `--out .../wm_96d128_g3_e160.pth`. Released ONLY if K0' passes; the queue
  gate now PARSES the instrument logs (no in-process model reload — the
  stability_v1 gate was OOM-killed doing that; rule 6 fix).

### Bars (frozen; baseline row unchanged from stability_v1)

K0' (same five as stability_v1, VAR_HI-adjusted):
- dense >= 0.985; veer val AND widened >= 0.95
- moving >= 0.8691, classic >= 0.7682
- val z-std max <= VAR_HI + 0.5 = 8.5
- budget unchanged (264.2 KB / est 17 ms)

K1' ("duration no longer destabilizes"):
- no-op MSE@32 <= 2x K0's no-op (the broken pair was 7.6 -> 99.4)
- val z-std max <= 8.5
- self-consistency, restated on the HOLDOUT instrument (stability_v1's
  "train-val AUC@32 >= 0.85" was mis-calibrated — the healthy 80-ep model
  itself prints 0.62 on the combined val, which includes the room world;
  recorded as a prereg defect, never graded against): holdout dense >= 0.90
  AND veer val >= 0.90.
- K1' is NOT held to the full K0 bar set (160 epochs is a different recipe
  point; the claim under test is stability, not apex-preservation). Its
  full per-world row is recorded for the record.

### GO / NO-GO (frozen)

- K0' passes + K1' passes -> **GO**: the guard is closed two-sided; the
  temporal gate from perception_v3 is satisfied by measurement.
- K0' fails -> **NO-GO**: with the ceiling provably dead (or near-dead) at
  80 epochs, a K0' failure would falsify the bit-determinism assumption or
  reveal ceiling contact below 6.44 — either is a finding; stop and record.
- K0' passes, K1' fails -> **NO-GO**: a ceiling alone does not stabilize
  the 160-epoch recipe (the EMA-chase may need a different fix: target-side
  normalization, momentum schedule — each a new registration). The
  two-sided guard STAYS in the code either way (it is strictly safer than
  one-sided and provably free at 80 epochs if the sha prediction held).

### Honesty clauses

Inherited verbatim from stability_v1 (unguarded `z_c_last`, mean-offset
drift, MPS two-tier language, journal-side artifacts only), plus:
- This revision is sanctioned by v1's own NO-GO clause and is chosen by a
  rule, not by the failing number: 8.0 was derivable from the SAME
  measurement table committed in v1's prereg before any training ran.
- If K0' bars pass but moving lands between 0.8691 and baseline 0.8891,
  that residual price is recorded honestly (pass is pass; the delta is not
  hidden behind the bar).

---

(verdicts land below when the queue completes)

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

---

## Mid-campaign record — 2026-08-31: K0' NO-GO on the bars, the sha prediction falsified — and the falsification is the finding

Queue record (logs `output/sv2_*`): the log-parse gate ran cleanly (rule 6
fix verified — no OOM) and correctly held K1' back.

| read (K0', 80 ep, band [1.0, 8.0]) | value | bar | verdict |
|---|---|---|---|
| **dense** | **0.9779** | >= 0.985 | **FAIL** (baseline 0.9965) |
| classic | 0.8555 | >= 0.7682 | pass (+0.067) |
| moving | 0.8701 | >= 0.8691 | pass (by 0.001) |
| veer val / widened | 1.0000 / 0.9860 | >= 0.95 | pass |
| val z-std max | 4.00 | <= 8.5 | pass |
| budget | 264.2 KB / 17 ms | unchanged | pass |
| sha(g3) vs sha(apex) | c0f02362… vs 52df88a3… | predicted equal | **PREDICTION FALSIFIED** |
| latent MSE / no-op (recorded) | 3.750 / 5.930 | — | baseline pair 5.289 / 7.563 |

Two candidate mechanisms, distinguishable by one cheap control:

1. **The dead term is not bit-neutral.** `relu(std - 8).mean()` evaluates
   to exactly 0 with exactly-0 gradients, but its PRESENCE changes the MPS
   kernel schedule / accumulation order; a one-ulp divergence compounds
   chaotically over 80 epochs into a different endpoint. Then K0' is a
   numerically perturbed re-draw of the frozen recipe — and the spread it
   reveals (dense 0.9965 vs 0.9779, moving 0.8891 vs 0.8701 across two
   draws of the same diet/seed) says **the apex row itself sits inside
   draw noise**, resurrecting the ROADMAP instrument lesson at 96-res.
2. **The ceiling touched the trajectory** (std transiently above 8 mid-run,
   invisible to the endpoint logger).

**C0 diagnostic, registered before running** (instrument validation, not a
knob): re-run the EXACT frozen recipe under the EXACT v0.17.0 code (git
worktree at `b250267` — the one-sided guard, byte-for-byte) with the same
diet/seed/flags, `--out experiments/stability_v2/artifacts/wm_96d128_c0.pth`.
- Prediction: sha(c0) == sha(apex) (`52df88a3…`) — re-verifying the
  representation_v1 bit-determinism finding on today's environment.
- c0 == apex  -> mechanism 1 stands: same-code determinism holds, the dead
  term's numeric perturbation is real, and the K0'-vs-apex delta is a
  DRAW-NOISE measurement, banked as such.
- c0 != apex  -> bit-determinism itself no longer holds on this
  environment (drift since 2026-07): every same-code determinism claim
  gets re-scoped, and single-run model-axis reads at 96-res inherit the
  ≥3-draw rule immediately.
No bars move; K1' stays unreleased; the C0 read cannot rescue K0'.

---

## Final verdict — 2026-08-31: NO-GO on the frozen bar — and the C0 control turns the campaign into an instrument finding

C0 (exact v0.17.0 code, worktree at `b250267`, same diet/seed/flags):

| comparison | tensors differing | max abs diff | training print |
|---|---|---|---|
| apex vs C0 (same code) | **0** | 0.0 | MSE 5.289 / no-op 7.563 — digit-for-digit the pv2 log |
| apex vs g3 (band [1,8]) | 28 | 0.692 | MSE 3.750 / no-op 5.930 |

- **Bit-determinism RECONFIRMED at the tensor level** on today's
  environment. The registered sha-of-FILE check was the wrong instrument:
  torch's zip container drifted since July (576,275 -> 576,377 bytes,
  identical tensors, identical meta) — bit-identity claims compare
  state_dict tensors from here on (rule 6, banked).
- **Mechanism 1 confirmed, mechanism 2 refuted**: with the C0 control
  clean, g3's divergence is caused by the PRESENCE of the dead
  `relu(std - 8)` term — exactly-zero value and gradient, but a different
  MPS kernel schedule; one ulp compounds chaotically over 80 epochs.
  K0' is therefore a fair re-draw of the frozen recipe, and the
  apex-vs-g3 deltas (dense 0.9965 -> 0.9779, moving 0.8891 -> 0.8701,
  classic 0.7882 -> 0.8555) are a DRAW-NOISE measurement at 96-res:
  the first one this tier has. The ROADMAP instrument rule (single-seed
  model-axis reads spread; use >=3-draw means or flight gates) now has
  direct 96-res evidence — and it covers the apex row itself.

**K0' stays NO-GO** (dense 0.9779 < 0.985 — bars are immutable), but the
bar FRAMEWORK is what the campaign actually measured: a single-draw
apex-preservation bar cannot price a recipe change at 96-res, because any
code change — even a provably dead term — reshuffles the draw. The
two-sided guard stays in the code at [1.0, 8.0] per the pre-registered
clause, with its reasoning updated: its loss-level effect at healthy
operating points is exactly zero, its measured single-draw cost is
inside draw noise (mixed signs across worlds), and it caps the explosion
path. K1' remains unflown here (its release condition failed).

Banked findings:
1. Same-code seed-0 training is tensor-level bit-deterministic (2nd
   confirmation, new environment). File-sha is not the instrument.
2. Dead ops are not draw-neutral on MPS: recipe identity includes the
   op graph, not just the math.
3. First measured 96-res draw spread: dense +-~0.02, moving ~0.02,
   classic ~0.07 between two draws. Single-draw rows at this tier carry
   at least that uncertainty — the apex included.

**Disposition**: the BLOCKER's actual question — does the ceiling stop the
160-epoch explosion? — is still unmeasured (K1' was never released, twice,
by its own registration). It goes to stability_v3 with STABILITY-level
bars only, since apex-preservation at n=1 is now measured to be
un-gradable. stability_v2 closes NO-GO with the instrument re-scope as its
finding.

### Evidence interpretation audit — 2026-09-13 (no remeasurement)

The C0 tensor comparison and original NO-GO above remain recorded. C0
reproduced the old one-sided recipe; it did not observe upper-hinge
activation along g3's changed-code trajectory. The current logger measures
validation statistics after training, so this control cannot distinguish
the two proposed mechanisms or establish that the added term was always
dead. The MPS scheduling explanation and treatment of g3 as a pure redraw
remain hypotheses. See the [research audit](../../docs/RESEARCH-AUDIT-2026-09-13.md).

# perception_v3 — closing the pincer: two cheap knobs against four clauses

Opened 2026-07-25, on perception_v2's near-miss (commit fb01321): the
96 x D128 pincer landed its three predicted recoveries (veer double-
perfect, dense 0.9965, saturation 0.31) and left four failing clauses
— all 0.8807, classic 0.7882 (by 0.013), moving 0.8891, open-space
over-warn (+0.32/+0.24, gap3 0.0658). This campaign plays the two
cheapest hypotheses against that cluster, one knob per arm, common
baseline wm_96d128.

## Pre-registration (committed before any number)

### The knobs (both vs the wm_96d128 baseline; same diet, same seeds)

- **K0 `wm_96d128_e160`** — the under-training hypothesis: 80 epochs
  was frozen for a ~110 KB model; the 96 x D128 net carries ~2.4x the
  parameters on 2.25x the input. Single knob: epochs 80 -> 160.
- **K1 `wm_96d128s8`** — the bearing-resolution hypothesis: the
  open-space over-warn may be lateral aliasing at 4 strips over 96 px.
  Single knob: strips 4 -> 8 (80 epochs).
- **K2 `wm_96d128s8_e160`** (conditional): released ONLY if K0 and K1
  each improve >= 2 of the four failing clauses without losing any of
  the three passing ones (dense >= 0.9335, veer == 1.00, saturation
  <= 0.4658) — complementarity, measured before combination.

### Bars — the FULL original set, unchanged

B1 dense >= 0.9335 AND all >= 0.9264; B2 saturation <= 0.4658; B3
|gap3| <= 0.0284; G1 veer == 1.00; G2 budget < 512 KB / < 83 ms at 96;
G4 classic >= 0.8011, moving >= 0.9357. Instruments: the same-seed
96-res configs of record.

### GO / NO-GO (frozen)

GO — any arm passes the FULL set: opens perception_v4 (closed-loop at
96; instruments predict, the loop certifies). NO-GO — the pincer's
residue is not epochs and not strips: the verdict banks the moving/
temporal hypothesis (motion traded for detail — a single-frame latent
cannot rank movers it cannot see move) and the tier's honest state:
one operating point (96 x D128) that owns dense outright and a
residue that names the next quarter's question. Either way the 0.17
narrative ships after this campaign (user-directed).

### Honesty clauses

Inherited verbatim. The epochs knob is a RECIPE variation and is the
registered treatment of its arm — no other arm's epochs move. MPS
determinism per seed continues to make single-seed deltas exact.

---

(verdicts land below when the queue completes)

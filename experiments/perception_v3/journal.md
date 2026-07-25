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

---

## Mid-campaign record — 2026-07-25: K0 destabilizes, K1 is harness-blocked; K1' deviation registered

The queue autopsy (logs `output/pv3_*`, plus an empirical exit-code
repro):

- **K0 `e160` — the under-training hypothesis INVERTS.** The 160-epoch
  run destabilized: the target-latent scale exploded ~13x (no-op MSE
  7.6 at 80 epochs -> 99.4 at 160 — the variance guard bounds the
  latent's spread from BELOW only, and the EMA target chases the
  inflating online encoder; at 2x duration the drift compounds), and
  the heads' operating points collapsed with it (train-val AUC@32 0.62,
  veer 0.69). The recipe does not under-train at 80 — it destabilizes
  before 160 helps. Mechanism finding, banked: the one-sided variance
  guard is a named suspect for any long-duration recipe work.
- **K1 `strips 8 @ 96` — HARNESS-BLOCKED, not refuted.** MPS's
  AdaptiveAvgPool requires divisible sizes: 96 px -> a 12-column
  feature map, and 8 does not divide 12 (empirical exit-1 repro; the
  64-res feature map is 8 columns, which is why strips 8 ran fine in
  representation_v1). Harness fixed: `scripts.train` now fails LOUD
  with the valid divisor list before training.
- **Queue-hygiene lesson, recorded:** the budget heredoc broke the `&&`
  chain — everything after `EOF` ran unconditionally, so the DONE
  marker fired despite the K1 crash killing the chain. All queues from
  here run under `set -e` (CLAUDE.md's own background-queue rule,
  now applied to heredoc-bearing chains).

**K1' deviation, registered with rationale:** same aliasing hypothesis,
nearest FEASIBLE divisor — `strips 6` (10°/bin vs the baseline's
15°/bin; 12 divides evenly; 12-strips/5° stays available if the
direction confirms). Single knob vs wm_96d128 unchanged. The repaired
queue grades K0's corpse through the registered instruments for the
record, then flies K1'.

---

## Final verdict — 2026-07-25: NO-GO (both hypotheses dead); the residue gets its name

Repaired queue under `set -e` (logs `output/pv3_*`, `pv3b_verify_*`).

| arm | dense | classic | moving | veer val/widened | sat | gap3 | verdict |
|---|---|---|---|---|---|---|---|
| baseline wm_96d128 | 0.9965 | 0.7882 | 0.8891 | 1.00/1.00 | 0.3080 | -0.0658 | (near-miss) |
| K0 e160 (registered row) | 0.9170 | 0.8851 | 0.7694 | 0.875/**0.539** | — | — | **destabilized** (scale x13; rows self-inconsistent) |
| K1' s6 | **0.6250** | 0.7568 | 0.8208 | 1.00/**0.546** | 0.1656 | **-0.1740** | **refuted** |

- **The under-training hypothesis is dead twice over**: the 160-epoch
  run's latent-scale explosion (one-sided variance guard + EMA chase)
  stands as a banked mechanism finding; its registered-instrument rows
  are internally inconsistent — an unstable model, not a better one.
- **The lateral-pooling hypothesis is now refuted at TWO operating
  points**: strips 8 @ 64/D64 cost dense -0.19 (representation_v1);
  strips 6 @ 96/D128 costs dense -0.37 and breaks veer-widened. Finer
  horizontal pooling has never once helped this program. (Its
  saturation 0.17 is confidence about nothing — low saturation only
  matters next to ranking.)
- Budget never binds (280 KB / 17 ms).

**perception_v3 closes NO-GO. The pincer's residue keeps its four
clauses (moving ~0.89 since 96-res, classic by 0.013, open-space
over-warn, the all-row) and now has a NAME with evidence behind it:
the moving/temporal hypothesis** — every 96-res arm trades motion for
detail, and a single-frame latent cannot rank what it cannot see move.
That is not a pooling knob or a recipe knob; it is the next real
question (temporal input under the stability finding above — the
one-sided variance guard must be fixed before any long-memory recipe).

### The tier's honest standing state

`wm_96d128` remains the program's offline dense apex (0.9965 dense,
double-perfect veer, saturation 0.31, 264 KB / 17 ms) — NOT deployable
(full bars unmet; no closed-loop row exists; the instruments predict,
never certify). The perception tier's offline landscape is mapped:
one sweet spot, one governing ratio, one validated design law, one
named residue. The 0.17 narrative ships next (user-directed).

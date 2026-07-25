# perception_v2 — match capacity to input: the pincer at the sweet spot

Opened 2026-07-25, on perception_v1's close (commit ae2d692). The
tier's governing curve is banked: resolution is an inverted U peaking
at 96 under the fixed 64-d latent (dense 0.9177 -> 0.9947 -> 0.6999
across 64/96/128 — the compression ratio governs). Three campaigns
triangulate one design point: the trilogy showed capacity reallocates
when input is starved; K0 showed the latent starves when input is
rich; K1 showed it drowns when input is richer still. **This campaign
holds the measured sweet spot (96) and widens the latent — the
trilogy's knob, returning with input worth spending on.**

## Pre-registration (committed before any number)

### The knob

- **K0 `wm_96d128`**: img_res 96 (the measured peak), LATENT_D 128,
  strips 4, the frozen recipe (80 epochs, batch 64, seed 0) on the
  EXISTING `output/combined_96.npz` (same-seed apex diet — no data
  regeneration; the compression ratio halves to 216:1, between the
  64-res 192:1 and the 96-res 432:1 operating points). Artifact
  `experiments/perception_v2/artifacts/wm_96d128.pth`.
- **K1 `wm_96d128s8`** (conditional): strips 8 on top — released ONLY
  if K0 passes >= 2 primary bars (lateral resolution re-enters only
  after width is priced at the sweet spot).

### Bars — the FULL original set; the first arm required to pass everything

- **B1**: dense AUC@32 >= **0.9335** AND all >= **0.9264**.
- **B2**: dense warn saturation <= **0.4658**.
- **B3**: high-clutter |warn gap| <= **0.0284**.
- **G1**: veer val == 1.00. **G2**: budget < 512 KB and est < 83 ms at
  96 (pre-estimate: ~150 KB weights + 96-res activations => ~280 KB,
  ~18 ms — inside). **G4**: classic >= **0.8011**, moving >= **0.9357**.
- Instruments: the same-seed 96-res configs of record
  (transit_eval_holdout_96 / combined_96 / dense_recal --img-res 96).

### GO / NO-GO (frozen)

GO — K0 (or K1) passes B1+B2+B3 with ALL guards green: opens
perception_v3, the closed-loop phase (the dense probe arms and the
assist guardian arms at 96 — general_wm_v2's law in full force:
offline rows adopt nothing; the closed loop is the only certifier).
NO-GO — capacity at the sweet spot still cannot hold both worlds: the
verdict prices the width dose-response (64 vs 128 at 96-res) and the
remaining options (strips at width, conv depth WITH width, or the
accepted floor with the tier's curve as its evidence).

### Honesty clauses

Inherited verbatim (deterministic seed-0; contrast conservation — the
same-seed mixed diet; sha brackets; sacred checkpoints read-only;
instruments predict, never certify). Single knob vs wm_96: LATENT_D.
The D=128 downstream caveats stand as in the representation program
(dispatch Z_DIM, detection heads latent-bound — adoption concerns,
not offline-grading concerns).

---

(verdict lands below when the queue completes)

---

## K0 verdict — 2026-07-25: NO-GO (1/3 primary bars; K1 not released) — and the pincer's three predictions all landed

Queue as pre-registered (sha brackets green; logs `output/pv2_*`).

| clause | wm_96 (D64) | wm_96d128 | bar | verdict |
|---|---|---|---|---|
| dense AUC@32 | 0.9947 | **0.9965** | >= 0.9335 | pass (held AND rose) |
| all AUC@32 | 0.8912 | 0.8807 | >= 0.9264 | FAIL |
| veer val / widened | 0.375 / 0.923 | **1.000 / 1.000** | == 1.00 | **PASS — capacity bought it back** |
| dense saturation | 0.5205 | **0.3080** | <= 0.4658 | **PASS — smashed** |
| high-clutter |gap| (open bins) | 0.0278 (+0.23/+0.14) | 0.0658 (+0.32/+0.24) | <= 0.0284 | FAIL (open-space over-warn inflated) |
| classic / moving | 0.7386 / 0.8948 | 0.7882 / 0.8891 | >= 0.8011 / 0.9357 | FAIL by 0.013 / FAIL |
| budget | 207.3 KB / 17 ms | 264.2 KB / 17 ms | < 512 / < 83 | pass |

Primary bars: B2 PASS, B1 FAIL (dense-clause pass, all-clause fail),
B3 FAIL -> 1/3. **K1 (strips 8) NOT released** by the frozen rule.
**perception_v2 closes NO-GO.**

### The design point validated, the deficit rotated

Match-capacity-to-input predicted three recoveries and got all three:
veer snapped back to double-perfect, dense held at its ceiling
(0.9965), and saturation fell through its bar (0.62 -> 0.52 -> 0.31
across the three operating points). What remains is a DIFFERENT
failure cluster than any previous arm's: moving-world ranking (stuck
~0.89 since 96-res arrived) and open-space over-warn (+0.32/+0.24 —
the wide latent spends its new confidence in the wrong bins), dragging
the all-row; classic misses its guard by 0.013 — the closest full-pass
approach in fifteen trained arms.

### What a perception_v3 would weigh (named, not claimed)

- **Lateral resolution at width** (96 x D128 x strips 8): K1's shape,
  re-registrable fresh — the open-space over-warn is a bearing-
  resolution story in part.
- **Moving is its own axis**: no perception knob has touched moving's
  bar since 64-res (0.9557 -> ~0.89 at every 96/128 arm) — the
  temporal information lost to higher spatial res is a v3 hypothesis
  (moving needs motion; the single-frame latent trades it for detail).
- **The steps-vs-size control**: 80 epochs may under-train the 2.4x
  parameter model — recipe-frozen here, priceable there.
- Or bank the tier's curve and the near-miss as the honest state.

Run-to-run caveat: deterministic seed-0; single-seed operating points.

# perception_v1 — the sensor question: does the wall eat pixels?

Opened 2026-07-25. Design note: `docs/PERCEPTION-TIER.md`. The
surviving hypothesis after the representation program: the 64x64
camera is the information bottleneck for dense separation. The first
knob that ADDS sensor information rather than reallocating it: input
resolution, same architecture (conv weights are resolution-agnostic),
same recipe, same-seed mixed diet — only the pixels double.

## Pre-registration (committed before any number)

### The knob

- **K0 `wm_96`**: the unified recipe (strips 4, D 64, 80 epochs, batch
  64, seed 0) on the 1x mixed diet REGENERATED at img_res 96 with the
  same seeds (`combine_rollouts --n-transit 120 --n-indoor 80 --seed 0
  --img-res 96 --out output/combined_96.npz` — course-identical to the
  frozen `combined.npz`, pixel-denser). Artifact
  `experiments/perception_v1/artifacts/wm_96.pth`.
- **K1 `wm_128`** (conditional): released ONLY if K0's dense AUC@32
  exceeds the 64-res unified row by >= 0.01 (> 0.9277) — the
  resolution direction confirmed before doubling again.

### Instruments (same-seed 96-res configs; semantics unchanged)

1. `eval_wm_checkpoint --ckpt wm_96 --data output/transit_eval_holdout_96.npz`
   — the seed-777 holdout regenerated at 96 (120 rollouts, 40/40/40).
2. `eval_head_calibration --ckpt-a <unified> --ckpt-b wm_96 --data
   output/combined_96.npz` — the candidate's dense saturation/ECE row;
   the 64-trained incumbent's row at 96 input is OOD and carries that
   caveat (only the candidate's ABSOLUTE bars bind).
3. `eval_dense_recal --ckpt wm_96 --img-res 96` — seed-160 clutter
   suite at the candidate's res.
4. `onboard_budget(..., img_res=96)` — measured pre-registration:
   207.3 KB total, 8.3 M MACs (~17 ms est at GAP8 throughput).

### Bars — representation_v1's frozen set, re-pinned on 96-res configs

- **B1**: dense AUC@32 >= **0.9335** AND all >= **0.9264**.
- **B2**: dense warn saturation <= **0.4658**.
- **B3**: high-clutter |warn gap| <= **0.0284**.
- **Guards**: G1 veer val == 1.00; G2 budget total < 512 KB AND
  estimated decision latency < 83 ms at the candidate's res; G4
  classic >= 0.8011, moving >= 0.9357.
- Honest note on re-pinning: the 96-res instrument configs are
  same-seed regenerations (identical courses and labels; only pixel
  density changes), so the bars' semantics carry over; the 64-res
  baseline rows are the comparison column, not re-measured at 96.

### GO / NO-GO (frozen)

GO — K0 (or K1) passes B1+B2+B3 with guards green: opens perception_v2
(closed-loop at the candidate's res — the dense probe and the assist
guardian arms; general_wm_v2's law applies in full: offline rows adopt
nothing). NO-GO — resolution does not move dense separation: the
sensor-information hypothesis dies, and with it the last cheap-ish
tier; the honest verdict prices what remains (depth supervision under
the v0.5 warning, or the accepted floor with the strongest possible
evidence file).

### Honesty clauses

Inherited verbatim (deterministic seed-0 training; contrast
conservation — the mixed 1x diet, never dense-heavy; sha brackets;
sacred checkpoints read-only). Data-scale confound guard: K0 changes
ONLY pixels (same rollouts, same seeds, same length, same count).

---

(verdict lands below when the queue completes)

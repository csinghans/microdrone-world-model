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

---

## K0 verdict — 2026-07-25: NO-GO on the bars as written (1/3, G1/G4 broken) — and the program's first breakthrough: THE WALL EATS PIXELS

Queue as pre-registered (sha brackets green; a plugin-reload kill at the
train step was repaired and the chain resumed from the completed data
gens — logs `output/pv1_*`; the saved-path print bug found in the
autopsy is fixed in `3ec4c95`'s follow-up).

| metric | 64-res baseline | wm_96 (pixels only) | bar | verdict |
|---|---|---|---|---|
| dense AUC@32 | 0.9177 (unified) / 0.9335 (champion) | **0.9947** | >= 0.9335 | **pass, +0.061 over the best row ever** |
| all AUC@32 | 0.9314 | 0.8912 | >= 0.9264 | FAIL |
| classic / moving | 0.8211 / 0.9557 | 0.7386 / 0.8948 | G4 | **both broken** |
| veer val / widened | 1.0000 / 0.9720 | **0.3750** / 0.9231 | == 1.00 | **G1 broken** |
| dense warn saturation / ECE | 0.6211 / 0.0687 | 0.5205 / 0.0556 | <= 0.4658 | FAIL (right direction) |
| high-clutter |warn gap| | 0.0567 | **0.0278** | <= 0.0284 | **PASS** |
| budget | 137.3 KB / ~8 ms | 207.3 KB / ~17 ms | < 512 / < 83 | pass |

B1 dense-clause smashed, all-clause failed; B2 failed while moving the
right way; B3 passed. **Formally NO-GO** — no closed-loop phase opens
from this arm. **K1 (128-res) RELEASES** per the frozen rule (0.9947 >
0.9277, the direction confirmed).

### What the breakthrough says (and what the breakage says)

Same seeds, same recipe, same architecture — only pixels — and dense
ranking jumped +0.077 to near-perfect while every dense-side
calibration metric moved toward its bar (saturation 0.62->0.52, ECE
0.069->0.056, high-clutter gap 0.057->0.028). After eight arms of
reallocation failures, the FIRST information-adding knob moved the one
number nothing else could: **the sensor was the bottleneck. The wall
eats pixels.**

The breakage is the same finding read backwards: at a fixed 64-d
latent, reading 2.25x richer input costs the easy worlds their
features (classic -0.08, moving -0.06, veer val collapsed) — the
representation trilogy showed capacity reallocates when input is
starved; K0 shows the latent STARVES when input is rich. The two
results triangulate one design point: **capacity was never the wrong
knob — it was waiting for input worth spending it on.** That pairing
(resolution x width) is perception_v2's natural prereg if K1's reading
concurs; nothing is claimed for it here.

### Disposition

K1 `wm_128` flies as pre-registered (holdout/diet regenerated at 128,
same seeds; budget pre-estimate ~305 KB / ~30 ms — inside bounds).
The reading to watch: does dense hold ~0.99 while the easy-world trade
steepens (resolution-capacity imbalance confirmed), or does 128 lift
everything (pure-resolution road still open)?

---

## K1 verdict — 2026-07-25: NO-GO (dense collapses at 128); resolution is an inverted U peaking at 96 — the compression ratio governs

| res (pixels : latent dims) | dense | classic | moving | all | veer val | dense sat |
|---|---|---|---|---|---|---|
| 64 (192:1) | 0.9177 | 0.8211 | 0.9557 | 0.9314 | 1.000 | 0.6211 |
| **96 (432:1)** | **0.9947** | 0.7386 | 0.8948 | 0.8912 | 0.375 | **0.5205** |
| 128 (768:1) | **0.6999** | 0.6499 | 0.9292 | 0.8585 | **1.000** | 0.6509 |

K1 fails every bar that matters (budget passes: 305.3 KB / ~29 ms).
**perception_v1 closes: both knobs formally NO-GO** — and the campaign
banks the tier's governing curve. The wall eats pixels AT THE RIGHT
DOSE: 96-res is a sharp sweet spot for dense under the fixed 64-d
latent; at 128 the compression ratio crosses a cliff and everything
drowns (while veer — the relative judgment — snaps back to perfect:
the latent triages, and what it keeps rotates with the dose).

### The two-campaign triangulation, now three-legged

1. Trilogy: at 64-res input, adding capacity only reallocates.
2. K0: at 96-res input, the 64-d latent starves the easy worlds.
3. K1: at 128-res input, it starves everything.

One design point survives all three: **match capacity to input.**
perception_v2's prereg writes itself — hold the measured sweet spot
(96), widen the latent (the trilogy's knob, returning WITH input worth
spending on), and demand the FULL original bar set: dense >= 0.9335
AND all >= 0.9264 AND saturation AND gap AND veer == 1.00 AND G4 —
the first arm in the program required to pass everything at once.

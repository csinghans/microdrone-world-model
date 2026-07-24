# representation_v2 — the data tier: does the wall eat rollouts?

Opened 2026-07-24, on representation_v1's NO-GO (commit dea29fa). The
architecture tier died with an unusually specific corpse: both capacity
knobs traded dense ranking for classic at the frozen 120-transit-rollout
diet, finer strips made saturation WORSE, and the budget never bound —
**the binding resource is data, not silicon**. This campaign plays the
clean next knob: the SAME architecture, three times the world.

## Pre-registration (committed before any number)

### The knob

- **K0 `wm_3x`**: the unified architecture (strips 4, D 64), trained on
  a 3x diet — `combine_rollouts --n-transit 360 --n-indoor 240 --len 120
  --seed 0 --out output/combined_3x.npz` (the v1 ratio 3:2, tripled;
  seed structure identical to the frozen 1x diet). Epochs 80, batch 64,
  seed 0, `--out experiments/representation_v2/artifacts/wm_3x.pth`.
- **K1 `wm_3x_s8`** (conditional): strips 8 on the 3x diet — released
  ONLY if K0's dense AUC@32 > **0.9277** (unified + 0.01: the data
  direction confirmed before resolution re-enters).

### Bars and guards — inherited from representation_v1's freeze, verbatim

B1 dense AUC@32 >= 0.9335 AND all >= 0.9264; B2 dense warn saturation
<= 0.4658; B3 high-clutter |warn gap| <= 0.0284 (the separation-AUC
clause is DROPPED with cause: v1 measured it instrument-constant —
geometric, 0.7358 for every arm — a recorded drafting flaw, not a bar
move; this is a new campaign's prereg citing a measured fact). Guards
G1 veer == 1.00, G2 budget < 512 KB, G4 classic >= 0.8011 / moving >=
0.9357. G3 (draw noise) is retired with cause: v1's control reproduced
the unified checkpoint to four decimals — seed-0 training is
deterministic on this machine, the floor is 0.000.

### Honesty clauses

- 80 epochs on 3x data = 3x optimizer steps: the knob as framed is "the
  diet at the frozen recipe (80 passes)". If K0 passes, a steps-matched
  control (27 epochs on 3x) is the named follow-up that separates
  more-data from more-steps BEFORE any closed-loop claim.
- The 3x diet is a NEW frozen file (`combined_3x.npz`); the v1 diet
  (`combined.npz`) is untouched. Sacred checkpoints read-only;
  `flight_mode --verify` brackets the queue.
- GO/NO-GO inherits v1's rule: a candidate passing B1+B2+B3 with guards
  green opens the closed-loop phase; NO-GO prices the data tier at 3x
  and the honest verdict says whether the slope even points up
  (dense AUC and saturation vs the 1x row are the dose-response read,
  bar or no bar).

---

(verdict lands below when the queue completes)

---

## Verdict — 2026-07-24: K0 1/3 bars, K1 unreleased; the wall does not eat rollouts — dense COMPETES with the curriculum

Queue as pre-registered (sha checks green; 480/120 train/val rollouts,
21182 train samples; logs `output/rep2_*`).

| metric | unified (1x) | wm_3x (3x) | bar | verdict |
|---|---|---|---|---|
| AUC@32 all | 0.9314 | **0.9512** | >= 0.9264 | pass (highest ever on this instrument) |
| AUC@32 dense | 0.9177 | **0.8417** | >= 0.9335 | **FAIL** (-0.076) |
| AUC@32 classic / moving | 0.8211 / 0.9557 | 0.9225 / 0.9620 | G4 | pass (+0.10 classic) |
| dense warn saturation | 0.6211 | 0.7155 | <= 0.4658 | **FAIL** (worse) |
| high-clutter warn gap | -0.0567 | **-0.0121** | |gap| <= 0.0284 | **PASS** (4.7x smaller) |
| veer val / widened | 1.0000 / 0.9720 | 1.0000 / 0.9860 | == 1.00 | pass |

B1 FAIL, B2 FAIL, B3 PASS -> 1/3. K1 (strips 8 on 3x) NOT released
(dense 0.8417 < 0.9277). **NO-GO** — the closed-loop phase stays shut.

### The dose-response, read (the verdict the prereg promised)

Dense rollouts went 40 -> 120 and dense ranking FELL. Everything else
rose — the 3x model is the best GENERAL anticipator ever measured here
(all 0.9512, classic +0.10, veer 0.986, high-clutter calibration 4.7x
tighter) — and dense ranking was again the currency every improvement
was paid in. Across the two campaigns the pattern is now three-for-
three: capacity (v1), resolution (v1) and uniform data scale (v2) each
trade dense discrimination away while improving the global objective.
**The dense representation is not starved; it is OUTCOMPETED.** The
latent that ranks clutter correctly is not on the path the global JEPA+
BCE objective descends when given more of anything uniform.

### What this prices, and what it names

- The data tier at uniform 3x: dead as a dense fix (slope negative).
- Named next knobs, in order of cheapness: (a) **diet COMPOSITION** —
  dense-heavier mix at the same 3x total (one knob vs wm_3x; v1's
  verdict already named composition); (b) **the specialist road** — a
  dense-specialist WM routed dispatch-style alongside the generalist
  (the two-WM residency pattern already shipped in v0.8 makes this a
  systems knob, not a science fiction); (c) input resolution / depth
  features (the expensive tier).
- Honest side-note for a DIFFERENT question: wm_3x would be a strong
  general-WM upgrade candidate (best all-world row ever) — but that is
  its own campaign (head retrains, zoo effects, closed-loop) and no
  such claim is made here.

Training determinism held (fixed seed); the steps-vs-data control is
moot for a failed K0.

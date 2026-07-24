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

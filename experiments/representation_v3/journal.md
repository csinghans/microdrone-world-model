# representation_v3 — the composition tier: pay dense with someone else's rollouts

Opened 2026-07-24, on representation_v2's verdict (commit 8ab7568):
dense is not starved, it is OUTCOMPETED — capacity, resolution and
uniform data scale each traded dense discrimination away while the
global objective improved. Before the specialist-and-router road (a
systems change) or the resolution/depth tier (the expensive one), one
cheap knob remains: **rebalance the curriculum**. Same total data, same
architecture, same recipe — twice the dense share.

## Pre-registration (committed before any number)

### The knob

- **K0 `wm_3xdense`**: unified architecture (4, 64), 3x total
  (360 transit + 240 room, epochs 80, batch 64, seed 0), transit mix
  `("dense","dense","classic","moving")` = **180 dense / 90 classic /
  90 moving** (vs wm_3x's uniform 120/120/120). Single knob vs wm_3x:
  composition. Diet file `output/combined_3xdense.npz` (new; both
  frozen diets untouched).
- **K1 `wm_3xdense_s8`** (conditional): strips 8 on the dense-heavy
  diet — released ONLY if K0's dense AUC@32 > **0.9277** (same release
  rule as v2's, unchanged).

### Bars — inherited from representation_v1's freeze, verbatim

B1 dense AUC@32 >= 0.9335 AND all >= 0.9264; B2 dense warn saturation
<= 0.4658; B3 high-clutter |warn gap| <= 0.0284. Guards G1 veer == 1.00,
G2 budget < 512 KB, G4 classic >= 0.8011 / moving >= 0.9357.

### The dose-response row this campaign adds

dense-share 22% (40/180, the 1x diet: dense 0.9177) -> 33% uniform 3x
(120/360: 0.8417) -> **50% (180/360: this read)**. If dense ranking
does not respond to a 2.3x share increase at constant total, the
composition tier is dead and the wall is not a curriculum problem at
all — the honest verdict then names the specialist road (a dense-only
WM routed alongside, the v0.8 residency pattern) and the
resolution/depth tier as the remaining roads, both with their real
price tags.

### Honesty clauses

Inherited verbatim from v1/v2 (deterministic seed-0 training; offline
instruments predict, never certify; sha brackets). The classic share
halves (120 -> 90 rollouts vs wm_3x): G4's classic bar (>= 0.8011)
polices the trade honestly.

---

(verdict lands below when the queue completes)

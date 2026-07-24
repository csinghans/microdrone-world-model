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

---

## Verdict — 2026-07-24: K0 1/3 bars, G1+G4 BROKEN, K1 unreleased; the composition tier is dead — the wall is not a curriculum problem

Queue as pre-registered (sha checks green; logs `output/rep3_*`).

| metric | unified (22% dense) | wm_3x (33%) | **wm_3xdense (50%)** | bar |
|---|---|---|---|---|
| AUC@32 dense | 0.9177 | 0.8417 | **0.8652** | >= 0.9335 **FAIL** |
| AUC@32 all | 0.9314 | 0.9512 | 0.9316 | >= 0.9264 pass |
| AUC@32 classic / moving | 0.8211 / 0.9557 | 0.9225 / 0.9620 | 0.9471 / **0.9212** | G4 moving **BROKEN** |
| veer val | 1.0000 | 1.0000 | **0.8750** | == 1.00 **G1 BROKEN** |
| dense warn saturation | 0.6211 | 0.7155 | 0.6676 | <= 0.4658 **FAIL** |
| warn gaps {0}/{1-2}/{>=3} | +.165/+.141/-.057 | +.122/+.186/-.012 | **+.223/+.292**/-.023 | |gap3| pass |

B1 FAIL, B2 FAIL, B3 PASS -> 1/3. **G1 broken** (the first candidate in
the program to fail the veer guard) and G4 broken (moving). K1 NOT
released (0.8652 < 0.9277). **NO-GO.**

### The completed dose-response (the campaign trilogy's one figure)

dense share 22% -> 33% -> 50% at the dense AUC@32:
**0.9177 -> 0.8417 -> 0.8652.** Doubling the dense share at constant 3x
total recovered +0.024 of the -0.076 the uniform scale-up lost — never
approaching the 1x baseline, let alone the bar — while breaking the
veer guard, dropping moving below its bar, and inflating open-space
over-warn 1.4-2x (+0.223/+0.292). Dense discrimination at this
architecture family is a FRAGILE SPECIALIZATION: the 1x models sit at
a local sweet spot every cheap knob only falls away from.

### The offline tier closes — the remaining roads, with price tags

Three campaigns, six trained arms, one control, zero bars passed:
capacity, resolution, uniform scale, and composition are ALL priced
dead against dense separation. Per the frozen verdict clause, the wall
is not a curriculum problem. What remains:

1. **The specialist road (systems, cheapest remaining):** a dense
   specialist does not need to win a shared latent — the champion at 1x
   effectively IS one (dense 0.9335). Route it alongside the generalist
   (the v0.8 two-WM residency + the dispatch router are shipped
   precedents). This changes no representation; it changes the org
   chart of models. Its real questions are router quality and budget
   (two-WM residency is already the deployed posture).
2. **The perception tier (expensive, true quarterly):** input
   resolution above 64x64, deeper conv, depth-supervised features —
   the first knobs that could give the latent MORE INFORMATION rather
   than reallocating the same information. Nothing cheaper is left.

Honest parking note: wm_3x remains the best GENERAL row ever measured
offline (all 0.9512) — a general-WM upgrade candidate for a separate,
closed-loop-gated campaign; no claim here.

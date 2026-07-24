# representation_v1 — the wall's first brick: lateral resolution vs latent capacity

Opened 2026-07-24. Two chapters now wait on the same wall: the autonomy
dense frontier closed at v0.14 ("the remaining roads are quarterly-class
representation or the accepted floor") and the assisted chapter closed
its cheap-knob era at assist_v4 ("the trigger can be made quiet, not
accurate"). The shared mechanism, measured three ways: **the collision
heads cannot separate clean gap-threading from about-to-hit in clutter**
— dense saturation (head_calibration), the anti-monotone warn gap
(dense_recal: over-warn where empty, UNDER-warn where thick), and the
assist chapter's false imminent fires.

The architecture suspect is concrete: the encoder pools the entire scene
into **4 horizontal strips** — 15° of bearing per bin at a 60° FOV. In a
dense field several pillars share a bin; the latent cannot say which one
is on the flight line. This campaign asks the cheapest representation
question first, OFFLINE (no closed-loop flights until a GO):
**does lateral resolution (strips 4→8) or latent capacity (64→128) buy
clutter separation, inside the embedded budget?**

## Pre-registration (committed before any number)

### Knobs (one 80-epoch train each; diet FROZEN = the unified recipe)

Every arm trains on the bit-identical `output/combined.npz` (the
unified WM's 120 transit + 80 room mix), epochs 80, batch 64, seed 0,
via `scripts.train --out experiments/representation_v1/artifacts/...`
— the sacred checkpoints are read-only baselines
(`flight_mode --verify` runs before and after the queue).

- **K0a `wm_control`** (strips 4, D 64): the unified recipe through the
  NEW meta-driven plumbing. Validates the harness (its Stage-A-metric
  deltas vs the unified checkpoint ARE the retrain-draw noise floor —
  the two-tier claim language made operational).
- **K1 `wm_s8`** (strips 8, D 64): the mechanism-matched knob — 7.5°
  of bearing per bin, +16 KB int8 in the projection.
- **K2 `wm_d128`** (strips 4, D 128): the capacity control — separates
  "resolution" from "just more parameters".
- **K3 `wm_s8d128`** (conditional): released only if K1 or K2
  individually passes >= 2 of the three primary bars.

### Instruments (all frozen, all checkpoint-parametrized)

1. `eval_wm_checkpoint --ckpt --data output/transit_eval_holdout.npz`
   — per-world AUC@32 + veer-ranking on the seed-777 held-out set.
2. `eval_head_calibration --ckpt-a <unified> --ckpt-b <candidate>` —
   dense warn/crit contrast, SATURATION (frac pinned past 0.95/0.05),
   ECE, per world.
3. `eval_dense_recal --ckpt <candidate>` — clutter-context suite on
   seed-160 rollouts: K0a clutter->dense separation AUC, K0b signed
   warn gap per clutter bin {0}/{1-2}/{>=3} + monotonicity.
4. `eval_latency_budget.onboard_budget` on the candidate modules.
5. Diagnostics (reported, never barred): indoor `det_probe` /
   `fwd_probe` on the candidate latent (detection heads are invalidated
   by any new latent BY DESIGN — lock `wm` bindings; a retrain is the
   later, gated step).

### Stage A — the baseline row (zero training)

Grade the UNIFIED and CHAMPION checkpoints through instruments 1-3
first; freeze the absolute bars FROM that row in their own commit
(the indoor-gate pattern) before any candidate trains. Known priors
(from journals, to be re-pinned by Stage A on these exact instrument
configs): unified holdout AUC@32 all 0.931 / dense 0.918; champion
dense 0.933; champion dense-recal separation 0.736, high-clutter warn
gap -0.034 (anti-monotone).

### Primary bars (delta-rules frozen NOW; absolutes at the bar-freeze)

- **B1 (ranking in clutter):** candidate dense AUC@32 >= the CHAMPION's
  Stage-A dense row (recover the specialist) AND overall AUC@32 >=
  unified - 0.005.
- **B2 (saturation):** candidate dense warn saturation <= 0.75 x
  unified's Stage-A row.
- **B3 (calibration structure):** candidate high-clutter |warn gap| <=
  0.5 x unified's Stage-A row, AND clutter-separation AUC >= unified
  + 0.03.

### Guards (sacred)

- **G1:** veer-ranking (val) == 1.00.
- **G2:** `onboard_budget` total < 512 KB; the dual-residency bill
  (candidate + champion) reported.
- **G3 (draw-noise floor):** a candidate's delta on any bar metric
  counts only if it also exceeds |K0a control - unified| on that
  metric. No claim inside the retrain noise.
- **G4:** classic and moving AUC@32 each >= unified - 0.02.

### GO / NO-GO (frozen)

GO — any candidate passes B1+B2+B3 with all guards green: opens
representation_v2 (closed-loop phase: the dense probe arms and the
assist guardian arms re-flown with the new eyes; its own prereg).
NO-GO — no candidate passes: the cheap-architecture tier is priced
dead, and the honest verdict names the next tier (input resolution,
depth features, data scale) — the wall is deeper than pooling.

### Honesty clauses

MPS retrain draws vary — mechanisms reproduce, third decimals don't;
that is exactly why K0a exists (G3). The offline instruments predict,
they do not certify: closed-loop truth stays gated behind
representation_v2. Old checkpoints reconstruct bit-identically through
the new plumbing (verified pre-registration: both sacred artifacts
load, forward, and sha-match the lock).

---

(Stage A row, bar freeze, and per-knob verdicts land below)

---

## Stage A — the baseline row (2026-07-24, zero training)

Instruments exactly as frozen; logs `output/rep_stageA_*.log`, JSONs in
this directory.

| metric (instrument config of record) | unified | champion |
|---|---|---|
| holdout AUC@32 all | **0.9314** | 0.8963 |
| holdout AUC@32 classic / dense / moving | 0.8211 / 0.9177 / 0.9557 | 0.6572 / **0.9335** / 0.9314 |
| veer-ranking val (n=8) / widened (n=143) | **1.0000** / 0.9720 | 0.3750 / 0.8252 |
| dense warn saturation / ECE / contrast | **0.6211** / 0.0687 / 0.1751 | 0.6046 / 0.0702 / 0.1482 |
| dense-recal separation AUC (k0a) | **0.7358** | 0.7358 (v0.14 record) |
| dense-recal warn gap by clutter bin {0}/{1-2}/{>=3} | +0.1647 / +0.1407 / **-0.0567** | +0.121 / +0.074 / -0.034 |

The anti-monotone signature reproduces on the unified WM — over-warn in
open space, UNDER-warn in thick clutter — and 62% of dense warn
predictions sit pinned past 0.95/0.05. The wall, quantified on the
campaign's own instruments.

## Bar freeze (from the Stage A row, per the pre-registered delta-rules)

- **B1**: dense AUC@32 >= **0.9335** AND overall AUC@32 >= **0.9264**.
- **B2**: dense warn saturation <= **0.4658** (0.75 x 0.6211).
- **B3**: high-clutter |warn gap| <= **0.0284** (0.5 x 0.0567) AND
  separation AUC >= **0.7658** (0.7358 + 0.03).
- **G1**: veer val == 1.00. **G2**: budget < 512 KB. **G4**: classic >=
  **0.8011**, moving >= **0.9357**. **G3**: per-metric deltas must
  exceed the K0a control's |delta vs unified|.

Committed before any candidate trains; the queue's sha verification
brackets the sacred artifacts.

---

## Verdict — 2026-07-24: NO-GO (0/3 bars on both knobs); the wall is deeper than pooling, and it points at DATA

Queue completed as pre-registered (sha checks green before and after;
logs `output/rep_train_*.log`, `output/rep_grade_*`; budget bill in
`output/rep_budget.log`).

### The control arm's gift

`wm_control` reproduced the unified checkpoint **to four decimals on
every instrument** (AUC rows, veer, saturation, gaps, separation) —
seed-0 training is deterministic on this machine, the new meta-driven
plumbing is EXACT, and the G3 draw-noise floor is 0.000: every candidate
delta below counts at face value.

### The bars, applied

| bar | wm_s8 (8,64) | wm_d128 (4,128) |
|---|---|---|
| B1 dense >= 0.9335 AND all >= 0.9264 | 0.7265 / 0.8997 **FAIL** | 0.7619 / 0.9100 **FAIL** |
| B2 dense saturation <= 0.4658 | 0.7123 **FAIL** (worse) | 0.5662 **FAIL** |
| B3 |gap{>=3}| <= 0.0284 (& sep) | 0.0173 ✓ (half) | 0.0289 (miss by 5e-4) |
| G1 veer == 1.00 | 1.0000 ✓ (widened 1.0000) | 1.0000 ✓ |
| G4 classic / moving | 0.8693 ✓ / 0.9301 ✗ | 0.8851 ✓ / 0.9149 ✗ |
| G2 budget | 153.3 KB ✓ | 194.2 KB ✓ |

K1 and K2: **0/3 primary bars each.** K3 (combo) not released. **NO-GO**
— representation_v2 (closed-loop) does not open on this tier.

Prereg drafting flaw, recorded: B3's separation-AUC clause is
instrument-constant (the clutter count is geometric — 0.7358 for every
arm including the baselines); the |gap| clause is the model-dependent
half and is what binds. No verdict changes under any reading.

### What the brick taught us (the mechanisms, named)

1. **Finer strips made saturation WORSE** (0.6211 -> 0.7123): sharper
   per-bin evidence pins the heads harder in clutter. The coarse 4-strip
   average was quietly acting as a regularizer, not only a bottleneck.
2. **Both capacity knobs traded dense for classic at frozen data.**
   classic +0.05/+0.06 and veer-ranking perfected (widened 1.0000, a
   first) while dense collapsed 0.16-0.19. With 120 transit rollouts,
   extra representational freedom reallocates toward the easy world's
   features — the knob is not wrong, it is UNDERDETERMINED. Architecture
   and data must move together.
3. **Budget was never the constraint** (153/194 KB << 512). The binding
   resource on this wall is DATA, not silicon.

### Disposition (per the frozen GO/NO-GO)

The cheap-architecture tier is priced dead — and unusually, the corpse
points somewhere specific: the next campaign is the DATA tier
(representation_v2: scale the frozen diet 3-5x at FIXED architecture
first — the clean single knob; architecture re-enters only after data
alone is priced). Input resolution and depth features remain named
alternates. This is what "quarterly-class" turns out to mean here: not
a bigger net, but a bigger world to learn from.

Run-to-run caveat: training proved deterministic on this machine (the
control), so these deltas are exact for this seed; cross-seed variance
remains unpriced (a v2 concern if data-tier deltas are small).

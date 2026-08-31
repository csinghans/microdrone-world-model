# stability_v1 — closing the variance guard (two-sided, before any temporal work)

Opened 2026-08-31, from perception_v3's banked mechanism finding (gate commit
`22ddecf`): the variance guard bounds the latent's per-dim std from BELOW only
(`relu(1 - std)`), the EMA target chases the inflating online encoder, and at
2x duration the drift compounds — the 160-epoch wm_96d128 run exploded
(no-op MSE 7.6 -> 99.4, latent scale ~x13, rows self-inconsistent). That
finding gates the program's next real question: "temporal input under the
stability finding — the one-sided variance guard must be fixed before any
long-memory recipe" (perception_v3 journal, final verdict).

This campaign closes the guard. A guard change is a recipe change for every
future WM training run, so it is a KNOB, not a silent fix: pre-registered,
then measured. No SACRED artifact is retrained; sha brackets run pre/post.

## Pre-registration (committed before any number)

### The measurement that sets the band (read-only, 2026-08-31, n=400 frames)

Per-dim std of z, plus mean |z|, per checkpoint:

| checkpoint | std min / med / max | mean abs z |
|---|---|---|
| `output/world_model_unified.pth` (SACRED, 64-res) | 1.08 / 1.33 / 1.88 | 1.9 |
| `output/world_model.pth` (SACRED, 64-res) | 0.97 / 1.21 / 2.53 | 2.2 |
| `wm_96d128.pth` (perception_v2 apex, 80 ep) | 1.52 / 2.66 / 6.44 | 6.7 |
| `wm_96d128_e160.pth` (perception_v3 K0, destabilized) | 0.98 / 4.21 / 12.05 | 13.4 |

Every shipped champion lives at std <= 2.53. The 96-res recipe is already
drifting at 80 epochs (6.44) and lands at 12.05 when it explodes. The upper
hinge is therefore set at **VAR_HI = 4.0**: strictly dead (zero loss, zero
gradient — the loss function is unchanged in value AND gradient) at every
shipped champion's operating point, and binding on the inflating recipe.

### The knob (single)

`variance_guard(z) = relu(VAR_LO - std).mean() + relu(std - VAR_HI).mean()`
with `VAR_LO = 1.0` (the old hinge, unchanged), `VAR_HI = 4.0`
(`world_model/losses.py`). `LAMBDA_VAR = 1.0` unchanged; the call site
(`world_model/training.py`, online `z_last`) unchanged. Everything else —
diet `output/combined_96.npz`, seed 0, batch 64, D=128, strips 4 — is the
frozen perception_v2 recipe.

Harness shipped alongside (instruments, not knobs): per-epoch val z-std
med/max + mean |z| in the training metrics and the `scripts.train` print
(the x13 was only ever INFERRED from no-op MSE — no std logger existed);
`eval.eval_latency_budget --ckpt/--img-res` replaces the uncommitted budget
heredoc that broke perception_v3's `&&` chain.

### Arms

- **K0 — 80 epochs under the two-sided guard** (control for recipe damage):
  `python -m scripts.train --epochs 80 --batch 64 --seed 0 --latent-d 128
  --data output/combined_96.npz
  --out experiments/stability_v1/artifacts/wm_96d128_g2.pth`
- **K1 — 160 epochs under the two-sided guard** (the e160 acceptance rerun;
  rule 6: harness fix -> rerun the same knob): same command, `--epochs 160`,
  `--out .../wm_96d128_g2_e160.pth`. **Released ONLY if K0 passes** — the
  queue is `&&`-chained under `set -e` with an explicit K0 bar assert between
  the stages; a K0 NO-GO stops the queue.

### Bars (frozen; baseline row = wm_96d128 of record: all 0.8807 ·
### classic 0.7882 · dense 0.9965 · moving 0.8891 · veer 1.00/1.00 ·
### sat 0.3080 · gap3 -0.0658 · 264.2 KB / 17 ms)

K0 ("the guard costs nothing the apex had"):
- dense AUC@32 >= 0.985 (holdout, `eval_wm_checkpoint`)
- veer val AND widened >= 0.95
- moving and classic within -0.02 of baseline (>= 0.8691 / >= 0.7682)
- val z-std max <= VAR_HI + 0.5 = 4.5
- budget unchanged: 264.2 KB / est 17 ms (`eval_latency_budget --ckpt`)

K1 ("duration no longer destabilizes"):
- no-op MSE@32 <= 2x K0's no-op (the broken pair was 7.6 -> 99.4)
- val z-std max <= 4.5
- rows self-consistent: train-val AUC@32 >= 0.85, veer val >= 0.90

Secondary (recorded, not gating): saturation, ECE, gap3, per-world table for
both arms — the perception-tier instruments keep the record comparable.

### GO / NO-GO (frozen)

- K0 passes + K1 passes -> **GO**: the guard is closed; perception_v3's
  temporal gate is satisfied by measurement; temporal_probe_v1 may proceed
  to a training-side follow-up if its own probe says GO.
- K0 fails -> **NO-GO**: the band [1.0, 4.0] is wrong for this recipe, not
  the idea. Record which bar broke and the measured std profile. Do NOT tune
  VAR_HI into passing — a revised band is a NEW pre-registration.
- K0 passes, K1 fails -> **NO-GO**: the one-sided hinge was not the (only)
  destabilizing mechanism. The EMA-chase hypothesis loses its cheapest fix;
  record what the std/no-op trajectory shows instead.

### Honesty clauses

- The counterfactual branch's latent (`z_c_last`) remains UNGUARDED — noted,
  not touched (one knob per run). If K1 still drifts, that path is the next
  named suspect.
- The mean-offset drift is a separate observation: at 80 epochs the apex has
  |z| 6.7 vs std 2.66 — the latent's CENTER wanders, which no std hinge
  constrains. Recorded for a later campaign, not fixed here.
- MPS nondeterminism: mechanisms reproduce, third decimals don't. Bars above
  are written with that margin; the n=60 borderline recheck rule applies.
- Nothing is deployed from this campaign. wm_96d128_g2* are journal-side
  artifacts (`*_g2*` names, never clobbering the perception_v2 apex).

---

(verdicts land below when the queue completes)

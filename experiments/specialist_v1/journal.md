# specialist_v1 — the org-chart road: a dense specialist that never has to share

Opened 2026-07-24, on the representation trilogy's close (commits
dea29fa, 8ab7568, 70cce47): six trained arms across capacity,
resolution, uniform scale and composition all traded dense
discrimination away — dense is a fragile specialization that loses
every fight for a shared latent. This campaign stops asking one latent
to do everything. **The specialist road: a dense-only WM alongside the
generalist, routed by context — the v0.8 two-WM residency and the
dispatch router as shipped precedents.** No representation change; an
org-chart change for models.

## Pre-registration (committed before any number)

### Structure: three conditional stages, offline first

- **K0 — the existence question.** Train `wm_dense` on a DENSE-ONLY
  diet (120 rollouts x 120 steps, seed 0 — the same transit total as
  the 1x recipe, all of it dense: 3x the champion's in-domain data at
  equal budget). Architecture, recipe, epochs: frozen at the deployed
  defaults (4 strips, D 64, 80 epochs). Diet file
  `output/dense_only.npz`; artifact
  `experiments/specialist_v1/artifacts/wm_dense.pth`.
- **K1 — the router-existence question** (released ONLY if K0 passes
  B1): can a vision-only probe on the FROZEN GENERALIST's latent
  (unified WM) classify the world within a 12-decision window? A new
  instrument (`eval/eval_router_probe.py`, selftest + ckpt-parametrized,
  built at K1 arbitration per the reserved-manual convention): linear
  probe on holdout latents, per-episode majority vote over the first 12
  decisions. Bar: episode routing accuracy >= 0.95 on held-out
  rollouts. Deployment shape declared now: probe window flies the
  generalist, then BINDS one WM for the episode (flight_mode-style late
  binding) — one encoder per tick always; both WMs resident in flash.
- **K2 — the routed system, offline synthesis** (released ONLY if K0
  and K1 both pass): per-episode routing on the holdout, the ROUTED
  system's per-world AUC rows. Bars: routed dense >= wm_dense - 0.005
  AND routed classic/moving >= unified - 0.005 (the system keeps each
  member's strong rows). GO -> specialist_v2 (closed-loop: the dense
  probe arms and the assist guardian arms with routed eyes).

### K0 bars (frozen from measured rows)

- **B1 (existence, gates K1):** wm_dense holdout dense AUC@32 >=
  **0.9435** — the champion's 0.9335 plus 0.01. A specialist that
  cannot beat the best shared-latent row by a visible margin is not
  worth a router; the road dies at birth and the verdict points
  everything at the perception tier.
- **Secondary rows (reported at K0; they gate the K2->closed-loop GO,
  not K1):** dense warn saturation <= **0.6046** (beat the champion's
  row); dense-recal high-clutter |warn gap| <= **0.0284** (the
  trilogy's inherited bar).
- **Guards:** G2 — the THREE-resident bill (champion + unified +
  specialist int8 weights + shared peak activations) < 512 KB, printed.
  Honesty rows: classic / moving / veer are REPORTED and expected BAD —
  the specialist never claims them; the router owns them (that is the
  entire point of the org chart).

### Honesty clauses

Inherited from the trilogy verbatim (deterministic seed-0 training on
this machine; offline instruments predict, never certify; sha brackets
around every queue; sacred checkpoints read-only). The specialist sees
3x the champion's dense data at equal total — in-domain data
concentration IS the treatment, stated not hidden. If B1 passes but
secondary rows fail, K1 still releases (ranking is the router's
premise; calibration gates the later closed-loop GO).

---

(K0 verdict lands below when the queue completes)

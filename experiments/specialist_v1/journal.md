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

---

## K0 verdict — 2026-07-24: B1 FAIL (0.6436 vs >= 0.9435); the org-chart road dies at birth — and names the real mechanism

Queue as pre-registered (sha checks green; logs `output/spec_*`).

| metric | wm_dense (dense-only) | champion | bar |
|---|---|---|---|
| holdout dense AUC@32 | **0.6436** | 0.9335 | >= 0.9435 **FAIL** |
| classic / moving (expected-bad rows) | 0.7366 / 0.6808 | 0.6572 / 0.9314 | reported |
| veer val / widened | **1.0000 / 1.0000** | 0.3750 / 0.8252 | reported |
| dense warn saturation | 0.6671 | 0.6046 | <= 0.6046 fail |
| warn gaps {0}/{1-2}/{>=3} | **+0.5638 / +0.4557** / -0.0267 | +0.121/+0.074/-0.034 | |gap3| pass |
| three-resident budget | 243.9 + 56.0 = **299.9 KB < 512** | — | pass |

K1 and K2: NOT released. **specialist_v1 closes at K0.**

### The mechanism the corpse names: dense discrimination is CONTRASTIVE

The pure specialist — all budget, all data, one world — is
catastrophically WORSE at its own world than every mixed model. Its
open-space over-warn explodes (+0.56: everything it ever saw was
cluttered, so "warn" is almost always right, so the heads saturate
toward yes) while within-dense ranking collapses (it never learned what
safe passage looks like against genuinely open baselines). The trilogy
said dense LOSES the fight for a shared latent; K0 says remove the
competitors and it dies faster. Both are one fact: **the mixed diet was
not diluting dense knowledge — it was supplying the negatives. Dense
discrimination is a contrastive property of the curriculum, not a
specialization you can isolate.** (The perfect veer rows fit: left-vs-
right is a relative judgment, learnable anywhere; near-vs-far absolute
discrimination in clutter is what needs contrast.)

### The program-wide table (eight arms, one instrument, one bar never met)

| arm | dense AUC@32 |
|---|---|
| champion (1x mixed) | **0.9335** |
| unified / control (1x mixed + indoor) | 0.9177 |
| 3x dense-heavy (50%) | 0.8652 |
| 3x uniform (33%) | 0.8417 |
| D128 | 0.7619 |
| strips 8 | 0.7265 |
| **dense-only (100%)** | **0.6436** |

Dense share vs dense skill is an inverted U peaking at LOW share — the
contrast hypothesis in one curve. The 1x mixed models are the apex of
this architecture family; capacity, resolution, scale, composition and
isolation all fall off it.

### Disposition — the cheap tier is now exhausted BY CONSTRUCTION

Architecture knobs (v1), data knobs (v2, v3) and the org chart
(specialist_v1) are all priced dead against the dense bar. One road
remains, now proven last by exhaustion rather than assumption: **the
perception tier** — input resolution above 64x64, deeper conv, depth
features; the knobs that give the latent MORE INFORMATION. Its design
must respect today's mechanism finding: whatever sees more must still
be trained on a CONTRASTIVE curriculum — the mixed diet is load-bearing
and comes along.

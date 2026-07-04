# head_calibration — the D0 follow-through campaign journal

## Hypothesis (pre-registered 2026-07-05, before any gate ran)

D0 (grounding_mechanism) measured the v0.5 flight loss's mechanism
candidate on frozen checkpoints: grounding improves the heads' ordering
and **inflates their warn-ring numbers** (dense warn ECE 0.0702 → 0.1225,
mean P up on every world). If the debased observation currency is what
broke the policy, then *restoring the currency without touching the
ordering* should recover the flight — and temperature scaling does
exactly that, at zero retraining: one T per (horizon, ring), fitted on
the train rollouts' FOV-masked counterfactual-oracle labels, baked into
the head weights so every consumer rides it unchanged. Monotone ⇒
per-world AUC is invariant **by construction**: this knob can only move
what D0 said is broken, never what M1 said was won.

A deliberately falsifiable side-note, frozen now: the training loop
oversamples decision-relevant frames 50/50 (`c_hard`), so *both* models'
heads may sit hot on the natural frame distribution; if the champion's
temperatures also fit well above 1, that supports the oversampling
origin story for the inflation (and C2 becomes the more interesting
arm).

Measurement basis: the unchanged M1 draw (`output/wm_dataset.npz`),
seed-0 split (fit = train rollouts, report = val), the M2 cell spec and
bars verbatim, the same model-swap protocol.

## The knob schedule (bars frozen here)

**C0 — fit + verify (no training).**
`python -m eval.calibrate_heads --ckpt <arm> --out <arm>_cal.pth` for
both arms: grounded-s0 (`wm_m1_ground.pth` → `wm_m1_ground_cal.pth`)
and the champion (`world_model_g1.pth` → `wm_g1_cal.pth`), then
`eval_head_calibration` (uncalibrated vs calibrated) and
`eval_wm_checkpoint` on each.

| kind | bar |
|---|---|
| target | calibrated-grounded dense warn ECE (val) ≤ **0.09** (uncal 0.1225; champion 0.0702) |
| guard | per-world AUC@32 identical to uncalibrated (monotone; \|Δ\| < 0.001 allowing float noise) |
| guard | no world's warn/crit ECE worsens by > 0.01 vs its uncalibrated value |
| finding, not a bar | fitted T values recorded for both arms; if all grounded T ∈ [0.95, 1.05], temperature cannot express D0's inflation → campaign ends early, honest negative |

C0 is deterministic (no seeds, no rechecks). If C0 fails its target,
C1 does not run.

**C1 — the flight gate (runs only if C0 passes).** The unchanged
champion recipe (`train(300000, hard=True, x_progress=True,
edge_bias=True, seed0 0)`) on the **calibrated grounded** model;
`experiments/metric_grounding/m2_cells.json` verbatim; the M2 bars
verbatim:

| kind | bar |
|---|---|
| target | dense@0.8 ≤ 12 % (champion 17 %) **or** dense@1.2 ≤ 20 % (champion 27 %) |
| guard | moving@0.8 ≤ 18 %, moving@1.2 ≤ 12 %, cluttered ≤ 5 %, sweep ≤ 5/5/5/10/10 % |
| rule | any cell within ±0.08 of its bar → n=60 fresh-seed recheck |

**C2 — the attribution control (runs only if C1 passes).** Same recipe
on the **calibrated champion**. Question: does calibration alone beat
the champion? Reading, frozen now: if C2 also clears the C1 targets,
calibration is the whole story and grounding stays dead; if C2 lands at
champion-level while C1 passed, the grounding+calibration synergy is
real and v0.5's model-layer win finally cashes out.

Budget: C0 + C1 + C2 (conditional). No reserves. Honest negatives get
recorded, not retried into passing.

---

## Gates

(appended per gate; numbers only from rerunnable commands)

### C0 — fit + verify — **FAILED**; campaign CLOSED (2026-07-05)

Fitted temperatures (warn/crit per horizon), both arms:

| arm | k4 | k8 | k16 | k32 |
|---|---|---|---|---|
| grounded-s0 | 0.84/0.92 | 0.81/0.85 | 0.77/0.92 | 0.88/0.84 |
| champion G1 | 0.90/0.84 | 0.88/0.89 | 0.83/0.95 | 0.85/0.83 |

**Every T is below 1** — the masked-BCE fit wants both models *sharper*
on the natural frame distribution, not cooler. Two pre-registered
readings resolve immediately:

- the c_hard-oversampling origin story is **refuted**: neither model is
  globally hot (if anything, both are slightly under-confident);
- the early-exit clause anticipated T≈1 ("temperature cannot express
  D0's inflation"); the measured T<1 is the same conclusion, stronger —
  the fit actively moves *away* from what D0's dense-warn finding needs.

Bars:

| bar | measured | verdict |
|---|---|---|
| target: cal-grounded dense warn ECE ≤ 0.09 | **0.1318** (uncal 0.1225 — got *worse*) | **FAIL** |
| guard: per-world AUC unchanged | 0.9148/0.8175/0.8872 — identical | pass (by construction, verified) |
| guard: no slice ECE worsens > 0.01 | dense crit +0.0130 | **FAIL** (classic/moving all improved) |

The failure pattern is the refined finding: global sharpening improved
the four cold slices (classic/moving, both rings) and worsened both
dense rings — the hot slice got hotter. **D0's warn inflation is
context-conditional, not a global logit scale**: the grounded (and to a
lesser degree the champion) heads over-report specifically in dense
geometry while sitting under-confident overall. One scalar per
(horizon, ring) cannot express that; fixing it is retraining-class work
(conditional recalibration needs a world label the flying drone doesn't
have; representational fixes reopen the model axis).

Per the frozen schedule, C1 and C2 do not run. Campaign cost: minutes —
the gate ordering (deterministic knob before the 2.5 h flight gate) did
its job.

## Campaign verdict: CLOSED (2026-07-05)

The cheap route to cashing grounding's detection win is measured dead:
temperature recalibration cannot even move the broken metric in the
right direction, because the miscalibration lives in the *conditioning*,
not the scale. Across three campaigns the grounding arc now reads:
detection win (M1) → flight loss (M2) → mechanism candidate measured
(D0: conditional warn inflation) → cheapest fix falsified (C0). The
champion stack (G1 + edge_hard_xp) stands. Remaining honest options are
all retraining-class and belong to future pre-registrations; the dense
17-27 % floor keeps its crown as the open frontier.

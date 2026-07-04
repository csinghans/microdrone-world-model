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

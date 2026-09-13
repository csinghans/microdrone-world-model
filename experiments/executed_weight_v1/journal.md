# executed_weight_v1 — registered moving executed-loss weighting study

## Registration — 2026-09-14, before research fitting or exam generation

Question: does increasing moving-world executed-loss weight recover moving
collision ranking without harming the other worlds, immediate danger or
action ranking? [schedule_support_v1](../schedule_support_v1/journal.md)
reconciled a moving training-window share of 32.75–33.36% under the legacy
corpus versus 17.77–18.00% under the balanced corpus. Each eligible window
is used exactly once per epoch by the current random permutation. This is
an allocation difference, not proof of the cause of the schedule NO-GO.
The separate CF hard-pool experiment is closed NO-GO; keep `legacy_masked`.

**Only knob:** `executed_moving_weight`, 1.0 control versus **2.25** candidate.
For each eligible training window, raw weight is 2.25 in moving and 1.0
elsewhere. Divide by the mean raw weight over the **training partition**,
computed once before fitting. Multiply each window's mean latent prediction
MSE and executed collision BCE by this normalized weight, then average over
the current batch. This one per-window coefficient applies to those two
executed-action objectives; their existing relative coefficients stay fixed.
The unit arm uses the original mean operations exactly.

The factor 2.25 is chosen from the already audited window shares, before
new model results: it approximately restores a one-third moving share of
total **weight mass**. It does not restore missing windows, observations,
action/label diversity or independent courses. Weight mass is not measured
gradient contribution; errors, derivatives and Adam state also matter.
Global training-partition normalization avoids intentionally scaling both
executed objectives up as a whole. No per-batch normalization is applied.

Keep every batch permutation, number of optimizer steps, CF/now sampling
rule, CF/now loss coefficient, variance penalty, EMA schedule, architecture
and corpus unchanged. No replacement sampling or extra epochs. Weights do
not consume RNG calls and are dropped at deployment. The increased moving
weight necessarily decreases the normalized weight assigned to other
worlds; those tradeoffs are protected by the registered guards.

Both arms use the same hashed 192-rollout balanced corpus (96 transit +
96 room, length 120), fixed in [registration.json](registration.json).
Six fresh 80-epoch fits at seeds 0/1/2, with matched rollout splits and
alternating order, are required. D64/four strips/64px/one frame, batch 64,
Adam 1e-3, no augmentation, temporal encoder or grounding. Fit on MPS,
score on CPU. Source, runtime, corpus and both protected WM hashes freeze
before execution. Old controls are not reused as new training draws.

A new independently generated exam contains 126 transit + 60 room courses
of length 160 at new seeds. Every model scores all courses. First pass all
four scene-present/removed render checks (moving at centreline crossing)
and verify each world's positive/negative horizon-32 support is at least
20. Match the source corpus's collection recipe; this is an offline test,
not an Indoor Active Search flight gate. Later indoor flight work must
use robust speed 0.6 if separately registered.

**Primary:** candidate-minus-control moving AUC@32 mean ≥ **+.03** over
three training seeds, and **strictly positive at every seed**.
**Every-seed guards:** classic/dense/room AUC@32 deltas ≥−.02; danger-now
AUC delta ≥−.02; pooled veer-ranking delta ≥−.05. Every model must have
finite decision metrics and both AUC classes; each veer reading needs at
least 20 frames from six independent exam courses. This is a pooled veer
guard, not a per-world ranking claim. Memory must remain ≤512 KB with the
exact same analytic bill/MAC count as its paired control.

Report every pair, failed guard and internal endpoint diagnostic. Export
collision and veer scores, with paired world-stratified rollout-bootstrap
intervals (2,000 resamples, seed 0), conditional on each fixed model pair.
Intervals are descriptive, not gating. The three-draw mean/range does not
estimate training-population uncertainty. No optional rechecks, replacement
seeds, early stopping, expanded exam or adjusted bars. Instrument failure
is INVALID; preserve outputs for inspection rather than fish for support.

GO only permits registering a later closed-loop study, never promotion.
The schedule-layout and CF-sampler NO-GOs remain closed. Both protected WMs
and every champion stay intact. No release tag.

Run `bash experiments/executed_weight_v1/run.sh` after checking existing
processes and receipts. Full persistent logs, immutable stage receipts and
fail-fast queue semantics match the previous studies. An incomplete stage
must be inspected; it cannot be silently rerun.

## Harness checks before research execution — 2026-09-14

`python -m world_model.executed_weighting` passes unit-mean parity,
training-only normalization, expected per-window gradients (float32
tolerance), zero RNG consumption and invalid-factor/missing-moving checks.
The default branch executes the original prediction mean and BCE reduction.

The existing source corpus gives moving weight-mass shares
17.7717%→32.7180%, 17.9959%→33.0550%, 17.9772%→33.0270% at seeds 0/1/2.
Normalizers are 1.2221456550 / 1.2249484991 / 1.2247149415. Each arm still
has 6,893 / 6,796 / 6,753 training windows respectively; the study's
training-data receipt will record all worlds and each fit must match it.

The checkpoint selftest fits a third two-epoch toy model at weight 2.25,
in addition to the existing unit/default and CF-option wiring fixtures.
It verifies persisted weight metadata, unchanged executed-window counts
and CF hard-pool size, increased moving weight mass, and finite probe
outputs. All destinations include `_selftest`; these are integration
checks, not research-model comparisons. The shared-runner and both closed
study report selftests pass. Whole-repo Black/Ruff passes for 161 files.

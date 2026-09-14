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

## Launch and preflight — 2026-09-14

The queue launched after registration commit `2362756`. Its initial shell
PID (18400), timestamp, command and full log path are saved in
`output/executed_weight_v1/queue.json`. PIDs can be reused; check the live
command and receipts before any resume. The [manifest](manifest.json)
freezes source files, runtime, input corpus and protected WM hashes.

All four preflight stages passed and their files were hash-verified.
Scene-present/removed images were inspected; the moving fixture observes
the centreline crossing at step 158. Both arms' train-partition weight
plans are recorded in [training_data.json](records/training_data.json).

The new exam has **186 courses / 12,179 overlapping valid windows**:

| World | Courses | Positive @32 | Negative @32 |
|---|---:|---:|---:|
| classic | 42 | 993 | 1,903 |
| dense | 42 | 2,558 | 321 |
| moving | 42 | 1,680 | 1,309 |
| room | 60 | 1,561 | 1,854 |

Each transit world has 14 passive courses and classic has 21 clear
courses. [Exam SHA](records/holdout.json):
`e241adddb83d636fdaa9665643929b4e7cf1a45671b2fad4c8334455ec21aac1`.
All class-support requirements pass. The first unit-control fit has
started; no research-model verdict is available at this entry. All six
fits and scores remain required before interpretation.

## Final result — 2026-09-14: NO-GO

All 17 stages completed once. The full log ends in
`EXECUTED-WEIGHT-STUDY COMPLETE`, `EXECUTED-WEIGHT-DONE` and
`EXECUTED-WEIGHT-EXIT=0`; no study worker remained at inspection. All frozen
sources/runtime/input/protected hashes and every stage output were verified
before adding report code. [Verification receipt](verification.json).
All nine locked artifacts remain valid.

| Seed | Control moving AUC | Weight-2.25 AUC | Delta |
|---|---:|---:|---:|
| 0 | 0.7687 | 0.7503 | −0.0184 |
| 1 | 0.6518 | 0.7745 | +0.1227 |
| 2 | 0.6517 | 0.7269 | +0.0752 |

Mean moving delta **+0.0598** passes +0.0300, but seed 0 fails the required
strictly-positive moving delta. Seed 1 also fails dense AUC (−0.0293 against
−0.0200) and pooled veer (−0.0737 against −0.0500). Every other per-seed
guard passes. This is NO-GO even though the mean target improves.
All models retain the identical 137.290039 KB analytic int8 bill and
3,856,768 MACs/decision, estimated 7.713536 ms at assumed 0.5 GMAC/s.
There was no hardware timing, int8 parity or closed-loop flight gate.

The 42-course moving AUC intervals are [−0.0424, +0.0027],
[+0.0785, +0.1667] and [+0.0279, +0.1200], conditional on their fixed
checkpoint pairs. They do not change the frozen per-seed rule or provide
training-population confidence. Full results and guards are in the
[generated summary](summary.md) and [raw report](records/report.json).

Post-hoc support accounting from the six unchanged score exports finds
190 veer frames / 20 independent courses: classic 43/7, dense 139/12,
moving 8/1, room 0/0. The frozen pooled support requirement passes. The
already implemented world-stratified bootstrap refuses intervals with a
singleton stratum, so all three veer intervals stay undefined and preserve
the reason. No fabricated interval or expanded exam replaces that gap.
This limits ranking uncertainty, not the separate 42-course moving AUC.

Fit receipts match the preflight weight plans exactly, with identical
executed-window counts, splits and CF hard-pool sizes within pairs. All
six models beat their own no-op latent MSE@32; that endpoint diagnostic
does not certify decision quality across the new exam. Control seed 2's
large absolute latent value is associated with weaker scores, not proof
of a failure mechanism. Weight mass is not gradient contribution, and the
single coefficient does not isolate prediction loss from collision loss.

The tested coefficient raises mean moving AUC but fails consistency and
regression protection. Default weight stays 1.0. Preserve all three draws;
no seed selection, retry, extra exam, moved bar or champion promotion.
The previous schedule-layout and CF-sampler NO-GOs remain closed.

`python -m eval.eval_executed_weight_report` rebuilds this study's summary
and six-panel figure from JSON alone. Its selftest verifies receipt hashes,
score/fit identity, one-knob metadata, preflight weighting plans, common
support and original guards; an invented veer interval is rejected.
`--audit-probe-support` reads only hashed exports and compares an existing
support record rather than overwriting it. Shared plotting/support helpers
were extended after the frozen queue completed; no research source was
edited during training or evaluation.

Final validation: whole-repository Black/Ruff passed for 162 Python files;
all three completed-study report selftests and the shared runner selftest
pass. The executed report selftest also passes in a directory containing
only its Python modules and JSON receipts, without `output/` or model files.
The extended plotting helper reproduces the previous CF figure pixel for
pixel; the new figure was visually inspected. These are local checks, with
no remote push, CI dispatch or release tag.

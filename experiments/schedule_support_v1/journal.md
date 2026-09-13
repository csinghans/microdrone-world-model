# schedule_support_v1 — retrospective supervision audit

## Scope fixed before the diagnostic — 2026-09-13

The completed schedule_layout_v1 study is NO-GO. This audit reads its two
training corpora and common holdout without fitting, scoring a model,
generating a course, or changing a gate. It is descriptive and post hoc;
it cannot identify the cause of the earlier model-performance differences.

Report every world and all registered training seeds (0, 1, 2): eligible
held-command windows, executed action/label support, positive/negative
course counts, classless AUC buckets and the exact rollout split. Reconcile
training/validation window totals with all six original fit receipts.
Room and transit action ids belong to different vocabularies; verify ids
against the recorded physical commands before assigning action names.

Also reproduce the existing counterfactual sampler's hard-pool rule and
compare it with disagreement between answerable candidate labels. Masked
labels must not be mistaken for observed safe labels in this diagnostic.
Report available CF labels and expected source-frame sampling per world
under the existing half-uniform/half-hard sampler. Expected draws are not
observed draws or gradient contribution: minibatch visibility normalization
prevents that inference. The same selected frames feed danger-now loss.

Use the frozen 80 epochs / batch 64 for nominal optimizer exposure. No new
threshold, fit, promotion or recheck is introduced. Preserve all raw study
records and dataset hashes. The already checked rendering belongs to the
source study; this metadata-only audit does not consume synthetic pixels.

Run `bash experiments/schedule_support_v1/run.sh` in the project environment.
New JSON outputs refuse overwrite. If interrupted, inspect existing output
and complete only a missing command, never erase/rewrite measured records.

## Completed diagnostic — 2026-09-13

The three metadata audits completed with `SCHEDULE-SUPPORT-DONE` and
`SCHEDULE-SUPPORT-EXIT=0`. Sources and dataset hashes are recorded in
[legacy.json](legacy.json), [world_balanced.json](world_balanced.json) and
[holdout.json](holdout.json). [verification.json](verification.json)
reconciles every train/validation count with the six original fit receipts,
and every common-exam class count with the original scoring receipt.
Recheck those relationships without generating anything using
`bash experiments/schedule_support_v1/verify.sh`.

### Executed-action coverage and density are different quantities

| World | Legacy eligible windows | Balanced eligible windows |
|---|---:|---:|
| classic | 910 | 1,470 |
| dense | 845 | 1,490 |
| moving | 2,816 | 1,506 |
| room | 3,962 | 3,962 |

These counts include all rollouts in each training corpus, before the
internal split. Moving gains five non-forward action categories (462
eligible non-forward windows) while its total eligible windows fall by
46.5%. Legacy's 2,816 moving windows are all forward. A passive 120-step
rollout supplies 88 eligible horizon-32 starts; action switches remove
starts that cross segment boundaries. Thus a fixed number of rollouts and
epochs is not a fixed allocation of executed-action supervision by world.

| Seed | Legacy moving train windows | Balanced moving train windows | Legacy optimizer steps | Balanced optimizer steps |
|---|---:|---:|---:|---:|
| 0 | 2,288 | 1,225 | 8,800 | 8,640 |
| 1 | 2,288 | 1,223 | 8,640 | 8,560 |
| 2 | 2,288 | 1,214 | 8,640 | 8,480 |

Optimizer counts follow 80 epochs and batch 64 exactly. Total steps fall
only about 0.9–1.9%; that aggregate conceals the much larger redistribution
of moving executed windows. This is a changed learning exposure, not proof
that it caused the completed study's AUC differences.

### A recorded 0.5 was undefined, not chance performance

Legacy seed 0's internal dense validation bucket contains 158 positive
windows from six courses and **zero negative windows**. Its stored AUC 0.5
is the metric's compatibility fallback. The common independent exam has
both classes in every world, so this does not invalidate the study's final
NO-GO. It does invalidate interpreting that particular internal 0.5 as a
measured chance-level ranker. No historical number was overwritten.

Future training metrics now carry class counts and an `auc_defined` flag;
classless world buckets print an explicit warning while preserving the
numeric API for old consumers. A self-contained two-epoch checkpoint test
checks training/probe count agreement and exercised the new warning on a
0-positive / 26-negative moving bucket. This logging change occurs after
optimization and changes no loss, split, sampler or gate bar.

### The current hard pool includes masked-only contrast

The sampler compares `label * visible` vectors. If all answerable candidates
are positive but another candidate is masked, its zero creates a difference
even though no answerable pair disagrees. A synthetic selftest isolates this
case. The real corpora contain it:

| Training seed | Legacy hard frames without answerable contrast | Balanced hard frames without answerable contrast |
|---|---:|---:|
| 0 | 223 / 2,628 (8.49%) | 303 / 2,562 (11.83%) |
| 1 | 225 / 2,617 (8.60%) | 337 / 2,590 (13.01%) |
| 2 | 231 / 2,478 (9.32%) | 324 / 2,613 (12.40%) |

These frames are not necessarily useless: their visible positive labels
still train the collision head, and the selected frames also feed danger-now.
The CF loss continues to mask unanswerable labels correctly. The finding is
about the meaning and allocation of the *hard pool*, not evidence that bad
labels entered the loss or that changing the pool would improve flight.
The training comment now states the actual heuristic; sampling is unchanged.

The existing sampler's expected moving source-frame draws per epoch increase
from 722.8 / 669.0 / 648.5 to 794.6 / 766.8 / 795.0 across seeds 0/1/2.
Room receives zero oracle candidate labels in both corpora, as intended,
but its selected frames still contribute danger-now loss. These expectations
are not reconstructed actual random draws or gradient weights.

### Next decision

Keep schedule_layout_v1 closed. A prospective comparison of the current
zero-masked hard pool with answerable-pair disagreement is now a concrete,
isolatable sampler knob, but its benefit is unmeasured. Alternatively,
restoring moving executed-window exposure is a different data/loss knob;
never combine them in one run. Register matched controls, per-seed guards,
an independent confirmation exam and the unchanged 512 KB architecture
before any fit. This audit alone authorizes neither a performance claim
nor promotion of a checkpoint.

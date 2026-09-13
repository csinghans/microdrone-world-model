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

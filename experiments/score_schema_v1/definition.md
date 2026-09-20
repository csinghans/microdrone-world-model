# Saved-score schema audit — 2026-09-21

Scope: repair malformed-input acceptance in `eval.compare_wm_scores` at
`1933b7d`. Synthetic fixtures show fractional/negative sample indices,
fractional world IDs/horizons and colliding world names can enter comparison.
The reserved world name `all` overwrites the pooled result dictionary entry.
This is a harness issue, not evidence of corruption in a historical study.

Require integral nonnegative indices and world IDs, a unique nonempty
string catalog without the reserved pooled key, strictly increasing positive
integer horizons ending at 32, and complete/aligned binary veer fields.
Check overlapping AUC/veer rollout IDs have the same world. Validate all
inputs before AUC calculation or resampling. Keep valid-input statistics,
bootstrap seeds, missing-support handling and scientific thresholds intact.

Before interpreting compatibility, freeze the 18 score exports and their
original receipts from schedule_layout_v1, cf_hard_pool_v1 and
executed_weight_v1 in registration.json. Read all 18 without fitting,
inference, bootstrap, score regeneration or reading pixels/checkpoints.
Verify their original hashes, validate each export and its paired arm,
and record acceptance or a concrete harness error. Preserve every original
record and NO-GO; do not rewrite, expand or remeasure a closed exam.

Artifactless selftests must exercise malformed cases on either or both
arms, rejection before metric/RNG calls, empty optional probes, course/world
consistency and unchanged results for valid synthetic examples. Retain the
old-code reproduction and all new local logs with true process exit codes.

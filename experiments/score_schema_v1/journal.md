# Paired-score schema validation — 2026-09-21

The [scope](definition.md), [18 export identities](registration.json) and
old-code reproduction were committed at `aed10de` before the compatibility
audit. This fixes a harness defect; it does not assert that historical
exports were corrupted or add a new scientific gate.

`bash experiments/score_schema_v1/verify_before.sh` reruns eight malformed
synthetic cases against the pinned `1933b7d` comparator. It accepted
fractional and negative pair indices, fractional world IDs, duplicate world
names, a world named `all`, horizon 32.5, nonbinary veer truths and veer worlds
inconsistent with AUC worlds. A world named `all` replaced the pooled output:
the synthetic pooled entry reported four samples from an eight-sample exam.

The comparator now validates these fields before computing AUC or creating
the bootstrap RNG. Pair/world indices must be nonnegative integers; world
IDs must index a unique, nonempty, trimmed Unicode catalog without the
reserved pooled key `all`. Horizons must be positive integers, strictly
increasing and ending at 32. Real finite scores and binary labels remain
required; complex-valued scores are rejected rather than implicitly cast.

Optional veer fields must be complete in both arms, with integral indices,
valid catalog IDs, binary truth/correctness and aligned exam identities.
Every course belongs to one world, and AUC/veer records for the same course
must agree. A veer course with no held-command AUC windows remains allowed;
the two sample sets need not have the same course membership. Empty probes
remain explicit null results. No sampling, metric or guard bar was changed.

The [compatibility receipt](compatibility.json) reports **18 accepted
exports in nine paired comparisons**, covering all three training seeds
and both arms of schedule_layout_v1, cf_hard_pool_v1 and executed_weight_v1.
All export and original-receipt hashes agree before and after inspection;
embedded metadata matches the original scoring receipt. The audit runs
only schema/identity validation on archived data. It reads no pixels or
checkpoints and computes no new historical AUC or confidence interval.

Five separate synthetic comparisons exactly match the old implementation's
complete results: ordinary AUC, populated probe, empty probe, singleton
probe and single-class support. These use fixed synthetic bootstrap seed
13 and 47 draws; they do not replace any study's settings or uncertainty.
Reproduce both compatibility and synthetic parity with:

```bash
bash experiments/score_schema_v1/verify.sh
```

The first compatibility-harness attempt failed before validation because
it compared export metadata to the receipt's outer result wrapper. The
scoring result is at `result.scores`. That lookup was corrected and the
same frozen inputs were checked successfully. Both full logs are retained
with hashes and exit codes in [verification.json](verification.json); no
input, stored number or registration was edited to obtain acceptance.

Other verification:

- `python -m eval.compare_wm_scores --selftest` adds 81 malformed-arm checks
  with the AUC function and RNG replaced by fail-if-called sentinels. It
  also tests incomplete/empty probes and additional probe-only courses,
  while retaining the existing paired-course bootstrap regressions.
- `python -m eval.eval_action_auc_audit --selftest` passes its decomposition
  and action/score alignment checks. Both commands already run in manual CI.
- Whole-repository `black --check .` (175 Python files), `ruff check .`
  and `git diff --check` pass. All nine locked artifact SHA checks pass.
  No remote push, CI dispatch or release was performed.

The source corpus is not available to the comparator itself, so these
checks do not establish frame upper bounds, exam completeness, rendered
vision or course independence. This offline validation adds no deployed
parameters or inference work. All closed studies keep their original
scores, support limits, intervals, bars and NO-GO verdicts.

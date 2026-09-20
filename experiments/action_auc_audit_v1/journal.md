# Action-pair AUC audit — 2026-09-20

The [protocol](definition.md) and [input identities](registration.json) were
committed at `2dac82a` before reading action-conditional results. This is
retrospective: the original `executed_weight_v1` model outcomes were known.
The instrument and artifactless selftest were committed at `04c01f1` before
the diagnostic ran. No training, model inference, new exam, resampling or
new pass/fail bar was introduced.

The [generated summary](summary.md), [complete matrices](report.json) and
[figure](moving_contributions.png) report every original seed/arm for all
three transit worlds. All six exports match their frozen hashes and score
receipts; their sample identities, labels and worlds align. Dataset action
IDs match physical commands at the exported frame indices. Every original
world AUC and paired delta reconciles within 1e-12; maximum reconstruction
error is 1.11e-16, recorded in [verification](verification.json).

The moving mean increase +0.059825 splits into +0.032170 from within-action
comparisons and +0.027656 from across-action comparisons. Seed 0 declines
in both parts (−0.009985 and −0.008417); seeds 1 and 2 improve in both.
Thus a change only in across-action comparisons does not describe the
observed mean increase. This accounting does not establish a perception or
optimization cause: within-category comparisons still mix speed and scene.
The failed seed and dense/veer guards remain the original **NO-GO**.

The decomposition exposes another limit of pooled readings. Moving uses
2,989 windows from 42 courses, with 1,680 positives and 1,309 negatives;
53.97% of its positive/negative score pairs compare the same action category.
Of those within-category pairs, **97.10% are forward/forward**. The same
forward dominance is 96.44% in classic and 98.21% in dense. A pooled or
within-category increase cannot certify each steering category separately.

Dense's veer-left subgroup has 134 positive windows and zero negatives,
so its within-action AUC is undefined. Slow, veer-right and climb negatives
come from only one course each (11, 7 and 24 windows respectively). These
are support limits in the existing exam, not new reasons to invalidate it
or enlarge it after the fact. All pair cells, including null ones, remain
visible in the report. The counts are correlated windows and course overlap
is allowed across actions/classes; no independent-sample or CI claim follows.

For a future mechanism targeting steering prediction, register the required
action categories and positive/negative **course** support before fitting;
the existing dataset-support audit can inspect those fields. Preserve this
closed exam and its verdict. This diagnostic does not pick a replacement
training seed or release a new knob.

Verification:

- `python -m eval.eval_action_auc_audit --selftest` passes the independent
  pairwise oracle, ties/permutation/empty-support checks and dataset/action
  alignment failures without artifacts. It is in manual CI's fast group.
- `bash experiments/action_auc_audit_v1/verify.sh` recomputes only the exact
  saved-score accounting and checks all published hashes; it needs the six
  local ignored score NPZs and original exam, never model weights or pixels.
- The original generation log is
  `output/research_integrity_selftest/action_auc_audit_v1.log`, exit 0.
  The figure was visually checked for complete seed labels and readable
  legends. Nothing was overwritten during generation or verification.
- Whole-repository `black --check .` (172 Python files), `ruff check .`
  and `git diff --check` pass. All nine locked-artifact SHA checks pass.
  No remote push or CI dispatch was performed.

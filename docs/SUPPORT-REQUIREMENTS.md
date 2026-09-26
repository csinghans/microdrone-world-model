# Register action support before fitting

`eval.eval_support_requirements` checks explicit count requirements against
a saved `eval.eval_dataset_support` report and the exact corpus SHA. It is
for **new** studies whose registration commits the requirements and the
response to insufficiency before fitting. It does not add gates to closed
studies or automatically permit another dataset draw.

The [action-pair audit](../experiments/action_auc_audit_v1/journal.md) found
that pooled metrics can conceal unsupported steering categories. Register
the worlds/actions the new scientific claim needs, not just a pooled window
count. The checker has no default scientific thresholds.

## Requirements format

Save a JSON object with exactly these fields. The following numbers are a
**format illustration**, not an adopted registration or a power calculation:

```json
{
  "schema_version": 1,
  "target": "executed_warn_at_32",
  "checks": [
    {
      "partition": "all",
      "world": "moving",
      "actions": ["veer_left", "veer_right"],
      "minimum": {
        "positive": 20,
        "negative": 20,
        "positive_rollouts": 5,
        "negative_rollouts": 5
      }
    }
  ]
}
```

Every action in a check must meet **all four** explicit positive-integer
minima. Add checks to cover other worlds, actions or partitions; repeated
`(partition, world, action)` entries are errors. No action or world is
implicitly required. Unknown keys, worlds and actions are errors.

`positive` and `negative` count eligible held-command windows for the warn
label over the flown future through control step 32. `*_rollouts` count
distinct rollout IDs that contain each label for that action. Courses can
contribute to both classes and to multiple actions; these counts must not
be summed as independent observations. Numerous windows from one course
cannot satisfy a requirement for several courses.

Use `all` for the complete corpus or `splits/<seed>/train` and
`splits/<seed>/val` for a recorded training split, for example
`splits/0/train`. Specify every training seed whose partitions matter.
A missing requested split is an error; the checker never substitutes the
complete corpus. A missing required world or action is insufficient support,
reported with zero counts. Classic, dense and moving use the transit action
catalog; room uses the separate navigation catalog (`reverse`, not
`veer_left`). This checker supports the standard horizons `[4, 8, 16, 32]`
and executed warn labels, not counterfactual or danger-now support.

## Run a fail-fast preflight

After the registration is frozen and rendering has been verified, produce
the metadata report. For a separately generated exam:

```bash
python -m eval.eval_dataset_support \
  --data path/to/exam.npz --independent-holdout \
  --out path/to/exam_support.json
```

For training data, omit `--independent-holdout` and specify the registered
`--seeds`, for example `--seeds 0,1,2`, to include train/val partitions. The
producer omits pixels; it reuses the training index, split and label oracle.
It performs no model inference or optimization.

Then check the explicit requirements against that exact file:

```bash
python -m eval.eval_support_requirements \
  --report path/to/exam_support.json \
  --requirements experiments/new_study/support_requirements.json \
  --data path/to/exam.npz --out experiments/new_study/support_receipt.json
```

| Process exit | Meaning | Receipt |
|---|---|---|
| 0 | Every requested count meets its minimum | `status: satisfied` |
| 10 | At least one requested count is too small | `status: insufficient`, all checks and deficits |
| 2 | Invalid config/report, wrong dataset, changed inputs, or output error | No new receipt |

In a queue, use `set -e` or `&&` so exit 10 stops fitting. Retain the complete
log and actual exit code. Follow the registration's response to insufficient
support; do not regenerate exams until they pass, weaken bars or overwrite
the negative receipt. The checker does not launch training or prove that a
downstream training command uses the checked corpus.

The output is published atomically and must be a new filename. It records
all effective requirements and observed counts, the corpus/report/requirements
SHA-256 identities, the report's original provenance and checker source
hashes. Input files are checked again before publication. The corpus is
streamed only for hashing; it is never decoded by this checker. Report
counts are checked for internal consistency, not recomputed from the corpus.
Preserve the trusted producer invocation, report and registration together.

Both metadata producers (`eval.eval_dataset_support` and `eval.eval_veer_support`)
also publish complete JSON atomically to fresh destinations. They reject
existing/reserved paths before loading data and recheck dataset/source
hashes after analysis and encoding. Failed encoding or interrupted writes
cannot expose a partial final report; an abruptly terminated worker can
leave a hidden temporary file. Existing partial results still require
inspection and are never silently overwritten. The
[publication tests](../experiments/support_publication_v1/journal.md) cover
these cases and verify unchanged historical support counts.

The [timing split audit](../experiments/early_intervention_split_v1/journal.md)
provides a measured example: a candidate passed its full-corpus steering
requirements, retained them in all 12 fixed-seed training action cells,
but passed only 2 of 12 validation cells under the same minima. A separate
geometric veer-probe inventory also found missing moving validation courses.
Full-corpus counts cannot substitute for either partition support or a
different endpoint's sample selection.

New producer reports declare schema 1 and their target. Historical reports
without these fields are not silently upgraded; historical records and
verdicts remain unchanged. For a new study, generate a fresh metadata report
under its registered recipe. The tool records the requirements identity,
but establishing that it was frozen before fitting is the campaign's job.

Passing these count bars does not establish power, independence, rendered
vision, train/exam separation, or model performance. In particular, distinct
rollout IDs need not mean independently generated courses. The tool runs
offline and adds no deployed-model parameters, RAM use or inference work;
embedded timing and budget claims still require their own measurements.

Run `python -m eval.eval_support_requirements --selftest` for synthetic
boundary/error/CLI regressions, including a real metadata-producer path
with deliberately unreadable pixels. No local model artifacts are needed.

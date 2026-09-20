# Prospective action-support requirements — 2026-09-20

The completed [action-pair audit](../action_auc_audit_v1/journal.md) exposed
classless steering buckets and negatives concentrated in one course.
This phase turns the suggested future preflight into an explicit count
checker. It introduces no experiment, scientific bar or new model result.

`eval.eval_support_requirements` consumes a new dataset-support report,
an explicit requirements JSON and the corpus file. Requirements name each
world/action/partition and all four minima: positive/negative windows and
positive/negative rollout counts. Transit and room action catalogs remain
distinct. Missing required worlds/actions produce zero-count deficits;
missing partitions, malformed counts and configuration typos are errors.

The checker emits a fresh atomic receipt with every expanded requirement,
observed count and deficit. It pins dataset/report/requirements/source
SHA-256 identities, checks the corpus against the report's recorded SHA,
and checks inputs again before publication. Exit 0 means satisfied; exit
10 means insufficient support; input/output errors exit 2. An insufficient
receipt is retained so a fail-fast queue stops with reviewable evidence.

The producer now identifies its report schema and executed-warn target.
Existing count calculations are unchanged. Unversioned historical reports
are not silently upgraded. Use the [guide](../../docs/SUPPORT-REQUIREMENTS.md)
to freeze requirements in a **new** registration, including what happens
after insufficiency. The illustrative numbers are not adopted study bars.
The checker does not enforce registration chronology or a later training
command's choice of input file.

Validation, recorded in [verification.json](verification.json):

- `python -m eval.eval_support_requirements --selftest`: 15 artifactless
  regressions pass. They cover exact boundaries, per-course deficits despite
  enough windows, missing classes/actions/worlds, explicit partition routing,
  catalog errors, malformed counts, strict JSON, changed inputs, wrong
  dataset identity, all three CLI exits and no-overwrite publication.
- The integration fixture invokes the real dataset-support CLI on synthetic
  metadata with an object-valued pixel payload that cannot be loaded with
  `allow_pickle=False`. Its new report reaches the checker successfully:
  24 positive and 24 negative windows from three courses per class. These
  are synthetic fixture counts, not rendered-vision or research results.
- `python -m eval.eval_dataset_support --selftest` passes its original
  indexing/split/catalog/CF checks. The new checker selftest is included
  in manual CI's pure-math group.
- Whole-repository `black --check .` (174 Python files), `ruff check .`
  and `git diff --check` pass. All nine locked-artifact hashes verify.
  No model checkpoint, training recipe, frozen gate or historical result
  was edited. No new fit, inference, remote push or release was performed.

Full local logs are listed with hashes in the verification receipt. These
checks ran on the local macOS/Python 3.14 environment; no Linux/Python 3.12
remote CI result is claimed. The previous artifactless workflow audit stays
at its frozen source and 116 commands; this added command is tested here.

Count requirements are an offline research control. They add no deployed
model parameters or inference work, and do not establish embedded timing,
power, independent courses, rendered frames, train/exam separation or a
performance improvement. Window correlation and course overlap still
matter. Closed studies retain their original NO-GO verdicts and support
limits; no historical exam was expanded or remeasured.

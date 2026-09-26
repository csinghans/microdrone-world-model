# Support-report publication reliability

## 2026-09-27 — Scope before repair

Inspect the two metadata producers `eval.eval_dataset_support` and
`eval.eval_veer_support`. Both write JSON directly to the final path and
capture source hashes only after analysis. This engineering repair changes
publication/provenance boundaries, not support counts, labels, splitting,
probe selection or any scientific threshold.

`verify_before.sh` replays source `cbd4549` in temporary directories with
mocked metadata/analysis and no model artifacts. It checks whether failed
serialization leaves invalid final JSON that blocks another invocation, and
whether an absent reserved artifact destination accepts JSON. No real
dataset, model path or earlier result is modified.

The intended repair uses the existing protected atomic publication helper,
rejects invalid destinations before reading input data, serializes a full
finite JSON payload before publication, and pins/rechecks source identities
around analysis. Existing outputs remain immutable. Preserve complete logs
and test genuine failure/race paths with isolated fixtures; do not fit,
regenerate data or reopen a closed research result.

## Reproduced before the repair

Commit `3edeffe` records the reproducer and [before.json](before.json).
For both CLIs, a non-serializable analysis field leaves invalid final JSON;
that file then blocks a clean invocation. Both also accept a reserved model
destination when it is absent in the temporary checkout. All observations
use synthetic temporary files, never the project's real protected paths.

## Completed repair and failure tests

Both producers now preflight outputs through `check_destination`, encode
the complete finite JSON first, and publish through `publish_checkpoint`.
That existing helper writes/fsyncs a sibling temporary and atomically links
a fresh final file, preserving a concurrent writer. Existing paths, symlink
destinations, protected paths and aliases are rejected before data loading,
including protected files absent on a fresh clone.

Source hashes are captured before metadata loading/analysis and compared
again after serialization, alongside the dataset identity. The veer tool
also rechecks every previously matched export after the complete export
list, preventing an earlier file's changed contents from retaining a stale
successful-match receipt. Reports keep their numerical schema and values;
new provenance records include the publication helper and relevant sources.

`python -m scripts.support_publication_selftest` passes **11** artifactless
regressions, covering both real metadata-analysis paths with intentionally
unreadable pixels, relative filenames, protected/alias/existing destinations,
bad JSON/NaN, disk failure, a competing writer, changed datasets/sources,
changes during serialization, and changed earlier exports. CI includes it.

The abrupt-exit test terminates each child writer with exit 37 after a
partial temporary write. Neither final report appears. Hidden temporary
files remain because an abrupt exit cannot run cleanup; they are not valid
results and the test's temporary directory removes them. This establishes
complete final-file visibility, not power-loss durability. Ordinary caught
serialization/write errors remove temporary prefixes. Old partial reports
are not automatically overwritten or deleted by this repair.

The initial eight-command validation passed, including existing metadata,
veer, requirements and split-instrument selftests plus full Black/Ruff.
The additional abrupt-exit regression and full lint then passed with all
**180 Python files**. Development lint caught one overlong display string;
it was split before the first regression run. All captured check commands
exited 0; the two deliberate child exit-37 events are asserted test behavior.

## Scientific compatibility

`verify_compatibility.sh` proves that every non-CLI function in the two
modules has exactly the same AST as `cbd4549`, including analysis, selection,
loading and existing selftests. It also recomputes four saved reports from
their SHA-pinned corpora without pixels or model calls:

- Both timing-pilot arms' complete and seed-0/1/2 partition support reports
  match all saved numerical/semantic fields, excluding separate provenance.
  Their 12,339 / 13,331 whole-corpus window totals remain unchanged.
- CF-hard-pool and executed-weight veer reports match exactly, including
  probe selection identities and all world support: 208 frames / 23 courses
  and 190 / 20 respectively.

[compatibility.json](compatibility.json) preserves input/archive hashes and
all nine intact protected-artifact hashes. No historical report, source data,
split, label, model score or verdict was overwritten. A historical strict
source verifier still requires its original snapshot; it should not accept
new CLI source hashes as if they were the recorded instrument. This explicit
compatibility check separates unchanged scientific values from changed
publication code.

Full logs are `output/research_integrity_selftest/support_publication_v1_*`.
The [verification receipt](verification.json) records their identities and
actual exits. Run `PYTHON=/path/to/python bash
experiments/support_publication_v1/verify.sh` to replay the before-case,
compatibility and frozen-file checks. Validation is local macOS/Python 3.14,
not remote Linux/Python 3.12 CI. No deployed RAM, parameters or inference work
is added; this offline repair makes no new 512 KB / 8 ms performance claim.

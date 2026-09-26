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

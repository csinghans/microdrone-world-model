# World-model export publication — 2026-09-21

At `3ec33ae`, the checkpoint probe used exclusive-create writes directly at
the final JSON and NPZ paths. This prevented overwrite but exposed partial
files when serialization failed. The [frozen before receipt](before.json)
and `bash experiments/wm_publication_v1/verify_before.sh` reproduce both
failures with the old CLI function: a failed NPZ writer leaves `partial NPZ`
bytes; an unsupported JSON value leaves an unparsable nonempty prefix.
Evaluation is mocked and no checkpoint is loaded or scored.

The probe now uses the existing `world_model.checkpoint_io` publication
helper. It checks every destination before loading inputs or evaluating:
paths must be fresh and distinct, symlink destinations are rejected, and
locked artifact paths remain reserved even on an artifactless checkout.
JSON metadata is fully encoded before either output is published. Each
file is serialized into a sibling temporary file, flushed and fsynced,
then linked into place without replacing a concurrent writer. Failed
serialization removes its temporary file and exposes no final-path prefix.

The score arrays, metadata contents, model evaluation and scientific bars
are unchanged by this work. JSON formatting and NPZ compression stay the
same. Each file is atomic; the **pair is not one transaction**. A second
publication failure retains the complete first NPZ (including its metadata)
and the command fails without printing `WM-PROBE OK`. Retain that file and
the full error log for recovery; do not treat its existence as a completed
two-output export or automatically rerun scoring. Completion requires exit
0 and both requested outputs with matching metadata.

Verification is recorded in [verification.json](verification.json):

- `python -m scripts.wm_publication_selftest`: eight artifactless regression
  tests pass through the real argument parser and CLI with only evaluation
  mocked. They cover successful score/metadata round trips, NPZ serialization
  failure, prepublication JSON encoding failure, partial JSON disk writes,
  failure of the second publication, existing/aliased/locked destinations,
  a competing writer, and changed input identity. Faults leave no temporary
  prefixes behind; the competing writer's bytes remain intact.
- `python -m scripts.dataset_identity_selftest` still passes source-mutation,
  original-validation and independent-holdout identity checks. The new
  publication selftest is included in manual CI's pure-math group.
- The frozen before-reproduction still verifies against the old source.
- Whole-repository `black --check .` (175 Python files), `ruff check .` and
  `git diff --check` pass. All nine locked artifact SHA checks pass before
  and after the work. Full local log hashes and source identities are in
  the receipt. Tests ran on local macOS/Python 3.14; no remote CI result
  is claimed.

This offline reliability change adds no deployed model parameters or
inference work. No training, model inference, historical remeasurement,
new gate, remote push or release was performed.

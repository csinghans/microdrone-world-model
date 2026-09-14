# Checkpoint publication repair — 2026-09-14

The world-model training CLI at `3884336` selected its destination after
fitting and called `torch.save` directly on the deployed champion path by
default. A synthetic reproduction replaced an existing temporary sentinel:
[original receipt](before.json). No real champion was written and no model
was fitted. Reproduce only in temporary storage with
`bash experiments/checkpoint_io_v1/verify_before.sh`.

The CLI now chooses `output/world_model_candidate.pth` for ordinary training
and validates the destination before loading/generating data. Existing
research outputs require a new `--out`; locked paths remain reserved even
when the artifacts have not been downloaded. Canonical paths, symlinks and
hard links cannot redirect a world-model write onto a locked asset.
Variant suffixes remain supported. Selftest mode keeps its own replaceable
`*_selftest*` filenames and ignores an explicit production `--out` as before.

Serialization finishes in a sibling temporary file, flushes the file, and
publishes a new checkpoint using a hard link that fails if the destination
already exists. Failed serialization leaves prior files intact and removes
temporary files. A concurrent publication cannot overwrite the winner.
Only explicit selftest replacement uses atomic replacement of an ordinary
file. This is local filesystem publication, not a distributed transaction.

The related artifactless-evaluation fallback previously wrote its tiny
stand-in to the missing requested model path. It now caches a labelled
`*_autotrained_selftest.pth` file separately. The research dry runner's
explicit selftest path is still honored, so its path/SHA provenance remains
valid. Existing measured models load through the original path.

Validation completed:

- `python -m world_model.checkpoint_io`: missing locked paths, symlink and
  hard-link aliases, roundtrip tensors, existing outputs, serialization
  failure, selftest replacement and a simulated publication race.
- `python -m scripts.checkpoint_io_selftest`: ordinary candidate publication,
  rejection before loading/fitting, explicit output, selftest naming,
  reusable tiny cache, explicit dry path and the actual dry-scope context
  manager's provenance. Model fitting and simulator generation are stubbed.
- `python -m scripts.dataset_identity_selftest`: source mutation still blocks
  publication; train-file identity and independent-exam checks still pass.
- `python -m scripts.research_selftest`: all 16 isolated regressions pass;
  full log `output/research_integrity_selftest/checkpoint_research_regressions.log`,
  actual exit 0.
- The real CLI rejects each protected WM destination before attempting to
  load a deliberately nonexistent dataset. Both original hashes remain
  intact; see [the rejection receipt](cli_rejection.json). No training or
  scoring takes place in this check.
- Whole-repository Black (167 Python files), Ruff and whitespace checks
  pass. All nine locked artifacts verify before/after the repair.

One initial synthetic test compared macOS `/var` with canonical `/private/var`
as path strings. Resolving the expected temporary root corrected that test
fixture; the destination's intended canonicalization stayed unchanged.
No model measurement, registration, historical verdict or training recipe
was changed. README and both onboarding languages explain candidate usage.

Scope: these guards cover the world-model CLI and evaluation fallback.
Policy training and standalone historical scripts still own their save
implementations; this is not a repository-wide interception of every save.
No remote push, CI dispatch, release tag or promotion was performed.

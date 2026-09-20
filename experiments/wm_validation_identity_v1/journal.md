# Original-validation corpus identity — 2026-09-20

At `5b40dff`, `eval.eval_wm_checkpoint.evaluate()` enforced the checkpoint's
training seed and rejected known training-file reuse in independent-holdout
mode. Ordinary `training_val` mode still accepted a known **different**
corpus SHA. A matching seed alone cannot establish that the same physical
courses enter validation when the corpus has changed or been reordered.

The [before receipt](before.json) pins the old source and a synthetic API
reproduction: a checkpoint with training hash `a…a` receives dataset hash
`b…b`, calls the scorer once, and returns its `training_val` result. Model
loading and scoring are mocked; no historical score is implicated by this
reproduction. Reproduce the frozen behavior with:

```bash
bash experiments/wm_validation_identity_v1/verify_before.sh
```

Ordinary validation now rejects known hash mismatches before scoring or
writing outputs. `datasets.provenance.require_training_file()` accepts a
renamed byte-identical file, including case-insensitive hex hashes. A
recompressed or reordered file is not the original file identity and is
rejected. The error directs the caller to restore the original corpus;
repacking training data does not make an independent exam.

Missing checkpoint or caller hashes remain supported for legacy/in-memory
workflows, with a warning in ordinary validation. Returned metrics now
record `dataset_file_relation` as `same_as_training`,
`different_from_training`, or `unverified`. In independent-holdout mode a
different hash still proves only different bytes, not disjoint courses;
the existing exact-reuse rejection is unchanged. In-memory API callers
remain responsible for binding a supplied hash to the data dictionary.

Validation:

- `python -m scripts.dataset_identity_selftest` passes the training identity
  and mutation checks, API/CLI holdout reuse and validation mismatch
  rejection, absence of output files on either error, correct-file success,
  explicit unknown identities and legacy compatibility. Its split-only
  synthetic fixture also verifies that reordering course identities while
  retaining the same seed preserves selected indices but changes which
  courses they represent. No fitting or model inference occurs.
- `python -m datasets.provenance` passes matching/renamed/case-normalized
  identities, opposite-direction holdout/validation errors and unknown
  legacy identities.
- `python -m eval.compare_wm_scores --selftest` passes its paired course
  bootstrap, alignment, identity and undefined-AUC regressions. No archived
  score export or bootstrap result was changed.
- The frozen before-reproduction still passes after the repair. These
  existing selftest commands are already in manual CI's fast group.
- Whole-repository `black --check .` (174 Python files), `ruff check .` and
  `git diff --check` pass. All nine locked artifact hashes match before
  and after this phase. See [verification.json](verification.json) for
  full-log hashes, source identities and runtime details.

This is an offline protocol check; it changes no model architecture,
training recipe, deployed memory use or inference work. No new training,
scientific bar, closed-study remeasurement, remote push or release was
performed. Results from legacy inputs remain explicitly unverified rather
than being retroactively relabelled as verified or failed.

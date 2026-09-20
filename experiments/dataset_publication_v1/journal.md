# Preserve generated corpora — 2026-09-21

At `ecb167e`, all three dataset CLIs wrote directly with
`np.savez_compressed(path, ...)`. Reusing `--out` silently replaced a
previous corpus after running generation. The [before receipt](before.json)
pins the three CLI sources; reproduce their overwrite behavior with
`bash experiments/dataset_publication_v1/verify_before.sh`. It uses temporary
synthetic files and mocked generators, with no simulation or model work.

`datasets.generate_rollouts`, `datasets.search_rollouts` and
`datasets.combine_rollouts` now preflight a fresh `.npz` destination before
simulation. Existing files, symlink destinations, reserved paths and missing
`.npz` suffixes fail early. Filename-only relative paths also work; their
parent is resolved instead of attempting to create an empty directory name.
Use a distinct output for each registered corpus, preserving the prior draw.

`datasets.provenance.save_dataset()` writes through the existing atomic
publication helper. A serialization failure leaves no partial final corpus;
a competing file created during generation is preserved. The helper is
available to programmatic callers, while `gen()`/`build()` continue to return
dictionaries. Standalone callers that directly invoke NumPy still own their
publication behavior. No overwrite option was added for ordinary datasets.

The transit selftest keeps its dedicated `wm_dataset_selftest.npz` and ignores
the ordinary `--out`, as before. Its replacement now occurs **after** all
smoke assertions pass. Explicit selftest replacement requires a `_selftest`
filename; a failed serialization preserves previous bytes. Indoor and
combined selftests retain their existing no-publication behavior.

The [verification receipt](verification.json) records source identities,
full-log hashes, actual exits and an AST comparison with `ecb167e` proving
that every non-CLI function in the three generator modules is unchanged.
CLI regression fixtures check explicit seed, repeated world order,
`legacy` schedule and the indoor FOV flag reach their generators unchanged;
saved arrays reload exactly. The default recipes and scientific bars stay
the same.

Validation:

- `python -m scripts.dataset_publication_selftest`: nine artifactless
  regressions cover all three CLIs, early rejection, exact array round trips,
  recipe forwarding, filename-only paths, partial serializer failure,
  competing publication, scoped replacement, ignored explicit selftest
  output and preservation after a real CLI smoke assertion fails.
- `python -m datasets.generate_rollouts --selftest`: the existing 12-rollout
  transit simulation passes reset, command/speed, role, label and nonblank
  camera checks, then saves only its selftest corpus.
- `python -m datasets.search_rollouts --selftest`: the existing three-rollout
  room simulation passes its schema/action/label checks. These smoke draws
  are not new study datasets or evidence of model performance.
- The existing `datasets.combine_rollouts --selftest`, `datasets.provenance`
  and `scripts.dataset_identity_selftest` checks pass. The new publication
  selftest is included in manual CI's pure-math group.
- Whole-repository `black --check .` (176 Python files), `ruff check .` and
  `git diff --check` pass. All nine locked artifact SHA checks pass before
  and after the work. No remote CI result is claimed.

This changes offline file handling, with no deployed parameters or inference
cost. There was no training, historical remeasurement, new performance gate,
remote push or release. Existing research corpora and negative verdicts were
not replaced; only the named transit selftest output was generated.

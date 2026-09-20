# Freeze evaluation settings before the first knob — 2026-09-20

At `23277c2`, campaign resumption checked skill/version and criteria, but
saved no cell specification or borderline-recheck settings. A frozen-source
synthetic reproduction accepted changes to world, speed, seed, sample count,
kwargs, cell role, recheck count and recheck margin under the same criteria.
The [before receipt](before.json) records the source SHA and eight accepted
changes. This establishes a missing check, not a finding that a historical
experiment changed these settings.

New campaigns now carry `evaluation_frozen`: the ordered complete EvalCell
records plus `recheck_n` and `recheck_margin`, detached from mutable nested
kwargs by JSON serialization. `step` and `run` save the initial result file
before their first fit/flight. Even if the first knob is interrupted, a
restart must match that snapshot. Loading a newer record and recording a
gate both check it; cell additions/removals/reordering and in-memory kwargs
mutation cannot silently change the exam. Criteria continue to use their
existing freeze. Adding justified knobs remains supported.

Legacy records without this evidence remain readable. `status --json`
identifies them as `legacy_unrecorded`, and completed `run` calls remain
no-ops. A new measurement against such a record stops before training. A
future continuation must recover the original pre-registration through an
explicit migration backed by historical source/configuration evidence;
copying today's skill settings would invent evidence and is not automated.
No historical result was upgraded, invalidated or resampled here.

The [legacy audit](legacy_audit.json) covers 15 existing runner result files.
All 15 remain byte-identical and readable by both the original and current
loader; none contains a frozen evaluation snapshot. This is a metadata-only
compatibility audit. Reproduce it and the before behavior with
`bash experiments/frozen_evaluation_v1/verify.sh` in the project environment.

Validation:

- `python -m scripts.research_selftest`: 23 isolated regressions pass, adding
  cell/recheck drift, nested mutation, interrupted-first-knob persistence
  for both routes, initial-write failure, legacy refusal and completed-legacy
  no-op checks, plus status labels for unsaved/frozen/legacy settings.
  All earlier negative-preservation, pooling, locking, scoped
  Git and WM-protection tests still pass.
- `python -m scripts.research status gap-flight --json`: the real read-only
  CLI reports `passed`, preserves the original verdicts and reports
  `evaluation_identity: legacy_unrecorded` with no next knob.
- Test log: `output/research_integrity_selftest/frozen_evaluation_selftest.log`,
  process exit 0. No optimizer, drone flight or research score was run.
- Whole-repository `black --check .` (170 Python files), `ruff check .`
  and `git diff --check` pass; all nine locked-artifact SHA checks pass.
  No remote push or CI dispatch was performed.

This freezes declarative evaluation settings, not transitive scenario or
success-predicate source code. The registered source revision still belongs
in the research evidence. Existing negative results, targets and guards are
unchanged; this repair does not authorize a rerun or release a reserve knob.

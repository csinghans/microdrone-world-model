# Early-intervention support pilot journal

## 2026-09-27 — Registration

Frozen before generating either arm. Prior held-command audit recovered
windows without adding training action/class course coverage. This pilot
tests intervention timing on paired, isolated random streams. No training
is authorized by its outcome. Definition, seed, counts, instrument checks,
support minima and negative-result response are committed first.

## Instrument preflight

Registration commit: `b56e007`. The new generator options retain shared RNG
and approach timing as defaults, including the old NPZ schema. Synthetic
tests check original schedule draws/RNG state, shifted command sequences,
stream isolation, and rejection of damaged pairing metadata. CI includes
the self-contained study selftest; no champion loads or fitting are needed.

The eight-command preflight passed, including 10 existing publication
regressions, 15 support-requirement regressions, dataset-support and schedule
selftests, whole-repository Black (178 Python files), Ruff and diff check.
Full log: `output/research_integrity_selftest/early_intervention_v1_preflight.log`.
Initial development lint found two unused imports; both were removed before
this preflight and before any generation. The registered simulator parity
and vision checks are the first two stages of the persistent queue.

Reproduce with `PYTHON=/path/to/python bash
experiments/early_intervention_support_v1/run.sh`, preserving full stdout and
stderr. The runner locks against duplicate processes, reuses only receipts
whose hashes verify, and refuses unfinished stage directories. `EXIT` and
`DONE` in its output directory retain process completion state.

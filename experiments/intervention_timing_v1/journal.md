# Intervention timing v1 journal

## 2026-09-27 — registration and instrument preparation

Registration committed as `f8acc83`, before new generation, fitting or scoring.
The [definition](definition.md) freezes the four action-specific primary
cells, forward/world/now/veer guards, all six training runs and the response
to insufficient support. This is a new model study using the closed pilot
as development data, with a new common exam; no old experiment is reopened.

The new runner reuses the established model fitting/scoring routines, while
adding an explicit preflight gate and paired data recipes. Source/runtime,
input and all nine locked artifact identities are frozen in a manifest;
each stage requires a complete process log, actual zero exit and immutable
output receipt before the next stage. Every fit uses a fresh study path.

Instrument development initially failed a synthetic support fixture because
it omitted the support checker's required horizon/count schema. The full
failure log is retained at
`output/research_integrity_selftest/intervention_timing_v1_initial_selftest.log`
(actual selftest exit 1). Corrected fixtures exercise the actual strict
schema. During source review, room-local world-ID remapping and distinct
room/transit action catalogs were handled explicitly before any study data
was generated. No scientific reading was produced by the failed selftest.

The evaluator tests tied scores, undefined classes, every individual guard,
memory/latency vetoes, missing/nonfinite/inconsistent metrics, all seed
identities and exact export-to-corpus/probe coverage. Its primary bootstrap
is checked against a separate pairwise AUC oracle with shared course draws,
duplicate multiplicity and a course containing no primary windows. The
runner tests support boundaries, world/action failures, room remapping and
the no-fit response to insufficient support. These use synthetic data, no
locked checkpoint or model fitting.

The [prelaunch verification](prelaunch_verification.json) records ten checks,
all exit 0: the new runner/evaluator, six dependency selftests, whole-repo
Black (182 Python files), Ruff and diff whitespace. All nine locked artifact
hashes match. These are local macOS/Python 3.14 checks, not remote CI.
Runtime records belong in `records/`; support receipts and models belong
in `output/intervention_timing_v1/`. An active queue is not a result.

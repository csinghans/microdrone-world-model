# Moving-only intervention timing v1 journal

## 2026-09-27 — registration and instrument

Registration committed as `0ea3f90` before instrument completion, new exam
generation or fitting. The closed all-world timing NO-GO and three subsequent
exploratory audits motivate a new moving-specific question; none is reopened.

The candidate copies complete moving rows from the registered immediate
development corpus into the paired approach corpus. The runner checks source
pairing, initial pixels/positions/distances, schedule-prefix correspondence,
unchanged passive rows and room rows, exact nonmoving array preservation,
and original approach train/validation memberships. New metadata explicitly
identifies the mixed timing recipe instead of calling every world immediate.

The independent exam and every support/performance floor are frozen in
`registration.json` and `definition.md`. Four moving action-by-timing support
checks and four corresponding performance guards supplement the pooled moving
primary and dense action guards. Training remains conditional on the complete
support gate. All six fits then run before scoring; internal validation does
not select an epoch, seed or candidate.

The first runner selftest failed before measurement because its synthetic
fixture inherited the helper's 8-frame default while the test needed a
24-frame approach prefix and a 32-frame forecast. Changing this synthetic
fixture to 64 frames fixed the test; no registered data, source corpus,
scientific input or threshold changed. Both initial and corrected logs remain
in `output/research_integrity_selftest/moving_timing_runner_*.log`.

The prelaunch suite passed 11 checks, including the new runner/metrics,
unchanged timing runner, support/veer tools, score comparison, combination,
shared training runner, whole-repository Black/Ruff and whitespace checks.
`prelaunch_verification.json` records commands, actual exits, log hashes and
all nine protected hashes. A final instrument check follows the addition of
read-only support/score recomputation to `--verify`; it does not refit or infer.

Execution uses 22 fresh stage directories, a single-runner lock, subprocesses
to release model memory between stages, complete logs, actual process exits,
immutable receipts, source/runtime/input hashes and preserved failed stages.
An insufficient-support result closes this study without fits or redraws.
No model-performance result exists at this instrument checkpoint.

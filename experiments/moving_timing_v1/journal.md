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

## 2026-09-27 — preflight READY, six-fit queue released

Instrument commit `92d2004` launched at 14:56:21 UTC. All nine prerequisite
stages completed on their first measurement attempt, with actual process
exit 0 and verified complete-log/output hashes. The frozen manifest is
`652b2b102b24a42c6c2649b298efd657d9b5173aab747ef9e7aa07dffb8f1c14`.
All four rendered/removed-body fixtures pass, with nonblank pixels and
visible geometry. The two 276-course corpora share exact initial scene
fingerprints, 20 unchanged passive moving rows and 96 identical room rows.

The fresh 1,440-course exam contains 100,548 eligible held-command windows.
It has no exact initial-scene fingerprint overlap with either development
arm or the 1,440-course closed timing exam. All 43 direct support checks and
both arms' required moving-action checks at all three training seeds pass.
The per-timing moving-action cells have at least 22 courses in each class.
The geometric probe has 1,347 frames / 162 courses, with moving contributing
134 frames / 16 courses. See `preflight.md` and all seven archived support
reports; these counts are coverage evidence, not power or performance.

Both arms preserve the original 221/55 train/validation memberships at
seeds 0/1/2. Their respective training-window counts are 14,202/14,432,
14,261/14,519 and 14,283/14,545. Total development windows change from
17,831 to 18,143; optimizer-step and exposure differences are registered
consequences of the moving-only timing knob. The dense training limitations
remain visible in the full reports, not treated as repaired.

The support gate released the six fits in registered order, starting with
`train_approach_0` on MPS. The background queue then scores all six models
on CPU and writes the final guarded report. No result is selected from
internal validation. `launch.json` records the launch, and
`preflight_verification.json` binds the nine successful stages and copied
support evidence. Recheck live processes before any resume; do not launch a
duplicate or repeat a stage with an orphan output directory. No performance
verdict, flight claim or promotion has been made at this checkpoint.

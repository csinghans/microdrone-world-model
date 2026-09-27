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

## 2026-09-28 (Asia/Taipei) — closed NO-GO

The background queue finished at 2026-09-27 15:54:18 UTC, after all 22
registered stages completed on their first measurement attempt with actual
exit 0. The six fits and six CPU scorings used the frozen instrument and
inputs throughout. The outer queue records EXIT=0 and `moving-timing-DONE`.
No worker remains active. After the assistant's quota pause, ordinary usage
was available at the 18:42 UTC wakeup; no reset credit was redeemed.

The first complete `--verify` invocation exited 0. It verified all original
stage exits, complete-log/output hashes, protected artifacts and source/input/
runtime identity, and exactly reproduced every support file and final score
reading, including the registered bootstrap. It performed no new fit or
model inference. All nine protected artifact hashes still match the lock.

The moving left/right primary deltas at seeds 0/1/2 are
+0.044979342370162656 / +0.02512747618233907 / −0.03971556722053182;
mean +0.010130417110656634 misses +0.03, and seed 2 fails positivity.
Moving geometric veer deltas are −0.29850746268656714 /
−0.23134328358208955 / −0.06716417910447764: all fail the −0.05 guard.
Dense-left action deltas at seeds 1/2 are −0.07883755939220016 /
−0.04946135390694828 despite identical dense training arrays. Dense-right
guards pass in every seed; this does not cancel the other failures.

Thirteen of 67 decision checks fail. Besides the primary and moving-ranking
failures, classic ranking fails seed 0; both pooled moving actions and three
of four moving timing-block cells fail seed 2. All pooled-world, forward,
danger-now and pooled geometric-ranking guards pass. The latter would hide
the moving ranking loss without per-world guards. No uncertainty interval
changes these point-estimate gates: all three fixed pairs have 2,000 valid
course-bootstrap replicates and zero undefined replicates.

Every architecture bill is 137.290039 KB analytic int8, 3,856,768 MACs per
decision and 7.713536 ms at the assumed 0.5 GMAC/s. Hardware timing,
quantization parity and flight behavior were not evaluated. Full point
estimates and every guard are in `report.json` and `summary.md`; original
process outcomes are copied to `process_exits/` and bound by `verification.json`.

This closes the moving-only recipe without a flight gate, recheck, changed
bar, additional seed/course, champion replacement or release. The old
all-world study used another exam and independent model draws, so the two
studies do not form a direct three-arm ablation. The consistent moving
ranking loss is a measured target for a separately declared diagnostic;
its training cause is not established and no further fit is released here.

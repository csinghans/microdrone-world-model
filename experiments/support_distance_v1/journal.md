# Finite distance support validation

## 2026-09-27 — Scope before repair

The metadata support producer compares distance minima and the danger-now
radius without first rejecting nonfinite values. A NaN comparison is false,
so corrupted inputs can appear as negative labels. This repair will reject
nonfinite/non-real distance matrices and nonfinite/nonpositive scalar radii
before indexing or oracle work, while preserving valid signed room
clearances. It does not validate all geometry or change label definitions.

`verify_before.sh` runs source `c7b6b89` on a synthetic six-course fixture,
with no pixels/models or real data changes. The reference has 48 positive
held windows. A single NaN inside every held window silently turns those
48 windows negative; a NaN radius turns 240 danger-now positives negative.
The exact fixture observations are saved in `before.json` before repair.

## Completed repair and verification

The producer now rejects nonfinite/non-real distance arrays, wrong matrix
dimensions, and nonfinite/nonpositive/non-real/non-scalar danger-now radii
before either indexing or the counterfactual oracle. It does not replace
NaNs, drop samples, or manufacture safe labels. Signed finite clearances
remain accepted: a room penetration is hazardous, not malformed data.
The current function still does not validate the complete geometry schema.

The expanded selftest checks 17 malformed distance/radius cases and proves
the index/oracle are never called for them. A negative room-clearance fixture
retains its three positive held-window and danger-now labels. Existing
publication, requirements and split-instrument regressions also pass;
whole-repository Black/Ruff pass for 180 Python files. All seven verification
commands exited 0. An initial patch context mismatch stopped loudly before
changing code; the patch was then applied against the actual current text.

`verify.sh` replays the before-case and recomputes four valid archived
corpora: both timing arms and both older combined schedule-layout arms,
including indoor data. Every complete-corpus and seed-0/1/2 partition
support value matches its archived record. No original records or datasets
are rewritten. The nine protected artifact hashes remain intact.

Full logs and checksums are recorded in [verification.json](verification.json).
The previous publication-only AST verifier requires its own source snapshot
now that `analyze` deliberately adds validation; this audit's valid-data
comparison provides the current numerical compatibility evidence.
No fit, new simulation, model score, bootstrap or scientific gate is added.
Validation is local macOS/Python 3.14, not remote CI. This offline change adds
no deployed parameters, RAM or inference work.

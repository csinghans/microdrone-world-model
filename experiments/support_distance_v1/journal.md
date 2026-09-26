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

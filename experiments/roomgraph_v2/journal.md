# roomgraph_v2 — a clutter-robust crossing detector

**Opened:** 2026-07-11 · **Owner:** Hans · **Source:** docs/REVIEW-2026-07.md (C4);
the named next of `search_roomgraph_v1` (clean-room 100 %, clutter 0.139 —
systematic over-counting from box-pinch false fires; single-frame
`-max_wall_run` measured insufficient at AUC 0.631 on the 935-firing
discriminator set).

## P0 — the traversal-window feature, offline (this sitting)

**Hypothesis.** A doorway is distinguishable from a box-pinch ACROSS A
TRAVERSAL, not from a vantage: the divider wall flanks the crossing on
BOTH sides for the whole window, while a passed box flanks one side and
drops away. Single frames cannot see persistence; a window can.

**Operationalization (frozen before any number).** For each firing
position in the v1 discriminator set (same seeds 210000+, n=12 rooms of
4, clutter=2, same `passage_score > FIRE_THR` firing rule, same
geometric labels): take the firing's best squeeze axis, set the crossing
direction to its perpendicular, and synthesize the traversal window —
9 samples at ±0.5 m along the crossing direction (≈ ±1.4 s at the robust
0.36 m/s; a per-decision trajectory would sample the same line). At each
sample read the 16-beam ring and ask: is there a short return
(≤ WALL_MAX) in BOTH half-planes flanking the crossing axis (fore/aft
cones ±~22° excluded so the opening never counts as a flank)? A sample
inside geometry (clearance ≤ collision radius) counts as NOT bilateral —
a real crossing could not produce it. **Primary feature =
`traversal_persistence`: the fraction of window samples with both flanks
present.** Geometry only — beam ring + a direction, no WM, no ground
truth in the feature (labels are ground truth, as in v1).

Secondaries (recorded, no bars): window-mean `-max_wall_run`;
window-min `passage_score`.

## Pre-registered bars (P0)

| primary AUC (doorway vs box-pinch, among firings) | consequence |
|---|---|
| **≥ 0.85** | releases the FLIGHT regate (P1: re-fly roomgraph clutter with the window detector in `track_rooms`; gate = accuracy recovery) |
| 0.75 – 0.85 | releases ONE knob: a learned head over windowed ring features (still geometry — no WM) |
| < 0.75 | the honest bound is recorded; the room graph stays clean-room-only and the richer-signal thread closes at its price |

Reference: single-frame `-max_wall_run` AUC 0.631 on the same set.

## Status

- [x] P0 pre-registration committed (this file, before any number)
- [ ] `traversal_persistence` primitive + `--window` discriminator
- [ ] P0 read → verdict

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

## P0 results (2026-07-11 — `eval_doorway_detect --window --clutter 2`)

Same firing set reproduced exactly (935 firings, 69 % box-pinch).

| feature | AUC |
|---|---|
| **traversal_persistence (primary)** | **0.486 — chance, BELOW the single-frame baseline** |
| window-mean −max_wall_run (secondary) | **0.735** (single-frame: 0.631) |
| window-min passage_score (secondary) | 0.566 |

## Verdict — the primary is REFUTED; the windowing direction is not

The bilateral-flank story died on contact with clutter: in a
clutter-2 room, short returns on BOTH sides of the crossing axis are
ubiquitous — box-wall corridors flank both sides for the whole window,
and a true doorway's window exits into the NEXT room's clutter — so
persistence saturates for true and false firings alike. The review
card's mechanism sentence ("a passed box flanks one side") assumed
sparse surroundings; measured, it does not survive the very clutter it
was meant to handle. **Per the frozen bar (< 0.75): the honest bound is
recorded — the room graph stays clean-room-only at P0's price.**

What the sitting DID buy: the windowed version of the RIGHT feature
gains real signal — window-mean `-max_wall_run` 0.631 → **0.735**
(+0.10 from integrating the same discriminator over the traversal).
Trajectory integration adds signal; the primary picked the wrong
feature to integrate. The 0.75–0.85 learned-head branch keyed on the
primary and does not fire; no bar is moved after the fact. **Named for
a future FRESH pre-registration (not run):** a learned head over
windowed ring features — starting evidence 0.735 from the plain
windowed wall-run — or a better-engineered windowed geometric feature.
Until someone pays that registration, `search_roomgraph_v1`'s
clean-room 100 % / clutter 0.139 stands as the honest boundary.

## Status

- [x] P0 pre-registration committed (this file, before any number)
- [x] `_squeeze_axis` + `bilateral_flanks` primitives (ring-only) +
      `--window` discriminator
- [x] P0 read → **primary REFUTED at 0.486 (below single-frame 0.631);
      honest bound stands; windowed wall-run 0.735 recorded as the
      named candidate for a fresh registration**

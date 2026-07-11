# person_pose_v1 — the realism stress test (the C8 trigger)

**Opened:** 2026-07-12 · **Owner:** Hans · **Source:** docs/REVIEW-2026-07.md
(C7); person_v1's own named next ("多姿態/部分遮蔽/瓦礫半掩壓測——崩才需
WM 重訓").

## The question

person_v1's GREEN (find+return 0.933) stands on ONE pose: an upright
capsule. Real SAR subjects sit, crouch, lie, and lie half-buried. Does
the frozen unified latent still separate a person from box clutter
across poses — and where exactly does the level (yaw-only) camera stop
being enough? The failing pose, if any, is the pre-registered
justification for C8's pitch-view step; if lying PASSES from a level
camera, that retrain loses its cheapest argument (the good cheap
outcome).

## Pose proxies (primitives, stated honestly)

Same capsule family as person_v1 (r 0.25; the probe measures POSE
GEOMETRY separability, not human appearance — the sim-to-real
appearance gap stays open regardless):

| pose | primitive |
|---|---|
| standing | upright capsule, len 0.9, centre z ≈ 0.70 (the v1 person) |
| sitting | upright capsule, len 0.45, centre z ≈ 0.48 |
| crouching | upright capsule, len 0.25, centre z ≈ 0.38 |
| lying | capsule rotated horizontal (axis along y), centre z = r ≈ 0.25 |
| buried | lying + a wall-grey slab (0.6×0.6×0.15) over the mid-section |

## Protocol (frozen before any number)

Fresh seed blocks (train 670000+, test 680000+ — disjoint from v1's
650000/660000), 6 rooms per block per pose, the v1 grid/labelling
convention (person-in-+x-FOV vs box hard-negatives), unified WM frozen
latent. Two arms per pose:

- **Frozen-latent linear probe** (fit train block, AUC on test) — the
  mechanism read: is the information in the latent at all?
- **The deployable multi-pose head**: ONE DetectionHead trained on the
  POOLED train blocks of all five poses, scored per pose on the test
  blocks (AUC + obstacle-FA) — the arm the bars sit on.

## Pre-registered bars (deployable-head AUC per pose)

| pose | bar |
|---|---|
| standing | ≥ 0.90 (must not regress from v1) |
| sitting | ≥ 0.80 |
| crouching | ≥ 0.80 |
| **lying** | **≥ 0.75 — the C8 go/no-go** |
| buried | recorded, no bar (the ladder's far rung) |

Guard: pooled obstacle-FA ≤ 0.15 (the v1 head-gate guard).

**Prediction on record:** lying fails from the level camera (< 0.75) —
a horizontal low blob at floor height, seen edge-on from cruise
altitude, collapses toward the box silhouette; and that pre-registered
failure is what arms C8's pitch step. Every cell is a finding either
way.

## Status

- [x] Pre-registration committed (this file, before any number)
- [ ] Pose primitives + collector + probe/head scoring
- [ ] Read → verdict (the C8 trigger state)

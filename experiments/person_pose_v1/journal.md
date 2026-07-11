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

## Results (2026-07-12 — `eval_person_pose --probe`, probe_results.json)

| pose | frozen probe AUC | head AUC (bar) | recall | obs-FA | verdict |
|---|---|---|---|---|---|
| standing | 0.965 | 0.904 (0.90) | 0.59 | 0.069 | PASS |
| sitting | 0.975 | 0.925 (0.80) | 0.74 | 0.000 | PASS |
| crouching | 0.934 | 0.892 (0.80) | 0.56 | 0.000 | PASS |
| **lying** | 0.953 | **0.933 (0.75)** | 0.74 | 0.034 | **PASS** |
| buried | 0.944 | 0.944 (—) | 0.70 | 0.034 | recorded |

Pooled obstacle-FA 0.028 (guard ≤ 0.15) ✓.

## Verdict — the prediction is REFUTED; the pitch step is NOT armed

**Every pose passes, lying by a wide margin (0.933 vs the 0.75
go/no-go), and the half-buried proxy scores highest of all.** The
on-record prediction — that a horizontal low blob seen edge-on from
cruise altitude collapses toward the box silhouette — is wrong, and
being wrong on a pre-registered prediction is the point of writing it
down: **C8's pitch-view WM retrain loses its cheapest argument.** The
frozen unified latent, through one pooled multi-pose head, separates
all five pose proxies from box clutter with the level camera alone.

Honest bounds, unchanged from the pre-registration and sharpened by
the result: these are RED CAPSULE proxies — the probe certifies pose
GEOMETRY separability, not human appearance (the monochrome arm of
int8_parity already measured how much colour carries elsewhere); the
buried proxy's clean grey slab is friendlier than real rubble
occlusion (its top score should not be over-read); per-frame recall
0.56–0.74 still leans on scan compounding, as everywhere in this
track. What would legitimately re-arm the pitch step now: a rubble
SCENE feasibility failure (C8 phase 0 — flight/reachability, not
detection), appearance-realistic subjects, or occlusion fractions well
past a half-slab — each a fresh pre-registration.

**Strategic consequence:** the review's largest deferred step (the
pitch-view retrain) stays parked with its trigger DISARMED by
measurement — convergence bought for the price of ten room-render
sweeps.

## Status

- [x] Pre-registration committed (this file, before any number)
- [x] Pose primitives + collector + probe/head scoring
- [x] Read → **all five poses PASS; lying 0.933 ≫ 0.75; prediction
      refuted; C8 pitch trigger DISARMED**

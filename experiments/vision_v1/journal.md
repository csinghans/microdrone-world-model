# vision v1 — visual-detection branch: feasibility (the WM's native home)

## Context

After coverage_v1's honest negative (the WM does not buy coverage — a
spatial/geometric job), the owner's queued next direction is the
visual-detection branch: find a target by SIGHT (a rendered object), not
the abstract omnidirectional beacon. This is where a camera-encoder world
model might genuinely re-enter — perception, not geometry.

## Feasibility probe — can the WM latent SEE a target? YES

`eval/eval_target_probe.py` (no flight, no WM training): render
`single_room` with a bright-red target (`spawn_target`) at the hidden-
target spot; via the coordinate-offset trick render the +x camera from a
grid of room positions (yaw==0 -> camera looks +x); encode each frame
with the SHIPPED WM encoder; linear-probe the 64-d latent for
"target in the +-28 deg FOV," held-out AUC, vs a raw-pixel redness
baseline. 601 frames over 6 rooms (target-in-FOV rate 0.17):

| signal | AUC |
|---|---|
| **WM latent (linear probe)** | **0.940** |
| raw-pixel "redness ahead" baseline | 0.818 |

**FEASIBLE (>= 0.80), and the WM latent BEATS the color-only pixel
baseline** — the collision-trained encoder already carries strong
target-appearance information, more discriminative than raw redness. So
the visual-detection branch needs only a small DETECTION HEAD on the
existing latent — NO WM retrain, no wider observation channel.

**The contrast that defines the WM's role:** the WM does not buy coverage
(coverage_v1: geometry/grid win) or safety (v3: rangefinders win) — those
are spatial jobs. But it carries detection signal at 0.94 — perception is
its native home. A camera-encoder world model is a SEEING instrument, not
a spatial-reasoning one. This is the through-line, now with a positive.

## Scoped architecture (informed by the probe; a pre-registration to come)

- **Detection head** on the frozen WM latent (target-present; possibly
  bearing). ~0.94 linearly separable -> a tiny head; trained on rendered
  target/no-target frames, held-out gate.
- **Mission = coverage-sweep + visual "found".** Reuse the coverage
  flight (Frontier / grid policy) to sweep the room; run the detection
  head each frame; "found" when it fires (target in view) + a confirm.
  This REPLACES the abstract beacon's magic omnidirectional sensing with
  real vision.
- **No yaw / no retrain.** The +x-locked camera can only detect a target
  it is FACING; the coverage sweep brings the +x cone past the target
  (the honest limit — a target never swept-past is never seen; turning
  to scan is a later, retrain-paying step).
- **Separate acceptance (v0.5 lesson: model metric up != flight good):**
  detection precision/recall as a perception gate, AND find-rate /
  false-alarm / collision as the flight gate.

## Honest caveats to verify in the build
- The 0.94 must be checked against OBSTACLE confusion: does the latent
  distinguish the red target from the orange obstacle boxes (not just
  "a box ahead")? The probe's negatives include obstacle-facing views, so
  0.94 is suggestive, but the detection head must be gated on cluttered
  rooms with obstacles in view (target vs distractor).
- Detection is FORWARD-only (the +x lock); recall is bounded by whether
  the sweep faces the target.

## Verdict
Feasibility GREEN — build the detection head + visual-search mission next
(its own pre-registration: detection precision/recall + flight gate).

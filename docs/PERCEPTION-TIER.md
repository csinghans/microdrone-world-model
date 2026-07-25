# The Perception Tier — design note (2026-07-25)

The last road standing after the representation program (articles #13,
#15): both chapters' wall is dense separation, and capacity,
resolution-of-pooling, data scale, curriculum composition and isolation
are all priced dead (`experiments/{representation_v1..v3,specialist_v1}/`).
The surviving hypothesis: the 64x64 sensor itself is the information
bottleneck — at 3 m distance one pillar subtends a handful of pixels,
and no reallocation of a starved signal can separate close-but-threading
from about-to-hit.

## The knob ladder, by information-added per risk

1. **Input resolution (THIS tier's K0/K1: 64 -> 96 -> 128).** The only
   knob that adds sensor information through the unchanged pipeline —
   conv weights are resolution-agnostic, so the SAME architecture reads
   more pixels. Priced (measured, `77f9aa4`): 96 -> 207.3 KB total /
   8.3 M MACs (~17 ms est), 128 -> ~305 KB / ~15 M (~30 ms) — both
   inside 512 KB / 83 ms. Costs: rollout npz ~2.25x/4x, retrained diet
   at the SAME seeds (course-identical, pixel-denser), deployment later
   needs the camera at the model's res (meta.img_res records it).
2. **Depth-supervised auxiliary (WARNED knob).** pybullet's depth
   channel exists and a train-only head is budget-free — but this is
   grounding's shape, and v0.5 measured that shape: detection up,
   flight down, dense warn ECE 1.75x. Released only if resolution
   moves ranking but calibration lags, never first.
3. **Deeper/wider conv (WARNED knob).** The trilogy showed capacity
   reallocates instead of adding. Released only paired WITH a
   resolution win whose reading says information-limited-became-
   capacity-limited.

## Conservation clauses (from the program's banked laws)

- **Contrast is the curriculum:** every arm trains on the same-seed 1x
  MIXED diet (the measured apex for dense) regenerated at the
  candidate's res. No dense-heavy diets return without their own
  prereg.
- **Instruments predict, never certify** (general_wm_v2's law): an
  offline pass opens a closed-loop phase; nothing is adopted from
  offline rows.
- Sacred checkpoints read-only; sha brackets; candidates park under
  `experiments/perception_v1/artifacts/`.

## Campaign shape

`perception_v1` K0 = wm_96 (this file's companion prereg). K1 = 128
conditional on K0's direction. The GO opens `perception_v2`
(closed-loop: dense probe + assist guardian arms at the candidate's
res — `make_env(img_res=...)` is already deployment-shaped). Bars are
representation_v1's frozen set, re-pinned on same-seed 96-res
instrument configs (semantically identical courses; AUC/saturation
meanings unchanged).

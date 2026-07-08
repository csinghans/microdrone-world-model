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

## Detection-head gate — pre-registration (2026-07-08, before the trained-head numbers)

`search/target_detector.py`: a small MLP (64->32->1) on the FROZEN WM
latent, trained supervised on rendered target/no-target frames (train
rooms seed0 600000), gated on FRESH rooms (seed0 610000). The decisive
number is the caveat — does it fire on the ORANGE OBSTACLE boxes, or only
the RED target?

Frozen bars (fresh rooms):
- detection test AUC >= 0.85 (the linear ceiling was 0.94; allow a
  generalization gap to fresh rooms);
- at threshold 0.5: recall >= 0.80 (catches targets it faces) AND
  precision >= 0.75;
- **obstacle false-alarm <= 0.15** — of frames facing an obstacle box
  with NO target in view, at most 15% may fire. If this fails, the head
  detects "a box ahead," not "the target" — the branch needs a
  target-vs-distractor signal, not just the shipped latent.

PASS = all three. Honest negative if the obstacle false-alarm is high
(the 0.94 linear AUC was riding "box ahead," not target identity).

## Detection-head gate result (fresh rooms 610000, n=590, pos 0.22, 152 hard-neg)

| metric | value | bar | |
|---|---|---|---|
| AUC | **0.925** | >= 0.85 | PASS (matches the 0.94 linear feasibility on FRESH rooms) |
| **obstacle false-alarm** | **0.105** | <= 0.15 | **PASS** |
| precision @0.5 | 0.742 | >= 0.75 | FAIL (borderline, −0.008) |
| recall @0.5 | 0.724 | >= 0.80 | FAIL (borderline, −0.076) |

**Gate FAILS as pre-registered (precision/recall at thr=0.5), but the
decisive scientific question passes: the head is TARGET-SPECIFIC.** Only
10.5% of obstacle-facing (no-target) views fire — the 0.94/0.925 is not
riding "a box ahead," it genuinely distinguishes the red target from the
orange obstacle boxes. The AUC (0.925) confirms a strong separator on
fresh rooms.

**The miss is an operating-point + metric-choice issue, not a capability
one:** thr=0.5 is not the AUC-0.925 detector's sweet spot, and per-frame
precision/recall are STRICTER than a sweep-based mission needs — during a
coverage sweep the target sits in the +x cone for many consecutive
frames, so per-frame recall 0.72 compounds to near-certain mission-level
detection (fire on any one of the in-view frames). Honest: recorded as a
pre-registered FAIL; NOT re-thresholded to manufacture a pass.

**So the deployable question is the FLIGHT gate, not this per-frame one:**
does a coverage-sweep + this head FIND the target (mission find-rate) with
few per-flight false alarms and no extra collisions? That is the next
pre-registration.

## Verdict: detection CAPABILITY confirmed (AUC 0.925, target-specific); per-frame gate misses at thr=0.5 (borderline); flight mission is the real test

The world model's latent supports a usable, target-specific visual
detector with no retrain — the branch's core feasibility. The per-frame
bars at thr=0.5 were stricter than a sweep mission requires; the honest
next step is the visual-search FLIGHT mission (coverage-sweep + detect ->
found), gated on find-rate / per-flight false-alarm / collision.

## Visual-search FLIGHT mission — pre-registration (2026-07-08, before the flight numbers)

`eval/eval_vision_search.py`: a Frontier coverage-sweep of a rendered
room + target; each decision the detection head reads the camera; on the
FIRST firing (prob >= thr) the drone declares "found" and flies home (the
honest deployable behaviour — it stops on the first detection, not
knowing yet if it is right). Replaces the abstract beacon entirely.
Threshold tuned on a VAL block (seed0 600000, a few thr, pick best
correct_find − false_alarm), then gated on FRESH rooms (seed0 620000).

Per-flight outcomes: **correct_find** (first firing WAS a true target-in-
FOV), **false_alarm** (first firing was spurious — target not in view),
**miss** (never fired across the whole sweep), plus collision / return.

Frozen bars (fresh rooms):
- correct_find_rate >= 0.70 (the sweep + detector finds the target);
- false_alarm_rate <= 0.20 (few spurious "founds");
- collision_rate <= 0.05 (beams8 safety holds, unchanged);
- return_rate >= 0.80 (gets home after declaring found).

PASS = all four. Honest negative if the sweep rarely faces the target
(miss high — the +x-lock limit bites) or the detector fires spuriously
mid-sweep (false_alarm high). This is the deployable end-to-end test of
"a drone that finds a target by SIGHT" — the vision branch's capstone.

## Flight gate result (single-frame trigger) — HONEST NEGATIVE, clear mechanism

Frontier sweep + detector "found" on the FIRST firing, threshold tuned on
val then gated on fresh (620000, n=20):

| thr | val correct | val false-alarm | val miss |
|---|---|---|---|
| 0.5 | 0.00 | 0.80 | 0.20 |
| 0.65 | 0.10 | 0.70 | 0.20 |
| 0.8 (tuned) | 0.10 | 0.60 | 0.30 |

`[vision-search] FRESH thr=0.8 | correct_find 0.05 | false_alarm 0.95 |
miss 0.00 | collision 0.00 | return 1.00` — **FAIL.**

**Mechanism (clear):** firing on the FIRST frame with prob >= thr, over a
~hundreds-of-frame sweep, COMPOUNDS the detector's small per-frame
false-alarm (0.105) into a ~95% per-FLIGHT false-alarm: 1 − (1−0.1)^~50 ≈
near-certain. Worse, a spurious firing ENDS the flight (declares found +
returns) BEFORE the sweep faces the target, so correct_find collapses to
0.05 too — not because the detector can't find the target (per-frame
recall 0.72), but because false alarms pre-empt it. Even the tuned higher
threshold (0.8) can't beat the compounding over so many frames.

**The detector is sound per-frame (target-specific, AUC 0.925); the
MISSION TRIGGER is the flaw.** This is exactly the "per-frame gate != mission
gate" caveat, realized: a single-frame first-firing trigger is far too
trigger-happy over a long flight. Fix (same shape as the roomgraph
crossing-debounce): require K CONSECUTIVE firings (the target genuinely
in view persists across frames; isolated spurious frames are suppressed).

## Debounce re-attempt — pre-registration (2026-07-08, before the debounced numbers)

Add a K-consecutive-firing debounce to the "found" trigger (fire only
after `debounce` consecutive frames of prob >= thr). Same frozen bars
(correct_find >= 0.70, false_alarm <= 0.20, collision <= 0.05,
return >= 0.80), same val-tune-then-fresh-gate protocol, sweeping
`debounce` in {2,3,5}. Hypothesis: a persistent target-in-view fires the
debounced trigger while isolated spurious frames do not, cutting
per-flight false-alarm and letting correct finds happen.

## Debounced flight gate result — FAIL, but the mechanism is now fully mapped

Debounce swept on val (thr 0.65), tuned, gated on fresh (620000, n=20):

| debounce | val correct | val false-alarm | val miss |
|---|---|---|---|
| 2 | 0.10 | 0.50 | 0.40 |
| 3 | 0.30 | 0.30 | 0.40 |
| 5 (tuned) | 0.60 | 0.00 | 0.40 |

`[vision-search] FRESH thr=0.65 debounce=5 | correct_find 0.25 |
false_alarm 0.35 | miss 0.40 | collision 0.00 | return 0.95` — **FAIL.**

- **The debounce fix WORKED directionally:** per-flight false-alarm fell
  from 0.95 (first-firing) to 0.35 (debounce 5) — requiring consecutive
  firings suppresses the isolated spurious frames, exactly as predicted.
- **But it traded false-alarm for MISS (0.40):** needing 5 consecutive
  in-view frames is too strict — the +x cone SWEEPS PAST the target
  (a brief glimpse), rarely giving 5 straight strong-detection frames.
  The mission is caught between false-alarm (low debounce) and miss (high
  debounce); no debounce value clears the bars.
- **And it generalizes poorly** (val db=5 correct 0.60 / FA 0.00 -> fresh
  0.25 / 0.35) — the fresh rooms are harder; the tuned point overfit.

## Verdict: vision branch — detector SOUND, but the FLIGHT is bound by the +x camera-lock

The chain: WM latent sees the target (0.94) -> a target-specific head
(0.925, obstacle-FA 0.105) -> but the FLIGHT search fails, caught between
false-alarm and miss. **The binding constraint is the yaw=0 +x camera-
lock** (kept all along to protect the WM's body==world coordinate frame):
the drone can only glimpse the target as its forward cone sweeps past —
it cannot TURN to steadily face and confirm it. So a per-frame-imperfect
detector, integrated over brief glimpses, cannot deliver a reliable
find without either false-alarming or missing.

**This is the session's through-line, sharpened one last time:** the +x
camera-lock blinded the WM to 60% of collisions (search_hybrid_v1), and
now it caps visual search. The abstract beacon (omnidirectional sensing)
sidestepped it; REAL vision hits it head-on.

## Named next (the real fix — the big deferred step)
Reliable visual search needs the drone to TURN to scan / face / confirm
the target — i.e., add yaw to the action set and RETRAIN the world model
on the turning vocabulary (body != world once yawing). This is exactly
the yaw/retrain step the original plan deferred to "the visual-detection
stage, when it's really needed, and when the retrain is paid." It is now
demonstrably needed. That is a major perception+retrain undertaking — its
own pre-registration, the owner's call to open. The detector, memory
grid, and mission scaffolding built here are the reusable substrate.

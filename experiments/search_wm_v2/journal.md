# search-wm v2 — FOV-honest labels: can the WM own FORWARD danger? (Phase 1b, step 3)

## Pre-registration (2026-07-08, before any number exists)

search_wm_v1 closed as an honest negative: the retrained WM predicted
room latents well (MSE@32 0.94) but its collision head sat at chance,
because the danger label was OMNIDIRECTIONAL `clearance()` — mostly
out of the forward 28-degree camera's view, hence not a function of
the observation. The named fix: **FOV-honest labels** — label danger
only for surfaces the forward camera can actually see (the
`metric_labels` visible=0 discipline), so the target IS in the frame.

**Machinery (shipped):** `SearchScenario.forward_clearance()` — nearest
wall/obstacle surface in the +x FOV cone (ray-cast, yaw==0 so
body==world); `search_rollouts --fov-honest` labels `dists` with it;
`eval_search_wm_probe --fov-label` scores against it.

**Protocol:** regenerate the search dataset FOV-honest, retrain the WM
80 epochs, re-probe with `--fov-label`.

**Frozen read:** forward AUC >= 0.75 (vs the FOV-honest label) -> the
WM CAN own forward danger; build the HYBRID safety filter (WM warn for
forward motion + the 4 rangefinders for side/behind) and gate it
against the geometric frontier. forward AUC < 0.65 -> even the
in-view danger is not learnable from this encoder at this scale
(deeper negative: the wall appearance itself, not just the label);
record and stop. Between -> marginal, recorded.

Honest note: FOV-honest labeling means the WM can only ever own
FORWARD danger; lateral/behind danger is out of view by construction
and stays the rangefinders' job. So even a pass does not give the WM
the whole safety signal — it gives it the FORWARD share, which is the
most it can honestly have on a fixed forward camera.

Cost: one FOV-honest dataset + one 80-epoch retrain + one probe.

## Verdict: FOV-honest labels do NOT rescue it — and the two negatives converge on a perceptual limit (2026-07-08)

FOV-honest dataset (near-forward-wall frac 0.16), 80-epoch retrain,
re-probe vs the forward-cone label:

| probe | pooled | forward | reverse/strafe |
|---|---|---|---|
| transit WM, omni label (v1) | 0.762 | 0.480 | 0.793 |
| room retrain, omni label (v1) | 0.384 | 0.567 | 0.377 |
| **room retrain, FOV-honest label (v2)** | 0.298 | **0.580** | 0.257 |

Forward AUC moved 0.480 -> 0.567 -> 0.580 across the three — **stuck
near chance regardless of label or retraining.** Putting the danger
in-view (FOV-honest) did not make it learnable. Below the 0.65
marginal bar; the frozen "deeper negative" branch fires.

**The two negatives converge on a PERCEPTUAL limit, not a label or
training one.** v1 already measured the tell: box obstacles (met via
strafe) scored 0.79 while walls (met head-on) scored 0.48. The WM's
collision signal rides the **apparent-SIZE cue of discrete obstacles**
— a pillar or box looms larger as you close, which a single frame
encodes. **A flat wall has no such cue**: a uniform surface filling a
64x64 monocular frame is nearly scale-free (0.5 m and 1.5 m away look
the same without texture gradient, stereo, or motion parallax), so
wall distance is ill-posed at this resolution. FOV-honest labeling
moved the target into view, but **the distance information is still
not in the pixels** — so the collision head stays at chance and
(trained on a sparse, hard target) even inverts.

Honest caveat kept on the record: the FOV-honest positives are sparse
(forward-wall frac 0.16) and the training AUC dipped below chance, so
"under-trained on a sparse target" is a partial confound — but it
cannot explain why forward AUC is ALSO chance for the transit WM (no
retrain, v1) and the omni-label retrain (v1). Three routes, one
answer: monocular flat-wall distance does not transfer here.

## Phase 1b — final synthesis (v1 + v2)

**Does the world model help indoor search? No — on this body, for
safety, and now understood WHY.** A vision safety filter would need
either (i) omnidirectional coverage the forward camera does not have
(side/behind walls out of FOV), or (ii) monocular distance to flat
walls, which is ill-posed at 64x64 without a size cue. The WM is
excellent at what it was built for — anticipating DISCRETE obstacles
by apparent size — and that is exactly the wrong shape for rooms
bounded by flat walls.

**What stands:** Phase 1a's privileged geometric filter is the working
sim safety layer, and on real hardware the SGBA-style 4 rangefinders
(cheap, omnidirectional, distance-direct) are the right instrument for
search safety — not a monocular world model. The WM's place in this
track, if any, is the BEACON/target-reasoning layer, not collision.

**Named (not scheduled):** a rangefinder-only safety filter (drop the
WM from the safety loop entirely, keep it for target reasoning); or,
far bigger, depth/parallax input (the sim renders depth the stack
discards) — a new perception channel, its own multi-version arc.

## ⚠ SETUP CORRECTION (2026-07-08): the WM investigation ran on EMPTY frames

Preparing the depth-channel follow-up, a depth grab flying INTO a wall
read constant far (~1.0) — the camera saw no wall. Root cause, verified:
**`SearchScenario` and `sim/indoor/rooms.py` spawn NO pybullet bodies**
(grep: zero createMultiBody/createVisualShape). The room's walls and
box obstacles exist ONLY as `clearance()` math for scoring and the
rangefinders — they are never RENDERED. So every camera frame in a
search room is near-blank (RGB mean 225.8, std 38.6, ~11 unique
values = floor gradient, no obstacle).

**What this invalidates:** the search_wm_v1/v2 MECHANISM claim —
"the WM is blind to walls because monocular flat-wall distance is
ill-posed / scale-free." That was over-attributed. The WM scored
forward danger at chance because **there was no wall in the image at
all**, not because a rendered wall is ambiguous. v1's "boxes 0.79 via
strafe" was likewise an action-conditioning artifact on blank frames,
not the WM seeing boxes. Those mechanism conclusions are RETRACTED
pending a rendered re-run. (Per house rule: numbers stay as recorded;
this note supersedes their interpretation.)

**What still stands, unaffected:** Phase 1a (GREEN) and search_room_v3
(rangefinder deployability, GREEN) — both use `clearance()`/rangefinder
MATH, never the rendered frame, so an unrendered room never touched
them. The capability result and the "rangefinders own safety"
deployability result are intact.

**The corrected experiment (search_wm_v3, next):** render the walls +
box obstacles as visual bodies, regenerate, and re-run the transfer
probe + retrain to get the HONEST answer to "can the WM see room
geometry when it is actually drawn?" Only then is the depth-channel
question (does depth beat RGB for wall distance) even well-posed.

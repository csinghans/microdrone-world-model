# search-wm v3 — the corrected answer: the WM DOES transfer (rendered rooms)

## The correction (2026-07-08)

search_wm_v1/v2 concluded the world model could not supply search
safety, and attributed it to a monocular perceptual limit ("flat walls
are scale-free at 64x64"). **That was wrong — a setup artifact.**
`SearchScenario` rendered NO pybullet bodies, so every camera frame was
a near-blank floor (RGB std 38.6). The WM scored forward danger at
chance because there was nothing in the image, not because walls are
ambiguous. Fix: `SearchScenario.spawn_bodies` now draws the walls
(slabs) and box obstacles; the camera sees the room (RGB std ~80).

## Re-probe: the transit WM transfers OUT OF THE BOX (no retrain)

Shipped champion WM (pillar-trained, never saw a room), re-probed on
RENDERED rooms vs the FOV-honest forward-cone label:

| probe | pooled AUC | forward | reverse/strafe |
|---|---|---|---|
| empty frames (v1/v2, RETRACTED) | 0.30-0.76 | 0.48-0.58 | 0.26-0.79 |
| **rendered rooms, transit WM, n=6** | 0.908 | 0.897 | 0.931 |
| **rendered rooms, transit WM, n=12** | 0.829 | **0.814** | 0.842 |

**Forward AUC 0.814 >= 0.75 — the frozen gate is CLEARED, with zero
retraining.** The pillar-trained collision head reads box-walls fine;
"apparent size of a discrete obstacle" generalizes from cylinders to
wall slabs and boxes. The whole v1/v2 negative — and its "monocular
flat-wall is ill-posed" mechanism story — dissolves: it was an
unrendered world, full stop.

## Corrected Phase 1b synthesis

**Does the world model help indoor search? For FORWARD collision,
yes — it works from vision alone at AUC 0.81, no retraining.** The
earlier "no" was a rendering bug. The honest, full picture now:
- The WM owns FORWARD danger from the camera (0.81) — genuine
  vision-based anticipation, and it would catch off-axis obstacles a
  4-beam rangefinder ring misses between beams.
- Side/behind danger is still out of the forward FOV — the
  rangefinders' omnidirectional job (unchanged).
- search_room_v3 already showed rangefinders ALONE pass the gate
  (collision 0.033), so a WM is not REQUIRED for deployability — but
  it is a real, working complement, not the dead end v1/v2 claimed.

Lesson (into CLAUDE.md): a vision experiment must FIRST assert the
frame is non-blank (render present). Two version-verdicts were built
on empty images before a depth-sanity-check caught it — the same
class as the split-identity leak: verify the instrument sees what you
think it sees before interpreting what it says.

## Named next (each its own pre-registration)
- WM-forward + rangefinder-side HYBRID safety filter, gated vs the
  rangefinder-only v3 baseline (does vision-forward cut the 0.033
  off-axis collisions?).
- The depth channel is now OPTIONAL, not required — RGB already
  clears the gate; depth would be an ablation, not a rescue.

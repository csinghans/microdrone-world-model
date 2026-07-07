# search-hybrid v1 — is a WM-forward + rangefinder-side safety layer worth building?

## The question (decision rule fixed BEFORE the numbers)

search_wm_v3 proved the transit world model reads rendered box-walls
head-on (forward AUC 0.814, zero retrain), and named a hybrid safety
layer — WM-forward warn for the +x cone, rangefinders for the sides —
as the next step. Before building it, one measurement decides whether
the WM can help the v3 rangefinder-only baseline AT ALL.

The v3 filter vetoes a cardinal nav action whose OWN rangefinder beam
(a single ray) reads < 0.55 m. Its residual crashes are "off-axis
corners the 4 beams miss." The camera is locked to +x (yaw=0 — the
constraint we KEPT so the world model's body==world assumption holds),
so the WM-forward warn scores only the +-28 deg cone around +x. Fixed
rule, stated before the run:

  * A FORWARD collision with a low forward-cone clearance is one the
    WM-forward warn WOULD have fired on (the cone is wider than the
    single beam) -> the hybrid helps, build it.
  * A STRAFE / REVERSE collision, or a FORWARD collision where the
    corner sits OUTSIDE the +-28 deg cone, is invisible to a +x-locked
    camera -> the hybrid cannot help; the fix is more beams, not vision.

Tool: `eval/diagnose_v3_collisions.py` — reruns the exact v3 config
(frontier, rangefinder safety, speed 0.6, 2 obstacles) over a wider
seed range, logs the FIRST contact per crashed episode (the failure
event; a collision does not end the episode, so grind-against-the-wall
repeats are counted only as `total_contacts`, never classified).

## Result (200 episodes, seed0 140000, reproducible)

`[diagnose-v3] 200 episodes, 10 crashed (rate 0.050); 10 failure events
(first contact per episode), 490 total contact-decisions`

| the 10 failure events | count | can the WM-forward see it? |
|---|---|---|
| FORWARD, forward-cone clearance < 0.7 m | **4** | **YES — warn would fire** (cone wider than the single beam) |
| FORWARD, corner OUTSIDE the +-28 deg cone (fwd_clear 1.0-1.8) | 3 | no — beyond the camera FOV |
| STRAFE / REVERSE (camera orthogonal to motion) | 3 | no — camera looks +x, drone moves sideways/back |

**A WM-forward + rangefinder hybrid could prevent 4 of 10 = 40% of the
residual collisions. The other 60% are geometry a +x-locked camera
fundamentally cannot see.** (The per-*clip* 27% from the first run was a
grind artifact — 490 contact-decisions across 10 stuck episodes — not
490 failures; first-contact-per-episode is the honest unit.)

## Verdict: DON'T build the hybrid as a safety layer — add beams, not a world model

The four the WM would catch are forward corners near the +x axis but
off the single beam ray — real, but a minority. The dominant residual
(6/10) is exactly what the yaw=0 camera-lock blinds the WM to:
sideways/reverse motion, and forward corners past +-28 deg. The cheap
fix covers ALL ten: **more rangefinder beams** (8 instead of 4, or
angled) sense off-axis corners AND the sides, omnidirectionally, for a
few dollars — no vision stack, no 137 KB / 8 ms-per-decision WM in the
safety loop. This QUANTIFIES v3's conclusion ("the right sensor is
cheap and omnidirectional"): the WM-forward can't close the gap because
the very constraint that keeps it valid (camera locked +x) is what
hides most of the failures.

Channel-limit theme, again and sharper: you cannot supply
omnidirectional collision safety through a channel (a +x-locked
monocular camera) built for forward transit — no matter how well the
world model reads what little that channel shows it (0.81 forward AUC
is real, and irrelevant to 60% of the crashes).

## Honest footnotes
- The diagnostic's 10/200 = 0.050 sits at the gate edge; v3's
  pre-registered verdict was pooled 2/60 = 0.033. This is a fresh,
  wider, same-difficulty sample — the ~0.03-0.05 spread is small-sample
  noise (a few episodes), and re-gating was NOT this run's job (mode
  characterization was). The v3 gate stands as pre-registered.
- What WOULD justify the WM in this track is target/coverage REASONING
  (its proven strength), not collision — unchanged from v3.

## Named next (each its own pre-registration)
- **8-beam (or angled) rangefinder ablation**: does doubling the beams
  cut the 0.05 residual toward zero? The measurement this diagnostic
  points at — cheap, deployable, no WM.
- WM for coverage/target reasoning (the honest role for the world
  model here), not safety.

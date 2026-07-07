# search-wm v1 — does the world model help indoor search? (Phase 1b)

## Pre-registration (2026-07-07, before any number exists)

Phase 1a is GREEN with a PRIVILEGED geometric safety filter (reads
true clearance): frontier find 0.933 / collision 0.000. That filter
is not deployable — a real drone has no ground-truth distance, only
its camera. Phase 1b asks the wedge question: **can the 512 KB world
model supply the safety signal from vision alone, matching the
geometric ceiling at deployable cost?**

The world model can only MATCH on safety (the geometric filter is
already at 0 collisions); its value is DEPLOYABILITY — a vision-only
safety layer. So the bar is parity, not improvement.

**Two honest obstacles, named up front:**
1. The shipped WM was trained on the TRANSIT action set (forward /
   slow / veer / hover, all vx>=0) in pillar/dense corridors. The nav
   set adds reverse and pure strafe — action vectors the predictor
   never saw (OOD).
2. The search rooms have WALLS + box obstacles; the encoder saw only
   thin cylinders. Walls are visually OOD.

**Step 1 — transfer probe (cheap, feasibility-first, THIS is gated
first):** fly the green geometric frontier and, alongside, tap the
existing WM's predicted collision probability for the executed nav
action at each decision. Score whether that probability RISES before
true low-clearance events (AUC of WM warn-prob vs "true clearance
drops below SAFE_MARGIN within the next few decisions"), split by
action (shared forward vs OOD reverse/strafe). Frozen read:
- AUC >= 0.75 on forward AND >= 0.65 pooled over nav actions -> the
  transit WM transfers usefully; a vision safety filter is worth
  building on it directly.
- AUC < 0.6 pooled -> the transit WM does NOT transfer (OOD actions +
  walls); a retrain on search+nav rollouts is REQUIRED before any
  vision safety filter — recorded as the finding, retrain pre-
  registered as step 2.

**Step 2 — retrain + vision safety filter (only as the probe directs;
its own protocol):** generate search-room rollouts under a random nav
policy (frames + collision labels at horizons), retrain the collision
heads (and encoder if walls demand it) on the translational nav set,
then replace `scenario.clearance()` in the safety filter with the WM's
predicted warn probability. **Gate (fresh seeds, vs the geometric
frontier reference):** WM-frontier collision <= 0.05, find >= 0.85,
return|found >= 0.90. Honest negative if vision safety cannot match
geometry — record WHERE it fails (walls? strafe? corners?).

Cost: step 1 probe ~a few episodes with a WM tap (~15 min). Step 2
(if triggered) is a dataset + retrain effort — a v0.8-scale piece,
carried across loop iterations.

## Step-1 verdict: the transit WM PARTIALLY transfers — blind to WALLS, fine on box obstacles (2026-07-07)

Transfer probe, n=12 (15,388 search-leg decisions, near-0.7 m rate 0.21),
seeds 130000; WM warn-prob (any-horizon, 0.7 m ring) vs true "within
0.7 m of a surface in the next 4 decisions":

| slice | AUC | read |
|---|---|---|
| pooled | **0.762** | >= 0.65 ✓ |
| forward | **0.480** | < 0.75 ✗ — near chance |
| reverse/strafe | **0.793** | good |

**The frozen rule's clean-transfer branch does NOT fire** (forward
0.48 << 0.75), and the shape is the finding — it inverts the
pre-registered worry:

- **The OOD-actions concern was WRONG.** Reverse and strafe — the
  action vectors the predictor never trained on — predict proximity
  WELL (0.79). The WM's collision head is robust to unusual action
  directions.
- **The walls concern was RIGHT, and it is the whole story.** Forward
  danger in a room is almost always a WALL ahead; the WM scores it at
  chance (0.48) because a flat wall filling the view looks nothing
  like the thin cylinders it trained on — **it is blind to walls
  head-on.** Reverse/strafe danger is mostly the BOX obstacles, which
  are pillar-like, so the WM warns correctly there.

**Consequence for Step 2 (now sharply scoped):** the retrain is a
VISUAL-transfer problem (teach the encoder walls), not an
action-transfer problem. A deployable vision safety filter on the
current WM would sail straight into walls. Step 2 pre-registration:
generate search-room rollouts (walls + boxes) under a random nav
policy, retrain the encoder+collision heads on them, and re-probe —
forward AUC >= 0.75 is the gate to earn a WM safety filter, then the
gate comparison vs the geometric frontier. This is a dataset + retrain
effort (v0.8-scale), carried across loop iterations.

Cost of step 1: 12 episodes with a WM tap, ~15 min, zero training —
and it redirected the whole of Phase 1b from "action OOD" to "walls".

## Step-2 verdict: the retrain confirms an OBSERVATION-CHANNEL bottleneck, not a model gap — honest negative (2026-07-07)

Retrained the WM 80 epochs on the wall-teaching search dataset (96
rooms x 150 steps, near-wall frac 0.40), then re-probed:

| probe | pooled AUC | forward | reverse/strafe |
|---|---|---|---|
| transit WM (step 1) | 0.762 | 0.480 | 0.793 |
| **retrained WM (step 2)** | **0.384** | 0.567 | 0.377 |

The retrain did NOT earn the vision safety filter — forward nudged
0.48 -> 0.567 (still far below the 0.75 gate) and the pooled signal
COLLAPSED to 0.384 (below chance). But the training metrics say the
model is not broken: **latent MSE@32 = 0.939 vs no-op 9.137** — it
predicts the room's future latents ~10x better than no-op. It learned
the dynamics; it could not learn the danger label (collision AUC@32
0.59, now-AUC 0.47 ~ chance).

**The MSE-good / AUC-chance split is the finding.** The danger label
is `clearance()` — the nearest surface in ANY direction — but the
camera sees only a forward 28-degree cone. In a room the nearest
surface is usually to the SIDE or BEHIND (a wall the drone is flying
parallel to), which the forward camera cannot see. So "am I within
0.7 m of something?" is **not a function of the observation** — and no
amount of training makes a head predict a label its input doesn't
contain. This is the repo's signature channel-bottleneck result
(cf. the dispatch arc, "you cannot identify a world through a channel
built to report only imminent danger"), now for search safety:
**a forward-only camera cannot supply the OMNIDIRECTIONAL safety
signal that 2D roaming needs.** The privileged geometric filter is
deployable-in-sim precisely because it is omnidirectional; vision on
this body is not its equal for lateral/behind danger.

**Why the pooled AUC went BELOW 0.5:** trained toward an unlearnable
(out-of-FOV) target, the warn head fit noise and anti-correlated with
the (mostly-lateral) true proximity — worse than the transit WM,
which at least got box obstacles right when they happened to be ahead.

**Named successors (each its own pre-registration; NOT run here):**
1. **FOV-honest labels + split safety** — label danger only for
   surfaces inside the forward cone (the `metric_labels` visible=0
   discipline), let the WM own FORWARD danger, and keep side/behind on
   the 4 rangefinders (which are already omnidirectional and cheap).
   A hybrid safety filter, honest about what each sensor can know.
2. **Look around (yaw)** — the deferred big step: a yaw command lets
   the camera sweep, making the omnidirectional signal observable —
   but it breaks the WM's body==world frame and forces the full
   retrain the nav-action-set analysis flagged.

**Phase 1b closes as an honest negative with a sharp mechanism map:**
the world model is not the missing piece for search safety on this
body — the forward camera's FOV is. Phase 1a's privileged geometric
filter stands as the working (sim) safety layer; a deployable vision
replacement needs FOV-honest labels or a wider view, not just wall
data. Cost: one dataset + one 80-epoch retrain + two probes.

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

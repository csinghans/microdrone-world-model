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

# slalom_feasibility — pricing the arena before the bars

## Pre-registration (2026-07-05, frozen before any episode flies)

**Why.** corridor-slalom v1 failed every target and its post-mortem
could not separate "policies can't chain" from "the arena can't be
chained at that spacing". This study prices the arena first — the
lesson v1 exported, applied.

**Design.** `eval/eval_arena_ceiling.py`: a scripted oracle pilot
(privileged gate ladder, bang-bang veer, deadband 0.06 m — the SAME
action set the learned policies use, so its ceiling is the right
reference) flies slalom3 arenas over a grid: dx ∈ {0.70, 0.85, 1.00,
1.15} (x0 auto-fit) × speed factors {1.0, 1.25, 1.5}, n=30 seeds per
config (seed0 30000), v1's gap-width/offset sampling untouched (the
no-straight-line theorem must keep holding).

**Frozen selection rules.**

1. **The v1 diagnosis check:** if the oracle's ceiling at (dx=0.70,
   speed=1.0) is itself far below the v1 bars (< 0.55), v1's verdict is
   re-attributed: the arena, not the policies, was the wall.
2. **v2 geometry:** the SMALLEST dx whose ceiling ≥ 0.90 at speed 1.0
   becomes v2's frozen spacing; ceilings at 1.25/1.5 are recorded and
   v2's speed-cell bars are set strictly under them
   (bar = ceiling − 0.25, rounded down to 0.05, floor 0.30).
3. **No-go:** if no dx in the grid reaches 0.90 at speed 1.0, the
   chaining question is CLOSED as "arena family infeasible for this
   action set at N=3" — recorded, no campaign, no bar shopping.

## The ceiling table

(appended when the grid lands)

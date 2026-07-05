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

| dx | x0 | @1.0 | @1.25 | @1.5 |
|---|---|---|---|---|
| 0.70 | 0.90 | **0.97** | 0.07 | 0.00 |
| 0.85 | 0.80 | 1.00 | 0.00 | 0.30 |
| 1.00 | 0.50 | 1.00 | 1.00 | 0.37 |
| 1.15 | 0.20 | 1.00 | 0.87 | 0.00 |

(`ceiling.json`, n=30/config, seed0 30000)

## Verdict, per the frozen rules (2026-07-05)

**Rule 1 — the v1 diagnosis, split cleanly in two.** The oracle flies
v1's spacing at cruise at **97 %** — far above the 0.55 re-attribution
threshold. v1's cruise-cell failures are therefore **a genuine
capability gap** (oracle 97 % vs the best learned 10 %), not an arena
artifact. v1's speed cell is the opposite: the oracle ceilings at
dx=0.70 are 7 %/0 % at 1.25/1.5 — the 40 % bar at speed was priced on
an arena the action set cannot fly. Both halves of the v1 post-mortem
were right about different cells; the probe finally says which.

**Rule 2 — v2 geometry.** Smallest dx with ceiling ≥ 0.90 at cruise:
**dx = 0.70** (97 %). Bar formula edge case, honestly noted: for the
speed cells the formula (ceiling − 0.25, floor 0.30) contradicts its
own "strictly under the ceiling" clause when the ceiling < 0.55 — the
strict clause dominates, so **cells with ceiling < 0.55 carry no bar**
(they fly as measured-only diagnostics). v2's single priced target:
slalom3@1.0 ≥ **0.70** (ceiling 0.97 − 0.25, rounded).

**Rule 3 — no-go: not triggered.**

**Curiosity on the record:** the speed columns are non-monotone in dx
(0.85 flies 0 % at 1.25 but 30 % at 1.5; 1.15 the reverse) — the
bang-bang weave period phase-locks with gate spacing per (dx, speed).
Real dynamics, n=30 noise on top; the oracle is itself a lower bound
(no anticipatory lead). Sweet spot for a future speed-chaining
question: dx = 1.00 (100 % at both 1.0 and 1.25).

**The sharpened v2 question:** at a spacing PROVEN flyable at 97 %, can
training close a 97-vs-10 gap? That is now purely a question about
learning, with zero arena alibi.

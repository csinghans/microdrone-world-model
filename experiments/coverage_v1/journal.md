# coverage v1 — world-model-driven complete indoor coverage (RL on WM latent)

## The question

Owner directive (2026-07-08): "coverage matters, not room count; FIRST
use the world model to completely cover the indoor space by flying, THEN
visual detection." Architecture chosen: **RL on the WM latent**. This is
the first time the world model DRIVES a task. Honest framing (search_wm_v3
verdict): the WM's role here is coverage/where-to-go reasoning, NOT
collision — so safety stays on the deployable beams8 rangefinder veto, the
WM supplies per-nav-action openness, and an egocentric covered/occupancy
grid carries the spatial memory the WM latent lacks.

The bet (from this session's clutter finding): the geometric Frontier's
coverage CRATERS under clutter (its safe-cell BFS graph fragments); a
learned reactive policy flying from WM perception + a coverage grid may
cover more — the win condition. If it merely ties a grid-only policy
(WM zeroed), that is the honest negative "the WM does not buy coverage."

## Phase 0 — Frontier ceiling (measured BEFORE freezing bars, no training)

`eval/eval_coverage.py`, `run_coverage_episode` (roam until covered
fraction plateaus — no new cell for 100 decisions — or hits threshold,
THEN BFS home), beams8 safety, speed 0.6, n=12, seed0 300000.

| condition | coverage_mean | complete | return\|done | collision | steps_to_cover(med) |
|---|---|---|---|---|---|
| clean `single_room` | **0.808** | 1.00 | 0.833 | 0.083 | 369 |
| clutter `n_room(3, clutter=2)` | **0.407** | 1.00 | 1.000 | 0.000 | 229 |

**Findings:**
- **The deployable-reachable ceiling is ~0.81, not 1.0.** Clean coverage
  is budget-INDEPENDENT (identical per-seed at 700 and 1500 decisions:
  0.85/0.84/0.76/0.91/0.76/0.74) — Frontier plateaus at its reachable set;
  the last ~20% (wall-hugging / behind-obstacle cells) is unreached
  because the beams8 safety margin keeps the drone off them. So "complete
  coverage" under deployable safety MEANS ~0.81 here; the mission returns
  on the coverage PLATEAU, not a fixed high threshold.
- **Clutter craters coverage to 0.407** (per-seed 0.20-0.77, many at
  0.20-0.27) — the safe-cell graph fragments and Frontier is trapped in
  its start fragment. This is the win opportunity (gap 0.808 - 0.407 =
  0.40). Collision stays 0.000 (it doesn't crash, it just can't reach).
- **G0 = GO**: clean is coverable to a real ceiling AND clutter craters,
  so a coverage win exists to compete for.

## Pre-registration — FROZEN bars (before any training)

Three arms under `run_coverage_episode` (same seeds, beams8, speed 0.6):
Frontier (privileged-planning ceiling) vs WM-coverage (CoveragePolicy) vs
Grid-only ablation (`wm_off=True`, trained). Metric of record:
`coverage_mean`.

- **Bar A — match clean:** WM-coverage clean coverage_mean **>= 0.758**
  (Frontier 0.808 − 0.05); collision_rate **<= 0.113** (0.083 + 0.03);
  return_rate **>= 0.80** (Frontier itself 0.833; the BFS homing is shared
  across arms, so this is a mission-viability check, not a policy metric).
- **Bar B — beat clutter (the win):** WM-coverage clutter coverage_mean
  **>= 0.557** (Frontier 0.407 + 0.15).
- **Bar C — WM necessity:** WM-coverage clutter coverage_mean
  **>= Grid-only clutter coverage_mean + 0.05**.

**PASS = A ∧ B ∧ C** (any read within ±0.08 of a bar → fresh n=60 block,
pooled). **Honest negatives (recorded, not retried):**
- Clean < Bar A → coverage-RL-on-WM not viable as-is → DAgger fallback
  (clone Frontier as a scripted teacher, then RL fine-tune).
- Bar B holds but Bar C fails (WM ≈ Grid-only) → the win is the GRID, not
  the WM → "use the WM" unsupported by evidence; the deployable tool is
  the grid policy. (Plausible: the beam-occupancy channel partly
  duplicates the WM collision probs.)
- Clutter doesn't crater for the learned arms either (cells genuinely
  unreachable under beams8, not a planning failure) → coverage is
  reachability-bound, no policy wins → honest negative.

Note the asymmetry, stated plainly: Frontier is a PRIVILEGED-planning
ceiling (reads true free cells); the fair deployable baseline is
Grid-only. A WM-coverage policy matching the privileged Frontier from
vision + beams + odometry is itself a strong result.

## Phase 1 — G1 learning-signal smoke: GO

Grid-only ablation (`wm_off`, no camera — fastest check that PPO + the
coverage-delta reward + the egocentric grid learns to cover), 40k
timesteps on clean `single_room`, evaluated vs RandomWalk on fresh seeds
(400000, disjoint from train 500000 / ceiling 300000):

| arm | clean coverage_mean |
|---|---|
| RandomWalk (null) | 0.424 |
| grid-only, 40k | **0.553** |
| Frontier ceiling (ref) | 0.808 |

**G1 = GO:** coverage climbs +0.13 above random after only 40k steps —
the reward/obs/RL machinery learns to cover. (Between random and the
Frontier ceiling, as expected for a short smoke; full train is 250k.)

## Phase 2 — full trains launched (250k, clutter_mix 0.5)

Both arms training on the single+clutter mix at speed 0.6: the WM-arm
(real champion WM, rendered rooms, 293-d obs) and the grid-only ablation
(`wm_off`). On completion: the A/B/C gate (Frontier vs WM vs grid-only,
clean + clutter, frozen bars above, pooled recheck at borderline).

## Verdict: HONEST NEGATIVE — the world model does not buy coverage (hurts under clutter)

A/B/C gate (n=30, gate seeds 310000, disjoint from ceiling/train,
`run_coverage_episode`, beams8, speed 0.6, plateau-terminated):

| arm | clean coverage | clutter coverage | clean return | clean collision |
|---|---|---|---|---|
| Frontier (privileged ceiling) | 0.774 | 0.395 | 0.967 | 0.000 |
| **WM-coverage** (250k) | **0.689** | **0.324** | 0.967 | 0.000 |
| grid-only ablation (250k) | 0.582 | 0.379 | 0.833 | 0.000 |

Frozen bars, all three FAIL:
- **A (match clean): FAIL** — WM clean 0.689 < 0.758 (borderline, gap
  0.069). Collision (0.000) and return (0.967) pass. So the WM policy
  covers clean rooms well but does not reach the privileged Frontier.
- **B (beat clutter): FAIL** — WM clutter 0.324 < 0.557; in fact NO
  learned arm beats Frontier's clutter 0.395. **The pre-registered win
  hypothesis is disconfirmed: cluttered-room coverage is reachability-
  bound under safe flight, not a Frontier planning gap a reactive policy
  fixes.** (Both learned arms land near/below Frontier — the cells
  Frontier misses are genuinely hard to reach under beams8, for any
  policy.)
- **C (WM necessity): FAIL, wrong direction** — WM clutter 0.324 is
  BELOW grid-only 0.379. **Adding the world model HURTS clutter coverage**
  — the 40 WM collision probs are OOD for reverse/strafe and scale-free
  for walls, so they inject net-negative noise the grid-only policy is
  better off without.

**The nuance, stated fairly:** the WM DOES help CLEAN coverage (0.582 ->
0.689 over grid-only, +0.107) — its forward-openness read aids the open-
room sweep. But that help (a) does not reach Frontier (0.774), and (b)
reverses to a HURT under clutter, where the win was supposed to be. So
across the mission the world model is not the coverage lever; the
geometric Frontier is the best coverer and a cheap grid-only policy is
the best deployable-learned one.

**This is consistent with the whole indoor-search arc:** the WM lost to
cheap rangefinders for SAFETY (v3), and now loses to cheap geometry/grid
for COVERAGE. The monocular threat-channel world model is not the right
instrument for indoor spatial tasks — the repo's honest through-line.

## Consequences (no retries without a new pre-registration)
- **Phase 2.5 (WM nav-retrain) is NOT released.** Its trigger was "the
  ablation shows the WM helps AND forward-only limits." The ablation
  shows the WM HURTS under clutter — retraining would sharpen a
  net-negative signal. Honest: do not spend the retrain.
- **Bar A's borderline is moot for the verdict** — B and C fail
  decisively, so a pooled recheck of clean-A cannot flip PASS. Recorded,
  not rechecked.
- **The DAgger fallback would at best MATCH Frontier** (it clones
  Frontier's geometric behaviour, no WM), so it cannot buy the clutter
  win either; it is a route to a deployable *grid* coverer, not a WM one.
- Deployable coverage today = the geometric Frontier (privileged) or a
  grid-only policy; neither needs the world model.

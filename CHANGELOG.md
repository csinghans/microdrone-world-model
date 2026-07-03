# Changelog

## Unreleased

- **G1 (motion-aware labels + hard-mix data, world model retrained):**
  per-world AUC@32 classic/dense/moving = 0.86/0.82/0.88 — the oracle fix
  lands (moving is now *detectable*: moving@0.8 wm crash 83 % → 47 %, and
  the privileged-direction reactive with the motion-taught danger-now head
  drops to 3 % at moving@1.2). But the recalibrated probabilities broke the
  hand MPC's fixed margins on classic/dense (sweep 30/33/23/3/17 %,
  dense up to 90 %) — the third measured instance of the same refrain: a
  better detector is not a better flight through hand-tuned margins. Dense
  remains a memory problem, as pre-registered. Consequences: step ② (GRU)
  attacks dense/FOV; step ③ (policy retrain on the new model) is now
  *required*, not optional — the decision layer must re-fit the new
  probability landscape.

- License changed from MIT to Apache-2.0 (patent grant; provenance kept in
  NOTICE).
- v0.2 opens with harder worlds: `spawn_dense_pillars` (5-7 pillars, two
  forced in-path) and `MovingCrosser` (a pillar crossing the corridor, its
  speed *aimed* at the encounter — an unaimed crosser misses on most seeds
  and measures nothing), plus `eval_hard_worlds`.
- **v0.2 baseline, measured before any model change** (30 seeds/cell,
  crash rate, zero-shot static-trained stack):

  | world @ cruise | reactive | hand MPC | learned |
  |---|---|---|---|
  | dense @ 0.8 m/s | 30 % | 50 % | 33 % |
  | dense @ 1.2 m/s | 70 % | 63 % | 50 % |
  | moving @ 0.8 m/s | 83 % | 83 % | 77 % |
  | moving @ 1.2 m/s | 37 % | 33 % | 40 % |

  Verdicts the v0.2 model work must answer: the home-turf crown does not
  transfer (the learned policy's 0 % becomes 33-77 %); nobody handles an
  aimed crosser at matched speed (the static-future assumption fails all
  three policies, including the privileged-direction baseline); and at
  1.2 m/s the moving world *inverts* — outrunning the crosser beats
  dodging it, an emergent "speed as evasion" the labels never taught.

## 0.1.0 — 2026-07-04

The port: the validated world-model stack from
[nanodrone-ai Lesson 29](https://github.com/csinghans/nanodrone-ai/tree/main/lessons/29_world_model)
re-homed as a clean research package.

- `world_model/` — bearing-aware encoder, multi-horizon residual predictor,
  dual-ring collision heads + danger-now head, JEPA losses (EMA target,
  variance guard), the training loop and the veer-ranking probe.
- `planner/` — the shared action set, the hand latent-MPC + reactive
  baseline, the learned-policy family (stacked / LSTM / edge-biased /
  curriculum) and a first-cut safety filter.
- `sim/` — the 48 Hz Crazyflie-class env + PID velocity commander, pillar
  scenarios and scoring rings, appearance-randomization primitives.
- `datasets/` — intervention rollout generation and the counterfactual
  label oracle with FOV honesty masks.
- `eval/` — the timing schematic, the cluttered closed-loop scoreboard, the
  speed sweep, the robustness pricing, and the embedded budget/latency bill.
- Everything keeps the `--selftest` / `XXX OK` convention; sys.path hacks
  from the course layout are gone (proper package imports, `pip install -e .`).
- PPO/RecurrentPPO training now seeded (`seed0`) for reproducibility.
- **Benchmark reproduced from scratch, twice** (64- and 96-rollout draws):
  mechanisms held on every draw (veer-ranking 1.00 x3, budget 137.3 KB
  exact, reactive speed collapse, zero false positives, robust-retrain
  buy-back); point numbers published as honest run-to-run ranges (AUC@32
  0.85–0.96, hand-MPC cluttered tail 9–16 %, learned-policy sweep 0–30 %
  per band — the course's all-zero was a strong-model draw). See the
  two-tier table in the README.

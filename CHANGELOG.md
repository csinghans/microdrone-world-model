# Changelog

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

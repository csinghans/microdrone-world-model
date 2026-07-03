# microdrone-world-model

> **A tiny latent world-model stack for micro-drones: action-conditioned
> prediction, proactive collision avoidance, and sim-to-real evaluation under
> embedded constraints.**

🚧 **Status: v0.1 — port complete, benchmark reproduction running.** The
validated baseline below shipped as
[Lesson 29 of the nanodrone-ai course](https://github.com/csinghans/nanodrone-ai/tree/main/lessons/29_world_model);
this repo re-homes it as a clean research package. The full pipeline already
runs here (the demo reproduces the course's numbers exactly from the same
checkpoint); the from-scratch benchmark reproduction is queued and the table
below flips to ✅ per row as it lands.

## Why this exists

Big world models (V-JEPA 2 class) need Orin-class GPUs. A 27 g drone has a
512 KB budget and a ~10 ms decision deadline. This project's wedge is the
gap between those two sentences: **how much anticipation can you buy under
embedded constraints?** See [docs/vision.md](docs/vision.md).

## The stack

```
camera frame ──> Encoder (bearing-aware, 64-d latent)
                   │
       candidate ──┤  MultiPredictor: z + Δk(z, a)  (k = 4/8/16/32 steps)
       commands    │
                   └─> CollisionHeads: P(warn 0.7 m), P(crit 0.35 m) per horizon
                                │
             planner reads the futures: latent MPC (hand) or PPO (learned)
```

| layout | what lives there |
|---|---|
| `world_model/` | encoder, predictor, collision heads, JEPA losses, training loop |
| `planner/` | action set, hand latent-MPC + reactive baseline, learned policies, safety filter |
| `sim/` | 48 Hz Crazyflie-class env + PID velocity commander, scenarios, domain randomization |
| `datasets/` | intervention rollouts, counterfactual label oracle + FOV honesty masks |
| `eval/` | timing schematic, closed-loop scoreboard, speed sweep, robustness pricing, embedded budget |
| `scripts/` | `train.py`, `evaluate.py`, `demo.py` |
| `hardware/` | v0.4 bridge design (Tello off-board → Crazyflie/GAP8 on-board) |

## Quickstart

```bash
conda env create -f environment.yml
conda activate microdrone-wm
pip install -e .

python -m datasets.generate_rollouts --rollouts 64   # 1. fly the data
python -m scripts.train --epochs 80                  # 2. train the world model
python -m scripts.demo                               # 3. one-course demo + plot
python -m eval.eval_closed_loop --seeds 100          # 4. the scoreboard
python -m eval.eval_speed_sweep --seeds 30           # 5. crash rate vs speed
python -m scripts.train --policy --timesteps 300000  # 6. learn the policy
python -m scripts.evaluate --seeds 60                # 7. every policy, same courses
```

Every module has a `--selftest` (or `python -m <module>`) that prints an
`XXX OK` line and asserts it.

## The validated baseline (measured in simulation; reproduction in this layout in progress)

| claim | number | reproduced here |
|---|---|---|
| collision prediction, 4 horizons (83–667 ms) | AUC ~**0.96** | ⏳ |
| "which way to dodge is safer" ranking | **1.00** (chance 0.5) | ⏳ |
| demo course: trigger lead over reactive | **~500 ms** earlier | ✅ (same checkpoint) |
| learned policy, 0.8–1.6 m/s sweep | **0 %** crashes (150 courses) | ⏳ |
| reactive baseline at the same speeds | up to **60 %** crashes | ⏳ |
| whole stack (weights + activations + workspace) | **137.3 KB** < 512 KB, ~8 ms/decision | ✅ |
| sim-to-real gap priced → bought back | AUC 0.96 → 0.82 → **0.92** | ⏳ |

Also inherited and kept honest: the four-run memory-architecture study
(stacked vs LSTM vs edge-biased diet vs curriculum — the stack never lost
anywhere; re-weighting moves the hole; ordering isn't consolidation).

## Roadmap

- **v0.1 — the port**: clean package, every claim reproduced. *(now)*
- **v0.2 — harder worlds & the model axis**: dense clutter, moving
  obstacles; model-side memory (GRU over latents).
- **v0.3 — metric grounding**: offline 4D-GS supervision so latents decode
  to collision-checkable distances.
- **v0.4 — hardware bridge**: Tello (off-board, honest about it) →
  Crazyflie + AI-deck (GAP8, truly on-board). See [hardware/](hardware/).

## Safety boundary

This project is for safety-focused autonomous navigation, collision
avoidance, education, and research. It does not support weaponization,
surveillance abuse, or evasion of safety/legal constraints. All flight
demos carry a geofence, manual override, emergency land, low-battery
behaviour, log replay, and a field-test checklist —
[docs/safety.md](docs/safety.md).

## Origins

Grew out of [nanodrone-ai](https://github.com/csinghans/nanodrone-ai) — a
30-lesson bilingual course that ends where this repo begins. 繁體中文的入門
導讀請從課程的[從這裡開始](https://github.com/csinghans/nanodrone-ai/blob/main/docs/zh-TW/START-HERE.md)出發。

MIT licensed.

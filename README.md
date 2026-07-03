# microdrone-world-model

> **A tiny latent world-model stack for micro-drones: action-conditioned
> prediction, proactive collision avoidance, and sim-to-real evaluation under
> embedded constraints.**

🚧 **Status: v0.1 porting in progress.** The validated baseline (model,
planner, learned policy, and all benchmark numbers below) shipped as
[Lesson 29 of the nanodrone-ai course](https://github.com/csinghans/nanodrone-ai/tree/main/lessons/29_world_model);
this repo is re-homing it as a clean research package, then pushing past it.
Watch the repo — the full port lands here commit by commit.

## Why this exists

Big world models (V-JEPA 2 class) need Orin-class GPUs. A 27 g drone has a
512 KB budget and a ~10 ms decision deadline. This project's wedge is the
gap between those two sentences: **how much anticipation can you buy under
embedded constraints?**

## The validated baseline being ported (measured in simulation)

| claim | number |
|---|---|
| collision prediction, 4 horizons (83–667 ms) | AUC ~**0.96** |
| "which way to dodge is safer" ranking | **1.00** (chance 0.5) |
| learned policy over the model, 0.8–1.6 m/s sweep | **0 %** crashes (150 courses) |
| reactive baseline at the same speeds | up to **60 %** crashes |
| whole stack (weights + activations + workspace) | **137.3 KB** < 512 KB, ~8 ms/decision |
| sim-to-real gap priced → bought back | AUC 0.96 → 0.82 → **0.92** |

## Roadmap

- **v0.1 — the port**: clean package layout, every claim above reproduced in
  this repo's harness.
- **v0.2 — harder worlds & the model axis**: dense clutter, moving obstacles;
  model-side memory (GRU over latents) after the course's four-run
  stacked-vs-LSTM study.
- **v0.3 — metric grounding**: offline 4D-GS supervision so latents decode to
  collision-checkable distances.
- **v0.4 — hardware bridge**: Tello (off-board, honest about it) →
  Crazyflie + AI-deck (GAP8, truly on-board).

## Safety boundary

This project is for safety-focused autonomous navigation, collision
avoidance, education, and research. It does not support weaponization,
surveillance abuse, or evasion of safety/legal constraints. All flight demos
carry a geofence, manual override, emergency land, low-battery behaviour,
log replay, and a field-test checklist.

## Origins

Grew out of [nanodrone-ai](https://github.com/csinghans/nanodrone-ai) — a
30-lesson bilingual course that ends where this repo begins. 繁體中文的入門
導讀請從課程的[從這裡開始](https://github.com/csinghans/nanodrone-ai/blob/main/docs/zh-TW/START-HERE.md)出發。

MIT licensed.

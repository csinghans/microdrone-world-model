# Vision — the wedge

Big world models are getting spectacular: V-JEPA-class video models
understand, predict and plan, and action-conditioned variants steer real
robot arms. They also assume an Orin-class GPU, hundreds of watts-seconds
per decision, and gigabytes of memory.

A 27 g micro-drone offers none of that. It offers:

- **512 KB** of fast memory for weights *and* activations *and* workspace,
- a **~10 ms** decision deadline at a useful control rate,
- one **fixed, forward, 60°** camera (body-mounted, no gimbal — the drone
  turns its whole body to look; v0.8 added a yaw command for indoor search,
  the camera still rigid to the frame),
- and a battery measured in minutes.

The wedge this project drives: **how much anticipation can you buy under
those constraints?** Not "shrink the biggest model until it fits" — start
from the budget and grow the smallest model that *chooses* correctly.

## The four questions

1. **How is the world represented?** A 64-d latent from a bearing-aware
   conv encoder — never pixels. Pixels are what you *have*, not what you
   need; a planner needs "which of my options gets close to something".
2. **How do actions change the future?** An action-conditioned residual
   predictor at four horizons (83–667 ms). Residual, so "nothing changes"
   is the free baseline; multi-horizon, because proactive is a claim about
   *time*.
3. **How do predictions become decisions?** Collision heads (warn + critical
   rings) per predicted future, read by a planner — hand-crafted MPC as the
   transparent rung, RL over the model's outputs as the measured champion.
4. **Does it fit?** 137.3 KB total, ~3.9 M MACs per decision — ~8 ms on a
   GAP8-class chip at an assumed 0.5 GMAC/s. Every claim ships with the
   selftest that asserts it.

## Method rules (inherited, kept)

- **Measure, don't claim.** Every script prints an `XXX OK` line and asserts
  it. Scoreboards over demos; crash rate over loss curves.
- **Vision-only in the loop.** Privileged state stages and scores flights —
  it never flies them. Baselines that cheat are labelled as cheating.
- **Honest limits, stated where they bite.** FOV blind sides, planar labels,
  sim-only optics: each is written next to the number it degrades.

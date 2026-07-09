# Sim-to-real

Everything here is measured in simulation. That sentence appears wherever
the numbers do, because the classic failure of sim-trained perception is not
that it breaks on hardware — it is that nobody *priced* the break before
paying it.

## The pricing protocol (shipped, `eval.eval_robustness`)

1. **Train clean, test weird.** Take the shipped model and measure it on a
   sim it never saw: randomized pillar shapes/colours, 0–2 control steps of
   command latency, ±8 % actuation noise, and a fixed "unseen camera"
   appearance shift on every frame the policy sees.
2. **Report the gap as a budget.** Baseline result: warn-ring AUC
   0.96 (clean) → 0.82 (randomized + unseen shift). That 0.14 is the
   modelled sim-to-real bill.
3. **Buy it back across the variation, not beside it.** Regenerate data
   with `--randomize`, retrain with `--robust` (appearance jitter on the
   online encoder only — the EMA target stays clean): 0.82 → **0.92**.
4. **Close the loop.** AUC is a detector score; the drone flies the planner.
   The same eval flies everything under randomization and reports crash
   rate + clearance per policy.

Two honest findings from the baseline worth keeping in view:

- A strictly better *detector* flew **worse** through the hand MPC (its
  margins were calibrated to the old probability floor) — a better score is
  not a better flight. The learned policy did not have that fragility.
- The clean-trained learned policy already flew the storm at the privileged
  baseline's level; storm-training the policy bought nothing more. The
  residual gap lives in *perception*, which is what `--robust` buys back.

## What randomization cannot buy

Randomization hardens against *modelled* gaps. Real optics, real airflow,
real motor wear are unmodelled — which is exactly what the v0.6 hardware
bridge measures (Tello first for the perception gap, Crazyflie + AI-deck
for the on-board story), with the same evals and the safety envelope of
`docs/safety.md`.

A concrete instance the indoor track surfaced (v0.8, `lowfly_v1`): the sim's
ground effect is a clean analytic term the PID already compensates, so
floor-hugging flight (hover + descent to z=0.15 m) is stable in sim — drift
<0.5 mm, descent overshoot <1 cm, no floor contact. That is precisely the
kind of "clean in sim" result to distrust: real near-surface aerodynamics
(prop-wash recirculation off floor/walls/clutter, turbulence, uneven ground)
are far nastier and unmodelled here. So near-floor / under-bed search is a
perception + geometry success in sim whose *flight* robustness is an open
sim-to-real bill — not settleable in this simulator, and a first thing the
hardware bridge would price.

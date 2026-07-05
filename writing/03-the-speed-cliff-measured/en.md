# Reactive vs Proactive: The Speed Cliff, Measured

*Article 3 of a series on building a latent world model that fits in
512 KB. Articles 1–2 argued why anticipation matters and what to predict;
this one is about the cleanest experiment in the repo — the one that
makes the whole case in a single curve. Every number reruns from
[microdrone-world-model](https://github.com/csinghans/microdrone-world-model).*

---

## Same drone, same camera, same courses — double the speed

Take two policies. Both read the **same** 64×64 camera through the
**same** trained encoder — same eyes, same visual features. The only
difference is what they do with them:

- **Reactive**: a head that answers "am I dangerously close *right now*?"
  Dodge when it fires. This is the honest version of every
  threshold-on-proximity controller ever shipped.
- **Proactive**: the world model — "if I hold this command for the next
  83–667 ms, do I get close?" — evaluated for every candidate command,
  every decision tick.

Fly both down the same single-pillar courses (same random seeds — literally
identical layouts), and raise the cruise speed in steps: 0.8, 1.0, 1.2,
1.4, 1.6 m/s.

At 0.8 m/s the two look similar. By 1.6 m/s the reactive policy crashes
**57–63 %** of the time (range across independent retrainings). The
proactive stack: **10–20 %**. Same eyes. Triple to six-fold difference in
survival, and the gap *widens* with every step of speed.

That widening is the point. It is not a tuning artifact; it is a unit
mismatch.

## Reaction is a distance budget; anticipation is a time budget

Here is the whole physics of it:

A reactive trigger fires at a fixed visual **distance** — the danger-now
head learned "planar distance < 0.7 m", and nothing about that number
knows your speed. So the time between trigger and impact is
*distance ÷ speed*: double the speed, halve your remaining time. Your
lateral authority is bounded (a 27 g drone corners only so hard), so the
evasion takes a roughly fixed time to execute. At some speed, the time
the trigger leaves you is less than the time the dodge needs. Below that
speed, reactive looks fine. Above it, it dies — not gradually, but like
walking off a cliff, because the deficit compounds quadratically
(stopping distance grows with v²).

The world model's trigger is denominated differently. Its collision
heads are conditioned on the commanded speed and look a fixed **time**
ahead (~0.7 s at the longest horizon). A fixed time budget is a
speed-*proportional* distance budget: fly faster and the model
automatically worries about pillars proportionally farther away. The
evasion-time requirement hasn't changed — but the warning now scales
with exactly the quantity that was killing the reactive policy.

One sentence to keep: **speed spends distance budgets and leaves time
budgets alone.** Any safety signal denominated in distance has a cliff
in it, and the cliff sits wherever your dynamics stop fitting in the
gap. The measured lead confirms the mechanism: on identical threatened
courses, the proactive stack triggers its evasions **~0.2 s earlier**
(+193 to +243 ms mean lead across draws) — with **zero false evasions**
on clear courses, because earlier-in-time does not mean jumpier.

## Why this experiment is built the way it is

Three design choices make the curve trustworthy, and they're worth
stealing for any evaluation you build:

1. **Single-pillar courses, on purpose.** The threat sits where both
   policies can see it. Cluttered scenes probe a *different* failure —
   the camera's field-of-view limit — and get their own scoreboard.
   One experiment, one mechanism; a curve that mixes failure modes
   proves nothing about either.
2. **The reactive baseline shares the encoder.** If the baseline had
   worse eyes, the comparison would be theater. It has the same eyes —
   it just refuses to look forward in time. (It is also *genuinely
   good* at low speed: 0 % crashes on the same courses at 0.8 m/s.
   A baseline that never wins anywhere is a strawman.)
3. **Same seeds across policies and speeds.** Every policy flies
   literally the same test. Differences are policy, not luck — and the
   whole sweep reruns from one command
   (`python -m eval.eval_speed_sweep --seeds 30`).

And the honesty tier, as always: the cliff *mechanism* reproduces on
every retraining draw; the exact crash percentages wobble (57–63 % at
the reactive end). Ranges are published, single draws aren't headlines.

## What the anticipation actually costs

The entire proactive overhead — encoder shared anyway, so: the
multi-horizon predictor plus collision heads — fits in the same
**137.3 KB int8, ~8 ms per decision** stack from article 1. There is no
Orin in this story; the time budget is bought inside a GAP8-class
envelope. That is the project's recurring claim, now with its sharpest
evidence: the single cheapest qualitative upgrade a micro-drone can buy
is *changing the unit its fear is denominated in* — from meters to
milliseconds.

A fresh footnote from this month's skill campaigns: anticipation isn't
all-or-nothing. A policy re-deciding every 5 control steps tracks a
*sliding* obstacle surprisingly well "for free" — fast reaction loops
recover part of what prediction buys, and the residual gap concentrates
exactly where approach times are long. The cliff, everywhere we look,
is about time.

## The takeaway

If your drone never exceeds ~0.8 m/s, save the kilobytes — a
well-tuned reactive head is honest work at low speed. The moment speed
is part of the mission, the question stops being "is my detector good?"
and becomes **"what unit is my safety margin measured in?"** Distance
margins have a cliff. Time margins scale. We measured where the cliff
is, published the seeds, and the curve reruns on your laptop.

---

*The sweep, the courses, and both policies:
[microdrone-world-model](https://github.com/csinghans/microdrone-world-model)
(`eval/eval_speed_sweep.py`). The course that taught the stack:
[nanodrone-ai](https://github.com/csinghans/nanodrone-ai).*

*Next in the series: **Building an action-conditioned latent world
model** — the encoder, the residual predictor, and the counterfactual
oracle that teaches ranking.*

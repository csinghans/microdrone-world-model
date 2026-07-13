# Reactive vs Proactive: The Speed Cliff, Measured

*Article 3 of a series on building a latent world model that fits in
512 KB. Articles 1–2 argued why anticipation matters and what to predict;
this one is about the cleanest experiment in the repo — the one that
makes the whole case in a single curve. Every number reruns from
[microdrone-world-model](https://github.com/csinghans/microdrone-world-model).*

---

> **The simple version.** A batter doesn't swing when the ball reaches the plate — they swing at where it WILL be. Give two pilots the same eyes: one reacts to what it sees, the other acts on a half-second forecast. Same drone, same camera, same courses, double the speed — the reactive pilot falls off a cliff and the forecasting one doesn't. One curve carries the whole argument.


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

## The same cliff, staged as a door

The speed sweep varies *your* speed. To show the unit mismatch is about
time itself — not about flying fast — we built the cliff a second body:
a fence with one gap whose edge pillars **converge** at 0.25–0.45 m/s.
The aperture is aimed to be comfortably flyable for an on-time arrival
and to shut completely within the episode, and success is judged
against the aperture **as it is at the crossing instant**. A policy
that reads *current geometry* sees an open door and commits; the
geometry it committed to is stale by mid-transit.

Four contenders flew identical courses on identical seeds — the full
spectrum from pure reaction to the strongest predictive stack we have:

| contender | door @ cruise | door @ 1.5× | how it loses |
|---|---|---|---|
| reactive (privileged direction) | 83 % | **40 %** | commits on stale width; 60 % pinched mid-transit |
| hand-tuned latent MPC | 33 % | 17 % | fixed margins charge and get crushed |
| general champion (no fence in its diet) | 10 % | 0 % | detours around the whole fence — reached, never threaded |
| moving-gap champion (time-trained) | **93 %** | **87 %** | it doesn't — commits earliest, threads with margin |

Three readings worth the table:

1. **The reactive row is the sweep's cliff, relocated.** At cruise, a
   still-open ~0.8 m door is passable by reacting — 83 %. At 1.5×
   cruise the same policy gets pinched 60 % of the time: not because it
   is slower to *see*, but because the width it saw no longer exists by
   the time it is between the pillars. Distance-denominated decisions
   go stale in proportion to speed × closure rate — the cliff, in a
   second currency.
2. **There is more than one way to lose to time.** The hand MPC's fixed
   margins commit-and-die; the fence-naive champion treats the whole
   wall as one obstacle and detours (our trajectory-level `transited`
   check catches reached-without-threading honestly). Losing to time is
   the *family* of failures; late reaction is just its loudest member.
3. **The winner never trained on this door.** The moving-gap champion —
   trained on static gaps and *sliding* gaps — threads a *shrinking*
   one at 93/87 %, zero-shot, guards green. Policies whose training is
   denominated in time generalize across kinds of motion; that is the
   dividend the unit change pays.

One number that surprised us into a design note: **nobody froze** — the
freeze-at-the-wall outcome we pre-registered never occurred for any
contender. This arena prices commitment errors, not hesitation; pricing
hesitation would need an *opening* door. (Both figures — the four-bar
outcome chart and the same-seed trajectory overlay where the champion
visibly commits earliest — live in
[`experiments/closing_door/`](../../experiments/closing_door/) with the
full gate-by-gate journal.)

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

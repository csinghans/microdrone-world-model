# Why Micro-Drones Need Tiny World Models

*Article 1 of a series on building a latent world model that fits in 512 KB.
Everything here is measured by rerunnable scripts in
[microdrone-world-model](https://github.com/csinghans/microdrone-world-model);
nothing is a demo cherry-pick.*

---

## The cliff

Take a 27-gram drone, give it a purely **reactive** vision policy — "if
something looks dangerously close, dodge" — and fly it down a pillar
corridor at increasing speed. At 0.8 m/s it looks competent. At 1.6 m/s it
crashes **57–63 % of the time** (three independent training draws; the
number wobbles, the cliff doesn't).

Same drone, same camera, same compute budget, one change: the policy now
asks a tiny **world model** "what happens in the next 83–667 ms if I keep
doing this — and what if I veer instead?" Crash rate at 1.6 m/s:
**10–20 %**.

That gap is not a tuning artifact. It is physics. A reactive policy sees
danger when danger is already close; stopping distance grows with the
square of speed; and a 60° camera at 1.6 m/s brings a pillar from
"just entered the frame" to "inside your warning radius" in a few hundred
milliseconds. React-when-close runs out of runway exactly when speed starts
to matter. The only way out is to *pull the decision earlier in time* —
and that is the entire job description of a world model.

Measured on the same courses: the anticipating stack triggers its evasions
roughly **0.2 seconds earlier** than the reactive baseline (+193 to
+243 ms mean lead across draws), with **zero false evasions** on clear
courses. Earlier, and not jumpier — that combination is what you cannot
get from a threshold on "how close does it look".

## What "world model" means here (and what it doesn't)

A world model, stripped of grandeur, answers one question:
**"if I see this and do that, what happens next?"**

The version that fits on a micro-drone:

```
camera frame ──> Encoder (64-d latent, bearing-aware)
                   │
     candidate ────┤  Predictor: z + Δk(z, a)   (k = 4/8/16/32 steps)
     commands      │
                   └─> Collision heads: P(within 0.7 m), P(within 0.35 m)
                       per horizon, per candidate
                                │
                  planner picks the safest future
```

Three design choices carry the whole thing:

1. **Predict in latent space, never pixels.** A planner doesn't need the
   next image; it needs "which of my options gets close to something".
   Pixel prediction spends the budget hallucinating texture no decision
   ever reads. (That trap deserves its own article — next in the series.)
2. **Residual prediction.** The predictor outputs a *change* on top of the
   current latent, so "nothing changes" is the free baseline and the model
   only has to earn the difference. At micro scale you cannot afford to
   re-learn the identity function.
3. **Action conditioning through counterfactual labels.** Executed flights
   only tell you what *did* happen. A planner asks what *would* happen —
   for every candidate command, at every frame. In sim, a privileged
   oracle labels those counterfactuals; the model is then graded on the
   one skill a planner relies on: on frames where geometry says one dodge
   is truly safer than the other, does the model rank it safer? Ours
   scores **1.00 on that ranking check, on every training draw** —
   chance is 0.5, and single-frame reactive baselines sit at chance.

## The budget is the point

The spectacular world models — V-JEPA-2-class video models that plan real
robot arms — assume an Orin-class GPU, tens of watts, gigabytes. A 27 g
drone offers:

- **512 KB** of fast memory for weights *and* activations *and* workspace,
- a **~12 Hz** decision loop (an 83 ms budget per decision),
- one **fixed, forward-facing 60° camera**,
- a battery measured in minutes.

Our entire stack — encoder, four-horizon predictor, collision heads —
comes to **137.3 KB int8, ~3.9 M MACs ≈ 8 ms per decision** on a
GAP8-class chip. That is a *nano distillation* of the world-model idea,
and we say so: it will not fold laundry. But the question it answers is
the question that matters at this scale, and it is the question the big
models never face: **how much anticipation can each kilobyte buy?**

Not "shrink the biggest model until it fits". Start from the budget and
grow the smallest model that *chooses correctly*.

## Receipts, and the honesty tax

Every number above comes from a script that prints a self-check line and
asserts it. Two habits keep those numbers trustworthy, and both cost
something to keep:

**Evaluate by crash rate, not loss.** A better collision detector is not
automatically a better flight — we measured a model upgrade that improved
detection AUC and then *broke* the hand-tuned planner riding on it, three
separate times. The scoreboard that counts is closed-loop: crashes per
hundred flights, at what speed, with how much clearance.

**Publish two tiers.** Retrain the whole pipeline from scratch and the
*mechanisms* reproduce every time: the ranking check at 1.00, the reactive
speed cliff, the zero false positives, the budget to the same decimal. The
*point numbers* do not: collision AUC lands anywhere in 0.85–0.96
depending on the draw; a strong-model draw once produced an all-zero crash
sweep that a fresh draw softened to 0–30 % per band. So the repo publishes
both tiers side by side — claims about mechanisms survive retraining;
claims about the third decimal do not. Any single-draw benchmark you read
(including ours) should be read with that split in mind.

## Where the floor is now

Anticipation is not magic; it is a budget line like everything else. The
harder worlds make that concrete. Zero-shot, our champion crashed into
**83 %** of aimed crossing pillars — a moving obstacle violates the
"world holds still" assumption baked into static training data. Teaching
the *labels* about motion and re-training the policy on a harder data
diet cut that to **33 %**; one odometry scalar (the drone's own corridor
progress, appended to each observation) plus an edge-biased diet cut the
worst dense-clutter cells from **37–50 % to 17–27 %** and the fast-crosser
cell to **7 %**. Three times in a row, the measured verdict was the same:
**a data diet and one well-chosen scalar beat architectural elegance** —
a policy-side LSTM and a model-side GRU both lost to a plain stacked
history plus better data, and the losses are recorded in the changelog,
not buried.

The floor that remains — dense clutter around 17–27 % — is a field-of-view
and memory problem, and it is exactly where the next experiments point
(metric grounding: does supervising the latent with "where is stuff, how
far" buy anything the collision labels don't already?).

## Why bother at this scale

Because the interesting deployment niche for drones that *think ahead* is
precisely where big compute cannot follow: palm-sized machines inspecting
indoor spaces, flying near people, searching collapsed structures,
operating in swarms where the unit cost is the whole ballgame. A 27 g
drone that anticipates 0.2 s further into the future is qualitatively
safer than one that reacts — and the entire upgrade costs 137 KB.

The big models are teaching us what world models *can* know. The nano end
teaches what anticipation *costs* — per kilobyte, per millisecond, per
gram. Both questions deserve real benchmarks.

---

*The stack, the scoreboards, and every claim's selftest:
[microdrone-world-model](https://github.com/csinghans/microdrone-world-model).
It grew out of a 30-lesson bilingual course,
[nanodrone-ai](https://github.com/csinghans/nanodrone-ai), which ends
where the research repo begins.*

*Next in the series: **Why predicting pixels is the wrong target** — what
latent prediction buys when every kilobyte is rent.*

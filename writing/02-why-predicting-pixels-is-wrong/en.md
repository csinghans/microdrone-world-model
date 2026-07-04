# Why Predicting Pixels Is the Wrong Target

*Article 2 of a series on building a latent world model that fits in
512 KB. Article 1 argued micro-drones need anticipation; this one is about
what, exactly, a tiny world model should be trained to predict. As always,
every number traces to a rerunnable script in
[microdrone-world-model](https://github.com/csinghans/microdrone-world-model).*

---

## The seductive default

Ask anyone to build a world model and the reflex is video prediction: feed
frames in, get future frames out. It feels rigorous — if the model can
paint the future, surely it *understands* the world. The biggest video
models do exactly this, spectacularly.

On a 27-gram drone, that reflex is fatal three separate ways — and the
third one is the interesting one, because we spent a training run this
month measuring what happens even when you avoid the first two.

## Failure one: the budget goes to texture

A pixel target makes the model spend capacity on everything the camera
sees — wall texture, lighting gradients, the exact silhouette of a pillar's
shadow. None of that changes a flight decision. Our entire flight stack is
**137.3 KB int8**; a decoder alone, at the resolution needed to paint a
0.18 m pillar at 2 m, would eat the whole budget before the first
convolution of an encoder existed. Every kilobyte spent painting is a
kilobyte not spent choosing.

The deeper version of this point: **prediction error in pixel space is
democratic, and danger is not.** A mean-squared-error loss weights a
mispainted patch of sky exactly as heavily as a mispainted obstacle edge.
The thing a drone needs — "which of my six candidate commands gets close
to something within 667 ms" — occupies a vanishing fraction of pixel
variance. Optimizing pixel fidelity optimizes almost entirely the wrong
thing, then hopes decision-relevance emerges as a side effect.

## Failure two: hallucination is not anticipation

Generative video models *hallucinate* futures: plausible, detailed,
frequently wrong in exactly the details that matter. For entertainment,
fine. For collision avoidance, a model that paints a beautiful
pillar-free corridor is worse than a model that outputs nothing, because
downstream code has no way to know which painted details are load-bearing.

The fix is old and good (it is the JEPA argument, and our stack is a nano
distillation of it): **predict in representation space, not pixel space.**
Our predictor never renders anything. It maps a 64-dimensional latent plus
a candidate command to the latent 4, 8, 16 and 32 control steps ahead —
`z + Δk(z, a)`, a residual, so "nothing changes" is the free baseline and
the model only earns the difference. The target latent comes from an EMA
copy of the encoder (stop-gradient, with a variance guard against
collapse), so the model is graded on "did you land where the world
actually went", never on "did you paint it prettily".

What reads those predicted latents is not a decoder but **two collision
rings per horizon** — P(within 0.7 m), P(within 0.35 m) — per candidate
command. That is the entire interface between prediction and decision:
eight numbers per candidate, forty-eight per frame. A planner needs
nothing else, and nothing else fits.

## Failure three — the subtle one: even the *right* extra knowledge can be the wrong target

Here is the fresh scar, and the reason this article exists now.

This month we ran a controlled campaign (v0.5, every gate pre-registered)
asking: if we supervise the latent with *metric* structure — a small polar
occupancy grid, "where is stuff and how far", the perfect-information
upper bound of what an offline 3D-reconstruction pipeline could provide —
does the drone fly better?

The model-layer answer was an emphatic yes. Against a same-draw control:
dense-clutter collision AUC **+0.07 to +0.24** across two seeds, every
world slice improved, the reactive danger-now head +0.13, the
dodge-ranking probe doubled. The grounded model *knows* strictly more,
and the auxiliary head that taught it is dropped at deploy — zero flight
cost.

The flight-layer answer: **the policy retrained on the grounded model
crashed dense courses at 37 % where the old stack crashed 17 %**, and
48 % vs 27 % at higher speed (n=60, fresh seeds). Not a tuning slip — the
same recipe, single knob changed, guards and rechecks all pre-registered.

The mechanism hypothesis (now under a fresh pre-registered campaign): AUC
is a *ranking* statistic, but a policy consumes the heads' raw
probability surfaces. The metric supervision visibly recalibrated those
surfaces — better ordered, differently *shaped* — and a decision layer
tuned to the old shapes found the new ones harder to exploit. Knowing
more, presented wrong, flew worse.

That is failure three in general form: **"predict X better" only helps if
X is the currency your decisions are denominated in.** Pixels fail this
test maximally. But so can any auxiliary target — even a geometrically
impeccable one — the moment it stops being the thing the planner reads.
The target isn't sacred because it's informative; it's sacred only if
it's *consumed*.

## What we train instead (and what it costs to keep honest)

The stack's supervision, end to end, is denominated in decisions:

1. **Latent prediction** (JEPA-style, EMA target): the representation
   must track where the world goes — cheap, non-generative, collapse-guarded.
2. **Executed-action collision labels**: did the flown future get
   dangerously close within k steps? True, but sparse in the dimension
   planners care about.
3. **Counterfactual collision labels**: for *every* frame and *every*
   candidate command, a privileged sim oracle answers "what if you held
   this instead?" — with an honesty mask that refuses to grade the model
   on threats outside its camera wedge. This is the supervision that
   makes the model *rank its options*, which is the one ability the
   planner actually rents: on held-out frames where geometry says one
   dodge is truly safer, the model ranks it safer with score **1.00 on
   every training draw** (chance 0.5).

Two honesty habits guard the whole arrangement, and both have now earned
their keep twice: evaluate by **closed-loop crash rate**, never by loss
or AUC (four separate times, a better detector has failed to be a better
flight); and publish **two tiers of claims** — mechanisms that reproduce
on every retrain, point numbers that wobble with the draw (a dense cell
read 26.7 % on one seed set and 48.3 % on another this month; the
pre-registered recheck rule exists precisely so that a friendly draw
cannot become a headline).

## The takeaway

Don't ask a tiny model to paint the future. Ask it to *place* the future
in a representation whose only job is answering the questions your
planner actually asks — and then grade the whole pipeline in the only
currency that matters at 1.6 m/s, which is crashes per hundred flights.

Pixels are what you have. Decisions are what you need. Everything your
budget spends between the two should be auditable against that exchange
rate — because as we just measured, even genuinely better knowledge,
delivered in the wrong denomination, buys worse flights.

---

*The stack, the scoreboards, and every claim's selftest:
[microdrone-world-model](https://github.com/csinghans/microdrone-world-model).
The v0.5 split-verdict campaign, gate by gate:
`experiments/metric_grounding/journal.md`.*

*Next in the series: **Reactive vs proactive — the speed cliff,
measured** — why reaction is a distance budget, anticipation is a time
budget, and what that means at 1.6 m/s.*

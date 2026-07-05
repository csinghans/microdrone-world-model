# Building an Action-Conditioned Latent World Model (in 81 KB of Weights)

*Article 4 of a series on building a latent world model that fits in
512 KB. Articles 1–3 argued the why; this one is the how — every design
choice, with the measured reason behind it and the scars from the
choices that lost. Everything reruns from
[microdrone-world-model](https://github.com/csinghans/microdrone-world-model).*

---

## The parts list

The whole stack is four small networks and one privileged teacher:

```
camera 64x64 ──> Encoder (64-d latent z, bearing-aware)
                    │
   command a ──────┤   Predictor: ẑ(k) = z + Δk(z, a),  k = 4/8/16/32 steps
                    │
                    ├─> CollisionHeads: P(within 0.7 m), P(within 0.35 m)
                    │       per horizon — what the planner reads
                    └─> DangerNowHead: "close right now?" — the honest
                            reactive baseline, same eyes

  (training only) EMA twin of the encoder — the target that never flies
  (training only) counterfactual oracle — the teacher that knows geometry
```

Weights: **81.3 KB int8**. With activations and workspace: **137.3 KB**,
~3.9 M MACs ≈ 8 ms per decision on a GAP8-class chip. Everything below
is about making those kilobytes answer one question: *which of my
candidate commands gets close to something, and when?*

## The data is an experiment, not footage

A frame-to-label mapping can be learned from passive video. A world
model cannot: it must learn how the world changes *because of what you
do*. So the dataset flies itself as a chain of tiny controlled
experiments: reset to a fresh random pillar course, cruise in, then
every ~1 second draw one of six commands (forward / veer left / veer
right / slow / climb / hover) and **hold it** for the whole segment.
96 trials × 120 steps at 48 Hz, each trial at its own cruise speed.

Holding is the point, twice over. First: the model must answer "what
happens if I *keep doing this* for k steps?", so the training pairs need
commands genuinely held for k steps. Second: every segment switch is a
natural contrast — same view, different command, different outcome —
which is precisely the action-conditioning a planner rents.

## The spine: three choices, three reasons

**The encoder is bearing-aware.** A drone's decision variable is not
"is there a pillar" but "where in my visual field is it" — bearing is
what separates veer-left from veer-right. So the encoder's pooling
preserves horizontal structure instead of averaging it away. A global
pool would compress "pillar on the left" and "pillar on the right" into
the same summary; ours keeps them distinguishable all the way into the
64 numbers.

**The predictor is residual.** ẑ(k) = z + Δk(z, a): "the future looks
like the present" is the free starting point, and the network only
earns the *difference*. At 81 KB you cannot afford to re-learn the
identity function — and at 48 Hz most of the world genuinely is
identity most of the time. (This choice later saved us from a real bug;
scar story below.)

**The heads read predicted futures through two rings.** Per horizon,
two logits: P(within 0.7 m) and P(within 0.35 m). One ring is a region
test, not a risk gradient — inside the warn ring *every* command's warn
label is 1, including the command that escapes. The critical ring keeps
the planner sighted where the warn ring saturates. This wasn't a
theoretical nicety: when we later taught a policy to fly through narrow
gaps, the warn rings saturated wall-to-wall inside the gap and only the
crit heads carried usable signal. The two-ring design passed its real
exam there (27 % → 87-90 % transit success).

## The teacher that never flies

What grades the predictor? Not pixels — a slow-moving **EMA twin** of
the encoder (exponential moving average of its weights, stop-gradient)
encodes the *actual* future frame, and the predictor is graded on
landing near that target in latent space.

Why a twin rather than the live encoder? Because a live target chases
its own student into collapse: the encoder can make every prediction
"correct" by encoding everything to the same point. Two defenses run
together: the EMA target moves slowly enough to be a stable answer key,
and a **variance guard** (a VICReg-style hinge) keeps the latent
dimensions from flatlining. Cheap, non-generative, collapse-proof — the
JEPA recipe at nano scale.

## The oracle that teaches ranking

Here is the supervision that matters most, and the easiest one to get
wrong. Executed flights answer "did what I flew get close?" — densely,
truthfully, and almost uselessly for a planner, because a planner asks
"which of my six options is safest *from here*?" Executed data answers
that only at segment switches. We measured the gap: with executed
labels alone, collision AUC looked fine (~0.9) while the model's
ability to *rank a left dodge against a right dodge* sat at chance.
Good detector, coin-flip chooser.

The fix is sim's one honest superpower: a **counterfactual oracle**.
For every frame and every candidate command, roll the command forward
kinematically through the known pillar layout and label whether it
would enter each ring within each horizon. Straight-line kinematics for
both parties — motion-aware since v0.2, so a crossing pillar is judged
by *relative* velocity — with the approximation symmetric across
candidates, so rankings survive it.

Two honesty rules ride along:

1. **The FOV mask.** If the threatening pillar sits outside the
   camera's wedge, the label is marked *unanswerable* and excluded from
   the loss. Grading a monocular model on threats it cannot see teaches
   noise, not vigilance.
2. **Decision-relevant oversampling.** Most frames are far from
   everything; every candidate is safe; there is nothing to rank. Half
   of each counterfactual batch is drawn from frames where the visible
   candidates *disagree* — the frames that actually teach choice.

## The training mix, and what it costs to change it

Five loss terms, summed: latent prediction MSE, the variance guard, BCE
on executed collision labels, BCE on the counterfactual labels
(FOV-masked), and the danger-now head. 80 epochs of Adam. Roughly half
an hour on a laptop.

That mix is a *coupled system*, and this is the part I'd underline for
anyone building their own. Two scars from our own changelog:

**Scar one — the memory that ate the baseline.** Adding a GRU over past
latents (model-side memory), the obvious wiring hands the GRU state to
the predictor as its residual base. Quietly, that replaces "the future
looks like the present *frame*" with "the future looks like my
*memory*" — and the free baseline stops being free. A smoke test caught
it: long-horizon prediction error *worse than a no-op*. The fix is a
design rule: **memory may condition the forecast; the residual stays
frame-based.** (Even fixed, the GRU lost its gate honestly: it helped
exactly the world slices where memory wasn't the constraint and hurt
the two hard ones. The stacked-history policy kept its crown. Elegance
must pay rent here.)

**Scar two — the auxiliary loss that flew worse.** This year we added a
geometrically impeccable auxiliary: supervise the latent with a metric
occupancy grid (article 2 tells the full story). Detection improved on
every slice — and the policy retrained on that model crashed *twice as
often* in dense clutter. The probability surfaces the heads emit are
the policy's sensory input; an extra gradient into the shared trunk
recalibrated them (conditionally, it turned out — uncorrectable by any
global knob). The lesson generalizes: **every loss you add reshapes the
observation space of whatever consumes your model.** Add losses the way
you add medications.

## Grading yourself without lying

Three habits, all cheap, all load-bearing:

- **Split by rollout, never by frame.** Neighbouring frames are
  near-duplicates; a random frame split leaks the val set into training
  and inflates every metric.
- **Probe the one ability planners rent.** The veer-ranking check: on
  held-out frames where geometry says one dodge is truly safer (one
  crosses the danger radius, the other clears by >0.12 m, threat inside
  the FOV), does the model rank it safer? Chance is 0.5. Ours scores
  **1.00 on every retraining draw** — it is the single number I trust
  most in the repo.
- **Slice your validation, then distrust small slices.** Per-world AUC
  told us dense clutter was the open frontier. It also taught us a
  harder lesson: on an 18-rollout val split, a *single-seed* dense AUC
  spans 0.47–0.99 across retrainings of the same recipe. Model-layer
  gates now require multi-seed means or defer to flight gates entirely.

## The cost sheet

| item | price |
|---|---|
| encoder + predictor + heads (weights) | 81.3 KB int8 |
| full budget with activations + workspace | 137.3 KB of 512 KB |
| decision latency | ~3.9 M MACs ≈ 8 ms |
| training | 96 self-flown trials + 80 epochs ≈ laptop-scale |
| the oracle & EMA twin | free at deploy — they never leave the lab |

The design fits because everything deploy-time is small and everything
expensive is a *teacher*, not a passenger. That split — heavy
supervision, light inference — is, I think, the most reusable idea in
the whole build.

---

*Every module named here has a `--selftest` that asserts its claims:
[microdrone-world-model](https://github.com/csinghans/microdrone-world-model).
The scars are in the changelog and the campaign journals, numbers
included.*

*Next in the series: **Evaluate by crash rate, not loss** — four
measured times a better detector was not a better flight.*

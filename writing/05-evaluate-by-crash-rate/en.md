# Evaluate by Crash Rate, Not Loss

*Article 5 of a series on building a latent world model that fits in
512 KB. This one is the series' thesis statement: the evaluation
discipline that every other article's numbers stand on — and the four
measured times it saved us from shipping something worse. Everything
reruns from
[microdrone-world-model](https://github.com/csinghans/microdrone-world-model).*

---

## The purchase we almost made

This year we upgraded our drone's world model with metric supervision —
"where is stuff, and how far". By every model-layer metric the upgrade
was a clean win, and not marginally: dense-scene collision AUC up
**+0.07 to +0.24** against a same-data control, the reactive head up
+0.13, the dodge-ranking probe *doubled*. If our evaluation had been
loss curves and AUC — which is to say, the evaluation most model
upgrades get — we would have shipped it that afternoon.

Then we retrained the flight policy on the upgraded model, exactly as
before, single knob, and flew the standard scoreboard: dense-clutter
crashes went **17 % → 37 %** at cruise and **27 % → 48 %** at speed
(n = 60, fresh seeds). The model knew more. The drone crashed twice as
often. The only reason this purchase never shipped is that our
acceptance test is denominated in **crashes**, not in model statistics.

That was the fourth time this repo measured some version of the same
sentence — **a better detector is not a better flight** — and the
sharpest, because this time a full policy retrain sat between the
detector and the verdict and still couldn't cash the gain.

## Why proxies decouple: three measured mechanisms

Loss and AUC are statistics about the *model, alone, on a dataset*.
Flight is a property of a *closed loop*: model, policy, environment,
feedback. Three specific ways we've measured them coming apart:

**1. Ranking is not calibration.** AUC only sees *order* — it is
blissfully invariant to what the probability numbers actually are. But
a learned policy consumes the heads' raw probability surfaces as its
sensory input. Our metric-grounding upgrade improved the ordering and
*inflated* the numbers — conditionally, in dense geometry specifically
(dense warn calibration error 1.75× worse), which no global correction
can even express. The policy's observation currency was quietly
debased while its report card improved.

**2. Fixed decision margins assume a frozen landscape.** Our first
planner was a hand-tuned latent-MPC with fixed probability margins. It
was broken three separate times — never by a worse model, always by a
*better* one whose recalibrated probabilities moved under the
thresholds (the third strike: a motion-aware retrain that made moving
obstacles detectable for the first time and simultaneously drove the
hand planner's dense-scene crashes to 90 %). Hand margins are a bet
that probability landscapes never shift. They shift every retrain.

**3. Averages hide slices; slices decide missions.** A model-side
memory (GRU) once raised our headline validation AUC — by helping the
easy world (classic 0.86 → 0.95) while *hurting* both hard ones (dense
0.82 → 0.74, moving 0.88 → 0.84). The average said progress; the
mission cells said regression. It lost its gate honestly and the
simpler architecture kept the crown.

## What we fly instead: the scoreboard

The acceptance test that catches all three failure modes is boringly
concrete — a grid of **mission cells**, each a (world × speed) pair
flown closed-loop:

| convention | why |
|---|---|
| crash rate per cell, n = 30 seeds | the mission's own currency |
| same seeds for every policy | differences are policy, not luck |
| **targets** on the cells you claim to improve | the point of the change |
| **guards** on every other cell | a win that breaks a guard is a hole that moved |
| bars frozen *before* any number exists | no post-hoc goalposts |
| borderline (±0.08) → n = 60 on fresh seeds | see below — this rule earns its keep |
| honest negatives recorded, never retried into passing | the journal is the product |

This is cheap to run (a cell is 30 simulated flights) and brutal to
argue with. Our autonomous research runner executes exactly this
protocol — the pre-registration, the gates, the rechecks, the journal —
so a campaign's discipline no longer depends on a human's mood at 1 a.m.

## The instrument lesson: even crash rates need error bars

Flight metrics are the right currency, not a magic one. Two measured
humilities:

- A dense cell once read **26.7 %** on its first thirty seeds and
  **48.3 %** on sixty fresh ones. The friendly first read was within
  our pre-registered borderline band, the recheck rule fired
  automatically, and the verdict flipped from "arguable" to
  "unambiguous". One campaign ran **seven** such rechecks. If your
  acceptance test has no recheck rule, your bars are softer than they
  look.
- Model-layer slice metrics are worse: across five retrainings of the
  *same recipe on the same data*, single-seed dense AUC spanned
  **0.47 to 0.99**. We now treat any single-seed model metric as
  weather, not climate — multi-seed means or straight to flight gates.

## What loss is still for

We didn't throw training curves away; we demoted them. Loss, AUC and
the smoke tests answer *harness* questions: is a head dead, has the
latent collapsed, is the wiring sound, does the budget fit. Our smoke
asserts are scoped to exactly what a tiny run can promise — and every
claim about *quality* is forwarded to the flight gates. (We learned
that scoping the hard way too: a shipped release's smoke test turned
out to assert more than smoke-scale training can deliver, and had been
failing silently on a job nobody had ever run. The recalibrated version
is green weekly, in public CI.)

## The recipe, portable

If you take one section to your own robot, take this:

1. Write down the mission cells — the (situation × condition) grid your
   system must survive.
2. Freeze targets *and guards* before any number exists. Guards are
   sacred: they are how you notice the hole moving.
3. Fly every candidate on the same seeds. Publish ranges across
   retrainings, not your best draw.
4. Give borderline results an automatic, pre-registered recheck at
   higher n on fresh seeds.
5. Record negatives in the same journal as wins. The negative that
   costs a training run today is the one nobody re-digs next year.
6. Let model metrics debug; let mission metrics decide.

Loss is what the model feels. Crashes are what the mission feels.
Evaluate in the mission's currency, and better-looking models that fly
worse get caught at the gate — which, four times now, is exactly where
ours were caught.

---

*The scoreboards, the runner, and all four verdicts with their numbers:
[microdrone-world-model](https://github.com/csinghans/microdrone-world-model)
(`experiments/*/journal.md`, `CHANGELOG.md`).*

*Next, closing the series: **From sim toward Crazyflie** — what the
512 KB budget was for all along.*

# Unit-Green Is Not Integration-Green: the Climb to a Deployment Gate

*Article 6 of a series on building a latent world model that fits in
512 KB. Articles 1–5 built and audited single skills; this one is
about what happens when you chain them — a flight exam the whole
catalog failed on day one, and the five lineups it took to pass it.
Everything reruns from
[microdrone-world-model](https://github.com/csinghans/microdrone-world-model).*

---

## The exam nobody had taken

By mid-2026 this repo had five flying skills, each with its own gated
record: thread a static gap, weave a three-pillar slalom, time a
moving gap, pass a door, wait out an opening door. In software terms
we had **unit tests** — and unusually strict ones. Every skill is
examined on frozen seeds against a pre-registered bar, guards protect
old skills when new ones train, and no number enters the record after
the fact.

What we did not have was the sentence every software team eventually
says out loud: *the units pass and the product is broken*. No
artifact had ever flown two different obstacles in a row.

So we built the missing tier and froze it before measuring anything.
An **integration test** is a course of three stages drawn at random
(with repetition) from the five-skill pool, flown end to end — about
forty control decisions with no reset between stages. The
**deployment gate**, the standing precondition for real hardware, is
**≥ 70 % success over n = 100 random courses**, and every passing
suite regenerates two videos of record (drone FPV + simulator god
view) committed to the repo. Red, then green, with receipts.

## Day one: everything is red

Four contenders flew the first suite, n = 30 each:

| contender | integration success |
|---|---|
| privileged per-stage expert relay (the "ceiling") | 13.3 % |
| five-skill generalist (KL-anchored fine-tune) | 13.3 % |
| moving-gap RL champion | 13.3 % |
| slalom behavior clone | **33.3 %** |

The headline is the ceiling's own number. The relay reads the course
layout directly and swaps in each stage's native expert — the
strongest composition privileged information can buy. If stages were
independent at the experts' native rates (~0.90 each), it would score
around 0.73. It scored **0.133**.

The difference is the **seam tax**. A unit episode starts from a
clean hover; stage two of a course starts with whatever velocity and
lateral offset stage one left behind. Per-stage success conditioned
on arrival was ~0.51 — mid-flight entry roughly *halves* every RL
expert, because the entry states are conditions no unit episode ever
produced. Units green, integration red, and the break lives precisely
in the thing unit tests cannot see.

The other signpost: the best contender was not the expert relay but a
single behavior clone, beating the privileged lineup 2.5×. Its
scripted teacher steered to the visible gap *from wherever it was*,
so the student inherited robustness to entry states the RL experts
never trained on. Seam robustness was distilled, never trained —
that observation picked the road for everything below.

## The climb: five lineups, each built from the last one's failure histogram

The suite reports per-stage-type conditional success, so every
failure names its stage. Each lineup below changed exactly one thing,
pre-registered, and the next lineup was designed from the previous
one's histogram.

**1. Course fine-tune — 0.48, and the killer is named.** PPO
fine-tuning the five-skill clone *on random courses themselves*
(the closed-loop law: train the component in the loop that feeds it)
repaired the seams almost entirely: doors 1.000, gap 1.000, moving
gap 0.848. But slalom fell to **0.500** — half of all deaths. This is
the fine-tune safety law from article 5's era, now at course scale:
fine-tuning repairs what reward can see and erodes the one skill
(the 40-decision chain) that reward search cannot relearn.

**2. Anchored course fine-tune — 0.39, and a protocol lesson.** A KL
anchor to the clone was supposed to keep the chain while the seams
healed. It half-worked — slalom +13 points, doors −15: the
repair/corrosion trade, visible in one histogram. It also taught us
an evaluation lesson the hard way: this lineup's n = 30 graduation
read 0.567, then n = 100 read 0.390. A friendly first block promoted
a mediocre lineup. **Graduation is judged on pooled n ≥ 60 now** —
the exam examines the examiner too.

**3. The flight-plan hybrid — 0.55.** If one network cannot hold all
five skills at course fidelity, stop demanding it. A mission plan
already knows the course composition (the same way it knows
waypoints), so it can hand each stage to a different artifact:
the course-fine-tuned generalist flies four stage types at 0.86–1.00
conditional, and the slalom clone takes the slalom slot. Composition
beat retention by 16 points — but slalom read 0.579 against its
native 0.967, the seam tax measured a second time on the one stage
type left.

**4. The hot-entry specialist — 0.62.** So collect the slalom data
*at real seams*: full courses flown by the teacher relay, keep only
slalom segments, and only from episodes that cleared the segment
(the filter matters — an earlier unfiltered pot silently taught
crashes too). A clone of hot segments raised the in-course slalom
conditional to 0.645. Better — and not enough.

**5. The big pot — 0.72, gate open.** The remaining gap was not
coverage but *fidelity*. A three-pillar chain is ~13 consecutive
decisions per stage; at 0.93 per-decision faithfulness the chain
arithmetic caps you near where we were stuck. One data doubling —
43,488 demonstrations, native chain-shape demos plus hot seam
entries, val accuracy 0.963 — moved the specialist past the
threshold the arithmetic demanded. The suite read **72/100. The
gate is open.**

The videos of record now committed in `docs/media/` come from
passing seed 110004: slalom → opening door → moving gap, three
stages, zero crashes, FPV and god view side by side.

## What the exam bought

Three laws, each measured at least twice on the way up:

- **The seam tax.** Composition is not concatenation; mid-flight
  entry states halve specialists trained on clean starts. Price the
  seams before pricing the skills.
- **Fidelity compounds.** A course is a product over ~40 decisions;
  0.93 vs 0.96 per-decision sounds like 3 points and is the
  difference between stuck and passed. Data volume, not architecture,
  was the lever.
- **Fine-tuning is a scalpel with recoil** — it repairs its diet and
  erodes what reward cannot relearn; anchors trade rather than
  cancel. The passing lineup avoids the dilemma by *composing*
  artifacts instead of merging them.

And one honest negative for symmetry: we spent five campaigns trying
to make the drone *classify* which obstacle it faces from cheap
onboard observation, so dispatch could be learned rather than
planned. All five failed; cold-start world identification at hover is
an open problem in this repo. The passing lineup does not classify —
the flight plan already knows the course, the way it knows the
waypoints. That ruling (plan-keyed dispatch is deployment-legal)
is what makes the hybrid a deployable answer rather than a
simulator trick.

The gate is now a standing exam, not a one-time stunt: any new skill
enters the pool through its unit campaign, and any new composition
mechanism faces the same 100 random courses. Real-hardware work is
unblocked by this gate — the first exam the whole catalog failed is
the one the pilot now passes on camera.

## Reproduce it

```bash
# the suite (n=100 random 3-stage courses) with the passing lineup
python -m eval.eval_integration --contender hybrid --suite 100

# the privileged ceiling relay (never a contender; arena pricing only)
python -m eval.eval_integration --contender ceiling --suite 30

# regenerate the climb chart and every gate figure
python -m eval.eval_results_figures --out docs/figures
```

Campaign journals with every pre-registration and verdict:
`experiments/integration_v1/journal.md`,
`experiments/integration_ft/journal.md`.

# The Seam Tax: The Teacher Always Drives Home

*Article 9 of a series on building a latent world model that fits in
512 KB. Article 8 was about the embedded budget and what quantization
kept and broke; this one is about a single number — a deployment gate
stuck at 72/100 — and the three campaigns it took to learn why the
obvious fix could never have worked, what the textbook cure actually
bought, and what the cure taught us about lineups that no single
experiment was designed to ask. Everything reruns from
[microdrone-world-model](https://github.com/csinghans/microdrone-world-model).*

---

> **The simple version.** Watching your driving instructor never teaches you how to recover after YOU drift out of lane — because the instructor never drifts. Our pilot kept dying at stage hand-offs, and better demonstrations couldn't fix it: a competent teacher steers back onto familiar roads within seconds, so the student's own mistakes never appear in the data. The cure — let the student drive while the teacher comments on every situation the student actually gets into — took the gate from 72 to 79.


## A gate is a chain, and chains die at the links

Our transit deployment gate flies 100 random three-stage courses —
gaps, doors, moving gaps, slalom runs, composed by seed — and the
lineup of record cleared 72. Dissecting its own 28 failures produced
the campaign's first real number: **24 of 28 (86 %) were seam
failures** — the pilot died not inside a stage but at the hand-off
INTO one. Sharpest of all: the slalom specialist failed **3 % of
stages it started cold and 26 % of stages it inherited mid-course** —
the same pillars, the same pilot, an ×8 penalty for arriving instead
of starting. Half its seam deaths came through one edge,
opening-door → slalom.

We call it the seam tax. Every number that follows is about who
actually charges it.

## The obvious fix, refuted on schedule

The obvious story: the specialist was distilled from demonstrations
that always BEGAN at a stage's canonical start, so mid-course entry
states are out of distribution — collect new demonstrations whose
entries match deployment, retrain, done. We pre-registered it, built
it properly — the deployed generalist flies the upstream stages, a
privileged oracle labels the slalom segments, **17,607
deployment-matched seam decisions** into the pot, fidelity floor held
at val 0.9658 — and the gate did not move a millimetre: graduation
pooled **0.725 vs the 0.75 bar, slalom seam 25.4 % vs the record's
26 %**. An earlier arm had already tried the mirror image — braking at
the hand-off to recreate the specialist's native near-still start —
and measured exactly null. Two eliminations, opposite directions:
neither recreating the entry the student trained on nor training on
the entries the student actually gets touches the seam.

## Measure the pilot, not the plan

So we stopped guessing and built a per-decision instrument: re-fly the
standing exam, and at every slalom decision record what the student
DID against what its teacher — a scripted weave oracle that is a pure
function of position against its gate ladder, so counterfactual
queries are exact — WOULD have done at the same state.

The instrument arrived over-credentialed. The re-fly reproduced the
gate of record **per-seed at 1.000** — the same 72, the same 72 —
after a full toolchain teardown and rebuild in between; and the
offline mirror of the student's observation pipeline reproduced its
executed actions at 1.0000. Then it read the lesion cleanly:

- cold slalom states: agreement **0.9523** (the pooled val meter,
  honest on its own distribution);
- seam-visited states: **0.8573** — the student leaves its teacher at
  3× the cold rate;
- on the stages that broke: **0.6667** — one decision in three,
  off-teacher;
- the entry window (first 12 decisions after hand-off): 0.7625,
  against 0.8845 once the trajectory settles;
- worst upstream: opening-door, 0.6875 — the failure map's worst edge,
  found again by a different instrument.

And the money read: the deployment-matched clone from the refuted fix,
scored offline on the SAME states, agreed at **0.8666** — seventeen
thousand matched demonstrations had bought less than one point where
it mattered.

That is covariate shift, and it explains both nulls at once. **The
teacher always drives home.** Start a demonstration anywhere you like
— within a few decisions a competent teacher has steered back onto
its own manifold, so teacher-flown data contains the entry states and
almost nothing after them. The states that kill the student are the
ones its OWN compounding errors produce, and no volume of
teacher-flown collection can contain them, because the teacher does
not make the student's mistakes.

## The cure was already in the room

The probe's instrumentation — student flies, teacher labels every
visited state counterfactually — IS the DAgger collector. Round one:
fly the deployed lineup on fresh courses, keep 7,289 labelled
student-visited decisions (a pre-registered floor refused the first
batch at 5,978 — floors exist to refuse), rebuild the pot, and the
slalom seam fell **30 % → 21.4 %**, formal 0.73: progress, short of
the pre-frozen 0.78 challenger bar, landing in the one interval we
had pre-authorized a second round for. Round two, canon aggregate —
the round-one student collects its own residual mistakes — and the
gate of record moved: **slalom conditional 0.814 → 0.917, seam
failures 12/40 → 4/42, formal 79/100, every per-type guard held.**
The ladder was frozen at two rounds before round one flew; it ended
there. The new pilot is published with its lineage; the 72 record
file stays in the tree as history.

## What the cure taught us — three laws we did not order

**Lineups are ABIs.** Chasing the next seam (moving-gap, the weakest
remaining stage), we swapped that slot's pilot for its solo champion
as a cheap probe. The champion bought nothing at moving-gap seams
(0.818 vs the generalist's 0.828 — and it degrades 10.5 points from
its own cold entries, so that wall is the task's random-phase
arrival, not the pilot). But downstream, **the slalom seam exploded
17.2 % → 43.8 %** — the DAgger-trained specialist had adapted to the
exit-state distribution of the exact lineup it trained under, and
changing any upstream pilot partially unwinds the adaptation.
Article 8 measured this law for latents (swap the encoder, the zoo
breaks, slalom 80 → 0); here it is again one level up, for
behaviour. Ordering law, now frozen in the ledger: fix upstreams
first, re-adapt downstream last, and price the re-adaptation into
any upstream change.

**Exam draws are not true rates.** The swap probe's collateral forced
us to pool every committed block per lineage, and the table is
humbling: the DAgger ladder's true, monotone effect is slalom seam
**34.6 % → 24.5 % → 17.2 %** — while the exam block happened to read
the final lineage at 9.5 %, a ~1.3σ friendly draw. The 79 stands as
the gate of record by protocol; planning arithmetic uses the truth
(~0.775–0.78 composite). One n=100 block is a draw, not a rate — the
same discipline that pools rechecks instead of replacing them.

**Fidelity is a meter, not the target.** Twice this campaign raised
the meter and flight refused to follow: the refuted fix lifted
seam-state agreement by less than a point (and success not at all),
and a final one-knob arm — upweighting the student-visited rows 3× in
the pot — lifted held-out student-manifold fidelity 0.918 → 0.926
while graduation fell to 88/120 and the seam got WORSE. The chain
flies mostly ON the teacher manifold; trading native fidelity for
student-manifold fidelity at the margin is a net loss exactly where
it counts. Unweighted DAgger aggregation was already at the flight
optimum. Canon earns its keep.

## Where it closed

The campaign past 79 closed by owner's call with the cheap knives
spent and every remaining arm priced: reinforcement learning from
success on the slalom residue, phase-randomized training for
moving-gap's two diseases (cold 0.902, seam 0.828) — the latter now
carrying the coupling law's surcharge, a downstream re-DAgger against
whatever new upstream it creates. Reaching the next challenger bar
(0.84) needs roughly +6.5 TRUE points, and honest arithmetic says
both arms must land to get there. The deployment threshold is 0.70;
the system flies at a true ~0.78 with nine points of margin, and the
findings — the seam tax's mechanism, the coupling law, the true-rate
table — are the assets we actually came for.

## Rerun the numbers

```bash
python -m eval.eval_integration --suite 100 --contender hybrid   # the 79 gate of record lineup
python -m eval.eval_seam_fidelity --capture                      # the R1 probe: fidelity at seam states
python -m eval.eval_integration --suite 100 --contender hybrid \
  --swap moving_gap=experiments/moving_gap_v2/artifacts/ppo_moving_gap_v2_K3.zip \
  --seed0 118000                                                 # the coupling-law discovery run
python -m scripts.build_bigpot_v2 --selftest                     # the DAgger pot builder
```

Bars, branch tables and every verdict, committed before the numbers:
`experiments/transit_gate_v2/journal.md` (the mechanism and the cure)
and `experiments/transit_gate_v3/journal.md` (the laws and the close).

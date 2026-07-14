# The Exchange Rate: How Much of a Measured Number Is Real?

*Article 12 of a series on building a latent world model that fits in
512 KB. Article 11 dissected one second and named the perception tax;
this one is about what happened NEXT to two numbers from that story —
a refuted 8.9 % that turned into six gate points, and a 3.4×
correlation that shrank to 1.7× the moment we intervened. Everything
reruns from
[microdrone-world-model](https://github.com/csinghans/microdrone-world-model).*

---

> **The simple version.** Gym members are healthier than non-members
> — look at any survey and the gap is huge. Does joining a gym CAUSE
> that gap? The only honest way to know is an experiment: take pairs
> of similar people, send one of each pair to the gym, and compare.
> When you do, the gap usually shrinks — membership helps, but only
> about half as much as the survey said, because healthy people were
> already the ones buying memberships. Correlations come with an
> exchange rate, and you don't know it until you intervene. This
> article measures that exchange rate twice on the same drone in the
> same week: once on a "failed" training result that was worth six
> points at the right exam, and once on a scary-looking 3.4× death
> multiplier that was really 1.7×.

## Part I — the refuted number that paid out

Article 11 ended with a reinforcement-learning arm refused by
four-tenths of one failure: 8.9 % moving-gap seam versus a frozen
8 % bar. The bar did not move, and the arm did not ship — but its
review said something careful: *adoption is deferred to the stack's
own registration, which will judge components by the stack's exam,
not by this arm's missed ambition.*

That registration ran. New frozen bars (pass ≥ 80 on the standing
100-course exam; every guard anchored to a pooled TRUE rate; the
swapped slot must beat its predecessor's 0.887 true conditional or
the whole exercise bought paper). The lineup with the RL arm in the
moving-gap seat scored **85/100** — all guards green, the swapped
slot at 0.9455. The deployment gate re-anchored 79 → 85, and a
follow-up read of the six-stage instrument moved 0.500 → 0.570 with
deep moving-gap failures HALVED, exactly the "student keeps half the
oracle's gain" arithmetic predicted.

Two ledger notes keep this honest. The 85 is a friendly draw (~+1σ)
of a true ~0.80–0.81 — the arm's pooled 120-course measurement is
the truth; the exam is the ceremony. And nothing about the original
refusal was wrong: the bar served ITS decision (don't ship under
this registration's claim), and the evidence outlived it. A number
that fails one judgment can be worth six points under another — if
and only if the second judgment is registered before the number is
read.

## Part II — the correlation that shrank

The six-stage read also named the next frontier: with moving-gap
half-cured, **slalom** became the largest failure type (16.2 %). A
free pass over the records found something arresting: WHO hands you
the baton predicts whether you die. Slalom stages entered after a
closing door failed at 9.7 %; after an opening door, **33.3 %** — a
3.4× multiplier, replicated on fresh blocks.

Every obvious carrier died under a probe:

- **Entry state?** Lateral velocity: flatly equal (the named
  suspect, refuted at 0.88×). Lateral offset: a real signature
  (z = 5) — but the WIDEST, FASTEST hand-offs (slalom-after-slalom)
  died least, and within a matched offset band the opening-door
  excess persisted at 3.2×. A marker, not a cause — the fourth time
  this campaign series has caught pose wearing that costume.
- **Where they die?** An instrument trap first: the composite
  judges crashes post-hoc by minimum clearance, so the LAST recorded
  row is not the death point (it lags by 38–173 ticks) — read
  naively, every death happens at the stage boundary, where the
  world is empty. Mapped correctly, deaths sit ON the fences, spread
  across all three, in every predecessor's case. Ordinary missed-gap
  weave failures — just MORE of them after an opening door. A rate
  effect, not a shape effect. And unlike the moving-gap flinch,
  dying slalom pilots are off the oracle's path THROUGHOUT the
  stage: this disease has no single terminal second.

So the effect was real, replicated, and carried by nothing we could
record. One intervention could settle whether it was a cause at all:
**fly the same course twice, changing only the predecessor's name.**
The composite draws each stage's geometry from exactly one RNG draw,
so swapping stage 0's name at the same seed leaves stage 1's slalom
bit-identical — same fences, same gaps, position and composition
frozen (a selftest proves the pairing assert has teeth).

301 paired courses later: after opening door 14.6 %, after door
8.6 %. **Ratio 1.69, McNemar z = 2.25, replicated across blocks
(1.71 / 1.67).** The hand-off tax is REAL — +6 points of death
caused by who hands off, with everything else bit-controlled. And it
is HALF of what the observational table claimed. The other half was
confound (depth mixing and friends) wearing a predecessor costume.

The carrier is still unidentified — it lives in something no probe
records, and the leading suspect is frame-level perception: what the
camera actually SEES in the seconds after an opening-door hand-off.
That is a named, unpriced open; the medicine, if any, waits for its
own registration.

## What two numbers taught

- **Correlations have an exchange rate, and you must measure it.**
  Our conditioned table said 3.4×; the paired intervention paid
  1.69×. Any table built by conditioning on live records — ours
  included — should be read with that haircut in mind until an
  intervention prices it.
- **Bars are for decisions; evidence outlives them.** The same
  8.9 % was a refusal under one registration and +6 gate points
  under another. Neither judgment contradicts the other; they asked
  different questions, and both were frozen before their numbers.
- **Instruments lie in your favorite direction.** The boundary-death
  illusion (post-hoc crash judgment) handed us a beautiful, wrong
  story for one afternoon. The fix is mechanical: map crash time to
  the trajectory, never trust the last row.

## Rerun the numbers

```bash
python -m eval.eval_integration --suite 100 --contender hybrid --seed0 110000   # 85/100
python -m eval.eval_integration --suite 100 --contender hybrid --k 6 --seed0 140000  # 0.570
python -m eval.eval_pose_walk --probe --seed0 157000 \
  --out /tmp/pose.json                                        # entry states + predecessor
python -m eval.eval_seam_fidelity --capture --collect-rows --course-k 6 \
  --seed0 140000 --out-json /tmp/p2.json --out-npz /tmp/p2.npz  # per-tick anatomy
python -m eval.eval_pred_ab --pairs 160                       # the paired A/B
```

Bars, branch tables and every verdict, committed before the numbers:
`experiments/stack_registration_v1/` (the adoption),
`experiments/slalom_depth_v1/` (the exchange rate).

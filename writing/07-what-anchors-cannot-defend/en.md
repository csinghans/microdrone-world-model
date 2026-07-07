# What a KL Anchor Cannot Defend

*Article 7 of a series on building a latent world model that fits in
512 KB. Article 6 chained five skills into one pilot; this one is
about keeping skills alive while you improve them — the fine-tune
safety law, six measured clauses, one crowned throne and one honestly
unclaimed one. Everything reruns from
[microdrone-world-model](https://github.com/csinghans/microdrone-world-model).*

---

## The problem: repair without erasure

Behavior cloning gave us a five-skill pilot in one 400 KB network.
Two of its skills were weak (gap 0.70, moving-gap 0.43 against bars
of 0.75 and 0.70), so the obvious move was PPO fine-tuning. The
obvious move failed in an instructive way: at EVERY dose from 25k to
450k steps, the weak skills healed and the one RL-unlearnable skill
(a 40-decision slalom chain) died — dead inside 25k steps, faster
than the repair completed. Early stopping cannot save what erodes
first. Re-optimization toward RL's own attractor begins immediately.

The standard fix is a KL anchor: penalize divergence from a frozen
copy of the prior on every training state. At a constant coefficient
of 1.0 it decoupled for real — chain intact at 0.933, gap repaired
past its bar — but moving-gap stayed at 0.43. The repair it needed
was simply farther than a 1.0-radius ball allows. A constant anchor
TRADES: pick a coefficient, pick which skill you lose.

## Lesson 1: schedules buy what constants trade

The dial campaign ran two arms against the same three bars. Constant
kl = 0.3: chain 0.833, gap 0.933, moving-gap 0.567 — one bar short,
and it pays the same chain tax as the arm that wins. **A linear
schedule, 1.0 → 0.1 over the run: chain 0.833, gap 1.000, moving-gap
0.800 — all three bars.** Early tightness carries the fragile skill
through the period when re-optimization pressure is fiercest (the
dose curve had already measured that corrosion starts immediately);
late freedom finishes the repair the tight ball measurably could not
reach. The scheduled artifact went on to take the corridor-slalom-v2
throne — vacant through eleven sittings, five RL knob families and
one distillation wall — at a pooled 84/120 = 0.700, exact equality,
all guards green. We publish the zero margin as plainly as the crown.

## Lesson 2: anchors protect only where the mass goes

The first promotion attempt died on a guard nobody had measured
during training: the fast-solo cell at double speed. The prior flew
it at 3 % crash; the anchored fine-tune flew it at **31.7 %** — a
10x corrosion straight through a kl-1.0 anchor. The mechanism is
embarrassingly simple once measured: the KL term is computed on
rollout states, and that slice carried ~4 % of rollout mass.
Protection proportional to visitation is no protection. One knob
later — `edge_bias`, which draws half the training episodes from the
fast end of the envelope — the slice's mass rose ~6x and the
corrosion vanished: 31.7 % → 5.0 %, with the fattest clearance
margin on the gate. **Clause five: anchor pressure is mass-weighted.
Thin slices corrode almost as if the fine-tune were naked.**

## Lesson 3: anchors defend against drift, not reward

Then we pointed the crown recipe at the dodgeball throne, where the
target behavior is *hold the station box while dodging*. The pot
clone held station at every ball speed. The schedule-anchored
fine-tune erased station-keeping to **0.000 at all four speeds** —
while an explicit station reward was paying for the box the whole
time, and the anchor was supposedly guarding the prior that held it.

What killed it is not drift. Five of eight diet worlds pay forward
progress; their gradient majority actively opposes staying in a box,
and the anchor's late freedom ratifies the vote exactly when it
consolidates. **Clause six: anchors defend against drift — behavior
reward is neutral about — not against behavior reward opposes.** The
slalom chain survived the same recipe because nothing in that diet's
reward opposed weaving.

Per-group coefficients (pin the ball-state anchor at 1.0, let
transit states keep the schedule) defend it in exact proportion:
ball-state success is monotone in the ball coefficient — 0.000 under
the global schedule, 0.2-0.4 at a 0.5 floor, 0.33-0.55 pinned. But
the pin strictly dominates the floor on every cell, which names the
wall: freedom on ball states buys erosion, never repair, because
**the behavior that must be defended and the behavior that must
improve live on the same states**. We then re-anchored ball states
to the scripted TEACHER itself (a shadow oracle labels every rollout
row; cross-entropy to a deterministic teacher is exactly the KL) —
and the pre-registered kill condition fired by its letter: the
frozen headline tied the pin at 21/60 exactly. The margins moved
(crashes fell 5x; the fastest cell crossed its bar; a guard went
green for the first time) — recorded, not litigated. The dodge
throne stays unclaimed, priced from five directions.

## The law, in six clauses

Fine-tuning a multi-skill prior: (1) repairs skills inside its diet;
(2) corrodes skills outside it; (3) erases RL-unlearnable skills
even inside it — corrosion outruns repair; (4) a strong-but-imperfect
prior can land a basin worse than from-scratch; (5) anchor
protection is mass-weighted — thin slices corrode as if naked;
(6) anchors defend against drift, not reward — and per-group
pinning buys defense at the price of repair when both live on the
same states.

Every clause is a measured campaign, not a belief. Three of them
were bought by failed crown attempts — which is what failed attempts
are for.

## Reproduce it

```bash
# the dial: constant vs schedule (the crown arm)
python -m scripts.distill --finetune <BC2.zip> --steps 450000 \
  --world slalom3_fixed,gap,moving_gap,classic,solo \
  --anchor 1.0 --anchor-end 0.1 --ft-edge-bias --out sched.zip

# per-group pinning / DAgger-anchor (the dodge arms)
...  --anchor-ball-end 1.0      # pin the ball group
...  --anchor-dagger-ball 1.0   # shadow-teacher CE on ball rows

# the exams
python -m eval.eval_policy_cells --zip sched.zip \
  --cells experiments/conservative_ft/index_cells.json \
  --skill corridor-slalom-v2
```

Campaign journals: `experiments/conservative_ft/`,
`experiments/anchor_dial/`, `experiments/slalom_v2_promotion/`,
`experiments/dodge_crown/`.

# The Flinch: Anatomy of One Second

*Article 11 of a series on building a latent world model that fits in
512 KB. Article 9 followed a deployment gate from 72 to 79; this one
follows a single SECOND — the moment a drone approaching a moving gap
turns away from a slot it could have threaded — through a six-suspect
murder investigation, a failed apprenticeship, and the naming of a
tax. Everything reruns from
[microdrone-world-model](https://github.com/csinghans/microdrone-world-model).*

---

> **The simple version.** Merging onto a highway, a nervous driver
> sometimes brakes at exactly the moment they should commit — and the
> gap they could have taken closes. Our drone does the same thing at
> moving gaps, and this is the story of catching that flinch in the
> act, proving the gap was takeable, and then discovering why the
> skill of NOT flinching is so hard to teach: the instructor knows the
> moment by seeing things the student's mirrors cannot resolve. You
> can execute every other suspect, clone the teacher's hands, reward
> raw success — and a stubborn residue remains, with a name: the
> perception tax.

## Act I — the investigation

We doubled the integration course from three stages to six and asked
one question: what does the deployed system score? **0.500** — below
the 0.55–0.65 that chain arithmetic predicted, and the dissection
found the excess concentrated in one place: seam failure rates RISING
with position, 3.2 % at the first hand-off to 20.6 % at the fifth.
Something compounded with depth.

Six suspects were executed in order, each by a pre-registered probe or
intervention: **entry pose** (we actively re-centred the aircraft at
every boundary — pose tightened to spec, deaths did not move a
decimal); **rendezvous displacement** (my own favourite theory — the
composite lazy-steps its stages and the instrument shot it);
**an accidental bypass** (audited, zero); **entry conditions**
(measured flat at every depth and non-predictive); **survivor
composition** (the upstream mix barely changes); **the controller's
time accumulators** (reset at every boundary — the gradient stood).
Six executions, no conviction.

What DID hold: the per-tick trajectories showed the dying pilots track
the moving slot BETTER than survivors through mid-approach, then turn
the wrong way in the terminal second — **0.90 wrong-way share in the
last twelve decisions**. And a privileged oracle settled causality:
force commitment in the final metre and the deaths vanish — deep-seam
failures **27 % → 4.2 %**, the whole six-stage composite **0.500 →
0.610**. One second of one stage type was worth eleven points. The
flinch was a MISTAKE, not a surrender: the slots were takeable all
along.

## Act II — the apprenticeship fails

The oracle cheats — it reads the pillars' coordinates. A deployable
pilot has a camera. So we ran the house playbook: let the cheating
teacher fly four hundred courses, record only what the student
legitimately sees and what was done, and clone the behavior.

The pot's own quality floor refused it, twice. The fit meter told a
precise story: the approach region cloned at 0.948, **the terminal
second at 0.856** — and the confusion structure was a razor.
Direction errors: **one in a hundred and four.** The student knows
exactly WHERE the slot is. What it cannot learn is WHEN: the teacher's
rule fires on a ±2 cm boundary around a moving slot, so the labels
FLICKER — veer, forward, veer — faster than any visual estimate can
resolve. We tried smoothing the teacher with commit-hysteresis, and it
backfired instructively: the smoother oracle flies BETTER (+8 on its
own missions), but its labels become history-dependent — the same
picture now means different things depending on the teacher's hidden
state — which is strictly harder to clone. **The disease was the
teaching, not the student.**

Flown anyway (with the fit floor honestly re-registered and every
flight bar untouched), the clone captured HALF the oracle's gain:
seam failures 17.2 % → 11.1 %, against a frozen ≤ 8 %. Real, and not
enough.

## Act III — the tax gets named

Reinforcement learning needs no consistent labels — only outcomes.
Thread-and-survive pays; flinching does not; the policy may place its
commit boundary wherever its own perception CAN resolve one. We
warm-started the clone (it knows WHERE) and fine-tuned with the
repo's crowned recipe — a KL anchor scheduled 1.0 → 0.1 over 450k
steps, the leash that starts tight and lets out.

Pooled over 120 fresh courses: the best graduation composite this
line has ever flown (0.808), no damage to any teammate, and the
primary read landed at **8.9 % versus the frozen 8 % — refuted by
four-tenths of one failure.** No bar moved. But the review the
refutation triggered had been pre-named, and its verdict is the
article's point: two independent, deployment-legal methods converged
— BC at 11.1 %, RL at 8.9 % — against a privileged ceiling of ~4 %.
The residue is not incompetence and not bad luck. **It is the
perception tax: the difference between what the oracle reads off the
simulator and what a 64×64 camera can resolve about a moving slot in
the final metre.** The frozen target had assumed a student could
capture three-quarters of the oracle's gain; reality priced it at
47–63 %.

## What one second taught

- **Intervention beats observation.** Correlations named three wrong
  mechanisms; two forced interventions (re-centre the pose, force the
  commit) settled what observation could not.
- **A skill can be unteachable for reasons that are nobody's fault.**
  The lesson "commit NOW" cannot be expressed in the student's
  senses; no volume of demonstration fixes that, and reward-only
  learning recovers exactly as much as perception permits.
- **Bars are for decisions; evidence outlives them.** The RL arm
  missed its bar by 0.4 of a failure and does not ship — but its
  measured value is banked, and the stack that eventually attacks the
  next gate will judge it by ITS exam. Meanwhile the guard-anchor
  lesson (freeze baselines from pooled true rates, never one exam's
  friendly draw) bit three times this fortnight before becoming a
  standing rule. The ledger is the teacher.

## Rerun the numbers

```bash
python -m eval.eval_integration --suite 100 --contender hybrid --k 6 --seed0 140000
python -m eval.eval_gap_phase --analyze                     # the terminal wrong-way turn
python -m eval.eval_integration --suite 100 --contender hybrid --k 6 \
  --seed0 140000 --thread-commit                            # the oracle: the flinch was a mistake
python -m scripts.build_mgap_commit --selftest              # the apprenticeship pot
```

Bars, branch tables and every verdict, committed before the numbers:
`experiments/integration_k6_v1/` (the investigation),
`experiments/terminal_commit_v1/` (the apprenticeship),
`experiments/mgap_rl_v1/` (the tax).

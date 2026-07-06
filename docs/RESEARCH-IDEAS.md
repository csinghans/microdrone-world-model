# Research ideas — a graded backlog anyone can pick up

Each entry: difficulty, expected cost, a hypothesis sketch (falsifiable
— being wrong is a finding), the conventions to reuse, and what "done"
looks like. Claim one by opening a campaign branch/PR whose skill
docstring carries the pre-registration. Newcomers: do the
[ONBOARDING](ONBOARDING.md) hour first; ★ ideas are deliberately sized
as first campaigns.

## ★ good first campaigns

### ~~opening-door (price hesitation)~~ — DONE 2026-07-05
Consumed as written (`skills/opening_door`,
`experiments/opening_door/journal.md`): capability yes (70/60 % with
visible waiting — PPO discovered hold-then-thread; the mgap champion
even cleared @1.0 zero-shot), promotion no (the perennial fast-solo
guard, 13 % vs ≤10 % at n=60). Two exported findings: froze = 0 across
*both* door arenas (policies charge, they don't hesitate), and the
sweep@2.0 characterization below is now the **prerequisite** for ever
adjudicating that guard again.

### ~~sweep@2.0 noise characterization~~ — DONE 2026-07-05
Consumed (`experiments/sweep2_noise/journal.md`): the cell is **honest
binomial** (dispersion 1.12, bootstrap p 0.25) — its historical chaos
was plain sampling noise at inadequate n (±8.3 pt at n=30, ±5.9 at
n=60). Inheritance: the per-n CI table; bars on this cell judged at
pooled n ≥ 200 or with explicit margins; and a pending protocol
proposal — **rechecks should pool, not replace** (the study caught the
replacement-style recheck re-rolling an opening-door PASS into the one
bad block in ten). The opening-door K3 title question now has a
legitimate path: a fresh pre-registered promotion gate at pooled n ≥ 200.

### ~~corridor-slalom (sustained weaving)~~ — CLOSED 2026-07-05, honest negative
No knob passed any target (best 10 % vs a 70 % bar): **the first
reversal is the wall** — the mgap champion dies at gate two zero-shot,
training pushes penetration (chain_break 2.17, weave_frac 0.85) but
joint success stays ≤10 %, and the double-share knob broke the mgap
guard. Exported lesson: pre-register a **scripted feasibility probe**
that prices an arena's physical ceiling BEFORE freezing bars (the
arena-side twin of the instrument lesson). The chaining question stays
open — see slalom v2 below.

### ~~slalom v2, feasibility-first~~ — CLOSED 2026-07-05, honest negative (structural)
The probe worked exactly as designed (`experiments/slalom_feasibility/`:
oracle ceiling 0.97 at v1's own spacing — v1's cruise verdict
re-attributed to capability, its speed bars to the arena), and the v2
campaign then failed its one priced target three ways
(`experiments/corridor_slalom_v2/`): fixed-spacing and budget
hypotheses both refuted, per-gate competence every time, full chains
~never. **Left standing: the observation-bottleneck hypothesis** — gate
period 0.875 s > the k=32 horizon (0.67 s); the camera sees gate k+1,
the collision-probability observation cannot represent it. See the
horizon campaign below.

### ~~the horizon campaign~~ — CLOSED 2026-07-06, hypothesis REFUTED
The signature fired on the refutation branch
(`experiments/horizon/journal.md`): a k=48 stack (1.0 s > the 0.875 s
gate period, observation widened to 10 probs/candidate) left
chain_break_at inside the k=32 baseline band with success ~0.
**Observability was not the wall.** The slalom arc is now fully priced:
arena flyable (0.97), per-gate competence learnable, and the chain
survives diet, budget, fixed rhythm AND observation horizon. Live
suspects moved off the model axis entirely — see below.

### ~~the chain-learning campaign~~ — CLOSED 2026-07-06, REFUTED (the fifth elimination)
The 2x2 factorial (per-gate reward x graded diet, pinned on v2 K1)
left the whole grid inside the baseline chain_break band
(`experiments/chain_learning/journal.md`): proximal gate pay, easier
chains in the diet, and their combination all move nothing. Secondary
finding worth stealing: the axes compose on GUARDS — K3 flew a 9-world
diet all-green where K1 alone broke mgap (dilution's ninth sighting).
The slalom arc now counts five eliminations: diet, budget, rhythm,
horizon, reward/credit-at-this-altitude.

### the chain-algorithm campaign (algorithm-class, deep water) ★★★
What survives five eliminations is the algorithm itself. Candidate
knobs, one per gate, each needing its own pre-registered signature:
**policy memory** (RecurrentPPO — the repo's LSTM lost 5x on transit
tasks, but chaining is the first task where a reversal must be *held
across* a gate; the old negatives don't price this shape), **PPO's
n_steps/GAE horizon** (the advantage window vs the ~2.6 s chain), or
an **algorithm swap**. Exam: slalom-v2 verbatim, sixth time. The bar
for opening this: argue in the pre-registration why the chosen knob's
mechanism differs from all five eliminated ones.

### ~~duel timelines (tooling, no training)~~ — DONE 2026-07-05
Consumed: `eval_duel_plots --timelines` renders, per duel cell, an
outcome grid (which courses kill whom) + a crossing-time strip (when
each contender commits, coloured by how it ended). Applied to BOTH door
campaigns' journals; in the opening-door figures, K3's wait is a
visible rightward shift and hard-course clustering (seeds ~14-17) is
legible. Renderer is pure and selftested; timelines re-fly cells for
per-episode data (diagnostic view, not the gate record).

## ★★ real campaigns

### dodgeball — station defense (a NEW task family) — campaign pre-registered 2026-07-06
The catalog's first non-transit arena: hover at a station, dodge balls
thrown head-on. The feasibility probe already priced the arena
(`experiments/dodgeball_feasibility/`: flyable at every speed, the
body's drift arithmetic binds — no strafe, no backward). The live
question is perception: the single-frame model is motion-blind, so the
policy's stacked history watching the probability ramp is the only
mechanism. Campaign pre-registered in `experiments/dodgeball/journal.md`
(K0 structural / K1 science / K2 conditional promotion); if refuted,
Tier-2 (strafe surgery, model-side motion) is priced there. *Done:* the
campaign closes with any verdict — support, partial, or an honest
perception negative.

### dense-speedrun (attack the known frontier, honestly)
Fly the dense world at factors 1.5-2.0. The dense floor (17-27 % at
cruise band) is the repo's stated open frontier and it has *survived*
grounding (λ two doses) and global calibration — so pre-register modest
bars and expect an honest partial. The value is the failure's *shape*
(where does it die: FOV edge? late re-plan?). Reuse `door_metrics`-style
outcome taxonomies. *Done:* a journal that sharpens the frontier's
mechanism map even if no bar passes.

### the λ multi-seed replication (instrument discipline, practiced)
v0.5's N1 measured single-seed dense AUC as a ~0.5-wide lottery. Run
grounding λ ∈ {0.1, 0.5} × 3 seeds each (six trainings, ~3 h) and
publish the *distribution* — the first properly-powered model-layer
comparison here. *Done:* per-λ mean±spread vs the control draw, and a
verdict on whether λ has any resolvable model-layer effect at all.

## ★★★ deep water

### predictor-side grounding (the N3 reserve, never played)
v0.5's mechanism story says the *frame-level* aux debased the warn
surface conditionally. Supervise polar occupancy from the *predicted
future* latents (ẑ_k vs time-extrapolated grids) instead — aligns the
aux with what the heads actually read. Needs training.py surgery +
fresh pre-registration; judge at flight gates only (model-layer AUC is
a weak instrument — see above). *Done:* the M1/M2 pair rerun with the
new aux placement.

### world_model knobs in the runner
`train_knob` currently rejects `kind="world_model"` — campaigns tune
policies only. Wire WM training (with `--out` + the model-swap protocol
from the M2 journal) into the runner so model-axis campaigns stop being
hand-run. *Done:* research --selftest covers a dry WM knob; one real
campaign uses it.

### conditional calibration
The heads over-report in dense geometry specifically while sitting
under-confident globally (head_calibration C0). A per-context correction
needs a context signal the flying drone actually has (its own stacked
history? the x-progress pin?). Retraining-class; pre-register against
the M2 flight bars. *Done:* dense crash parity with the champion, warn
ECE halved, or an honest negative closing this road too.

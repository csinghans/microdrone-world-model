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

### slalom v2, feasibility-first (the reopened chaining question)
Before any bar exists: fly a hand-scripted optimal weave (open-loop
oracle path) across candidate (dx, speed, off) grids to establish each
arena's physical ceiling; freeze the campaign's geometry where the
ceiling sits ≥90 %, THEN re-ask whether learned evasion chains. Reuses
the v1 scenario verbatim with recalibrated constants. *Done:* the
ceiling table + a campaign whose bars sit under a proven ceiling.

### ~~duel timelines (tooling, no training)~~ — DONE 2026-07-05
Consumed: `eval_duel_plots --timelines` renders, per duel cell, an
outcome grid (which courses kill whom) + a crossing-time strip (when
each contender commits, coloured by how it ended). Applied to BOTH door
campaigns' journals; in the opening-door figures, K3's wait is a
visible rightward shift and hard-course clustering (seeds ~14-17) is
legible. Renderer is pure and selftested; timelines re-fly cells for
per-episode data (diagnostic view, not the gate record).

## ★★ real campaigns

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

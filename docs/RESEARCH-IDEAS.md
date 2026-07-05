# Research ideas — a graded backlog anyone can pick up

Each entry: difficulty, expected cost, a hypothesis sketch (falsifiable
— being wrong is a finding), the conventions to reuse, and what "done"
looks like. Claim one by opening a campaign branch/PR whose skill
docstring carries the pre-registration. Newcomers: do the
[ONBOARDING](ONBOARDING.md) hour first; ★ ideas are deliberately sized
as first campaigns.

## ★ good first campaigns

### opening-door (price hesitation)
The closing-door duel measured that **nobody froze** — that arena
prices commitment errors only. The mirror scenario prices hesitation:
the fence's gap starts too narrow to fly and *opens* at 0.25-0.45 m/s;
an over-cautious policy wastes the episode waiting (or detours), an
over-eager one clips the still-narrow edges. Reuse `ClosingDoorFence`
almost verbatim (negative rate + start-narrow aiming), the
threaded/pinched/froze metrics (froze finally gets to fire), and the
duel knob pattern (`builtin:` contenders + the mgap champion).
*Cost:* zero-shot knobs are minutes; one training knob if no contender
clears. *Done:* the four-contender table + figures, and an answer to
"does the timing skill generalize to waiting?"

### corridor-slalom (sustained weaving)
Offset pillars forcing alternating dodges (left-right-left) — probes
whether evasion *chains* or each dodge resets the next one's setup.
Static scenario (no aiming math), `new_skill --kind static` covers most
of it. *Hypothesis:* the general champion chains 2 but not 4; an
edge-diet share fixes rhythm at speed. *Done:* success-vs-pillar-count
curve, per the standard bars.

### duel timelines (tooling, no training)
Extend `eval/eval_duel_plots.py` with a per-seed outcome timeline
(which seeds pinched vs froze, at what crossing time) — makes duel
tables debuggable at a glance. Pure matplotlib; selftest pattern
already in the file. *Done:* one new figure + selftest + used in the
next duel campaign's journal.

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

### sweep@2.0 noise characterization (cheap, high leverage)
The fast-solo cell bounced 27/22/8/17/17 across knobs. Fly ONE fixed
policy on it 10×60 seeds (pure eval, ~1 h) and publish its sampling
distribution. Every future bar on this cell inherits your error bars.
*Done:* a short journal + a recommended (n, bar-margin) pair.

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

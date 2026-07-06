# lambda-multiseed — the instrument-discipline debt, paid

## Pre-registration (2026-07-07, before any number exists)

v0.5's N1 measured single-seed dense AUC@32 as a ~0.5-wide lottery
(0.4705 vs 0.9504 on the same draw, training seed only) and the repo
has since treated single-seed model-layer AUC as weather. This
campaign runs the first properly powered model-layer comparison:

**Design (frozen):** one dataset draw (the M1 protocol verbatim:
--worlds hard --rollouts 96 --seed 0), then NINE trainings — three
arms × three training seeds {0,1,2}:
- control (no grounding aux)
- ground λ = 0.1
- ground λ = 0.5

80 epochs each, out-paths per arm/seed. Probe: eval_wm_checkpoint per
checkpoint (dense AUC@32 the headline; slices recorded). **Verdict
rule:** λ has a resolvable model-layer effect iff the arm means differ
by more than the pooled within-arm spread (a plain eyeball-t at n=3 —
this is instrument characterization, not a promotion). Either outcome
pays the debt: "resolvable at n=3" or "the lottery swamps λ even at
n=3, single-seed model AUC stays weather" (the standing instrument
note gets its proper footing).

Wall-clock: ~9 × 20-30 min, sequential, background.

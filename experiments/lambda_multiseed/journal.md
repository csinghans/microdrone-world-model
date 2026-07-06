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

## Verdict: NOT RESOLVABLE — the lottery swamps λ even at n=3 (2026-07-07)

Nine trainings landed (one frozen draw, three arms × seeds {0,1,2});
probe = eval_wm_checkpoint, headline = dense AUC@32.

| arm | s0 | s1 | s2 | mean | sd |
|---|---|---|---|---|---|
| control | 0.7511 | 1.0000 | 1.0000 | 0.9170 | 0.1437 |
| λ = 0.1 | 0.4705 | 0.9451 | 1.0000 | 0.8052 | 0.2912 |
| λ = 0.5 | 0.8175 | 0.8829 | 0.8755 | 0.8586 | 0.0358 |

**Frozen rule applied:** max arm-mean separation 0.112 < pooled
within-arm sd 0.189 → **no λ effect is resolvable from training-seed
weather at this power.** The instrument debt is paid in the other
currency: the noise floor of single-seed dense AUC@32 is now measured
— the CONTROL arm alone spans 0.75→1.00 on identical data.

**Reproduction sanity:** both s0 columns reproduce their historical
runs exactly (control 0.7511 = M1's control; λ0.5 0.8175 = M1's
grounded seed-0; λ0.1 0.4705 = the mechanism-era read). M1's
*seed-1* grounded number (0.9948) did NOT reproduce under this queue
(0.8829 here) — seed-adjacent nondeterminism is real at this scale;
one more reason arm means, not single runs, are the only readable
unit.

**The honest retro-read on M1 (v0.5.0):** M1 judged grounded
{0.8175, 0.9948} (mean 0.9062) against a SINGLE control seed
(0.7511) and passed by +0.105. This campaign prices the control arm's
own 3-seed mean at 0.9170 ± 0.14 — seed 0 was the control's WORST
draw, and the grounded mean sits *below* the powered control mean.
**M1's model-axis PASS does not survive a powered control.** This
dissolves the M1→M2 paradox (better model, worse flight): there was
likely no model-axis gain to cash. Consistent with C0 (conditional
miscalibration) and M2 (policy regression); the grounding arc's final
shape is now one sentence — *the polar-occupancy aux never bought a
resolvable model-axis gain at this data scale.* v0.5.0's record
stands as written (its era's rules, honestly applied); this entry is
the powered instrument reading, prospective from here.

**Instrument caveats (recorded, not litigated):** the dense slice
saturates (3/9 runs read exactly 1.0000 — ceiling compresses measured
spread, so true seed variance is if anything larger); veer val (n=20)
swings 0.40→1.00 across seeds — same lottery, smaller n. λ0.5 is the
tightest arm (sd 0.036 vs 0.144/0.291) — "λ0.5 stabilizes training"
is a legal HYPOTHESIS for a future pre-registration (needs ~n≥8/arm
at this noise floor), not a claim.

Cost: 9 trainings + 9 probes, ~35 min wall (background). Ledger
updated; the standing house rule — single-seed model-layer AUC is
weather, never evidence — now rests on a measured floor instead of an
anecdote.

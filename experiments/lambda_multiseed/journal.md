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

## Escalation pre-registration: the λ0.5-stabilizes hypothesis at n=8 (2026-07-07, before any number)

The n=3 verdict left one legal hypothesis: λ0.5's arm was the
tightest (sd 0.036 vs control 0.144). This escalation gives it the
power the verdict said it needs (n≥8/arm).

**Design (frozen):** the SAME frozen draw (output/wm_dataset.npz
verified untouched — sha256 prefix 2c3d0884fa96a343, mtime = the
original datagen), five NEW training seeds {3..7} for the control
and λ0.5 arms only (the hypothesis names those two), 80 epochs,
probes via eval_wm_checkpoint. Pooled n=8/arm with the existing
seeds {0,1,2}.

**Frozen verdict rule:** the hypothesis is SUPPORTED iff
Var(control) / Var(λ0.5) on dense AUC@32 ≥ F₀.₉₅(7,7) = 3.787 at
n=8/arm; otherwise NOT RESOLVABLE (there is no "refuted" here — a
ratio under the critical value at this n is absence of evidence,
recorded as such).

**Saturation caveat, pre-stated:** dense AUC@32 clips at 1.0000
(2/3 control reads did at n=3). The count of saturated reads per arm
is reported; if ≥ half the control arm saturates, the variance
comparison is confounded by the ceiling and the verdict line says
so. Secondary OBSERVATIONAL readout (no verdict power): the same
ratio on now-AUC, which does not saturate.

Cost: 10 trainings x ~3 min + 10 probes, ~45-60 min, &&-chained.

## ⚠ INSTRUMENT CORRECTION: the probe's split did not follow the training seed (2026-07-07)

**The flaw.** `eval_wm_checkpoint --seed` defaults to 0 and both this
campaign's probe passes omitted it. Models trained with `--seed N`
hold out a seed-N rollout split; graded on the seed-0 split, their
"val" rollouts overlap their TRAIN set — leakage. Every s1+ read in
the sections above is affected. Caught by the escalation run's
training printouts disagreeing with its probe reads; the sections
above stay as written (era rules; numbers never edited), this
section supersedes their numbers.

**Instrument rehabilitated, bit-exact.** Re-probed with matching
seeds: l05_s1 = **0.9948** (M1's historical seed-1 number, exact)
and l01_s1 = **0.9504** (N1's historical second number, exact).
Training was deterministic all along. **The "seed-adjacent
nondeterminism" note in the n=3 verdict is RETRACTED** — the
mismatch was split protocol, nothing else. The three 1.0000 reads
were leakage artifacts, not saturation; the saturation caveat is
moot. Hardening shipped: checkpoints now store their training seed
in meta; the probe reads it, REFUSES a contradicting --seed, and
warns loudly on legacy checkpoints.

**Every verdict re-derived on clean per-seed val reads:**

| read | leaked | clean |
|---|---|---|
| n=3 arm means (ctrl/λ.1/λ.5) | 0.917 / 0.805 / 0.859 | **0.878 / 0.772 / 0.822** |
| n=3 verdict | NOT RESOLVABLE | **NOT RESOLVABLE (survives)** — max sep 0.106 < pooled sd 0.193 |
| "λ0.5 tightest" (sd) | 0.036 | **0.170 — the observation was itself a leakage artifact** |
| n=8 var ratio ctrl/λ0.5 | (ungraded) | **0.96 → NOT RESOLVABLE; the stabilizer hypothesis dissolves** — equal variances, born of a leaked read, dead on clean ones |
| n=8 arm means | — | ctrl 0.8041 vs λ0.5 0.7688 (SE ≈ 0.054): indistinguishable |

**The M1 retro-read, recomputed.** The published supporting number
(powered control mean 0.917) was leaked; the clean powered control
is **0.8041 ± 0.153 (n=8)**. The mechanism sentence changes: not
"control's seed 0 was its worst draw" but "M1's grounded pair
(0.8175, 0.9948) were among the λ-arm's LUCKIEST draws — ranks #3
and #1 of its eight." The clean λ0.5 arm at full power means 0.7688
— nominally BELOW the control's 0.8041, difference ≈ 0.6 SE.
**The retro-read's conclusion SURVIVES, strengthened: no model-axis
gain is resolvable at any power measured; the M1→M2 paradox stays
dissolved.** What changes is only the arithmetic that carried it.

Cost of the correction: 16 re-probes (~10 min), one tool hardening,
and the reminder that instrument bugs do not respect how much you
liked the old number: two of today's numbers got WORSE for our own
published story (control mean 0.917→0.804) and one got better —
they land where they land.

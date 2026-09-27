# Moving-only intervention timing v1 — prospective model study

The all-world timing study and its three exploratory diagnostics are closed.
They are development evidence, not this study's exam or proof of a mechanism.
All-world immediate timing improved pooled moving left/right AUC but lost
dense-right AUC. The loss also exists in agreeing-label comparisons. This
study asks whether moving-specific data changes can preserve the moving
benefit without changing the nonmoving data recipe or losing guarded skills.

## Sole training knob and fixed development inputs

Control is the existing 276-course approach development corpus. Candidate
replaces **only complete moving-world rows** with their paired immediate
counterparts from the existing all-immediate corpus. Classic, dense and
room arrays remain exactly the control arrays. Both source corpora share
the same initial scenes, roles, speeds and the same 96-room block; verify
their existing receipts and exact row pairing before publication.

Both arms get six fresh, matched 80-epoch fits in total, seeds 0/1/2 and
the registered alternating order. Reuse no checkpoint from a closed study.
Keep the original splitter, architecture, losses, optimizer and augmentation.
No early stopping, model selection or seed selection on internal validation.
Changed eligible windows/steps/CF-now exposures in the moving rows are
consequences of the single timing-recipe knob, not a separate controlled
gradient intervention. Other worlds' data must remain byte-array identical.

Primary endpoint: the equal-weight mean of **moving left/right warn AUC@32**.
This is a new domain-specific question, not a revision of the closed four-cell
timing gate. Dense left/right remain separate guards at the same −0.02
tolerance. Both arms deliberately retain the known sparse approach-style
dense steering training support; this study does not claim to repair it.
Identical sparse nonmoving data is held fixed to test the moving-data change.
Final independent exam support, not internal validation, protects every
reported action/guard. No old result, threshold or NO-GO is reinterpreted.

## New common exam and preflight

Generate exactly 630 approach and 630 immediate transit courses, each with
its own new registered seed, plus 180 new room courses, length 160 / 64px.
Use world-balanced roles and isolated per-rollout RNG, no randomization.
The same fixed 1,440-course exam grades every checkpoint. Both timing blocks
are separate scene draws; the mixture is 1:1 by course count, not windows.
The old timing exam is never rescored in this study. Require no exact initial
scene fingerprint overlap with either development arm or that closed exam.
This plus distinct generator seeds is identity evidence, not proof of
deployment representativeness or formal statistical power.

Before any fit:

- New rendered/removed-body fixtures for all four worlds, plus nonblank
  corpus samples, must pass the unchanged pixel thresholds. Room generation
  keeps its established 0.6–1.0 randomized data-speed / omnidirectional-label
  recipe; it is not an Indoor Active Search flight evaluation.
- Both arms at all three training seeds: moving left/right each have ≥20
  windows per class from ≥3 courses per class; pooled warn labels in each
  of classic/dense/moving/room meet the same minima. Report all training/
  validation action and now counts, including unchanged dense deficits.
- Exact train/validation memberships match between arms and the original
  approach development splits. Nonmoving arrays, initial scene identities,
  passive moving courses and the complete paired replacement rows match.
- Exam: ≥100 windows per class from ≥10 courses per class for each pooled
  moving primary cell, each dense action guard, each transit forward action,
  each world pooled AUC and pooled danger-now. Apply the same minima to
  moving left/right **separately in each timing block**.
- Geometric veer probe: ≥40 frames / ≥10 courses in each transit world.

Support floors are prospective coverage requirements, not power or confidence
guarantees. If any fails, close INSUFFICIENT_SUPPORT without fits; no redraw,
added course, seed substitution or changed bar. Instrument errors stop with
original logs intact and can be repaired only without changing scientific
inputs or registration. A pass releases all six fits unconditionally, then
all six CPU scorings and the final report. Preserve every failed result.

## Performance bars

Across three matched seeds, primary mean improvement must be ≥+0.03 and
each seed's primary improvement strictly positive. For every seed:

- Each pooled moving left/right and dense left/right AUC delta ≥−0.02.
- Each moving left/right AUC delta in each timing block ≥−0.02. This prevents
  the within-condition decline previously hidden by a pooled action gain.
- Pooled classic/dense/moving/room and each transit forward AUC delta ≥−0.02.
- Pooled danger-now AUC delta ≥−0.02.
- Geometric ranking delta, pooled and each transit world, ≥−0.05.
- Architecture bills equal, analytic int8 total ≤512 KB and estimated latency
  ≤8 ms at the existing assumed 0.5 GMAC/s. No hardware/flight certification.

Any failed performance bar means NO-GO. No optional recheck, new seed,
inference on another exam, sample filtering or chosen checkpoint. GO would
permit only a separately registered flight study, never champion replacement
or a release tag. All nine locked artifacts are protected by hashes.

Report all point estimates and every guard. Add 2,000 paired whole-course
bootstrap draws for each fixed pair's two-action primary macro, stratified
by moving exam timing block. Draw all 210 courses per block, including those
without primary windows, using shared draws across models and actions.
Retain duplicate-course multiplicity; missing-class replicates are null and
counted, never replaced by chance AUC. Percentile intervals are descriptive
conditional on the checkpoint pair, not training-population uncertainty and
not additional gates. Record all seed deltas and their mean/range.

Freeze source/runtime/input hashes before generation. Each stage owns fresh
outputs, a complete log, actual exit status and immutable receipt; no silent
restart of an unfinished stage. No outcome reopens any closed experiment.

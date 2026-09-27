# Intervention timing v1 — prospective model comparison

Registered after the closed paired support pilot and split diagnostic, before
new corpus generation or any fit in this study. Those records are development
evidence; their verdicts, samples and bars remain unchanged.

## Question and intervention

Does moving nonpassive transit intervention onset from the usual 24–48-step
approach to step zero improve collision discrimination for lateral actions?
The primary endpoint is the equally weighted mean of four within-action
warn-ring AUCs at horizon 32: dense/moving × veer-left/veer-right. This avoids
allowing the much larger forward category to determine the steering result.
It is still a discrimination measure across scenes and speeds, not a direct
closed-loop steering or calibration test.

Reuse both immutable 180-course pilot corpora as development/training inputs.
Append the same newly generated 96-course room block to each. Both arms keep
the original splitter at seeds 0/1/2, 80 fixed epochs and identical architecture,
losses, optimizer and augmentation recipe. Final-epoch checkpoints only.
Timing is the sole varied recipe field. The changed eligible-window counts,
optimizer steps and CF/now sample exposures at fixed epochs are consequences
of that recipe; this study does not isolate label quality or gradient mass.
The internal validation metrics (including any widened training veer probe)
are descriptive only and cannot select epochs, seeds or models.

The closed split audit found adequate candidate training support but inadequate
internal validation support. It froze a diagnostic, not a model-performance
gate. This **new** registration explicitly replaces internal validation as
the decision exam with independently generated courses. It does not declare
the old validation partitions adequate. Control action deficits are the
condition under study, so they are retained and reported; requiring control
to repair them before comparison would remove the intended contrast.

## Common exam and support gate

Generate exactly 630 approach and 630 immediate transit courses with distinct
registered generator seeds, giving 420 courses per world, plus 180 room
courses. The two transit blocks are separate draws, not paired duplicates.
Use all 1,440 courses for every checkpoint. The timing mixture is fixed 1:1
by course count, not by eligible-window count or selected probe frames.
No per-timing performance endpoint is added after seeing scores.

Rendering fixtures must first show actual scene bodies and a pixel difference
from the removed-body scene. All corpus worlds also need nonblank sampled
pixels. Validate pilot pairing, exact room reuse, per-world role counts,
split membership and exact-scene fingerprint non-overlap with the exam.
Distinct seeds plus fingerprint checks are generation/identity evidence,
not proof that the simulator distribution represents real deployment.
The room generator keeps its established 0.6–1.0 randomized data speed and
omnidirectional clearance recipe in both arms. This is offline WM data,
not an Indoor Active Search flight eval; those still require speed 0.6.

Before **any** fit:

- Candidate training, each seed and each primary cell: at least 20 positive
  and 20 negative windows, each class from at least three distinct courses.
- Both arms' training partitions, each seed and all four worlds: the same
  20-window / three-course class minima for pooled warn AUC. Report complete
  all/train/validation action and now support for both arms without selecting
  a split. Transit memberships must match the closed split diagnostic.
- Exam, each primary cell, each transit forward action and each of the four
  pooled world AUCs: at least 100 windows of each class, each class from at
  least ten courses. Apply the same 100-frame / ten-course class minima to
  pooled danger-now support.
- Exam geometric veer probe: at least 40 frames from ten courses in **each**
  of classic/dense/moving. Room is outside this pillar-geometry probe.

These are prospective coverage floors chosen to avoid the observed zero/
singleton weaknesses. The larger fixed exam is motivated by the pilot's
sparse action/probe course support. It is not a formal power calculation
or a guaranteed precision level. Counts can overlap across actions/classes.
If any floor fails, close as **INSUFFICIENT_SUPPORT**, retain the first draw
and launch no fits. No added courses, replacement seeds or weaker thresholds.
Instrument/identity failures instead stop as harness errors with original
logs preserved; any repair must retain the exact scientific registration.

## Performance bars and uncertainty

After preflight passes, run all six fresh fits unconditionally in the frozen
alternating order, then score all six on CPU on the same exam. Primary mean
paired improvement across seeds must be at least +0.03; each seed's macro
improvement must be strictly positive. For **every** seed:

- No individual primary cell may fall by more than 0.02 AUC.
- Pooled warn AUC in classic/dense/moving/room and forward-only warn AUC in
  each transit world may fall by at most 0.02.
- Pooled danger-now AUC may fall by at most 0.02.
- Geometric veer accuracy, pooled and separately in every transit world,
  may fall by at most 0.05.
- Both architecture bills must match, total analytic int8 memory ≤512 KB,
  estimated decision time ≤8 ms at the existing assumed 0.5 GMAC/s.

Any failed bar is NO-GO. Support/identity/finite-metric failures cannot be
converted into a performance pass. The deployment bill is analytic, without
hardware timing, quantization parity or flight certification.

Report every cell and guard, all paired seed deltas and their mean/range.
Additionally compute 2,000 paired whole-course bootstrap draws for each
fixed pair's **primary macro delta**, stratified by dense/moving world and
timing block. Use the same course draw for both models and both actions
within a world, retaining all windows and duplicate-course multiplicity.
Sample all courses of each stratum, including those with no primary windows.
A replicate missing either class in any primary cell is undefined, counted
and omitted from the percentile calculation. Report valid/undefined counts;
never substitute AUC 0.5 for an undefined cell. Bootstrap intervals are
descriptive, do not change gates, and do not estimate training-population
uncertainty. There is no bootstrap requirement for the guard point estimates.

Source, registration, runtime, inputs and all nine locked artifact hashes
are bound before measurement. Each stage owns a fresh directory, complete
log and immutable receipt. Incomplete stages cannot silently rerun. A
support failure stops the queue; a GO only permits separately registering
a flight study. Never change the champions or tag a release here.

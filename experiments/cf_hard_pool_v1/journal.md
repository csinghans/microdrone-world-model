# cf_hard_pool_v1 — registered answerable-contrast sampler comparison

## Registration — 2026-09-14, before research fitting or exam generation

Question: does selecting actual answerable action contrast for the CF hard
pool improve action ranking without harming collision prediction? The
retrospective [support audit](../schedule_support_v1/journal.md) found that
11.83–13.01% of the balanced recipe's training hard pool was selected solely
because an unknown candidate label was zero-masked. Those frames may still
be useful for positive collision labels and danger-now; no benefit is assumed.

The only varied training knob is `cf_hard_pool`: `legacy_masked` compares
zero-masked vectors exactly as before; `answerable` requires both zero and
one among answerable candidates at the same horizon/ring. Both fall back
to the full frame pool if their hard pool is empty. Half-uniform/half-hard
sampling, batch sizes, loss weights and visibility masking stay unchanged.
The sampled frames also train danger-now, a downstream effect of this one
sampler choice. No executed-window reweighting or latent-centering knob.

Both arms use the same hashed, existing world_balanced corpus: 96 transit
and 96 room rollouts, length 120. The generator, action catalogs, per-seed
rollout splits and eligible executed windows are identical within each
pair. All six models are freshly fit for 80 epochs at seeds 0, 1 and 2 in
the alternating order in [registration.json](registration.json). Historical
schedule_layout_v1 controls/results remain closed; these are controls for
a different registered question, not replacement attempts at that NO-GO.
The default public sampler remains `legacy_masked` pending evidence.

Representation and optimizer: D64, four strips, one 64px frame, batch 64,
Adam 1e-3, existing EMA and [1,8] std-band, no augmentation, grounding or
temporal encoder. Collection speeds and room label definitions stay frozen
in the source corpus. No new trainable parameter or deployment computation.

A **new confirmation exam**, generated only after this registration, has
126 transit + 60 room rollouts of length 160 with distinct generation seeds.
Every model scores every course. The previously inspected holdout will not
choose this study's verdict. The training corpus has rendered-geometry
evidence; additionally run the scene-present/removed fixture for all four
worlds before generating the exam, observing moving at its centreline
crossing. Require 20 positive and 20 negative horizon-32 labels per world.
Insufficient instrument support stops the study without seed/sample fishing.

**Primary bar:** candidate-minus-control veer-ranking accuracy must improve
by at least **+.05 on average over the three training seeds**, with **no
seed regressing**. Nondecreasing permits parity when a control reaches the
accuracy ceiling. This probe directly tests action ranking, the CF hard
pool's intended contribution. Each model requires at least 20 eligible
probe frames from at least six independent exam rollouts; report both
counts, never equate frames with independent flights.

**Every-seed guards:** classic, dense, moving and room AUC@32 deltas must
each be at least −.02; pooled danger-now AUC delta at least −.02. Every
candidate must stay within 512 KB and have exactly its control's analytic
memory/MAC bill. All bars are immutable. Missing/nonfinite metrics or
insufficient support mean INVALID, not a numerical fallback pass. All
guarded comparisons use the common new exam, not internal validation.

Export aligned veer probe pairs, truth and correctness as well as collision
scores. Report per-seed paired, world-stratified rollout-bootstrap intervals
(2,000 resamples, seed 0) for AUC and veer, conditional on each fixed model
pair. These intervals are descriptive and not gating; the three-draw
mean/range is not a training-population confidence interval. No optional
rechecks, seed replacements, early stopping or sample expansion.

GO permits registering a later closed-loop study, not changing a champion.
Report the full analytic int8 bill and assumed-throughput latency estimate
separately from any hardware claim. Indoor flight gates, if later registered,
must use the track's robust speed 0.6. This is currently an offline study.

## Execution

Run `bash experiments/cf_hard_pool_v1/run.sh` in the project environment.
The shared paired-study runner freezes sources/environment, the training
corpus SHA and both protected WMs; locks concurrent runs; records immutable
stage receipts; and stops on incomplete outputs. Inspect full logs and
processes before resuming. All large outputs belong under
`output/cf_hard_pool_v1/`; no source corpus or champion is overwritten.

## Harness checks before research execution — 2026-09-14

The pure sampler selftest proves exact default-mask equivalence and that
unknown labels cannot change the answerable pool. Reconciliation against
the independent retrospective audit matches every frame mask: training
hard-pool sizes at seeds 0/1/2 are 2,562/2,590/2,613 for legacy_masked and
2,259/2,253/2,289 for answerable. The registered training-data stage records
these counts, and each fit must match its pool receipt before checkpointing.

The self-contained checkpoint test fit both modes for two epochs on eight
fresh toy rollouts, using only `*_selftest.pth` destinations. It passed
recipe persistence, unchanged split sizes, default train/probe AUC and
label-count agreement, and seed-invariant exam/probe exports. This tests
wiring, not the research hypothesis. The classless-AUC warning was exercised.
Run `python -m eval.eval_wm_checkpoint --selftest` to reproduce the checks.

The paired-bootstrap selftest keeps duplicated within-course frames
together. The shared-runner selftest rejects per-seed guard failures,
negative ranking draws hidden by a good mean, insufficient probe support,
classless/nonfinite metrics and incomplete/duplicate seed sets. It also
checks stage receipts cannot overwrite or silently repeat a measurement.

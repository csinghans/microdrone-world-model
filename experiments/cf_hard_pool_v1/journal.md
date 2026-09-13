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

## Launch and instrument evidence — 2026-09-14

The background queue started from committed registration/source revision
`19106b2`. Its PID and timestamp are saved in
`output/cf_hard_pool_v1/queue.json`; inspect the live process before any
resume, since PIDs are not permanent identities. The immutable
[manifest](manifest.json) freezes code, runtime, training corpus and both WMs.

All four scene-present/removed checks pass, with images inspected. The
moving fixture observes its centreline crossing at step 155. The existing
training corpus passes role/label coverage and both hard pools match the
audited counts. The new exam contains **186 courses / 12,147 overlapping
valid windows**, with both label classes in every world:

| World | Courses | Positive @32 | Negative @32 |
|---|---:|---:|---:|
| classic | 42 | 1,060 | 1,881 |
| dense | 42 | 2,469 | 442 |
| moving | 42 | 1,376 | 1,520 |
| room | 60 | 1,573 | 1,826 |

All three transit worlds have 14 passive courses; classic has 21 clear
courses. [The exam receipt](records/holdout.json) records dataset SHA-256
`16986ffa08f24bac9ca3f5775ed8f8fa419aa5eb54851f123b1dd7f0416ebf53`.
The four preflight receipts and their files have been hash-verified.
The first control fit has started; this entry contains no research-model
evaluation or verdict. All six draws and their common-exam evaluations
remain required before the study is interpreted.

## Final result — 2026-09-14: NO-GO

All 17 stages completed once. The full queue log ends with
`CF-HARD-POOL-STUDY COMPLETE`, `CF-HARD-POOL-DONE` and
`CF-HARD-POOL-EXIT=0`; no worker remained at the completion check. Before
adding report code, all frozen source/runtime/input/protected hashes and
every stage output were verified. [Verification receipt](verification.json).
All nine locked artifacts still match their lock hashes.

| Training seed | Control veer | Answerable veer | Delta |
|---|---:|---:|---:|
| 0 | 0.8510 | 0.8990 | +0.0481 |
| 1 | 0.8606 | 0.7692 | −0.0913 |
| 2 | 0.5817 | 0.7452 | +0.1635 |

Mean delta +0.0401 misses the immutable +0.0500 primary bar, and seed 1
violates the per-seed nondecrease requirement. Seed 0 fails classic AUC
(−0.0428), moving (−0.0742), room (−0.0787) and danger-now (−0.0475), each
against −0.0200. Other per-seed AUC guards pass. Every model has the same
137.290039 KB analytic int8 bill and 3,856,768 MACs/decision; estimated
7.713536 ms assumes 0.5 GMAC/s, with no hardware or flight certification.

All six ranking readings use 208 eligible frames from 23 independent
courses. The [paired intervals and all guards](summary.md) condition on
the fixed checkpoints; the three training draws do not provide a
training-population confidence interval. No mean or favorable seed can
erase a failed guard. This tested recipe does not establish the joint
improvement claimed in registration, and the default stays `legacy_masked`.

Post-hoc support accounting (no new scoring or changed eligibility) checks
all six hashed exports: classic 39 frames / six courses; dense 145 / 15;
moving 24 / two; room zero. The pooled probe meets its frozen support bar,
but its dense-heavy composition limits broader interpretation. The room
oracle is unanswerable for pillar-kinematic CF/veer labels, while room's
executed collision AUC remains separately guarded on 60 exam courses.
Reproduce with `python -m eval.eval_cf_sampler_report --audit-probe-support`;
an existing support record is compared, never overwritten.

The fit receipts confirm identical executed-window counts and splits within
each pair, plus the intended hard-pool membership. Every model beats its own
no-op latent MSE@32, yet this is insufficient to certify ranking or collision
quality across the exam. Large endpoint latent magnitude is an association,
not an established cause of failure. No historical result was edited, no
research draw repeated, no exam expanded and no model promoted.

The completed-study summary and figure are generated solely from saved JSON
by `python -m eval.eval_cf_sampler_report`. Its selftest verifies receipt
hashes, individual score/fit identity, one-knob metadata, equal support and
all original decisions; malformed course counts and summaries are rejected.
This reporting code was added after the frozen training queue completed.

Validation: whole-repository Black/Ruff passed for 158 Python files, along
with CF report, historical schedule report, paired-runner and support-export
checks. The report selftest also passed in an isolated directory containing
only its Python modules and JSON receipts, with no `output/` directory.
The six-panel figure was visually inspected. These are local checks;
no remote push, CI dispatch or release tagging was performed.

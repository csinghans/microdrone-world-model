# Research evidence audit — 2026-09-13

This audit improves the measurement machinery and narrows unsupported
explanations. It does not change a frozen bar, historical measurement,
campaign verdict or deployed champion. Numerical examples in the regression
tests are synthetic instrument checks, not flight results.

## Measurement fixes

### Equal scores must receive half credit in AUC

The previous rank calculation gave distinct ranks to tied scores after
concatenating positive and negative examples. With labels `[1,1,0,0]`,
the following checks reproduce the error:

| scores | previous implementation | pairwise definition / repaired metric |
|---|---:|---:|
| `[0.5,0.5,0.5,0.5]` | 0.0 | 0.5 |
| `[0.9,0.5,0.5,0.1]` | 0.75 | 0.875 |

`world_model.metrics.roc_auc` assigns average ranks, matching a direct
positive–negative comparison that awards half a point for a tie. It is
shared by training validation and the four indoor detection/probe wrappers.
Nonfinite scores/labels and mismatched shapes fail loudly, so a numerically
invalid predictor cannot acquire a plausible AUC through sorting alone.
Existing missing-class behavior is preserved: the core returns 0.5, while
the indoor wrappers return `nan`. The new comparison report instead marks
undefined AUC as missing and counts undefined bootstrap draws explicitly.

The method is identified as `mann_whitney_average_ranks_v2` in new score
exports. Method references: [SciPy average ranks](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.rankdata.html)
and [Mann–Whitney rank-sum relation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.mannwhitneyu.html).

Reproduce: `python -m world_model.metrics` and
`python -m world_model.losses`. Saturated/quantized outputs can contain
ties, but the size of the historical impact has **not** been established
by these fixtures. Preserve old records and audit saved score arrays in a
new diagnostic before making any numerical correction to published claims.

The subsequently registered [metric_integrity_v1 diagnostic](../experiments/metric_integrity_v1/journal.md)
scored both locked float WMs on a common 60-rollout dataset. Neither had
cross-class ties among its 4,083 valid samples; the corrected-minus-legacy
AUC difference was exactly zero in pooled and per-world rows. This negative
is limited to those models and that recorded diet, not the unavailable
96-pixel or quantized historical outputs.

### Gate verdicts and their evidence must agree

`python -m scripts.research_selftest` exercises these failure cases in
temporary repositories and synthetic cells:

- A later criterion could trigger a pooled recheck after an earlier
  criterion had already passed. The fixture previously reported success
  1.0 despite a final pooled success of 0.4. Rechecks are now selected from
  initial readings, then every criterion reads the final pooled cell.
  Both initial and fresh blocks remain available.
- A gate commit could include unrelated staged files and omit the current
  `results.json`. Results now persist before journal/Git writes; the commit
  includes only the campaign directory. JSON records the parent revision,
  since a commit cannot contain its own hash.
- Resume previously remeasured recorded knob IDs and replaced their blocks.
  Recorded IDs now remain immutable, `run` skips them, and duplicate `step`
  calls fail before training. An advisory lock rejects simultaneous writers.
- New records freeze criterion roles as well as bars. Historical records
  that omitted roles remain readable without rewriting them.
- Real gates require a non-tiny WM. Missing dry-test models live under the
  selftest artifact directory. Both protected WM files are hash-checked
  around the gate, and the evaluation WM receives a full SHA-256 record.

Atomic JSON replacement preserves earlier evidence on serialization failure.
If a journal or commit fails after measurement, repair those saved outputs;
do not repeat the flight measurement. These changes apply prospectively.

### World identity must not select the intervention label

The completed metric diagnostic exposed a generator alias: both world
selection and passive-flight selection used the global rollout index
modulo three. In the legacy `(classic, dense, moving)` recipe, all moving
rollouts were passive and the other worlds had no passive trials. Its
60-rollout dataset confirmed 20 passive moving rollouts and zero passive
classic/dense rollouts. With `(dense, dense, classic, moving)`, classic
always occupied an even index, so its threatened/clear flag was always
threatened. These are corpus coverage defects, not proof of their impact
on any historical trained model.

`datasets.rollout_schedule.plan` now cycles roles on each world's own visit
count. Every complete six visits contain four intervention and two passive
trials; classic crosses those with threatened/clear courses. World order
and explicit repetition weights remain intact. Partial cycles can still
be incomplete and must be reported.

Both data generators and their Python APIs default to `world_balanced` for
new corpora. **Historical reproduction requires `--schedule-layout legacy`
or `schedule_layout="legacy"`.** The pure schedule test covers all world
permutations, repeated weights and legacy parity. A six-rollout simulator
fixture additionally compared every output array and metadata field against
the old `8de0e75` generator. Legacy mode retains the old blob schema and
consumes randomness in the same order; the completed metric audit script
now pins this mode explicitly. Its saved dataset and results were not touched.

New balanced corpora carry `schedule_layout`; combined corpora carry
`transit_schedule_layout`. Future checkpoints preserve that field, or say
`unrecorded` for data lacking it. This changes the prospective data recipe;
any performance comparison needs a newly registered, single-knob study.
The generator's simulator selftest now requires both flight roles in each
world and saves to `wm_dataset_selftest.npz`, protecting the real corpus.

The subsequent registered [schedule_layout_v1 study](../experiments/schedule_layout_v1/summary.md)
closed **NO-GO** on six fresh 80-epoch fits and a shared independent exam.
Moving AUC deltas across the three matched seeds were +0.0133, −0.0745 and
−0.1042; several per-seed guards failed. This is evidence against the tested
fixed-rollout/epoch learning recipe meeting its improvement bar. It does
not undo the demonstrated coverage repair or isolate a universal causal
effect of balanced roles: generator RNG consumption, valid-window support
and internal splits also change. New default data is role-complete, not a
certified checkpoint upgrade. The negative remains closed without retries.

The subsequent metadata-only [schedule_support_v1 audit](../experiments/schedule_support_v1/journal.md)
reconciles the saved corpora with all six fits. Moving's eligible executed
windows fall from 2,816 to 1,506 while action diversity increases; total
optimizer steps change by only 0.9–1.9%. Internal legacy seed-0 dense AUC
0.5 was a classless fallback (158 positive / zero negative windows), not a
chance-ranking measurement. The independent final exam retains both classes.
Future training output now records support and warns on undefined world AUC.

The same audit finds 8.49–9.32% of legacy and 11.83–13.01% of balanced
training hard-pool frames have no disagreement between answerable candidate
labels: zero masking itself creates their vector contrast. This does not
mean the CF loss trains on masked labels; that loss still masks correctly.
Changing the sampling pool may also affect danger-now because both losses
consume the same sampled frames. The subsequently registered
[cf_hard_pool_v1 comparison](../experiments/cf_hard_pool_v1/summary.md) tested
that one knob with fresh matched fits and a new confirmation exam and closed
NO-GO: mean ranking +0.0401 missed +0.0500, with seed 1 ranking regression
and seed 0 collision-guard failures. The default sampler remains unchanged.
The pooled ranking probe's 208 frames span 23 courses, including only two
moving courses and no rooms; it does not establish all-world ranking gains.

The separate [executed_weight_v1 study](../experiments/executed_weight_v1/summary.md)
then tested moving executed-loss weight 2.25 versus 1.0, with batches and
CF/now recipes fixed. Mean moving AUC improved +0.0598, but seed 0 moving
positivity and seed 1 dense/veer guards failed: NO-GO. It shifts objective
weight mass, not independent data support, and does not isolate prediction
from collision loss. Its pooled veer support passes the registered bar,
but moving has only one probe course, so the existing world-stratified
bootstrap returns no veer interval. Preserve that missing value and reason;
future preflight checks should expose per-stratum support before training.

## Research explanations that needed narrowing

### Perception results are checkpoint observations

The [perception-v2 table](../experiments/perception_v2/journal.md) records
dense 0.9965, perfect veer ranking and saturation 0.3080 for `wm_96d128`.
It also records failures on overall AUC, high-clutter calibration and both
classic/moving guards: one of three primary bars passed. Describing the
whole gate as missing only classic by 0.013 was incomplete.

The [resolution sweep](../experiments/perception_v1/journal.md) records
seed-0 dense AUC 0.9177 / 0.9947 / 0.6999 at 64 / 96 / 128 pixels.
This supports the observed sweep and identifies a candidate. It does not
establish a universal resolution optimum or a causal compression mechanism.
The candidate's estimated 17 ms fits its campaign's 83 ms period bar but
exceeds the project's approximately 8 ms baseline compute target; it is
not a measured hardware latency or closed-loop certification.

### Temporal NO-GO is not proof that motion information is absent

The [latent probe](../experiments/temporal_probe_v1/probe_results.json) and
[pixel campaign](../experiments/temporal_v1_pixel/journal.md) missed their
registered moving-world improvement bars. These verdicts stand. Failure
of the tested probes/recipe does not prove all latent motion information
is absent or all temporal models must fail.

Two additional comparison limits matter:

1. The checkpoint training seed also selected the scored subset of the
   independently generated holdout. Across-seed ranges therefore mix
   training variation and evaluation-course variation.
2. The pixel campaign reused the old apex as its single-frame seed-0
   control. [Stability-v2 C0](../experiments/stability_v2/journal.md)
   reproduced that apex under the old one-sided loss. The fresh pixel
   campaign arms used the two-sided loss. C0 did not establish that all
   six comparison cells shared the changed recipe.

The reported dense range is 0.2276 (rounded to 0.228), larger than the
separately quoted 0.077 and 0.19 changes. Thus the original assertion that
all those changes lie outside the range is arithmetically unsupported.
Even a difference exceeding a range would not be a paired effect estimate.
Three-row ranges are not confidence intervals or a power calculation;
they cannot prove that a +0.03 question is unanswerable at every affordable
sample size, nor that increasing the training diet will fix it.

### A soft variance penalty does not identify the instability's cause

[Stability-v3](../experiments/stability_v3/journal.md) failed its stability
bars under the two-sided penalty. Its large mean absolute latent value
motivates center/target diagnostics. Standard deviation is invariant to
a uniform offset, so the penalty cannot directly constrain that offset.
This mathematical observation does not isolate the causal training failure
or establish a successful cure.

The current logger in `world_model.training.train` measures validation
std/absolute value **after** the training loop, not once per epoch or per
batch. The old-code C0 reproduction therefore cannot rule out transient
upper-hinge activity in the changed-code run. The claimed dead-op/MPS
kernel explanation remains a hypothesis. The two-sided penalty remains
unchanged; evaluating another loss requires a separate registered knob.

The stability/pixel checkpoint files, training corpora and raw logs are
not tracked in Git and were absent from this checkout. Their journal
tables can be checked for internal consistency, but their training draws
have not been rerun here. The pinned deployed artifacts are a different
set, restored and verified using `scripts.fetch_champions`.

## The next instrument, now available

Use `--independent-holdout` only with a dataset generated independently of
**every** compared checkpoint's training data. This is a caller assertion:
old checkpoint metadata cannot prove dataset disjointness. Known exact
training-file reuse is now rejected when both hashes are available. The default
training-validation mode still follows the checkpoint's own seed and
rejects contradictory seeds, including through the Python API.

The 2026-09-14 identity regression reproduced a concrete contradiction:
paired-score comparison accepted `independent_holdout_all` even when its
checkpoint metadata and exam provenance named the same SHA-256. The probe
also lacked an input for comparing its loaded dataset identity. A caller
assertion must not override an identity already known to be the training file.

`datasets.provenance.reject_training_file` now enforces this check in the
probe and paired comparison. The CLI supplies the hash computed from the
dataset it loads; Python file callers should pass `dataset_sha256` to
`evaluate`. Rejection happens before model scoring or output publication.
Ordinary training-validation mode still accepts the training dataset.

File-backed `scripts.train` now freezes the NPZ identity before loading,
verifies it after loading and fitting, and saves `training_dataset_sha256`
in checkpoint metadata. Source mutation prevents checkpoint publication.
This changes metadata only, not tensors, optimizer steps or RNG calls.
Generated in-memory corpora and legacy checkpoints may lack file identity.
Different SHA values can result from repacking or selecting overlapping
rollouts, so passing this check does **not** establish independence.

Reproduce the synthetic acceptance-boundary and publication checks with
`python -m datasets.provenance`,
`python -m scripts.dataset_identity_selftest` and
`python -m eval.compare_wm_scores --selftest`. The fixtures require no saved
model: they check renamed identical files, both comparison arms, API/CLI
rejection before inference/writes, source mutation during load/fit, original
validation mode and legacy compatibility. No closed study is rescored.

Validation also exercised the actual CLI with a saved CF control and its
recorded training NPZ: it exited with the identical-SHA rejection and wrote
neither scores JSON nor NPZ. The two-epoch checkpoint integration selftest
passed, including training/probe metric agreement; both completed-study
report checks and all nine locked-artifact hashes remain valid. Full-repo
Black/Ruff passed for 160 Python files. These are local validations.

```bash
python -m eval.eval_wm_checkpoint --ckpt path/to/control.pth \
  --data path/to/independent.npz --independent-holdout --device cpu \
  --out experiments/new_audit/control.json \
  --scores-out experiments/new_audit/control_scores.npz
python -m eval.eval_wm_checkpoint --ckpt path/to/candidate.pth \
  --data path/to/independent.npz --independent-holdout --device cpu \
  --out experiments/new_audit/candidate.json \
  --scores-out experiments/new_audit/candidate_scores.npz
python -m eval.compare_wm_scores \
  --baseline experiments/new_audit/control_scores.npz \
  --candidate experiments/new_audit/candidate_scores.npz \
  --seed 0 --n-boot 2000 --out experiments/new_audit/comparison.json
```

All rollouts now remain common across models regardless of training seed.
Exports preserve sample IDs, labels, world IDs, horizons, checkpoint/data
hashes, checkpoint metadata and evaluation runtime. Existing output files
are refused. Missing veer probes serialize as `null` with sample count zero.
Class counts accompany the legacy AUC fields, so a 0.5 fallback from an
absent class can be distinguished from a measured chance-level ranking.
Since the CF sampler registration, exports also retain eligible veer probe
course/time pairs, geometric truth, world identity and per-frame correctness.
The aggregate includes both probe-frame and independent-course counts.

The comparison refuses mismatched datasets, sample order, labels, horizons
or metric versions. It reports candidate-minus-control AUC@32 and paired
world-stratified rollout-bootstrap percentile intervals. Resampling whole
rollouts preserves within-flight dependence. These intervals describe
test-course uncertainty conditional on the two fixed models; they do not
measure training-draw uncertainty, establish causation or promote a model.
New exports also receive paired veer-accuracy intervals, grouping all probe
frames from a course together. Legacy exports without veer samples retain
their AUC-only comparison. A world stratum with fewer than two probe courses
has no estimated interval; a missing probe has no measured accuracy.

Before another temporal training campaign, freeze a diagnostic manifest:
exact checkpoint hashes and training recipes, independent holdout generation
recipe and seed, included worlds, metric version, device, bootstrap seed
and number of draws. Score every registered model once on that common exam
and retain all outputs, including negatives and undefined cells. Audit the
old apex separately from same-recipe controls. A new training campaign then
needs its own unchanged bars and matched controls; these diagnostics do not
reopen the original NO-GOs.

Verification commands: `python -m eval.eval_wm_checkpoint --selftest`,
`python -m eval.compare_wm_scores --selftest`, and
`python -m scripts.research --selftest`. The module tests include a
rendered non-blank image check, train/probe metric parity, holdout invariance
across split seeds, paired identity and refusal of misaligned samples.

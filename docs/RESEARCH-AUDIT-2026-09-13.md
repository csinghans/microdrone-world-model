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
old checkpoint metadata cannot prove dataset disjointness. The default
training-validation mode still follows the checkpoint's own seed and
rejects contradictory seeds, including through the Python API.

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

The comparison refuses mismatched datasets, sample order, labels, horizons
or metric versions. It reports candidate-minus-control AUC@32 and paired
world-stratified rollout-bootstrap percentile intervals. Resampling whole
rollouts preserves within-flight dependence. These intervals describe
test-course uncertainty conditional on the two fixed models; they do not
measure training-draw uncertainty, establish causation or promote a model.

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

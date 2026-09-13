# metric_integrity_v1 — quantify the AUC instrument repair

## Diagnostic registration — 2026-09-13, before scoring

Question: how much does assigning half credit to equal positive/negative
scores change AUC@32 for the two locked, deployed float WMs on one new
common transit dataset? This diagnoses the metric; it is not a model
competition, promotion gate, retry of a historical result, or training run.

Frozen scope:

- Models: `output/world_model.pth` and `output/world_model_unified.pth`,
  with their SHA-256 values in `artifacts.lock.json`, verified before/after.
- Data: `datasets.generate_rollouts.gen(60, 160, seed=20260913,
  worlds=("classic", "dense", "moving"))`, default remaining arguments,
  64-pixel camera, saved at
  `output/metric_integrity_v1/holdout_64.npz`. This new seed is independent
  of the historical training runs; no data from this draw trains a model.
- Vision preflight: a separate one-rollout instrument fixture at seed
  20260912 must have a non-blank frame and a visibly rendered obstacle.
  Do not interpret scored results until that preflight passes.
  The t=45 frame was inspected before the scored run: the red pillar is
  visible on the left, with floor/background on the right. `run.sh`
  additionally requires the pillar's red pixels to cover more than 5%
  of that fixed fixture and saves the image alongside the dataset.
- Exam: all valid held-command samples in all 60 rollouts, with the same
  data file for both checkpoints; CPU inference; no seed-dependent val
  subsampling. Scores and metadata exported by `eval.eval_wm_checkpoint`.
- Metric: `mann_whitney_average_ranks_v2`, compared to the previous
  positive-first distinct-rank formula on the identical score arrays.
  Report per-world and pooled AUC, corrected-minus-legacy difference,
  cross-class tied-pair fraction and its worst-case absolute bias bound.
  Undefined cells are missing, never reported as successful discrimination.
- One analysis of each frozen score export. Record a zero/negligible effect
  as a negative finding, without increasing sample size or changing seeds.
  Harness errors are repaired under the same configuration.

No effect-size bar is introduced: this is a descriptive instrument audit.
The analytical maximum absolute tie bias is half the fraction of tied
positive–negative pairs. It quantifies metric ambiguity on this fixed
sample, not uncertainty across courses or training draws.

Limits: the release lacks the 96-pixel research checkpoints and their
training/score corpora. This audit cannot repair their historical numbers,
generalize to their saturation regimes, or establish int8 behavior.
Historical result JSON, bars and verdicts remain unchanged.

Rerun from the persistent `run.sh` alongside this journal. The script
requires new output files, checks the locked artifact hashes, records full
logs, and stops on any failed stage. Re-running a completed diagnostic
requires an explicit new registration, not overwriting these outputs.

## Result — 2026-09-13: no tie-induced change on this float sample

Registration commit: `4aeac99`. The queue completed with `EXIT=0` and
`METRIC-AUDIT-DONE`; the full log is `run.log` (git-ignored). Vision
preflight and all nine locked artifact checks passed before/after.
CPU inference used torch 2.14.0 and NumPy 2.5.3.

Both checkpoints were scored on the same 60 rollouts / 4,083 valid
held-command samples (2,195 positive, 1,888 negative). Dataset SHA-256:
`4d33c09da99d5d793200341d0ce2102f64167b983256d8f38ca599dab894772f`.
The JSON exports record the checkpoint SHA-256 values and full provenance.

| checkpoint | world | legacy AUC@32 | corrected AUC@32 | difference | tied cross-class pairs |
|---|---|---:|---:|---:|---:|
| transit | all | 0.820471 | 0.820471 | 0 | 0 |
| transit | classic | 0.783918 | 0.783918 | 0 | 0 |
| transit | dense | 0.869508 | 0.869508 | 0 | 0 |
| transit | moving | 0.774451 | 0.774451 | 0 | 0 |
| unified | all | 0.818842 | 0.818842 | 0 | 0 |
| unified | classic | 0.838850 | 0.838850 | 0 | 0 |
| unified | dense | 0.811430 | 0.811430 | 0 | 0 |
| unified | moving | 0.773229 | 0.773229 | 0 | 0 |

Sources: `transit_audit.json`, `unified_audit.json`, with scoring metadata
in `transit_scores.json` / `unified_scores.json`; full arrays remain in
`output/metric_integrity_v1/`. The reported difference is exactly zero,
not merely a rounded nonzero change. The analytical tie-bias bound is
also zero for each row because no opposite-label pair tied.

### Researcher notes

The implementation bug is real on tied-score fixtures, but it does not
explain any ranking difference on these two float checkpoints and this
registered draw. Record the negative; do not enlarge the sample or hunt
for a checkpoint where it appears. Saturated 96-pixel and int8 outputs
remain outside this diagnostic's scope. These offline rows do not grade
flight behavior or replace an earlier scoreboard.

The raw dataset also exposed a separate, post-hoc instrument issue:
with the default three-world order, `r % 3` selects both the world and
passive schedule. The 20 moving rollouts here are all passive, and neither
classic nor dense has passive rollouts. That limits the diet represented
by this negative result. Audit and repair this schedule aliasing as a
separate data-generation change; preserve this completed dataset and its
registered audit outputs.

### Reproduction note after the generator repair

New generator calls now default to `world_balanced`. `run.sh` explicitly
selects `schedule_layout='legacy'` to preserve the already-registered
recipe above; the original data/results were not regenerated. Legacy
replay was checked against the pre-repair `8de0e75` implementation on a
separate six-rollout fixture, comparing every array and metadata field.

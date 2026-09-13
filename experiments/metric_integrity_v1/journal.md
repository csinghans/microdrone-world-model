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

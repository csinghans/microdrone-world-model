# Research continuation state — 2026-09-14

The ongoing objective is to improve this project's implementation, content
and research with rerunnable evidence. An hourly follow-up is active in the
existing Codex task. It does not bypass account limits; local scheduled work
needs the computer and app available. Check current processes and Git state
on resumption rather than assuming this snapshot is still current.

## Completed and verified

- Research runner: consistent pooled verdicts, preserved initial/recheck
  evidence, append-only resume, concurrent-writer exclusion, atomic JSON
  before journal/Git writes, scoped commits and protected WM hashes.
  `python -m scripts.research_selftest` passes 16 isolated regressions;
  `python -m scripts.research --selftest` passes a simulator-backed dry gate.
- Metrics: shared tie-aware AUC, explicit rejection of nonfinite/mismatched
  inputs, independent holdout export, paired rollout uncertainty and a
  legacy-metric audit. Core, indoor-wrapper, checkpoint, head-calibration,
  temporal-probe and int8-parity selftests passed locally. The real-checkpoint
  CLI export/compare roundtrip also passed identity and no-overwrite checks.
- Registered [metric_integrity_v1](../experiments/metric_integrity_v1/journal.md)
  is complete: 60 rollouts, 4,083 valid samples, zero cross-class ties and
  zero legacy-to-corrected AUC change for both locked float WMs. Do not
  rerun this diagnostic looking for a different outcome.
- The diagnostic exposed world/role schedule aliasing. New generation now
  uses `world_balanced`; explicit `legacy` reproduces older recipes.
  Pure schedule tests cover world permutations/weights; the simulator
  selftest requires passive and intervention flights in every world.
  A separate six-rollout replay matched every array against the old
  `8de0e75` generator. New data/checkpoints carry layout provenance.
- The [evidence audit](RESEARCH-AUDIT-2026-09-13.md), roadmap, README and
  bilingual articles #15–#16 distinguish recorded rows from unproven
  explanations. Historical journal corrections append dated notes.
- Whole-repository Black/Ruff and diff-whitespace checks passed. These
  are local validations, not a claim that remote CI was dispatched.

All nine locked artifacts were restored from the existing release and
verified. Both protected WM hashes remain those in `artifacts.lock.json`.
No frozen skill declaration or existing results JSON was changed. No
release was tagged or remote push performed.

## Next research work

The [schedule_layout_v1 study](../experiments/schedule_layout_v1/summary.md)
is **complete: NO-GO**. Six 80-epoch fits, three paired training seeds, one
186-course independent exam. Moving AUC deltas are +0.0133 / −0.0745 /
−0.1042 (mean −0.0551; required +0.0300). Room/now guards fail at seed 1;
all behavioral guards fail at seed 2. Budget is unchanged at 137.29 KB.
No model was promoted or valid measurement repeated. Do not restart or
expand this completed study and do not select its favorable seed 0 alone.

All 19 stage receipts and artifacts were hash-verified before closing;
the full log ends in `SCHEDULE-LAYOUT-DONE` and `SCHEDULE-LAYOUT-EXIT=0`.
No experiment worker remained at the completion check. Recheck processes
on every wakeup rather than assuming that remains true. Raw data, models
and scores stay under `output/schedule_layout_v1/`; committed receipts are
in `experiments/schedule_layout_v1/records/`, including `report.json`.
`python -m eval.eval_schedule_report` regenerates the summary/figure from
committed records alone, with no scoring, fitting or resampling. Its
selftest rejects altered decisions or summaries. The original training
sources are pinned in the manifest at `e4053e8`; new report code was added
only after the training/evaluation queue completed.

The first vision attempt stopped before data generation because the moving
crosser starts outside the camera cone. The corrected instrument observes
its geometric centreline crossing, with unchanged thresholds, seeds and
training recipe. All four rendered-scene checks passed; the original
failure and manifest remain in `harness_attempt_1/`.

The metadata-only [schedule_support_v1 audit](../experiments/schedule_support_v1/journal.md)
is also complete. All six train/validation window counts and the common
exam's class counts reconcile. Moving executed windows fall 2,816→1,506
while non-forward categories appear. The legacy seed-0 dense internal
validation AUC 0.5 was undefined: 158 positive / zero negative windows.
Training now records class support and warns on such fallbacks; numeric
values and all archived results remain unchanged. The two-epoch checkpoint
selftest passed training/probe count agreement and exercised a warning.

`python -m eval.eval_dataset_support --selftest` checks exact window/split
counts, room/transit action-id separation, classless labels and masked
contrast. `bash experiments/schedule_support_v1/verify.sh` checks saved
audit/fit/exam agreement without fitting or rewriting outputs. The audit's
raw data is under its campaign directory; no experiment worker is active.
Original manifest source hashes describe the historical training revision;
the new class-support logging was added only after both studies completed.

The next registered study is [cf_hard_pool_v1](../experiments/cf_hard_pool_v1/journal.md):
the current zero-masked-vector rule versus disagreement between answerable
candidate labels. The explicit recipe flag preserves `legacy_masked` by
default. The audit measured masked-only contrast in 11.83–13.01% of balanced
training hard frames; both implemented masks reconcile with that audit.
Two-epoch integration tests pass for both recipes using selftest artifacts.
Veer exports now retain individual course/time/truth/correctness for paired
rollout-bootstrap intervals; frame and independent-course counts are separate.

Six new 80-epoch fits reuse the identical hashed balanced training corpus.
A fresh 186-course confirmation exam uses new generation seeds. The frozen
bar is mean veer improvement ≥+.05 with every seed nondecreasing; each
world AUC and danger-now guard is ≥−.02 at every seed, with identical ≤512 KB
analytic bills. All six draws run after instrument checks, with no optional
rechecks or replacement draws. The historical schedule-layout NO-GO stays
closed. The CF loss already masks labels correctly; benefit from changing
the sampling allocation is still unmeasured. Danger-now consumes the same
sample pool, so its downstream effect belongs to this one knob.

Run `bash experiments/cf_hard_pool_v1/run.sh` only after checking existing
processes and receipts. A background launch receipt, when present, is
`output/cf_hard_pool_v1/queue.json`; the full queue log is in the campaign's
`run.log`. Sources, runtime, corpus SHA and protected WMs freeze at launch.
Do not edit Python sources while this queue is active. Incomplete stage
directories require inspection and cannot be silently retried. Expected
completion markers are `CF-HARD-POOL-DONE` and `CF-HARD-POOL-EXIT=0`.

The queue has now launched from `19106b2` (initial shell PID 63607). All four
preflight stages passed and their receipts/files were verified. New exam:
186 courses, 12,147 valid windows; every world has both classes. Exam SHA:
`16986ffa08f24bac9ca3f5775ed8f8fa419aa5eb54851f123b1dd7f0416ebf53`.
The first control fit was active at this snapshot; inspect current state
before acting. Results are pending, and Python sources must remain frozen.

Restoring moving executed-window exposure is a separate possible knob;
do not change it together with the hard pool. Do not infer the cause from
balanced seed 2's endpoint offset alone: seed 1 also loses without that
symptom. Keep optimization exposure, latent scale, course uncertainty and
training-draw spread distinct. Any next fit needs its own registration and
frozen bars; this retrospective audit does not pass a flight or promotion gate.

The coverage repair remains a structural data fix, **not a demonstrated
performance upgrade**. README, roadmap, changelog and the evidence audit
now carry the measured negative. Any next training study needs a new
registration and frozen bars; this NO-GO does not authorize a flight gate.

The 96-pixel research models/corpora are absent from this checkout and
are not assets in the inspected `champions-2026-07` release. Do not silently
substitute the deployed 64-pixel models for those historical candidates.
A reconstruction or new training study needs explicit recipe provenance
and its own registration; preserve the earlier NO-GOs.

The manual CI workflow includes the new fast integrity/metric/schedule
tests. If a later step pushes this branch, run whole-repository lint and
dispatch CI as required by AGENTS.md. Conditional training stages must
remain gated with `research step` or a fail-fast persistent queue.

Local validation environment for resumption:
`/Users/hans.chen/.cache/microdrone-research-venv/bin/python`
(Python 3.14.5, torch 2.14.0, NumPy 2.5.3, pybullet 3.2.7).
The repo's declared conda/CI Python is 3.12; it was not replaced. New
statistical records include their actual evaluation runtime. Full audit
logs are in the campaign folder; local selftest logs are under
`output/research_integrity_selftest/` and the task's cache directory.

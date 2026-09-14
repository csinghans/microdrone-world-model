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
- Independent-exam identity: the probe API/CLI and paired comparison now
  reject known exact training-file reuse. File-backed training records its
  source SHA and rejects a file changed during load/fit before publishing
  a checkpoint. Synthetic tests cover both comparison arms, renamed copies,
  no scoring/writes on rejection and compatibility with original validation
  and legacy metadata. This is not a proof of rollout independence: missing
  or different file hashes cannot exclude overlap from repacking/subsets.
  The two-epoch checkpoint integration test passed. A saved CF control
  paired deliberately with its own training file was rejected by the real
  CLI before result files appeared. All 160 Python files pass Black/Ruff;
  both completed-study report selftests and all nine locked-artifact hashes
  also pass. No research model was fitted or rescored for this repair.
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

The [cf_hard_pool_v1 study](../experiments/cf_hard_pool_v1/summary.md) is
**complete: NO-GO**. Six new 80-epoch fits share the same balanced corpus;
the sole knob selects zero-masked-vector versus answerable-label contrast.
On the fresh 186-course / 12,147-window exam, veer deltas are
+0.0481 / −0.0913 / +0.1635, mean +0.0401 versus required +0.0500.
Seed 1 ranking regresses, and seed 0 fails classic/moving/room/now guards.
All six analytic bills remain 137.29 KB; default sampling stays `legacy_masked`.
There is no promotion, retry, exam expansion or change to any earlier NO-GO.

All 17 stages and files, frozen sources/runtime/corpus and protected WMs
were verified at completion before adding report code; see the campaign's
`verification.json`. Original sources are pinned at `19106b2`. Full logs
end in `CF-HARD-POOL-DONE` and `CF-HARD-POOL-EXIT=0`. No worker remained at
the completion check. `output/cf_hard_pool_v1/queue.json` is a historical
launch receipt, not an active-work indicator. Recheck processes on wakeup.
The closed exam SHA is
`16986ffa08f24bac9ca3f5775ed8f8fa419aa5eb54851f123b1dd7f0416ebf53`.

`python -m eval.eval_cf_sampler_report` rebuilds the summary/figure from
committed JSON alone; its selftest checks individual receipts, single-knob
metadata, matched support and frozen decisions. The optional
`--audit-probe-support` reads six hashed NPZ exports without running models
and compares an existing support record rather than replacing it. Probe
support: 208 frames / 23 courses; classic 39/6, dense 145/15, moving 24/2,
room 0/0. This passes the frozen pooled support bar but does not establish
per-world ranking gains. No retrospective support expansion is authorized.

Both sampler recipes passed the two-epoch integration selftest. The CF
loss already masks unknown labels correctly; changing allocation also
changes the danger-now samples. The study failed the registered joint
improvement test, not an assertion that every contrast curriculum must fail.

The [executed_weight_v1 study](../experiments/executed_weight_v1/summary.md)
is **complete: NO-GO**. Six fresh 80-epoch fits compare moving executed-loss
weight 1.0 vs 2.25 on a shared balanced corpus. A training-only normalizer
raises moving weight mass from about 18% to 33%, with batches, CF/now recipes
and the 137.29 KB analytic bill fixed. Moving AUC deltas are
−0.0184 / +0.1227 / +0.0752 (mean +0.0598). The +.03 mean bar passes;
seed 0 fails moving positivity and seed 1 fails dense (−0.0293) and veer
(−0.0737) guards. Default weight remains 1.0. No promotion or repeat follows.

All 17 stages and files, sources/runtime/corpus and protected WMs were
verified before report changes; `verification.json` records this. Original
training sources are pinned at `2362756`. Full logs end with
`EXECUTED-WEIGHT-DONE` and `EXECUTED-WEIGHT-EXIT=0`. No worker remained at
completion; the old queue PID is historical, not an active-work indication.
The exam contains 186 courses / 12,179 windows; its SHA is
`e241adddb83d636fdaa9665643929b4e7cf1a45671b2fad4c8334455ec21aac1`.

`python -m eval.eval_executed_weight_report` generates the summary/figure
from committed JSON only. Its selftest verifies original decisions, fit
and score identity, one-knob metadata and preflight weight plans; fabricated
intervals fail. `--audit-probe-support` checks six hashed exports without
model calls. Veer has 190 frames / 20 courses: classic 43/7, dense 139/12,
moving 8/1, room 0/0. Pooled support passes its frozen bar, but the singleton
moving stratum makes every veer bootstrap interval undefined. Preserve the
missing intervals and reason; do not expand this exam or change its verdict.

The [veer_support_v1 instrument audit](../experiments/veer_support_v1/journal.md)
is complete. `world_model.veer_probe.select` is now the common geometric
selector for scoring and a model-free preflight, `eval.eval_veer_support`.
It reads no pixels and exposes pooled/per-world course counts, absent worlds
and singleton strata before future fits. It does not certify rendering,
course independence or statistical power; it creates no new gate.

Original `016dc94` geometry matches the new selector on both closed exams
and the shared training corpus (208/23, 190/20 and 53/10 frames/courses).
All twelve archived score exports match exact pairs, ground truth and world
identity. `bash experiments/veer_support_v1/verify.sh` reruns only that
accounting and checks existing receipts without overwriting them. The three
new synthetic selftests and the two-epoch checkpoint integration passed.
Whole-repository lint and locked-artifact checks are recorded in the journal.

Next research should register a specific remaining failure and one mechanism,
with required exam worlds, support bars and the response to insufficient
support frozen before any fit. The support tool is available as a separate
preflight command; historical queues and gates were not changed. Do not
repeat, expand or reinterpret a closed draw as a new instrument failure.
No new training study is active.

The tested loss weight changes objective allocation, not independent data
support or measured gradient mass. It does not isolate prediction from
collision loss. Do not infer a training cause from a large latent endpoint
alone. Any next fit requires a new one-knob registration and frozen guards.

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

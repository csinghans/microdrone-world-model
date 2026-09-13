# Research continuation state — 2026-09-13

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

The new [schedule_layout_v1 study](../experiments/schedule_layout_v1/journal.md)
is **running in a detached background queue**. Registration committed at
`765b917`; harness correction at `e4053e8`. Six unconditional 80-epoch fits
compare `legacy` with `world_balanced` at training seeds 0, 1, 2, with the
same 96-rollout room corpus in both 96-transit + 96-room diets. All fits use
the same independently generated 126-transit + 60-room exam. These counts
have now been generated: all six preparation stages and their hashes passed
verification. The queue has entered `train_legacy_0`; no fitted-model result
or final verdict has yet been recorded in this snapshot.

On resumption, inspect `output/schedule_layout_v1/queue.json`, the current
PID/process tree, `experiments/schedule_layout_v1/run.log` and stage logs.
Do not launch another queue while it is alive. Completed stages have hashed
receipts in `experiments/schedule_layout_v1/records/`; the final result is
`records/report.json`. A real success marker requires `SCHEDULE-LAYOUT-DONE`
and `SCHEDULE-LAYOUT-EXIT=0`. A scientific NO-GO still completes normally.
If a process is gone, inspect its complete log and any `failure.json` before
using `bash experiments/schedule_layout_v1/run.sh` to resume. The runner
skips verified receipts and refuses incomplete directories; inspect/recover
an interrupted stage rather than automatically retraining its seed.

**Do not change Python source, the registration, environment or protected
models during this campaign.** The manifest freezes all tracked Python
files and rejects drift at stage boundaries. Documentation can continue.
The new pure selftest covers per-seed guard failure, incomplete/duplicate
draws, nonfinite metrics, no-overwrite publication and actual resume refusal.
All 154 Python files passed whole-repository Black/Ruff before launch.

The first instrument attempt stopped before data generation: the moving
crosser begins outside the camera cone. The corrected fixture observes its
geometric centreline crossing with the camera fixed. All four rendered
versus removed-scene checks then passed and their images were inspected.
The original manifest/failure and PNGs are preserved; no training recipe,
pixel threshold or outcome bar changed. See the journal's harness note.

After all planned draws finish, interpret every seed and guard, append the
researcher notes, and commit new records. Report the three-draw mean/range
separately from the per-seed paired rollout bootstrap intervals. An offline
GO only permits registering a subsequent closed-loop study; no automatic
promotion. Neither the coverage fix nor the float AUC audit establishes a
learned-policy improvement. Keep any honest NO-GO without sample expansion.

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

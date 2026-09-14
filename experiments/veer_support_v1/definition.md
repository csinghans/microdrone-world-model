# Veer support instrument audit — 2026-09-14

This is a compatibility audit, with no fitting, checkpoint scoring, new
simulator courses, bootstrap draws or performance hypothesis. The preceding
`executed_weight_v1` and `cf_hard_pool_v1` verdicts stay closed NO-GO.

Extract the existing geometric eligibility loop into `world_model.veer_probe`.
Training/checkpoint scoring and a metadata-only preflight use that function.
Keep the old forward-action restriction, speed, motion, longest horizon,
strict 0.12 m contrast, danger-radius crossing and camera-FOV tests unchanged.
No requirement for a held-command future is added; end-of-rollout frames
remain eligible. Room NaN pillars remain outside this oracle's scope.

The preflight reports all-course and per-world frame/course support before
future fits. Its bootstrap diagnostic reproduces the existing comparator's
minimum of two courses in each *observed* world stratum. Zero-support worlds
are displayed but are not certified. This minimum does not establish power,
course independence or rendered visibility. Future registrations must freeze
their required worlds, support bars and response to an insufficient exam.
This audit does not create a retry rule or apply new bars to old studies.

Compatibility checks:

- Synthetic geometry: asymmetric truth, symmetry, cruise filtering,
  out-of-FOV threats, NaN rooms, moving pillars, input ordering and empty sets.
- Scorer wiring: exact current/previous/memory-window pixel ordering,
  normalized veer commands, residual base, tie handling, no model calls for
  empty support and no random-number consumption. Toy callables only.
- Original source reference: `016dc94:world_model/training.py`. Execute its
  `veer_ranking` function using shape-only frame placeholders and intercept
  the first tensor construction; compare its complete selected pairs and
  safer-side truths with the new selector, before any model inference.
- Real metadata: the closed CF and executed-weight exams and their shared
  training corpus. Match both exams against all twelve hashed score exports
  and their original receipts. No accuracy is recomputed.
- Existing two-epoch checkpoint integration selftest, with selftest-only
  model filenames, plus whole-repository lint and locked-artifact hashes.

`bash experiments/veer_support_v1/verify.sh` verifies existing evidence without
overwriting it; on the first invocation it creates the new support receipts.
It requires the original Git revision and local ignored corpora/exports.
The three module selftests are synthetic and work without those artifacts.

# Review response — 2026-09-29

**Deliver the verified fixes as small MRs, preserve the author's text, and
make the deployed-checkpoint common exam the next research decision.**

The review covers `6def4ea..dfa9ad6`. The later `834828c` closes
moving_timing_v1 (six fits and scorings, NO-GO); `10e2a0e` closes the declared
fixed-checkpoint probe replay. Both results were complete before this review
response. Their recorded measurements and bars are unchanged. The large
research branch is an evidence archive, not the merge unit for the fix MRs.

| Review item | Response / evidence |
|---|---|
| AUC ties | [MR #1](https://github.com/csinghans/microdrone-world-model/pull/1): isolated metric change, Python 3.12 tests and full CI passed |
| Gate commit order / old campaigns | [MR #2](https://github.com/csinghans/microdrone-world-model/pull/2): current JSON in gate commit, legacy warning/continuation, explicit harness invalidation retaining original blocks; 25 isolated regressions pass |
| Schedule coverage / dataset clobber | [MR #3](https://github.com/csinghans/microdrone-world-model/pull/3): `legacy` retained and dense recalibration explicitly pinned to it; Python 3.12 checks and CI passed |
| Champion protection | [MR #4](https://github.com/csinghans/microdrone-world-model/pull/4): candidate paths and isolated selftest writes; Python 3.12 checks and CI passed |
| Policy seed and worlds | [MR #5](https://github.com/csinghans/microdrone-world-model/pull/5), based on #4: CLI arguments reach training, protected candidate policy paths; load-policy and observation-inference ASTs unchanged from main; Python 3.12 checks and CI passed |
| Missing moving-timing results | Completed at `834828c`; mean +0.0101 misses +0.03 and moving-ranking guards fail all seeds |
| Author prose | README, ROADMAP and both article #16 versions restored byte-for-byte from main, then evidence notes appended; six lessons preserved |
| CLAUDE / onboarding | Defaults and fresh-output behavior documented; repeatable dry path uses `research --selftest` |
| Legacy training parity | Main versus review-adjusted research tree: 16 arrays including pixels and 28 state tensors exactly equal after two CPU epochs; see below |
| Precision / power | Stop launching small three-seed gates by habit. Declare the estimand, seed/course uncertainty, precision or power assumptions before a future fit; never change existing bars |
| Deployed-model common exam | Two locked WMs are present; `experiments/perception_v2/artifacts/wm_96d128.pth` is absent in this executor. User asked for its accessible location. Do not substitute a retrain or silently drop this candidate |
| Receipts / attribution / CI | New study receipts stay in persistent `output/`; commit summaries, definitions, code and hashes. Existing evidence stays intact. New commits carry Codex co-authorship. Pushes dispatch manual CI; no automatic merge or release |

## Legacy parity measurement

Python 3.12.14, Torch 2.12.1, CPU with one thread. Generate nine legacy
classic/dense/moving rollouts, length 80, seed 29; train two epochs with seed
7 and batch 64 in each checkout. All 16 baseline arrays, including pixels,
and all 28 tensors in encoder/predictor/collision/now state dictionaries
match exactly. All nine locked artifacts match before/after. Checkpoint
container hashes differ because metadata differs; tensor identity is the
tested claim. This does not assert bitwise MPS identity on long runs.

Reproduce with `python -m scripts.check_legacy_training --baseline
/path/to/main-6def4ea --out output/new_legacy_parity`. The main snapshot can
be an extracted Git archive. Full logs and report are in
`output/review_delivery/legacy_parity_v1/`; no inference or fits use champion
output names. Initial string-format lint errors were fixed before training.

The standalone [evidence MR #6](https://github.com/csinghans/microdrone-world-model/pull/6)
contains the comparator, compact status/response pages and receipt hashes,
without importing raw study receipts. Local checks passed; manual CI run
`36538322880` tracks its branch. The five fix MRs all passed manual CI.
The archive source `888daaf` also passed manual CI run `36537639894`.
None of these MRs has been merged automatically.

Report SHA256:
`c8c97a7e8b94c7e0d1031ef60c86478c1ce8231f50a5bb75ea8c355c5cec2e33`.
Source/recipe manifest SHA256:
`cd7690ee0e0bffe7121bdd80d69c6923e88386192ecd28d3f5dde18f201a092b`.
The exact candidate Python source is preserved at `888daaf`; a rerun must
pass that checkout as `--candidate`, alongside main `6def4ea` as `--baseline`.

## Research interpretation and continuation

Unified's existing independent 60-rollout scores (all 0.818842; classic
0.838850; dense 0.811430; moving 0.773229) are now prominent in the evidence
updates. They are different exams from the historical validation numbers.
The first three matched-study seed ranges support the practical resolution
concern. A fixed exam removes variation from changing the exam across arms;
it does not remove finite-exam uncertainty or estimate training-population
power. The fourth study changed both endpoint and exam, so attributing its
smaller range solely to exam size would go beyond the measurement.

Next: finish the small fix MRs, obtain the actual 96×D128 checkpoint, then
freeze a role-complete independent common-exam recipe that honors each
checkpoint's image recipe. Price candidates against 512 KB and approximately
8 ms. Use the result to choose among the original larger-diet, 96-pixel
closed-loop and center-drift directions. No new training gate is released.

The existing hourly task now creates or updates an MR when a meaningful,
tested batch is ready, tracks CI, and remains quiet without new results.

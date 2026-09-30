# Review response — 2026-09-29

**Five focused fix MRs are ready for review; the author's narrative is
preserved and the next research decision is the deployed-model common exam.**

The reviewed span was main `6def4ea` through `dfa9ad6`. The later
`834828c` completed moving_timing_v1, and `10e2a0e` completed the declared
fixed-checkpoint probe replay. Their original measurements remain in the
[research archive](https://github.com/csinghans/microdrone-world-model/tree/888daaf8265f16f52e6dad2b05b8788eea56aec6).
The archive is separate from the following merge units. These MRs are open;
operational changes take effect only when their corresponding MR is merged.

| Review item | Delivery and validation |
|---|---|
| AUC ties | [MR #1](https://github.com/csinghans/microdrone-world-model/pull/1): average tied ranks, preserved import/fallback; [CI passed](https://github.com/csinghans/microdrone-world-model/actions/runs/36511686782) |
| Gate save order / legacy campaigns | [MR #2](https://github.com/csinghans/microdrone-world-model/pull/2): JSON before commit, legacy warning/continuation, reasoned harness invalidation retaining original blocks; 25 regressions and [CI passed](https://github.com/csinghans/microdrone-world-model/actions/runs/36511966351) |
| Role coverage / dataset protection | [MR #3](https://github.com/csinghans/microdrone-world-model/pull/3): world-balanced default, explicit legacy dense recalibration, fresh output paths; [CI passed](https://github.com/csinghans/microdrone-world-model/actions/runs/36512453780) |
| Champion protection | [MR #4](https://github.com/csinghans/microdrone-world-model/pull/4): candidate paths and isolated selftest writes; [CI passed](https://github.com/csinghans/microdrone-world-model/actions/runs/36512698270) |
| Policy CLI | [MR #5](https://github.com/csinghans/microdrone-world-model/pull/5), based on #4: seed/world/output propagation, unsupported-option validation, protected policy paths; local Python 3.12 checks and [CI passed](https://github.com/csinghans/microdrone-world-model/actions/runs/36537662321) |
| Author text | README, ROADMAP and both article #16 versions retain the exact main prefix, then append evidence updates; original six lessons unchanged |
| CLAUDE / onboarding | Operational notes travel with their fix MRs. MR #2 documents repeatable `research --selftest`; persistent `step --dry` retains duplicate protection |
| Legacy numeric path | Sixteen arrays including pixels and 28 state tensors match after two CPU epochs; recipe and limits below |
| Research direction | [Compact status](RESEARCH-STATUS.md) foregrounds independent unified scores, completed moving-timing results, precision/power planning and the missing third checkpoint |

## Legacy two-epoch parity

Python 3.12.14, Torch 2.12.1, CPU, one thread. Generate nine legacy
classic/dense/moving rollouts of length 80 with seed 29; train two epochs
with seed 7 and batch 64 in each checkout. All 16 baseline arrays, including
pixels, and all 28 encoder/predictor/collision/now tensors are exactly equal.
All nine available locked artifacts remain unchanged. Checkpoint container
hashes differ because metadata differs; tensor identity is the tested claim.
This fixture does not establish long-run MPS identity or flight performance.

Baseline: `6def4ea75feefe43220fcf364f9cea0eda81203a`. Candidate Python source
is preserved at `888daaf8265f16f52e6dad2b05b8788eea56aec6`; the measurement
manifest hashes the exact source files. To reproduce, use the same Python
environment and checkout/archive paths:

```bash
python -m scripts.check_legacy_training \
  --baseline /path/to/main-6def4ea \
  --candidate /path/to/research-888daaf \
  --out output/new_legacy_parity
```

The output directory must be fresh. Full receipts stay at persistent
`output/review_delivery/legacy_parity_v1/` on the measuring host. This MR
contains the comparator, its artifact-free selftest, and a compact
[evidence manifest](review-evidence-2026-09-29.json):

- Report SHA256: `c8c97a7e8b94c7e0d1031ef60c86478c1ce8231f50a5bb75ea8c355c5cec2e33`.
- Source/recipe manifest SHA256: `cd7690ee0e0bffe7121bdd80d69c6923e88386192ecd28d3f5dde18f201a092b`.

New study receipts follow this summary/code/hash pattern. Original studies
remain intact in the archive. New commits include Codex co-authorship;
pushes receive whole-repository Black/Ruff and relevant Python 3.12 checks,
followed by manual CI dispatch. No MR is automatically merged or release
published. The hourly continuation resumes remaining work and reports
meaningful deliveries, research results, failures or required input.

# CF score attribution v1 journal

## 2026-09-27 — completed fixed-score join

Registration `638d675` preceded category-specific score inspection.
Instrument `c3ed618` adds this audit and its artifactless CI selftest; no
original trainer, scorer, oracle, index, splitter or diagnostic was edited.
All seven [preflight checks](preflight_checks.json) pass, including Black and
Ruff over 185 Python files. Synthetic tests compare the two contribution
totals to explicit positive×negative comparisons and retain null empty-class
terms, ties and the precedence of masked over conflicting targets.

The first analysis and exact rerun both exit 0, with complete logs and exit
records in `output/cf_score_attribution_v1/`. At the next continuation, these
completed artifacts were inspected and archived, not measured again. All
36 action/block/seed deltas reconstruct (maximum error
1.5265566588595902e-16). The 24 timing-specific and 12 pooled readings remain
the same as the original timing-mixture diagnostic. Every category count
matches the preceding executed/CF agreement report before interpreting scores.

Immediate-exam dense-right's no-conflict comparison contributions are
−0.070860/−0.039886/−0.031652 at seeds 0/1/2, while conflict contributions
are +0.003745/−0.008185/−0.003486. Both agree/agree and masked/agree pair
rankings decline in every seed. The [summary](summary.md) distinguishes
weighted contributions from pair AUCs and keeps all cells in the full report.
This locates the loss beyond conflicting exam examples; it cannot exclude
a training conflict influencing other examples through shared parameters.

All frozen source/input hashes and nine locked artifacts match. The original
model study's complete tracked-Python inventory has three additional audit
modules now; original manifests and results remain unmodified. Each new
diagnostic verifies the original saved source hashes directly.

Close this exploratory join. No new inference, fit, course, resampling,
sample removal, favorable seed selection, threshold change or promotion
occurred. A further model test needs its own single-knob registration and
independent exam; none is automatically released by these findings.

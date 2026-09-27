# Timing-mixture audit v1 journal

## 2026-09-27 — fixed diagnostic, completed

The parent model study was already unblinded and closed NO-GO. Registration
`1b2d906` froze this diagnostic before timing-stratified scores were read.
Instrument `96a5544` adds one metadata/score-only audit and its CI selftest.
No original Python source, generator, trainer, scorer, bars or checkpoint
was changed. Initial formatting identified two E501 lines, corrected before
measurement; the synthetic selftest passed on its first execution.

[Seven preflight checks](preflight_checks.json) all exit 0, including full
repo Black/Ruff (183 Python files). Tests compare every pair contribution
against a direct pairwise oracle, exercise tied scores, missing classes,
unmatched support, wrong block identities and a case where only cross-block
ranking changes the pooled score.

The first analysis and its exact verification each exit 0, with full logs
and exit records in `output/timing_mixture_audit_v1/`. All six original score
exports match their receipts; all sample pairs, labels, commands, worlds
and timing memberships match the complete fixed exam. Every one of the 12
original action-cell deltas and three primary macros reconstruct; maximum
accounting error 1.249000902703301e-16 is below the frozen 1e-12 tolerance.

Dense-right loss persists within the immediate exam block at all three
seeds (−0.067115/−0.048071/−0.035138), on 45 positive and 25 negative courses.
Both within-block and cross-block contribution deltas are negative. The
approach block has only four negative dense-right courses and five for
dense-left; its sparse readings stay explicit. Moving-right seed 0 has
negative AUC deltas in both blocks but positive pooled AUC, because positive
cross-block contributions outweigh negative within-block contributions.
The [summary](summary.md) retains all four original cells, not only these
selected observations. Interpretation is accounting, without intervals or
causal/deployment conclusions.

All nine locked artifact hashes match. The original timing study's strict
`--verify` compares its complete tracked-Python inventory, so adding this
audit module makes that inventory differ. Its original verifier/receipts
are retained unchanged. This audit separately verifies every original saved
source hash and input hash, then reconstructs every original primary-cell
reading from unchanged saved scores. No old hash or result was relaxed or
rewritten; the inventory difference is not a changed model result.

Close this diagnostic. No new inference, fit, course, bootstrap, favorable
seed selection, default change or promotion occurred. A further diagnostic
must declare its scope before more slicing; a training idea still requires
a new single-knob registration and independent exam.

# CF score attribution v1 — exploratory pair accounting

The timing model study is closed NO-GO, and both subsequent diagnostics are
unblinded. Freeze this score join before inspecting category-specific model
readings. Use only the same six saved score exports and common exam.

At each held-command warn@32 window, assign exactly one metadata category:
**agree** if the CF target is answerable and matches the executed target;
**conflict** if answerable and different; **masked** if CF answerability is
zero, regardless of its stored target. These categories are defined before
joining predictions and must reconstruct the prior agreement audit's counts.

For all four original action cells, all three matched seeds and each exam
timing block (approach/immediate), decompose AUC into the nine ordered
positive-category × negative-category pair contributions. Also retain the
same decomposition pooled over both timing blocks. Preserve every category's
window/class/course support, null missing-class AUC and all pair weights.
Reconstruct all 24 timing-specific and 12 original pooled action deltas to
absolute tolerance 1e-12, using unchanged sample/label/world/action identities.

Aggregate the nine contribution deltas into two disjoint totals: comparisons
involving **at least one conflict window**, and comparisons involving **no
conflict window** (agree/agree, agree/masked, masked/agree, masked/masked).
Their sum must equal the same full-cell AUC delta. These are contributions
under the original full-cell denominator, not scores on replacement exams
and not causal effect shares. Retain all nine terms so masked and agreeing
comparisons remain inspectable. Do not remove or relabel samples.

This is descriptive accounting after observing the regression, not a new
gate or confidence statement. Course/window overlap, rare classes and distinct
simulator draws remain limitations. Disagreement counts are not actual loss
or gradient exposure, and a score association cannot prove which supervision
caused learning. Do not add calibration thresholds, new bins, actions, seeds,
inference, fitting, generated courses, bootstrap or flight claims.

Validate every frozen input/source hash and all nine protected artifacts.
Verify full exam sample coverage and category counts before interpretation.
Archive all 36 cells and a numeric rerun. Any outcome leaves the original
NO-GO, approach recipe and champions unchanged and releases no training.

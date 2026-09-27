# CF score attribution v1 — the dense-right loss is not confined to conflicts

This **exploratory, unblinded accounting** joins existing scores to the fixed
agree/conflict/masked categories. No new inference, model fit, data draw,
bootstrap, sample removal or performance gate is introduced. All **36**
action/block/seed cells reconstruct their prior AUC deltas; maximum error
is **1.526557e-16**, below the registered 1e-12 tolerance. The original
timing-study NO-GO remains unchanged.

## Immediate-exam dense right

| Seed | Contribution from comparisons involving conflict windows | Contribution from comparisons without conflict windows | Full action/block AUC delta |
|---|---:|---:|---:|
| 0 | +0.003745 | −0.070860 | −0.067115 |
| 1 | −0.008185 | −0.039886 | −0.048071 |
| 2 | −0.003486 | −0.031652 | −0.035138 |

Every seed loses on comparisons involving **no conflicting window**. At seed
0, comparisons involving conflicts actually improve, partially offsetting
the other losses. The measured regression is not confined to the 84
conflicting exam windows identified by the preceding diagnostic.

These are additive contributions under the **original full-cell denominator**.
They are not AUCs on replacement exams, losses after deleting samples or
causal effect shares. In this cell all 342 negative windows are answerable
and agreeing, leaving only three nonempty positive/negative category pairs:

| Positive category | Positive windows / courses | Negative category | Pair weight | Pair AUC delta, seed 0 | Seed 1 | Seed 2 |
|---|---:|---|---:|---:|---:|---:|
| Agree | 264 / 24 | Agree (342 / 25) | 0.325123 | −0.063574 | −0.040310 | −0.014708 |
| Conflict | 84 / 10 | Agree (342 / 25) | 0.103448 | +0.036202 | −0.079121 | −0.033695 |
| Masked | 464 / 32 | Agree (342 / 25) | 0.571429 | −0.087833 | −0.046866 | −0.047023 |

Agree/agree ranking declines in every seed, with both classes supported by
more than 20 courses. Masked-positive/agree-negative ranking also declines
in every seed and has the largest pair weight. Masked means the CF oracle
excludes that candidate's label from CF loss; it does **not** mean the
executed label is missing or that other training signals cannot affect it.
Within-conflict and within-masked AUCs are null here because those categories
have no negative windows. No numeric chance fallback is substituted.

## All registered comparisons retained

The report contains every original dense/moving left/right cell at seeds
0/1/2, separately in approach, immediate and pooled exam blocks: 36 cells,
each retaining support and all nine ordered pair terms, including zero
terms and null AUCs. Category counts reconstruct the previous agreement
audit before score accounting. No unfavorable cell or seed is omitted.

For pooled dense-right, comparisons without conflicts contribute
−0.054708 / −0.014079 / −0.016379 across seeds; conflict comparisons contribute
+0.002137 / −0.011945 / −0.009506. Moving-left's positive AUC deltas retain
positive no-conflict contributions in both timing blocks in every seed.
Other cells contain mixed signs and remain available in [report.json](report.json).

## Interpretation and verification

This result narrows a localization hypothesis: the regression is broader
than the identified conflicting **exam** examples. It does **not** rule out
conflicting **training** targets affecting other examples through shared
parameters. Neither these contributions nor the earlier available-target
counts measure training gradients or establish a cause. Declining agreement
and masked comparisons should remain visible in any next experiment;
changing CF masks or loss weights is not validated by this diagnostic.

The first run and its exact verification both exit 0. Seven preflight checks
pass, including a direct pairwise oracle, category precedence, ties, absent
classes, dependency selftests, whole-repo Black (185 Python files), Ruff and
whitespace. All frozen source/input hashes and nine protected artifacts
remain unchanged. Run
`python -m experiments.cf_score_attribution_v1.audit --verify`
with retained inputs and the recorded runtime.

Close this score join. Keep the original bars, approach recipe and champions.
A next model experiment must name a falsifiable data/loss hypothesis, vary
one knob and use a new independent exam; these reused scores are development
evidence and cannot become that exam. Further exploratory slicing must
declare its scope first. [Definition](definition.md),
[registration](registration.json) and [journal](journal.md) retain the boundaries.

# Action-pair decomposition of a closed exam — 2026-09-20

This is a retrospective descriptive audit of `executed_weight_v1`, whose
six model outcomes and NO-GO verdict are already known. This definition is
written before inspecting action-conditional results, not before the
original study. No fitting, model inference, new courses, resampling,
replacement seeds, new gates or reinterpretation of that verdict is allowed.

Question: how much of each saved collision AUC@32, and of the paired change,
comes from comparisons within the same executed action category versus
comparisons across different categories? Action categories are the six
transit `act_id` values at each exported (rollout, frame) index. Speed and
scene geometry still vary within a category: this is not a controlled
counterfactual-action experiment or a causal attribution.

Inputs are all six immutable score NPZs and the original common exam of
`executed_weight_v1`. Freeze their paths/hashes in `registration.json`.
Report all three training seeds and both arms for classic, dense and moving;
room uses a separate navigation action catalog and is outside this audit.
Do not select a seed, action or subgroup based on its reading. Read metadata
and stored scores only; pixels and model weights are unnecessary.

For each positive-action i / negative-action j pair, report N+_i, N-_j,
their product, and the fraction of positive/negative score comparisons won
(ties receive half credit). Weight each pair AUC by N+_i N-_j / (N+ N-).
The complete matrix must exactly reconstruct the existing world AUC within
1e-12; diagonals are within-category contributions, off-diagonals across-
category contributions. Their candidate-minus-control contributions must
sum to the original paired AUC change. Also report conditional within/across
AUCs, their pair-mass shares and per-action positive/negative course support.
Missing classes yield null conditional scores, never fabricated 0.5 values.

Before interpretation, verify saved-score hashes against original receipts,
the dataset hash, aligned pairs/labels/worlds across models, valid integer
pair bounds, and action IDs against recorded physical commands and speed.
All original AUCs and deltas must reconcile. Synthetic selftests cover a
direct pairwise oracle, ties, permutations, missing classes/categories and
a case where group-constant scores have good pooled AUC but no within-group
ranking. Artifactless CI runs only synthetic tests.

Outputs: a rerunnable JSON report with complete matrices/support, a generated
Markdown summary for all transit worlds, and a static moving-world figure
showing within/across contributions for every seed. The descriptive tables
have no confidence intervals: overlapping windows and score-pair products
are not independent observations. No pooled action diagnostic becomes a
promotion criterion or replaces the frozen per-seed/guard requirements.

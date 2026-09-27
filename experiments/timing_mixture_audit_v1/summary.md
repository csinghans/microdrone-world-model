# Timing-mixture audit v1 — dense-right loss remains within a supported block

This is an **exploratory, unblinded diagnostic** of the closed timing study,
using only its six saved score exports and common-exam metadata. It adds no
model inference, fitting, generated course, bootstrap or performance gate.
The original NO-GO and approach default remain unchanged.

Dense right-veer AUC falls inside the **immediate exam block** in all three
registered seeds: **−0.067115, −0.048071, −0.035138**. That block has 812
positive windows from 45 courses and 342 negative windows from 25 courses,
meeting the original exam count floors descriptively. The pooled dense-right
loss therefore cannot be accounted for solely by cross-block comparisons.
This locates a measured loss; it does not establish its training mechanism.

## All four original cells, both exam blocks

Each delta is candidate (immediate-training) minus control (approach-training)
within the named **exam** block; model arm and exam block are distinct axes.

| Action cell | Exam block | Seed 0 AUC delta | Seed 1 | Seed 2 | Positive windows / courses | Negative windows / courses | Original count floors? |
|---|---|---:|---:|---:|---:|---:|---|
| Dense left | Approach | +0.002161 | −0.177977 | −0.078989 | 750 / 44 | 58 / 5 | Below |
| Dense left | Immediate | −0.024600 | +0.054571 | +0.015227 | 901 / 50 | 303 / 25 | Met |
| Dense right | Approach | +0.015887 | −0.018041 | −0.053348 | 826 / 45 | 61 / 4 | Below |
| Dense right | Immediate | −0.067115 | −0.048071 | −0.035138 | 812 / 45 | 342 / 25 | Met |
| Moving left | Approach | +0.199212 | +0.169666 | +0.054391 | 495 / 32 | 328 / 23 | Met |
| Moving left | Immediate | +0.087796 | +0.129322 | +0.065795 | 403 / 28 | 642 / 42 | Met |
| Moving right | Approach | −0.053553 | +0.001402 | +0.028558 | 445 / 29 | 367 / 31 | Met |
| Moving right | Immediate | −0.008430 | +0.018975 | +0.008940 | 200 / 16 | 946 / 45 | Met |

The 100-window / ten-course-per-class annotations are not new pass/fail gates
or power guarantees. Dense approach-block negatives are sparse despite the
full exam's sufficient pooled support. Keep these small-support readings,
without expanding the closed exam or interpreting them as precise effects.
Every table cell has both classes; the instrument also preserves null AUC
for hypothetical absent-class slices instead of returning the legacy 0.5.

## Exact accounting of the pooled dense-right loss

| Seed | Within-block pair contribution delta | Cross-block pair contribution delta | Original pooled action AUC delta |
|---|---:|---:|---:|
| 0 | −0.027022 | −0.025549 | −0.052571 |
| 1 | −0.021600 | −0.004423 | −0.026024 |
| 2 | −0.018854 | −0.007031 | −0.025885 |

Both components are negative in all seeds. Within-block comparisons account
for 49.70% of dense-right's positive×negative score pairs; cross-block pairs
account for the rest. These are additive AUC contributions weighted by pair
counts, not equally weighted block AUCs, independent observations or causal
effect shares. The full report retains all four pair directions and weights
for every original cell and seed.

Moving-right seed 0 exposes the opposite masking pattern: both block AUCs
decline (−0.053553 approach, −0.008430 immediate), yet pooled action AUC rises
**+0.010177**. Its within-block contribution is **−0.012211**, outweighed by
**+0.022388** from cross-block ranking. The previous statement that pooled
moving-right AUC improves in every seed remains numerically correct, but
must not be read as improvement inside every timing condition.

Moving-left gains occur in both blocks across all three seeds. Dense-left
patterns vary by seed and block, with especially sparse approach negatives.
All findings are descriptive on this one exam; there are no confidence
intervals here and the timing blocks also use different simulator draws.

## Verification and continuation

All **12** original action-cell deltas and all three original primary macros
reconstruct. Maximum pair-accounting error is **1.249001 × 10⁻¹⁶** (registered
tolerance 10⁻¹²). Both initial analysis and exact rerun exit 0. Seven preflight
checks pass, including the synthetic pairwise oracle, dependency selftests,
whole-repo Black (183 Python files), Ruff and whitespace. Nine locked artifact
hashes and all original timing-study source/input identities remain intact.

Run `python -m experiments.timing_mixture_audit_v1.audit --verify` with the
recorded runtime and retained inputs. [Report](report.json),
[definition](definition.md), [registration](registration.json) and
[journal](journal.md) contain the complete evidence and boundaries.

Next examine candidate explanations for dense-right failure **within the
immediate block**, such as the relationship between executed-action labels
and the geometric ranking probe, before choosing another training knob.
These data do not identify the cause. Any further slicing needs a separately
declared exploratory scope; any new model trial needs its own registration
and exam. No result here releases training or changes a frozen verdict.

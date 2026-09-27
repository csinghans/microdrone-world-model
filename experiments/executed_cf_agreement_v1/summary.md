# Executed/CF agreement v1 — target mismatch exists; regression cause remains open

This **exploratory metadata diagnostic** uses the frozen timing-study corpora,
with no new inference, model fit, course, bootstrap or performance gate.
All instantaneous transit-clearance reconstructions pass: maximum error
across the three inputs is **4.307475e-7 m**, below the registered 1e-4 m
instrument tolerance. This checks simulator metadata arithmetic, not physical
sensor accuracy.

Within the immediate exam block's dense-right held windows, **84 / 690
answerable windows (12.17%) from ten courses** disagree: the actual flown
future enters the warn radius, while the straight-line CF target says safe.
The other **464** windows are CF-masked and do not receive this CF loss.
These quantities do not demonstrate that the candidate learned the wrong
target or explain its AUC regression; no predictions are inspected here.

## Every registered exam cell

`E0→CF1` means the flown window is safe but the CF target is dangerous;
`E1→CF0` is the reverse. Counts below concern **answerable** CF labels only.
Masked windows stay in the final column and are not direct CF conflicts.

| Exam block | Cell | Disagreements / answerable windows | Disagreement courses | E0→CF1 | E1→CF0 | Masked windows |
|---|---|---:|---:|---:|---:|---:|
| Approach | Dense left | 5 / 276 | 1 | 0 | 5 | 532 |
| Approach | Dense right | 12 / 432 | 1 | 12 | 0 | 455 |
| Approach | Moving left | 28 / 416 | 7 | 0 | 28 | 407 |
| Approach | Moving right | 18 / 480 | 3 | 0 | 18 | 332 |
| Immediate | Dense left | 71 / 648 | 10 | 2 | 69 | 556 |
| Immediate | Dense right | 84 / 690 | 10 | 0 | 84 | 464 |
| Immediate | Moving left | 75 / 828 | 11 | 1 | 74 | 217 |
| Immediate | Moving right | 1 / 1,051 | 1 | 0 | 1 | 95 |

## Actual training partitions

Each entry is disagreements / answerable windows, followed by contributing
disagreement courses in parentheses. Seeds reuse the same development corpus
with fixed, overlapping training partitions; they are not independent new
data draws. Full masked and 2×2 counts/course IDs remain in [report.json](report.json).

| Training arm | Cell | Seed 0 | Seed 1 | Seed 2 |
|---|---|---:|---:|---:|
| Approach | Dense left | 2 / 62 (1) | 2 / 51 (1) | 5 / 59 (2) |
| Approach | Dense right | 0 / 100 (0) | 0 / 124 (0) | 0 / 111 (0) |
| Approach | Moving left | 0 / 104 (0) | 0 / 126 (0) | 0 / 146 (0) |
| Approach | Moving right | 0 / 104 (0) | 0 / 98 (0) | 0 / 79 (0) |
| Immediate | Dense left | 9 / 94 (1) | 0 / 82 (0) | 0 / 96 (0) |
| Immediate | Dense right | 5 / 183 (1) | 6 / 159 (2) | 6 / 193 (2) |
| Immediate | Moving left | 17 / 169 (4) | 15 / 160 (3) | 10 / 171 (2) |
| Immediate | Moving right | 4 / 188 (2) | 6 / 211 (3) | 4 / 186 (2) |

Candidate dense-right's available training conflicts are only 5–6 windows
from 1–2 courses (2.73% / 3.77% / 3.11% of answerable windows). Five windows
are E0→CF1 in every seed, with one E1→CF0 added in seeds 1/2. This differs
from the immediate exam's exclusively E1→CF0 pattern. Control dense-right
has no answerable conflicts on these training windows. Moving-left has more
candidate training conflicts yet its AUC improved in the closed model study.
Conflict counts therefore do not supply a simple explanation of which
action regressed. They describe available targets, not actual CF draws,
loss weights, gradient mass or learned response.

## Geometric ranking measures a different domain

| Input | Classic probe frames / courses | Dense | Moving | CF safer-side mismatches | Both CF labels answerable |
|---|---:|---:|---:|---:|---:|
| Approach development | 84 / 14 | 111 / 15 | 20 / 2 | 0 | 215 / 215 |
| Immediate development | 52 / 9 | 70 / 9 | 71 / 5 | 0 | 193 / 193 |
| Common exam | 425 / 72 | 802 / 82 | 177 / 19 | 0 | 1,404 / 1,404 |

The geometric probe and CF labels agree exactly on its selected safer side.
Both are based on the same kinematic assumptions. In every input and every
primary action cell, the probe and executed held-action exam share **zero
frames**: the probe selects forward-command frames, while those action cells
select left/right-command frames. Courses can overlap, so this does not
assert independent datasets. For exam dense-right, six courses overlap but
zero frames do. Improved geometric ranking cannot substitute for an
executed-right trajectory result.

The distance instrument is consistent; the difference is between stored
flown futures and idealized straight-line futures. A discrepancy is not
automatically an oracle bug. This audit does not fly alternate commands
from identical states and cannot certify hypothetical left/right outcomes.

## Verification and next question

Initial analysis and exact rerun both exit 0. Seven preflight checks pass,
including synthetic visible/masked target conflicts, geometric reconstruction,
probe parity, dependent selftests, whole-repo Black (184 Python files), Ruff
and whitespace. All original source/input hashes and nine locked artifacts
remain intact. Run `python -m experiments.executed_cf_agreement_v1.audit --verify`
using the retained inputs and recorded runtime.

Keep the closed NO-GO, approach default and champions. A next bounded
diagnostic could join the existing score exports to these predeclared target
categories to determine whether the observed ranking loss involves agreeing,
conflicting or masked windows. That question has **not** been measured here;
it needs its own declared scope and cannot by itself establish causality or
release training. [Definition](definition.md), [registration](registration.json)
and [journal](journal.md) retain the full boundaries.

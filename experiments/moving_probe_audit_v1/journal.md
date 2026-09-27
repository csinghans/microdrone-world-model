# Moving probe audit v1 journal

## 2026-09-28 — exploratory diagnostic closed

Registration `fc5f71b` preceded inspection of per-course, timing-block and
truth-side prediction breakdowns. The model-study aggregate NO-GO was already
known, so this is unblinded accounting, not confirmatory causal research.
The schema inspection found only truth/correctness flags in saved exports;
the scorer's strict inequalities make an incorrect flag compatible with
either an opposite ordering or a tie. The registration therefore specifies
identified bounds, not invented opposite-direction predictions.

Instrument `9ac59ae` passed synthetic tests before analysis. An independent
three-way prediction enumeration proves the bounds tight, including ties
and missing truth classes. Tests also cover frame versus course weighting,
empty cells and malformed arrays. Two long string literals were wrapped
after the initial Ruff check; the first selftest and all six preflight checks
passed. Black checks 188 Python files. All nine protected artifacts and 192
original saved source hashes match before measurement.

The first analysis and its exact numeric rerun both exited 0; complete logs
and actual exits are in `output/moving_probe_audit_v1/`. All 27 cells, twelve
original aggregate readings and course contributions reconstruct, with
maximum error 6.938893903907228e-17. No new fit, model inference, generated
course, bootstrap or changed gate was involved.

Moving's 134 probe frames / 16 courses split into approach 32/5 and immediate
102/11. Immediate-block accuracy deltas are −0.4117647058823529 /
−0.27450980392156865 / −0.0784313725490196; approach deltas are +0.0625 /
−0.09375 / −0.03125. The complete moving table has 59/35/19 lost frames and
19/4/10 gained frames across seeds. Declining course counts are 9/8/7,
improving counts 3/2/4, unchanged 4/6/5. Every course remains in the report.

Left-safer truth occurs on 101 frames / eleven courses; right-safer truth
on 33 / five. Correct left-truth counts change 82→25, 64→32 and 51→33;
correct right-truth counts change 9→26, 29→30 and 22→31. Control strict-left
count bounds [82,106]/[64,68]/[51,62] exceed candidate bounds
[25,32]/[32,35]/[33,35]. The decrease in strict-left preference is identified;
its split between extra strict-right choices and ties is not. Right-preference
bounds overlap; possible ties are bounds, never observed counts.

Seed 2 has frame-weighted delta −0.06716417910447761 but equal-course mean
delta +0.054174498746867084. This describes a different weighting of the
same data, not a replacement for the registered frame-level guard. Sparse
truth-side/block course counts remain explicit; no new uncertainty estimate
or performance bar is introduced. The old model-study NO-GO is preserved.

The new additive module changes the closed model study's strict Python
inventory; this audit verifies the original saved hash map without modifying
its manifest. All protected hashes remain unchanged. Future raw-score export
work could make exact ties/preferences observable, but would need tested
compatibility and separately declared rescoring. This audit releases no fit
or inference and makes no training-mechanism claim.

# Timing-pilot split-support journal

## 2026-09-27 — Scope registered

The full-corpus pilot remains closed with sufficient candidate support.
Before fitting, this new metadata audit freezes split seeds 0/1/2 and asks
whether its same structural minima hold in every train/validation partition.
It also inventories the scorer's geometric veer probe on those exact
partitions. No source data, label, splitter, model or earlier verdict changes.
Registration is committed before any partition counts are inspected.

Before any real audit counts, clarify the definition's overlap note:
per-action, per-class course counts DO add across disjoint train/validation
partitions. The overlap caveat applies when summing across classes/actions,
not across those disjoint partitions. The instrument checks this additive
identity as well as window counts. This changes no requirement or method.

## Instrument preflight

Registration commit `60e6a8d`. The new audit reuses the original index,
splitter, label producer, requirements checker and geometric probe selector.
Its selftest checks noncontiguous original IDs, absent worlds, wrong probe
truth, and corrupted window/course accounting. CI includes this artifactless
selftest. No production training/evaluation algorithm changed.

The first synthetic test failed because the generic schema fixture had
zero command vectors with forward action IDs; the existing producer correctly
rejected that mismatch. The fixture now supplies the real forward vector
and both label classes. The failed preflight log is preserved at
`output/research_integrity_selftest/early_intervention_split_v1_preflight.log`.
Initial development lint also found three long display strings; those were
split before validation. No real split counts were read during these fixes.

The corrected eight-command preflight passed: the new selftest, dataset
support, 15 requirements-checker regressions, geometric selector selftest,
whole-repository Black (179 Python files), Ruff, shell syntax and diff check.
Log: `output/research_integrity_selftest/early_intervention_split_v1_preflight_fixed.log`.

## 2026-09-27 — Completed: validation support remains insufficient

Instrument commit `eee839d`. The first actual audit completed with
`TIMING-SPLIT EXIT=0` and `timing-split-DONE`; no generation or model call
occurred. Both corpora retain their original hashes and exact full-corpus
support counts. For every seed, both arms use identical 144-course training
and 36-course validation memberships. They are disjoint and exhaustive.
Every action/class window and course count adds back to its whole-corpus
count; direct geometric probe selection matches filtering the full probe.

The registered diagnostic is **insufficient for both arms**, while the
original full-corpus candidate pilot remains sufficient. These statements
refer to different partitions and do not revise either set of bars.

| Arm | Training cells meeting minima | Validation cells meeting minima |
|---|---:|---:|
| approach | 7 / 12 | 0 / 12 |
| immediate | 12 / 12 | 2 / 12 |

Each denominator is three fixed seeds × two worlds × two veers. A cell
needs both classes, at least 20 windows and 3 distinct courses per class.
The candidate improves retained training support, but its validation
cells pass 0/4, 1/4 and 1/4 for seeds 0/1/2. None of its required validation
cells is classless; ten fall below the registered count minima. The control
has one classless required training cell and three classless validation
cells. Those cells do not have a defined action-specific AUC.

## The geometric probe has a separate limitation

Executed-action labels and the veer-ranking guard do not select the same
examples. The guard uses hypothetical left/right actions on recorded
FORWARD frames with a visible asymmetric threat. Full-corpus moving probe
support grows from 20 frames / 2 courses to 71 / 5, but **both arms' moving
validation probe counts are 1, 0, 0 courses** for seeds 0/1/2. Those partitions
cannot support a moving-stratum course bootstrap. No bootstrap was run.
The immediate seed-2 validation partition also has no classic probe frames.

All worlds, action cells, deficits and probe counts appear in the generated
[summary](summary.md); [report.json](report.json) retains the exact IDs,
all executed-action/now/CF support and hypothetical optimizer counts.
Count presence is not power, and the nominal one-epoch accounting records
no actual optimizer steps. The transit-only corpora say nothing about room
guards. No new model-performance verdict follows these metadata findings.

## Continuation and verification

Close this audit without a new seed, altered split, corpus expansion or
relaxed minima. Do not use these internal validation partitions as if they
were a complete action-specific or per-world veer exam. The timing idea has
training-support evidence; a future separately registered model study must
justify its endpoint support and independent exam before fitting, with
forward/room/now/veer guards and the embedded budget frozen. The source
pilot and every earlier NO-GO remain closed.

`python -m experiments.early_intervention_split_v1.audit --verify` recomputed
the report and summary exactly and rechecked all source/data/receipt/locked
artifact hashes, exiting 0. The nine protected artifacts are unchanged.
Logs are under `output/research_integrity_selftest/early_intervention_split_v1_*`;
`output/early_intervention_split_v1/EXIT` is 0 and `DONE` exists.
The [verification receipt](verification.json) also preserves the failed
synthetic preflight rather than presenting it as a scientific failure.
Run `bash experiments/early_intervention_split_v1/verify.sh` with the recorded
source/runtime to check the archive. Validation is local macOS / Python 3.14;
remote Linux CI and the optional training smoke were not run.

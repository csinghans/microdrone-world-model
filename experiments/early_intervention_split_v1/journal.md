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

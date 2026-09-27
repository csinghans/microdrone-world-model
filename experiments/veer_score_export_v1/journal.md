# Raw veer score export — instrument compatibility

## 2026-09-28 — complete

The closed moving probe audit could bound strict direction preferences but
could not recover exact ties from correctness flags. This instrument change
adds `veer_score_left` and `veer_score_right`: the two existing sigmoid warn
probabilities at the longest horizon, aligned with `veer_pairs`. It copies
already computed values and leaves strict correctness, selection, model
architecture, losses and training recipes unchanged. Empty probes export two
empty float arrays. Nonfinite probabilities cannot be exported.

The comparison reader treats the new fields as optional per arm. It accepts
old/old, old/new and new/new comparisons. If either field is supplied, both
must be real, finite, one-dimensional probabilities in [0,1], with the same
length as the probe. They must reproduce the saved correctness flag under
the original strict comparison. Equal scores remain incorrect for either
ground-truth side. Partial or inconsistent exports stop before metrics/RNG.

Before edits, `before.json` recorded all nine locked artifact hashes, the
three affected source hashes and 30 existing exports from five closed model
studies (15 matched pairs). After edits, all 30 files have identical hashes
and all 15 pairs still pass validation. No archived checkpoint was rescored,
no previous number was edited and no fit or scientific verdict was changed.

Seven recorded checks passed on their first execution:

- Probe wiring for single/two-frame/recurrent inputs checks raw probabilities,
  exact ties, nonfinite-output rejection, empty probes and unchanged RNG.
- Comparison selftests retain old/mixed/new numeric parity and exercise
  24 malformed raw-score arms, existing 81 malformed legacy-arm checks,
  empty arrays and lossless NPZ roundtrip.
- Shared geometric selection and the moving-timing decision selftests pass.
- Whole-repository Black (188 files), Ruff and whitespace checks pass.

See `verification.json` for commands, full-log hashes, actual exits, legacy
export identities and protected hashes. Rerun `python -m scripts.veer_probe_selftest`
and `python -m eval.compare_wm_scores --selftest`; both are artifactless and
already included in manual CI. These local checks are not a remote CI run.

Only future exports gain the raw fields. Missing values in old exports stay
missing; the earlier direction bounds and NO-GOs stand. A separately declared
fixed-checkpoint instrument study would be needed before collecting raw
scores for a closed experiment. This change does not release that work or
another fit, and makes no flight/hardware timing claim under the existing
512 KB / approximately 8 ms constraint.

The three shared source changes intentionally invalidate earlier strict
source-hash verifiers on the current tree. Reproduce those closed studies
using their original revisions (for example `16920e8` for the probe audit).
Do not alter their manifests to accept this later instrument.

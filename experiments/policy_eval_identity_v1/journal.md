# Policy-cell evaluation identity and publication — 2026-09-20

At `5d2ad0e`, `eval.eval_policy_cells` opened `--out` with `w`, replacing
previous results after flying. Repeated cell IDs silently collapsed in the
result dictionary: a synthetic two-cell evaluation saved only the last
cell. Its output recorded the policy pathname and metrics, with no world
model or cell-spec identity. These are instrument properties, not evidence
that a particular historical campaign used wrong inputs.

The [before receipt](before.json) pins the original source SHA. Run
`bash experiments/policy_eval_identity_v1/verify.sh` with the project Python
environment to reproduce the temporary-file overwrite and duplicate-ID
collapse. Models, environment and flight are doubles; no real score is
computed. The same script checks the
[compatibility receipt](spec_compatibility.json): all nine archived
`*cells*.json` list files, 52 cells in total, pass the stricter parser with
their original SHA, IDs and counts. This is metadata-only verification.

Changes:

- `--wm` selects a checkpoint directly, defaulting to the transit champion
  path. The file must exist. The explicit factory route loads this file
  without auto-training or replacing a champion and rejects metadata marked
  `autotrained_tiny`. The research runner's existing default factory route
  and dry-scoped fallback are unchanged.
- Saved schema-2 JSON retains `zip` and `cells`, adding SHA-256/path
  identities for policy, WM and cell-spec files, selected effective cells,
  override values, judge kind/skill name/version, runtime package versions
  and completion time. Named built-in baselines retain their explicit ID
  instead of a policy-file hash. Input files are checked before/after model
  loading and again after evaluation; a changed input prevents publication.
- Existing or locked outputs fail before model loading. The shared atomic
  publisher writes only a new result and preserves a concurrent writer.
  Exceptions close the environment; failed/nonfinite results cannot publish
  a partial or nonstandard-JSON record.
- Empty lists, duplicate/empty IDs, invalid counts/seeds/speeds/roles and
  unsupported kwargs fail early. Registered-world kwargs are rejected
  because `run_cell` does not forward them; that runner's scoring semantics
  are unchanged. `--n 0` no longer silently falls back to the original count.

Validation:

- `python -m eval.eval_policy_cells --selftest`: 12 isolated regressions
  covering real CLI parsing, recorded identities/settings, default/explicit
  WM selection, skill/baseline routing, invalid specifications, missing or
  marked-tiny WMs, changes during load/evaluation, failure cleanup, nonfinite
  metrics and competing result publication. Factory tests assert loaded
  components reach learned, reactive and hand-MPC constructors; the legacy
  factory route still calls its original loader.
- `python -m scripts.research_selftest`: all 16 existing regressions pass.
- `python -m world_model.checkpoint_io`: shared publication/alias/partial
  serialization/concurrent-writer checks pass.
- The before/compatibility verification script passes. All tests use
  temporary synthetic artifacts; the existing manual CI probe selftest now
  runs the expanded suite without requiring local champions.
- Whole-repository `black --check .` (170 Python files), `ruff check .`
  and `git diff --check` pass. All nine locked-artifact SHA checks pass
  before and after the work. No remote push or CI dispatch was performed.

Full logs are `output/research_integrity_selftest/policy_eval_selftest.log`,
`policy_eval_research_selftest.log` and `policy_eval_checkpoint_io.log`;
each process exits 0. No new policy fit, drone flight or scientific score
was run. No historical record, frozen bar or verdict was revised.

The JSON identifies input files and the selected judge's name/version; it
does not archive all transitive source code or certify a training/test seed
split. Retain the source revision and pre-registration alongside results.
The override flags do not themselves authorize a new draw or implement
pooled borderline arbitration; campaigns still apply their frozen rule.

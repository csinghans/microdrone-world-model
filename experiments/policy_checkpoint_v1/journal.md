# Policy checkpoint publication repair — 2026-09-20

At `2e6c22d`, `planner.learned_policy.train` derived the standard general
champion filename for `(edge_bias, hard, x_progress) = (True, True, True)`
and called `model.save` without checking it. Separately, the policy CLI
accepted `--out` but never forwarded it, including curriculum runs.

A synthetic reproduction replaced a temporary champion sentinel using a
fake policy/environment and confirmed the dropped CLI argument. It did not
create a simulator or run an optimizer. The
[before receipt](before.json) records the original source hashes.
`bash experiments/policy_checkpoint_v1/verify_before.sh` reruns that
reproduction on temporary files using the frozen Git revision.

The standard policy APIs now append `_candidate` to default output names
and check the destination before environment/model creation. Explicit
outputs must be fresh `.zip` files, with `_recurrent` present exactly when
the model uses that loader class. Reserved paths and aliases use the same
artifact-lock checks as world-model training. Both CLI branches forward
the resolved `--out`. Historical `zip_path()` lookups stay unchanged;
candidate evaluation uses an explicit `eval.eval_policy_cells --zip` path.

The WM writer's atomic publication was factored into a binary-stream writer
shared with policy saves. Actual SB3 source in the installed environment
accepts buffered binary streams; tests save and reload real PPO and
RecurrentPPO objects and assert every policy parameter matches. These are
initialized objects only: no `learn` call, drone simulation or flight score.
No temporary filename can cause SB3 to silently append another `.zip`.

Ordinary research outputs remain immutable. The module's existing smoke
training now explicitly requests replacement only for `_selftest` files,
and both recurrent smoke names include `_recurrent` for compatibility with
`load_policy`. The CLI's `--policy --selftest` invokes those existing three
smoke variants. The normal optimizer arguments and curriculum budget split
are unchanged. The environment is closed on success and failure.

Validation:

- `python -m scripts.policy_checkpoint_selftest`: locked/existing outputs,
  extension/model-name mismatches, no environment on preflight failure,
  both CLI routes, explicit selftest dispatch, original PPO/RNN constructor
  arguments and curriculum `(edge_p, chunks)`, cleanup on constructor/learning/save
  failure, plus real PPO/LSTM serialization and exact parameter roundtrips.
  Full log: `output/research_integrity_selftest/policy_checkpoint_selftest.log`;
  process exit 0. The new test is in manual CI's fast group.
- `python -m world_model.checkpoint_io`,
  `python -m scripts.checkpoint_io_selftest` and
  `python -m scripts.dataset_identity_selftest` pass after the shared writer
  refactor, including partial-save and concurrent-publication checks.
- `python -m scripts.research_selftest`: all 16 isolated regressions pass.
- Whole-repository `black --check .` (168 Python files), `ruff check .`,
  and `git diff --check` pass. All nine locked-artifact SHA checks pass.
- Call-site inspection finds the standard training APIs used by the CLI,
  module selftest and research runner; the runner already supplies explicit
  paths, with recurrent suffixes. Scoreboards keep their historical readers.

This is a persistence fix, with no new training draw, model evaluation,
research gate, retry, promotion or change to a frozen bar. Standalone
historical scripts that implement their own saves are outside this scope.

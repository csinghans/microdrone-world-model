# Policy CLI recipe repair — 2026-09-20

At `7e98802`, the policy CLI parsed `--seed` but omitted `seed0` from both
training calls. A requested seed 17 therefore reached the API's default 0.
It also implemented `--worlds` only as `args.worlds == "hard"`: a registered
comma-list or even an unknown name silently selected the classic default.
Curriculum ignored worlds, randomization, edge bias and x-progress flags.

The [before receipt](before.json) records the frozen CLI source SHA and
three intercepted calls. Reproduce it with
`bash experiments/policy_recipe_v1/verify_before.sh` using the project Python
environment. This executes only the original function with mocked training
APIs and output-path resolution: no optimizer, simulator or checkpoint write.

The CLI now forwards the seed to ordinary and curriculum training. World
names resolve through the existing scenario registry before output-path
selection. Explicit lists preserve order and multiplicity, so
`moving,dense,moving` remains a weighted three-slot schedule. Non-preset
world selections require a fresh explicit `--out`; the filename presets
continue to represent exactly classic or hard. Unknown and empty selections
fail before the training API is called. Registered skill worlds must already
be loaded into the process, as required by the existing registry.

Curriculum keeps its existing recurrent, classic-world speed-diet recipe.
Combining it with other worlds, `--randomize`, `--edge-bias` or `--x-progress`
now fails explicitly. The seed and resolved world sequence appear in the
startup log. Help text identifies `--n-steps` and `--lstm-size` as recurrent
settings; this change does not alter the stacked PPO rollout length.

Validation:

- `python -m scripts.policy_recipe_selftest`: real argument parsing checks
  default seed 0 and explicit seed 17, classic/hard presets, weighted lists,
  a registered custom world and seven invalid recipes. Three routes then
  call the real training functions with mocked library/environment objects,
  confirming the seed reaches both PPO and the environment and the world
  sequence reaches the environment. No fitting or drone simulation occurs.
- `python -m scripts.policy_checkpoint_selftest`: existing publication,
  cleanup, constructor/curriculum recipe and real PPO/LSTM parameter
  save-load checks pass. Its synthetic curriculum CLI fixture now uses the
  supported classic-only settings.
- `python -m scripts.research_selftest`: all 16 isolated regressions pass.
  The research runner directly calls the policy API with the registered
  `train_kwargs`; it does not route through this CLI parser.
- The original bug reproduction matches its saved receipt; all nine
  locked-artifact SHA checks pass.
- Whole-repository `black --check .` (169 Python files), `ruff check .`
  and `git diff --check` pass. The new selftest is in manual CI's fast group;
  this phase did not push or dispatch remote CI.

Full local test logs are in `output/research_integrity_selftest/` as
`policy_recipe_selftest.log`, `policy_checkpoint_selftest.log` and
`policy_recipe_research_selftest.log`; all three process exits are 0.

This establishes a CLI wiring defect and its correction, not a new model
result or a historical campaign's effective recipe. Existing scores,
negative verdicts, frozen gates and checkpoints are unchanged. No new
training draw was started. Future studies should retain the command and
resolved startup configuration with their pre-registered recipe.

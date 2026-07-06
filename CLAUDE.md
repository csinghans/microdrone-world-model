# CLAUDE.md — working in microdrone-world-model

A tiny latent world-model stack for micro-drones. The wedge: **how much
anticipation can you buy under embedded constraints** (512 KB, ~10 ms
decisions, one fixed 60° camera)? Everything here serves that question.

## Environment & commands

```bash
conda env create -f environment.yml && conda activate microdrone-wm
pip install -e .                      # flat packages, no sys.path hacks

black . && ruff check .               # line length 88, select E/F/I/W
python -m <module>                    # EVERY module has a selftest that
                                      # prints "XXX OK" and asserts it
python -m scripts.train --epochs 80              # world model
python -m scripts.train --policy --worlds hard   # PPO policy
python -m scripts.demo / -m scripts.evaluate / -m eval.<scoreboard>
python -m scripts.research skills/<name>         # autonomous research loop
```

CI: lint + fast selftests on push/PR; training smoke is manual/weekly.

## Architecture (one line each)

- `world_model/` — bearing-aware encoder, multi-horizon residual predictor,
  dual-ring collision heads, JEPA losses, training loop + veer-ranking probe.
- `planner/` — action set, hand latent-MPC + reactive baseline, learned
  policies (PPO over the model's outputs), safety filter.
- `sim/` — 48 Hz env + PID velocity commander, **scenario registry** (worlds
  register once; builtins classic/dense/moving keep ids 0/1/2), scenarios, DR.
- `datasets/` — intervention rollouts + motion-aware counterfactual oracle.
- `eval/` — frozen historical scoreboards + `episode.py` (the unified,
  path-recording runner all new work uses).
- `skills/` — flight capabilities as plugins: scenarios, frozen
  targets/guards, knob schedule, trajectory-level success predicate.
- `scripts/research.py` — the gate runner; `.claude/commands/research.md` —
  the researcher's charter for agent-driven campaigns.

## The measured discipline (non-negotiable house rules)

1. **Every claim comes from a rerunnable selftest or eval** — no numbers
   from memory, no prose-only results.
2. **One knob per training run.** Multi-variable runs prove nothing.
3. **Pre-registered bars are immutable.** Skills freeze targets and guards
   at their version; campaigns may add knobs, never move bars.
4. **Guards are sacred.** A win that breaks a guard is a hole that moved.
5. **Honest negatives get recorded**, not retried into passing. The only
   legitimate re-measurement is the built-in n=60 borderline recheck.
6. **Harness error ≠ scientific failure**: fix the tool, rerun the same
   knob; never edit recorded numbers.
7. **Never tag a release on your own** — propose it; the user decides.
8. Expect run-to-run variance (MPS nondeterminism): mechanisms reproduce,
   third decimals don't — write claims in that two-tier language.

## Conventions & gotchas

- `output/` is git-ignored; the policy-zip filename suffix IS the experiment
  id (`zip_path` bools); skill campaigns write to
  `experiments/<skill>/{journal.md,results.json,artifacts/}` and the runner
  makes path-scoped `gate(<skill>): K<i> — <verdict>` commits.
- `load_policy` sniffs `_recurrent` in the zip basename — keep it for
  recurrent artifacts.
- `LearnedPolicy` infers stack depth AND the x-progress layout from the
  loaded obs dim (47 vs 48 per step) — old zips keep flying; don't break
  that inference.
- Selftests that train must save to `*_selftest*` artifact names so they
  never clobber real checkpoints.
- Long runs go in background queues with `*-DONE` echo markers; deviation
  knob JSONs must live at a persistent path (not a sandboxed tmp dir).
- Never judge a run by `... | tail -N` + `&&`: a pipe masks the exit code,
  and stderr (unbuffered) lands *before* block-buffered stdout, so the
  traceback is exactly what tail cuts off. Capture the full log to a file
  and `echo EXIT=$?` — a green-looking tail hid a failed smoke once.
- CI runners have NO local artifacts (output/ is git-ignored): every
  selftest must be self-contained via `load_or_train` / a dry-scoped
  stand-in, never a bare `load_model()`/champion-zip read. Two weekly-job
  steps sat broken-from-birth this way — the job had never actually run.
- Current champions: general = `output/ppo_wm_policy_edge_hard_xp.zip`
  (hard worlds + odometry pin + edge diet); gap-flight =
  `experiments/gap_flight/artifacts/ppo_gap_flight_KD1.zip`.

- `scripts.research run` plays the WHOLE knob schedule unconditionally: a
  knob whose pre-registration is CONDITIONAL (released only on an earlier
  knob's reading) must be arbitrated with `research step`, never `run`
  (measured: dodgeball K2 played against its own release condition, 2026-07-06).

## Relationship to nanodrone-ai

This repo grew out of the nanodrone-ai course (Lesson 29) and inherits its
voice: state limits where they bite, prefer scoreboards to demos, and keep
the embedded budget (512 KB, currently 137-162 KB) in every design
conversation. The course is frozen at v1.0; new research lands here.

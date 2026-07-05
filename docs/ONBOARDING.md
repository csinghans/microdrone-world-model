# Onboarding — your first hour, then your first campaign

This is the shortest verified path from `git clone` to running real
research here. It works the same whether you are a person or an AI
agent; agents should also read
[`.claude/commands/research-operator.md`](../.claude/commands/research-operator.md)
(the operator charter) before touching a campaign. 繁體中文讀者：先看
[docs/START-HERE.zh-TW.md](START-HERE.zh-TW.md)。

Words you don't know yet (knob, gate, bar, guard, draw, champion…) are
all in [docs/GLOSSARY.md](GLOSSARY.md) — keep it open in a tab.

## 0. What this repo is, in three sentences

A tiny latent world model (81 KB of weights) gives a simulated 27 g
drone ~0.7 s of anticipation, and a set of policies fly on its outputs.
New flight capabilities are **skills** — plugins declaring scenarios,
frozen pass/fail bars, and an experiment schedule — which an autonomous
runner executes as **campaigns**, one measured gate at a time. The
product of this repo is not the model; it is the **journals**: every
claim, win or loss, traces to a rerunnable command.

## 1. Environment (three commands, verified 2026-07-05)

```bash
conda env create -f environment.yml && conda activate microdrone-wm
pip install --no-deps git+https://github.com/utiasDSL/gym-pybullet-drones.git
pip install -e .
```

(The sim dependency is a deliberate second step — conda's inline pip
chokes on it under some versions. If you use uv/venv instead, mirror
`environment.yml`'s package list.)

**Smoke it** (~2 min, matches the push-CI battery):

```bash
python -m skills.base && python -m sim.scenario_registry && python -m sim.envs
python -m skills.gap_flight.skill && python -m eval.eval_duel_plots --selftest
```

Every module in this repo has a selftest that prints an `XXX OK` line
and asserts it — if one fails on a fresh clone, that is a bug; please
report it.

## 2. Fetch the champions (~1 min)

Measured artifacts are git-ignored on principle, so a fresh clone can't
fly real campaigns yet. Pull them, hash-verified:

```bash
python -m scripts.fetch_champions
```

## 3. Read one journal (15 min, the highest-value 15 min here)

Read [`experiments/gap_flight/journal.md`](../experiments/gap_flight/journal.md)
top to bottom — 113 lines that walk a complete campaign: an honestly
predicted zero-shot failure (K0), targets passing while a guard breaks
(K1), a deviation knob with a written rationale (KD1), and a PASS with
every number against its frozen bar. Every mechanism you'll use is in
there. Then skim
[`experiments/closing_door/journal.md`](../experiments/closing_door/journal.md)
to see a *benchmark* campaign (four contenders, same seeds, two
figures).

## 4. Fly a dry gate (2 min)

```bash
python -m scripts.research doctor skills/gap_flight            # preflight
python -m scripts.research step skills/gap_flight --knob 0 --dry --no-commit
```

`doctor` is your preflight for *everything*: schema, worlds actually
fly, artifacts present, the cost estimate before you pay it. `--dry`
runs the whole gate machinery at n=2 with tiny stand-ins — safe
anywhere, including CI.

## 5. Your first real measurement (5 min)

```bash
python -m eval.eval_policy_cells \
    --zip experiments/moving_gap_v2/artifacts/ppo_moving_gap_v2_K3.zip \
    --cells experiments/metric_grounding/m2_cells.json --only dense@0.8
```

That's a real cell: 30 seeded flights of the current best policy
through dense clutter, crash rate out. You have now produced a number
with the same machinery every journal number came from.

## 6. Your first campaign

1. Pick an idea from [docs/RESEARCH-IDEAS.md](RESEARCH-IDEAS.md) (they
   are graded ★ / ★★ / ★★★ — start at ★) or bring your own.
2. Scaffold: `python -m scripts.new_skill my-skill` (add `--kind moving`
   for a moving scenario). Every convention is pre-filled; every
   decision left to you is a `TODO(researcher)` marker.
3. **Write the docstring pre-registration first** — scenario, why it
   separates policies, per-knob hypotheses, what the bars mean. Bars
   freeze when the skill lands; campaigns may add knobs, never move bars.
4. `python -m skills.my_skill.skill` → selftest green (write the
   soul-assert: the one synthetic-path check that IS your skill).
5. `python -m scripts.research doctor skills/my_skill` → green.
6. `python -m scripts.research step skills/my_skill --knob 0 --dry --no-commit`.
7. Add your selftest line to `.github/workflows/ci.yml`.
8. Launch: `python -m scripts.research run skills/my_skill` — the
   runner journals, rechecks borderline cells, and commits per gate.
   Judgment *between* gates is yours (or a researcher-mode agent's):
   the charter is [`.claude/commands/research.md`](../.claude/commands/research.md).

## Wall-clock expectations (Apple Silicon; CPU is slower)

| thing | time |
|---|---|
| fresh env + install | ~5-10 min |
| selftest battery | ~2 min |
| `doctor` / dry gate | seconds / ~2 min |
| one eval cell (n=30) | ~1-3 min |
| a zero-shot knob (all cells) | ~5-15 min |
| a training knob (450k / 900k steps) | ~30-60 / 60-120 min |
| a full campaign | one evening to overnight |

## Honesty notes that will save you a bad day

- **MPS vs CPU:** training auto-selects MPS on a Mac; evals force CPU.
  Mechanisms reproduce across machines; third decimals don't. Never
  compare your single draw against a journal's single draw and call it
  a regression — see "two-tier claims" in the glossary.
- **Dense-slice model metrics are weather, not climate** (single-seed
  dense AUC spanned 0.47–0.99 across five same-recipe retrainings).
  Flight gates with n=30/60 and rechecks are the reliable instrument.
- **Some manual scoreboards assume local artifacts** (`eval_hard_worlds`
  wants several policy zips; `eval_robustness` wants the robust
  checkpoint). `fetch_champions` covers the campaign path; the
  historical scoreboards may still need their own training runs.
- The runner makes **path-scoped commits per gate** — keep your tree
  clean before launching (`doctor` warns about this).

# Contributing

Start with [docs/ONBOARDING.md](docs/ONBOARDING.md) (one hour, verified
path) — 繁體中文導覽在 [docs/START-HERE.zh-TW.md](docs/START-HERE.zh-TW.md)。
The non-negotiable house rules live in [CLAUDE.md](CLAUDE.md); the words
in [docs/GLOSSARY.md](docs/GLOSSARY.md); ideas sized for a first
contribution in [docs/RESEARCH-IDEAS.md](docs/RESEARCH-IDEAS.md).

## What a campaign PR must contain

- [ ] the skill package (`skills/<name>/skill.py`) whose **docstring is
      the pre-registration**, written before any number existed — bars
      are frozen at skill version; campaigns add knobs, never move bars
- [ ] `experiments/<name>/journal.md` + `results.json` — the numbers,
      gate by gate, honest negatives included (they are contributions)
- [ ] any referenced policy artifacts pinned by sha256 (the runner
      records them in results.json; large files go to a Release, not git)
- [ ] the skill's selftest line added to `.github/workflows/ci.yml`,
      and CI green — `doctor` and a `--dry` gate must pass on a clone
      with nothing but `fetch_champions` run
- [ ] plots, if the campaign is a benchmark/duel (committed under
      `experiments/<name>/`, force-added past the global `*.png` ignore)

## What review checks (and what it doesn't)

Review verifies the *discipline*, not the outcome: single-variable
knobs, frozen bars, sacred guards, rechecks where the rule fires,
rationale-before-launch on any deviation. A campaign that honestly
fails its targets merges just like a pass — the journal is the product.

## Code changes outside campaigns

Match the house style (`black`, `ruff`, line length 88); every module
keeps a `--selftest` that prints `XXX OK` and asserts it; selftests must
be self-contained on artifact-less runners (`load_or_train`, dry
stand-ins — never a bare champion read). If you learned a trap the hard
way, add it to CLAUDE.md's gotchas: that file is the repo's scar tissue.

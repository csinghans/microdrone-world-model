# Glossary — the words this repo runs on

Alphabetical-ish, grouped by layer. Every term links to a live example.

## The experiment layer

- **campaign** — one skill's full research arc: a pre-registered knob
  schedule executed gate by gate until the targets pass or the budget
  runs out. Example: [gap-flight](../experiments/gap_flight/journal.md).
- **knob (K0, K1… / KD1…)** — one experiment: a *single* variable turned
  (a diet change, a budget change, a zero-shot baseline). "One knob per
  run" is house rule #2 — multi-variable runs prove nothing. `KD*` are
  **deviation knobs**: unscheduled experiments a researcher may add
  *only* with a written rationale committed before launch
  ([the first KD1](../experiments/gap_flight/journal.md)).
- **gate** — the measured verdict at the end of a knob: every cell flown,
  every criterion checked, journal + results written, a path-scoped
  commit made. Verdicts: `passed` / `continue` / `guard_regression`.
- **cell** — one (world × speed) measurement unit, e.g. `dense@0.8`:
  n seeded episodes, crash/success/clearance aggregated. Speeds are
  **cruise factors ×0.8 m/s** (so `@1.5` = 1.2 m/s — a classic trap).
- **bar** — a criterion's frozen threshold. Bars freeze when the skill
  version lands, *before any number exists*; campaigns may add knobs,
  never move bars.
- **target vs guard** — targets are the cells the campaign claims to
  improve; **guards** are regression bars on everything the champion
  already does. *Guards are sacred: a win that breaks a guard is a hole
  that moved* (see the moved-hole refrain below).
- **recheck** — any cell landing within ±0.08 of its bar automatically
  gets a fresh n=60 block **pooled** with the original (judged at
  combined n). Pooling, never replacement — the calibration study
  ([sweep2_noise](../experiments/sweep2_noise/journal.md)) caught a
  replacement-style recheck re-rolling a passing read into the one bad
  block in ten. The rule has also flipped verdicts the right way
  ([26.7 % → 48.3 %](../experiments/metric_grounding/journal.md)); a
  bar without a recheck rule is softer than it looks. (Pooling
  semantics are prospective from 2026-07-05; older journals record the
  replacement-era numbers.)
- **soul-assert** — the one synthetic-path selftest check that encodes
  what a skill is *about* (gap: through=success/around=fail; moving-gap:
  now=success/was=fail; door: on-time=success/late=fail). If you can't
  write it, the success predicate isn't done.

## The evidence layer

- **draw** — one training run's random outcome. **Two-tier claims**:
  *mechanisms* reproduce on every draw; *point numbers* wobble with the
  draw (dense AUC spanned 0.47–0.99 across five same-recipe draws).
  Write claims in that two-tier language; publish ranges, not best runs.
- **instrument discipline** — knowing which measurements can bear
  weight: flight gates at n=30/60 with rechecks yes; single-seed
  per-world AUC no; the fast-solo cell (`sweep@2.0`) only at n≥60.
- **honest negative** — a failed hypothesis recorded with the same care
  as a win, never retried into passing. Two campaigns here are *built*
  of them ([grounding](../experiments/metric_grounding/journal.md),
  [calibration](../experiments/head_calibration/journal.md)).
- **harness error ≠ measurement** — when the *tooling* breaks (a wrong
  path, a sandboxed tmp dir), fix the tool and rerun the same knob;
  never edit recorded numbers, never count it as a scientific retry.
- **the moved-hole refrain** — "patch the band you point at, watch the
  hole move." Measured six times. Corollary from moving-gap v2: the
  hole *closes* when the diet holds every band at once.
- **a better detector is not a better flight** — the house's oldest
  refrain (four measured sightings, sharpest at
  [v0.5 M2](../experiments/metric_grounding/journal.md)): model-layer
  gains do not transfer to closed-loop crash rates by right. Hence:
  evaluate by crash rate, not loss.

## The stack layer

- **champion** — the current title-holder: best-or-tied on the full
  scoreboard with **zero broken guards**, recipe recorded and
  reproducible. General champion ≠ skill champions (each passed skill
  has its own); a contender that wins its target cells but breaks a
  guard stays in the archive, not on the throne.
- **diet** — the mixture of worlds a policy trains on (e.g.
  `classic×2 + dense + moving + gap + moving_gap + solo`). Re-weighting
  the diet is the repo's most-measured knob family.
- **chassis** — the frozen non-diet part of a training recipe
  (x-progress + edge-bias + budget). "K1 on the KD1 chassis" = only the
  diet changed.
- **warn / crit rings** — the two collision heads: P(within 0.7 m) and
  P(within 0.35 m) per horizon. Two rings because one ring is a region
  test, not a risk gradient — inside the warn ring only the crit ring
  still carries signal (the gap campaign's real exam).
- **aimed encounter** — moving scenarios must aim the mover to meet the
  drone around arrival time; an unaimed mover misses on most seeds and
  measures nothing (MovingCrosser's convention, inherited by every
  moving skill).
- **`builtin:` contenders** — non-zip baselines the runner can bench:
  `builtin:reactive` (privileged-direction danger-now — it can only
  lose on *timing*) and `builtin:wm_mpc` (the hand latent-MPC).
- **operator vs researcher** — two agent modes: the researcher
  ([charter](../.claude/commands/research.md)) judges between gates and
  may write deviations; the operator
  ([charter](../.claude/commands/research-operator.md)) executes,
  reports in a fixed format, and never designs. Not a demotion — a
  division of labour.

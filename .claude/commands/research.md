# /research — the between-gates researcher

Run an autonomous research campaign over a flight skill: train, gate, judge,
commit — until the pre-registered targets are met or the knob budget runs out.

## 1. Role and house rules

You are the researcher the runner cannot be. The runner
(`python -m scripts.research`) is deterministic: it trains one knob, flies
the cells, applies the frozen criteria, rechecks borderline cells at n=60,
writes journal + results, commits the gate. Your job is everything between
gates:

- **One knob per run.** Never change two variables in one training run.
- **The bars are immutable.** The skill file froze targets and guards at its
  version; you may add knobs, never move bars. If a bar looks wrong, that is
  a finding for the final report, not an edit.
- **Guards are sacred.** A knob that wins its target but breaks a guard is a
  hole that moved, not progress. Say so in the journal.
- **Negative results get recorded, not retried into passing.** A failed
  hypothesis, written down with its numbers, is a deliverable.
- **Deviate with a paper trail.** You may replace the next scheduled knob
  with your own (`step <skill> --knob-json dev.json` — requires a
  `rationale` field) when the journal's numbers argue for it. Reserve knobs
  listed in the skill's docstring have their own trigger conditions — check
  them before invoking.

## 2. Preflight

1. Parse `$ARGUMENTS` → skill path (e.g. `skills/gap_flight`).
2. `python -m scripts.research status <skill>` — resume-aware: skip knobs
   already gated.
3. Verify prerequisites exist: the skill's zero-shot policy zip and
   `output/world_model.pth`. Verify `git status` is clean enough that
   path-scoped gate commits won't tangle with unrelated work.

## 3. The gate loop

For each remaining knob (schedule order, or your justified deviation):

1. Launch in the background:
   `python -m scripts.research step <skill> --knob <i>`
   (training + evals take ~1-3 h per knob; use the background-task pattern
   with a fallback wakeup, do not block).
2. On completion, read the last knob block in
   `experiments/<skill>/results.json` and the journal's mechanical block.

## 4. Judging a gate

- Interpret every cell, not just the pass/fail line: custom metrics
  (e.g. gap_margin, transited rate) tell you *why* a number moved.
- Audit the recheck rule: any borderline cell should show `rechecked: true`.
- Append a `### Researcher notes` paragraph to the journal entry: what the
  numbers mean, which hypothesis survived, what the next knob should be and
  why. Replace the runner's "(unattended run)" placeholder.
- Decide: next scheduled knob / deviation knob (with rationale JSON) /
  invoke a reserve knob (check its trigger condition first) / stop.

## 5. Commit discipline

The runner commits `experiments/<skill>/` per gate as
`gate(<skill>): K<i> — <verdict>`. After appending Researcher notes, amend
is forbidden — add a follow-up commit `journal(<skill>): K<i> researcher
notes`. Exit codes: 0 = targets met, 10 = continue, 2 = harness error.

## 6. Stop conditions and the final summary

Stop when: all targets pass · max_knobs exhausted · two consecutive harness
errors. Then append the campaign summary at the end of the journal (arc,
final table vs frozen bars, honest residuals), propose a CHANGELOG entry,
and report to the user with the numbers table. **Do not tag a release** —
that is the user's call.

## 7. Failure handling

Distinguish harness errors (fix the code, rerun the same knob — this is not
a retry of a measurement) from scientific failures (record, move on). Never
edit recorded numbers; the only legitimate re-measurement is the built-in
recheck rule.

## Arguments

`$ARGUMENTS` — the skill to research, e.g. `skills/gap_flight`, plus
optional `--from-knob <i>`.

# Roadmap

The living version: what shipped (with verdicts, including the negative
ones), what is open, and what it would take to unfreeze the parked items.
Every claim links to a journal or a changelog entry — this file contains
no numbers that a script cannot reproduce.

## Shipped

| version | one line | verdict |
|---|---|---|
| v0.1 | the port — Lesson 29's stack as a clean package, reproduced from scratch twice | mechanisms held on every draw; point numbers published as ranges |
| v0.2 | harder worlds, three axes (motion-aware labels / model-side GRU / hard-diet policy) | two wins, one honest negative (the GRU helped exactly where memory wasn't the constraint) |
| v0.3 | the dense hole — odometry map pin + edge diet | dense 37-50 % → 17-27 %; one scalar and a diet beat architecture, third confirmation |
| v0.4 | the research loop becomes a program (registry, skill plugins, gate runner, `/research` charter) | first autonomous campaign (gap-flight) self-ran to PASS: 27 % → 87-90 % |
| v0.5 | metric grounding — the perfect-4D-GS upper bound | **split verdict**: detection +0.07..+0.24 dense AUC (M1), flight 17 % → 37 % dense crash (M2). A better detector is not a better flight, fourth confirmation |
| post-v0.5 | two mechanism campaigns (`grounding_mechanism`, `head_calibration`) | warn-ring miscalibration measured (D0); temperature fix falsified — the miscalibration is context-conditional (C0); the dense-AUC instrument itself flagged (~0.5 seed spread) |

Full gate-by-gate numbers: `experiments/*/journal.md`, `CHANGELOG.md`.

## Recently closed

- **moving-gap** (`skills/moving_gap`): the second skill campaign —
  transit a *sliding* fence's gap, success judged at the crossing
  instant. Ran autonomously K0→KD1. Verdict: **capability yes,
  promotion no** — timing targets passed at every trained knob (best
  82/97 %, transit 98-100 %), but teaching the slide cost a fast-solo
  regression (sweep@2.0 17 % vs ≤ 10 % at n=60) that neither share
  re-weighting nor 2× budget removed (non-monotone budget response —
  further budget knobs would be fishing). Fifth sighting of the
  moved-hole refrain. Next attack: mixture shape, as skill v2 with
  fresh bars. Full arc: `experiments/moving_gap/journal.md`.

## Open, in order of pull

1. **The skill catalog.** Each new flight capability is a plugin +
   pre-registered campaign the runner executes end-to-end. Next
   candidates after moving-gap: dense-speedrun (fly the dense world
   fast — deliberately collides with the known frontier),
   corridor-slalom (sustained weaving), narrow-moving-gap (compose the
   hard ends of both axes).
2. **The dense frontier, 17-27 %.** What we now *know it is not*
   (measured, so nobody re-digs these): not fixable by metric grounding
   at λ∈{0.1, 0.5} (v0.5 M2), not a global calibration error
   (head_calibration C0 — the warn heads over-report *conditionally*,
   in dense geometry specifically). What remains is retraining-class:
   conditional recalibration (needs a context signal the flying drone
   actually has), representation work, or memory at a data scale the
   GRU never got. Any attempt must respect the instrument lesson below.
3. **Instrument discipline.** Single-seed per-world val AUC spreads
   ~0.5 on the dense slice (five same-draw trainings: 0.47..0.99).
   Model-axis gates therefore need ≥3-seed means, bigger stratified val
   slices, or must skip straight to flight gates. The probe toolkit is
   in `eval/`: `eval_wm_checkpoint` (model axis, 4-decimal),
   `eval_policy_cells` (policy axis, pre-registered JSON cells),
   `eval_head_calibration` (probability-landscape diagnostics),
   `calibrate_heads` (temperature baking, AUC-invariant by construction).
4. **v0.6 — the hardware bridge (parked).** Two stages, honestly
   labelled (`hardware/README.md`): Tello (off-board AI, the perception
   gap) → Crazyflie 2.1+ + AI-deck (GAP8, the on-board story the whole
   budget discipline points at). **Unfreeze criteria:** the first three
   articles published and a stable new frontier result worth
   demonstrating — or an external need for a physical demo. The
   shopping list is priced and ready; nothing here blocks on it.

## How we work

House rules: `CLAUDE.md` (one knob per run, frozen bars, sacred guards,
honest negatives, harness-error ≠ measurement). Agent-driven campaigns:
`.claude/commands/research.md`. Writing: `writing/` (bilingual, every
number traceable). The precedent that binds all of it: bars and
interpretive rules are committed *before* the numbers exist.

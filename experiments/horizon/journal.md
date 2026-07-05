# horizon — the chaining bottleneck, attacked at the architecture

## Pre-registration (2026-07-06, frozen before any number exists)

**Hypothesis (inherited from the slalom arc).** Chaining fails because
the policy's observation cannot represent the NEXT gate: at dx=0.70 and
cruise the gate period is 0.875 s, the longest collision-head horizon
is k=32 ≈ 0.67 s, and the observation carries head outputs only — the
camera sees gate k+1, the bottleneck discards it. H1 extends the
horizon ladder to k=48 (1.0 s > 0.875 s): the whole stack — labels,
predictor heads, collision heads, and therefore the policy observation
(10 probabilities per candidate instead of 8) — retrains under
`WM_HORIZONS=4,8,16,32,48`. One coupled system-level knob: the stack's
horizon. Everything else (hard data diet, 96×120 seed 0, 80 epochs,
v2-combination policy diet + slalom3_fixed, 900 k, the slalom-v2 exam
cells and bars) is inherited unchanged.

Honest data note: H_MAX drives the intervention hold lengths, so the
H1 dataset is necessarily a different draw (longer holds, fewer long
windows at L=120) — recorded, not hidden; the exam is closed-loop
flight, where the draw lesson says the verdict belongs anyway.

**The pre-stated falsifiable signature (from the slalom-v2 close):**

- Baseline (k=32 stacks): slalom3@1.0 success 0 %, chain_break_at
  1.33-2.10 across four trained attempts.
- **Support:** chain_break_at moves first — ≥ 2.5 mean — whether or not
  success clears the bar. Full support: success ≥ 0.70 (the inherited
  target on the 0.97-ceiling arena).
- **Refuted:** success ≈ 0 AND chain_break_at unmoved (< 2.5) with the
  manipulation checks green — then the bottleneck is not observability
  (credit assignment / exploration become the live suspects) and the
  campaign closes honestly.

**Bars (inherited verbatim from slalom-v2):** target slalom3@1.0 ≥
0.70; guards gap ≥ 0.75, mgap ≥ 0.70, cluttered ≤ 0.05, sweep@2.0 ≤
0.10 (all on the NEW stack; n and seeds per `exam_cells.json`, judged
with the skill's own predicates via `eval_policy_cells --skill`).
Manipulation checks (harness, not science): WM48 trains to completion,
val AUC@48 > 0.60, deploy budget prints and fits; the classic-stack
regression probe already reproduced 0.8389/0.7511/0.8390 bit-for-bit
after the layout surgery.

**H2 (reserve, played only if chain_break moves but success
undershoots):** k=64 (1.33 s — two gate periods). No other reserves; a
refuted H1 closes the campaign.

**Protocol:** every step of the H1 queue runs under the env switch and
is listed here verbatim; the G1 champion is restored to
`output/world_model.pth` after the exam (the horizon stack lives in
`experiments/horizon/artifacts/`).

## Gates

(appended when the queue lands)

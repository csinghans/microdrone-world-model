# surpass-the-teacher — can BC + RL fine-tune beat the pilot it copied?

## Pre-registration (2026-07-06, before any number exists)

The question Hans asked, made falsifiable: **teacher first, then RL,
keep the world model — does the student end up ABOVE the teacher?**
BC's objective is agreement (capped at the teacher); PPO's objective
is the task (capped only by physics). The teacher's own losses are
scripted-heuristic losses (bang-bang, deadband, no anticipation), so
headroom exists if and only if the fine-tune can shave them without
destroying the imitation prior — the known failure mode (policy walks
off the demonstrated manifold and never returns) is pre-stated as the
refuted branch, measured with SB3 defaults on purpose (no tuning; one
knob).

**Arena: moving_gap@1.0** — chosen because the teacher is measurably
imperfect there (OracleTrack, probe 27/30), the observation is proven
sufficient (pot val 0.88-0.89), a trained RL line exists for context
(mgap champion 82 % at n=200), and it is the generalist campaign's
open sore (closed-loop drift) — the fine-tune doubles as that
campaign's natural sequel.

**Protocol (all lines n=200, seeds 50000-50199 — untouched by any
training or prior exam; judge = the moving-gap skill's own timing
predicate):**

1. Teacher line: OracleTrack, n=200.
2. Student-BC line: pure mgap clone (400 teacher episodes, seeds
   48000-48399; manipulation floor val ≥ 0.80), n=200.
3. Student-FT line: BC init + PPO 450k on moving_gap (standard transit
   reward, SB3 defaults verbatim), n=200.

**Frozen verdicts:**
- **SURPASS** = FT ≥ teacher + 0.05 (absolute, at n=200 — beyond the
  ±~4 pt CI band, one pre-registered shot, no retries).
- **Support** = FT ≥ BC + 0.05: the fine-tune adds real skill even if
  the teacher line is not crossed.
- **Refuted** = FT ≤ BC: RL on top of the prior destroyed or added
  nothing — the recipe's second leg fails honestly at SB3 defaults,
  and KL-anchored fine-tuning becomes the (separately registered)
  follow-up.
- Recorded either way: BC − teacher (the imitation loss in closed
  loop) and FT − champion 0.82 (context line, not a verdict).

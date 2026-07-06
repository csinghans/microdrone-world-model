# chain-distill — imitate the pilot that CAN chain (the sixth cut)

## Pre-registration (2026-07-06, before any number exists)

Full design, knobs and the frozen signature live in the skill
docstring (`skills/chain_distill/skill.py`). The operational order:

1. Collect 400 oracle episodes on slalom3_fixed (seeds 40000+, exam
   courses unseen), BC 40 epochs → `artifacts/ppo_chain_distill_BC.zip`.
2. **Obs-sufficiency gate (manipulation check): BC val top-1 ≥ 0.80**,
   recorded below before any exam number. Below the floor → the
   campaign closes WITHOUT flying (the observation cannot represent
   the teacher's decision function — itself a finding that sharpens
   the horizon refutation).
3. `research step skills/chain_distill --knob 0` — the exam (eval
   only; the artifact is hand-built).
4. K1 reserve (PPO fine-tune on the BC init) is step-arbitrated on the
   frozen condition: chain_break_at > 2.10 with success < 0.70.

Baseline band, five gated attempts (v1 K2 / v2 K0-K2 / h48 / cl-K1-K3
consolidated): chain_break_at 1.33-2.10, success 0-6.7 %, weave_frac
0.62-0.85. Signature thresholds shared with the horizon and
chain-learning campaigns: support = chain_break_at ≥ 2.5, full =
success ≥ 0.70, refuted = val ≥ 0.80 yet chain in band → the SIXTH
elimination (open-loop imitation does not survive the closed loop).

**Obs-sufficiency gate (2026-07-06): PASSED decisively.** 400/400
oracle episodes reached; 24,705 decisions; BC val top-1 = **0.965**
(train 0.982) against the 0.80 floor. Standing finding regardless of
the exam: the vision observation CAN represent the chaining teacher's
decision function in open loop — whatever fails from here fails in the
closed loop, not in the representation. Exam launched.

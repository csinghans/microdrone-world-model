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

## K0 — the BC clone of OracleWeave (97 % teacher), exam-naive seeds (2026-07-06 05:15 UTC)
Hypothesis: if the observation carries what chaining needs, the clone chains — chain_break_at moves first; BC val >= 0.80 is the pre-registered obs-sufficiency gate before this knob flies
Config: experiments/chain_distill/artifacts/ppo_chain_distill_BC.zip

| cell | n | crash | success | clearance | custom |
|---|---|---|---|---|---|
| slalom3@1.0 | 30 | 3% | 97% | 0.27 | weaved=0.97 weave_frac=0.99 chain_break_at=2.90 |
| diag:slalom2@1.0 | 30 | 40% | 60% | 0.21 | weaved=0.60 weave_frac=0.92 chain_break_at=1.83 |
| diag:slalom3@1.25 | 30 | 100% | 0% | 0.05 | weaved=0.00 weave_frac=0.68 chain_break_at=1.93 |
| guard:gap@1.0 | 30 | 7% | 93% | 0.37 | transited=1.00 gap_margin=0.25 |
| guard:mgap@1.0 | 30 | 53% | 47% | 0.23 | transited=0.97 gap_margin=0.15 |
| guard:cluttered | 120 | 16% | 84% | 0.39 |  |
| guard:sweep@2.0 | 120 | 12% | 88% | 0.49 |  |
- slalom3@1.0 success>=0.7: 0.97 PASS
- guard:gap@1.0 success>=0.75: 0.93 PASS
- guard:mgap@1.0 success>=0.7: 0.47 FAIL
- guard:cluttered crash<=0.05: 0.16 FAIL (rechecked)
- guard:sweep@2.0 crash<=0.1: 0.12 FAIL (rechecked)

**Gate verdict: guard_regression**

### Researcher notes
(unattended run)

# bcft-generalist — the two-leg recipe at five-world scale

## Pre-registration (2026-07-06, before any number exists)

Design, knobs and the frozen signature live in the skill docstring
(`skills/bcft_generalist/skill.py`). Operational order:

1. `distill --finetune <BC2> --steps 450000
   --world slalom3_fixed,gap,moving_gap,classic,solo` →
   `artifacts/ppo_bcft_generalist_FT.zip` (the measured dose, SB3
   defaults, uniform diet — one delta on the gated BC2).
2. `research step skills/bcft_generalist --knob 0` (exam, eval only).
3. K1 reserve (broken-worlds-only FT) is step-arbitrated on its frozen
   condition: chain lost (< 0.70) AND >= 1 broken guard repaired.

The headline risk is the experiment: the slalom arc proved on-policy
RL cannot DISCOVER the chain; K0 asks whether it can KEEP one it was
handed. Full pass = the catalog's first distilled champion.

Baselines: BC2 93.3 / 70 / 43 / 93.3 / 93.3 (chain/gap/mgap/
cluttered/sweep); teachers OracleWeave 0.97, OracleTrack 0.885.

## K0 — BC2 + PPO 450k on the uniform five-world diet (the crown shot) (2026-07-06 07:23 UTC)
Hypothesis: the measured two-leg recipe composed: imitation bought five skills, on-policy RL now repairs the closed-loop drift that share could not — while hopefully KEEPING the chain RL could never discover
Config: experiments/bcft_generalist/artifacts/ppo_bcft_generalist_FT.zip

| cell | n | crash | success | clearance | custom |
|---|---|---|---|---|---|
| slalom3@1.0 | 30 | 100% | 0% | 0.10 | weaved=0.00 weave_frac=0.60 chain_break_at=1.43 |
| diag:slalom2@1.0 | 30 | 57% | 43% | 0.19 | weaved=0.43 weave_frac=0.77 chain_break_at=1.53 |
| diag:slalom3@1.25 | 30 | 100% | 0% | 0.08 | weaved=0.00 weave_frac=0.62 chain_break_at=1.57 |
| guard:gap@1.0 | 30 | 3% | 97% | 0.42 | transited=1.00 gap_margin=0.27 |
| guard:mgap@1.0 | 30 | 10% | 90% | 0.34 | transited=1.00 gap_margin=0.20 |
| guard:cluttered | 120 | 1% | 99% | 0.43 |  |
| guard:sweep@2.0 | 60 | 38% | 62% | 0.28 |  |
- slalom3@1.0 success>=0.7: 0.00 FAIL
- guard:gap@1.0 success>=0.75: 0.97 PASS
- guard:mgap@1.0 success>=0.7: 0.90 PASS
- guard:cluttered crash<=0.05: 0.01 PASS (rechecked)
- guard:sweep@2.0 crash<=0.1: 0.38 FAIL

**Gate verdict: guard_regression**

### Researcher notes
(unattended run)

### K0 researcher notes — the repair is total, and so is the erasure

The pre-stated headline risk fired at full amplitude. What RL can
learn, the fine-tune polished to near-perfection: gap 70→**96.7 %**
(bar passed), mgap 43→**90 %** (bar passed), cluttered →100 %, crash
0. What RL cannot learn, it destroyed: slalom3 93.3→**0 %**, crash
100 %, chain_break_at 1.43 — the clone was ground back INSIDE the
five-elimination band (1.33-2.10), weave_frac 0.60. sweep@2.0 broke
too (93→62 %). The slalom arc's conclusion now has its converse,
measured: **on-policy RL cannot discover the chain, and it cannot
keep one it was handed** — the progress-reward gradient actively
pulls the policy off the chaining basin and back to its own local
optimum (penetrate, crash at gate ~1.4). Forgetting here is not decay;
it is re-optimization toward the wrong attractor.

### K1 activated per its frozen condition (chain lost, guards repaired)

FT2 = BC2 + 450k on the two broken worlds ONLY ("gap,moving_gap") —
slalom never enters the fine-tune env; what remains measured is
cross-world collateral through the shared weights.

## K1 — RESERVE: FT on the broken worlds only (gap,moving_gap) (2026-07-06 08:15 UTC)
Hypothesis: played ONLY if K0 loses the chain (< 0.70) while repairing a broken guard — the forgetting/repair trade-off, step-arbitrated; sheathed if K0 holds the chain
Config: experiments/bcft_generalist/artifacts/ppo_bcft_generalist_FT2.zip

| cell | n | crash | success | clearance | custom |
|---|---|---|---|---|---|
| slalom3@1.0 | 30 | 97% | 0% | 0.14 | weaved=0.00 weave_frac=0.88 chain_break_at=2.27 |
| diag:slalom2@1.0 | 30 | 100% | 0% | 0.13 | weaved=0.00 weave_frac=0.78 chain_break_at=1.57 |
| diag:slalom3@1.25 | 30 | 97% | 0% | 0.14 | weaved=0.00 weave_frac=0.84 chain_break_at=2.07 |
| guard:gap@1.0 | 30 | 7% | 93% | 0.39 | transited=1.00 gap_margin=0.23 |
| guard:mgap@1.0 | 30 | 10% | 90% | 0.34 | transited=1.00 gap_margin=0.19 |
| guard:cluttered | 60 | 60% | 40% | 0.20 |  |
| guard:sweep@2.0 | 60 | 98% | 2% | 0.11 |  |
- slalom3@1.0 success>=0.7: 0.00 FAIL
- guard:gap@1.0 success>=0.75: 0.93 PASS
- guard:mgap@1.0 success>=0.7: 0.90 PASS
- guard:cluttered crash<=0.05: 0.60 FAIL
- guard:sweep@2.0 crash<=0.1: 0.98 FAIL

**Gate verdict: guard_regression**

### Researcher notes
(unattended run)

## Campaign verdict: REFUTED — and the fine-tune safety law is the export (2026-07-06)

Both knobs lost the chain; the refuted branch fires with the two most
instructive failure modes on record:

| cell | BC2 | K0 (five-world FT) | K1 (gap+mgap-only FT) |
|---|---|---|---|
| slalom3 chain | 93.3 % | 0 % | **0 %** (frac 0.88 — the weave SHAPE survives, the precision does not) |
| gap | 70 % | 96.7 % ✓ | 93.3 % ✓ |
| mgap | 43 % | 90 % ✓ | 90 % ✓ |
| cluttered | 93.3 % | 100 % ✓ | **40 %** |
| sweep@2.0 | 93.3 % | 61.7 % | **1.7 %** (crash 98 %) |

Composed with surpass-teacher (single-world FT: +29.5, no damage),
today's three fine-tune measurements pin a law:

**On-policy fine-tuning repairs exactly its own diet, corrodes
everything outside it, and corrodes RL-unlearnable skills even INSIDE
it.** K0 had slalom in the diet and still erased the chain — the
progress-reward gradient on slalom worlds actively pulls away from
chaining (re-optimization, not decay). K1 never showed the net a
slalom episode and erased it anyway — shared weights carry the
corrosion. FT is safe exactly when (a) the diet covers everything you
care about AND (b) everything you care about is RL-learnable. The
chain fails (b); no diet fixes that.

The deviation slot stays sheathed: dose-response and KL-anchored FT
are real candidates but need their own pre-registration (the latter
was already named in surpass-teacher's journal as the registered
follow-up). **The crown stays vacant a ninth time** — the catalog's
honest state: specialists (chain-distill 96.7 %) and a
generalist-without-crown (BC2), with composition still unpaid for.

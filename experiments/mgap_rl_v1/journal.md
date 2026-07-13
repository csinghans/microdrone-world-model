# mgap_rl_v1 — RL-from-success on the terminal window

**Opened:** 2026-07-14 · **Priors:** `integration_k6_v1` (K5 kill
mechanism: terminal wrong-way 0.90; K6 causality: MISTAKE, oracle
ceiling ~4 % seam / +11 composite), `terminal_commit_v1` (BC refuted
at 11.1 % vs ≤8 % — the student learned WHERE but only half of WHEN;
the disease is label consistency at a visually-unresolvable
boundary), `anchor_dial` (the crowned FT recipe: scheduled KL
1.0 → 0.1). Owner:「go RL-from-success」.

## Why RL sidesteps the BC disease

BC needs consistent labels; the commit boundary cannot be labelled
consistently from vision (±2 cm on a moving slot). **RL needs only
outcomes** — thread-and-survive pays, fleeing pays less — so the
policy may place its own boundary wherever its perception CAN resolve
it. The warm start already knows WHERE (direction confusion 1/104)
and flies 11.1 % seam; RL's job is the remaining WHEN.

## K1 recipe (one knob, frozen)

- **Warm start:** `terminal_commit_v1/artifacts/ppo_mgap_commit.zip`
  (the K1 BC clone — memoryless teacher, seam 11.1 %).
- **Fine-tune:** `scripts/distill --finetune` = AnchoredPPO on
  `WMPolicyEnv(world=moving_gap)` with the UNMODIFIED success reward
  (progress −0.02/step, −30 crash, +50 goal — no new shaping), the
  crowned schedule **--anchor 1.0 --anchor-end 0.1, 450k steps**,
  seed 0. Solo-world training is justified by the k6 campaign's own
  measurements: mgap entry conditions are flat and non-predictive
  (K3 addendum), the failure is terminal and encounter-geometry
  driven, and StageLocal makes the stage-local view identical.
- No unit gate: graduation is the judge (declared; a broken policy
  costs one 40-minute block).

## Bars (frozen)

- **Graduation:** k=3, n=60 @ **147000** (fresh), deployed HYBRID
  with the mgap slot swapped to the student. Wins ≥ 45 (42–44 →
  recheck @148000, pooled ≥ 90/120).
- **PRIMARY: pooled mgap seam ≤ 8 %** (the standing target; true
  baseline 17.2 %, BC 11.1 %, oracle ~4 %).
- **Guards, anchored per the recorded lesson (pooled TRUE rates where
  the truth table exists):** slalom ≥ **0.82** (true ~0.87 − 0.05 —
  NOT the exam-draw 0.917 anchor that misfired twice); door ≥ 0.930,
  gap ≥ 0.880, odoor ≥ 0.873 (79-record − 0.05, no truth-table
  correction known for them).
- **The held re-DAgger ticket transfers:** if the arm graduates AND
  the slalom guard trips pooled, the ticket is spent (slalom
  re-DAgger vs the new upstream, seeds 152000+) before banking.
- **Exam hygiene:** 110000 untouched; a graduating arm BANKS as a
  stack member for the parked 0.84 ambition.
- **Refuted branch:** if RL also lands above 8 %, two independent
  methods will have converged at ~11 % — the frozen target itself
  goes under review (as a review, on the record; never a silent bar
  move), with the vision-information constraint as the named suspect.

## K1 results (2026-07-14 — grad_n60.json + grad_n60_b2.json, pooled n=120)

| pooled read | value | bar | verdict |
|---|---|---|---|
| wins | **97/120 = 0.808** | ≥ 90 | ✓ — the best graduation-level composite this line has seen |
| **PRIMARY mgap seam** | **4/45 = 8.9 %** | ≤ 8 % | **missed by 0.4 of a fail** |
| guard slalom (true-rate anchor) | 0.855 | ≥ 0.82 | ✓ comfortable |
| guard door | 0.926 | ≥ 0.930 | tripped by 0.004 |
| guards gap / odoor | 1.000 / 0.960 | | ✓ |
| mgap conditional | **0.938** (true baseline ~0.887) | reported | real lift |

**REFUTED as written.** The anchor schedule landed (kl 1.0 → 0.103),
no coupling damage appeared (slalom 0.855 ≥ the mis-anchored old bar
too), and the arm is a genuine improvement — but 8.9 > 8.

## The pre-named review (open, on the record)

Two independent deployment-legal methods have now converged:
**BC 11.1 %, RL 8.9 %**, against the privileged oracle's ~4 %. The
residual is the **perception tax** — the oracle reads pillars; the
camera at terminal range resolves the slot's position but not the
±2 cm commit boundary (the same info-constraint the confusion
diagnostic measured). The frozen 8 % assumed a student could capture
~¾ of the oracle's gain; two methods captured 47 % and 63 %. Review
verdict: **the target sat inside the perception tax. No bar moves;
the arm does not bank under THIS registration.** Its measured value
(mgap seam 17.2 → 8.9 %, conditional 0.887 → 0.938, est. +2.5–3 true
points on the k=3 gate) is banked as EVIDENCE; adoption is deferred
to the 0.84 stack's own registration, which will judge components by
the stack's exam, not by this arm's missed ambition.

Also recorded: the door guard tripped by 0.004 on an anchor frozen
from the 79-record's friendly door draws (0.980/1.000) — **the
guard-anchor disease, third occurrence** (beam_latency band, the
slalom guard, now door). Standing rule going forward: every guard
anchor in a new registration must cite a pooled true rate or be
flagged as draw-anchored.

## Status

- [x] Pre-registration (this file, before any number)
- [x] K1: anchored FT (kl 1.0→0.1, 450k) → pooled graduation:
      **REFUTED as written (8.9 % vs ≤8 %) — with wins 0.808, mgap
      conditional 0.938, no coupling damage; the pre-named review
      names the perception tax; the arm banks as EVIDENCE for the
      0.84 stack registration; no bar moves**
- [x] Campaign CLOSED; re-DAgger ticket still unspent (no coupling
      damage ever materialized); slalom RL-from-success remains the
      stack's other named component

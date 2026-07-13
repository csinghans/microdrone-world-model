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

## Status

- [x] Pre-registration (this file, before any number)
- [ ] K1: anchored FT 450k → graduation @147000 → primary + guards

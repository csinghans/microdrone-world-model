# terminal_commit_v1 — distilling the commit: the oracle's second, earned from perception

**Opened:** 2026-07-13 · **Prior:** `experiments/integration_k6_v1/`
(K5: the kill mechanism — terminal wrong-way divergence 0.90; K6: the
causality — MISTAKE, forced commitment erases mgap deaths 27→4.2 %
deep, composite +11 at k=6, est. +3–4 on the standing k=3 gate).
Owner:「go terminal-commit 訓練臂」.

## The arm

The oracle is privileged (it reads pillars); the deployed pilot must
EARN the commit from perception. The house playbook applies:
**privileged-teacher distillation** — fly the oracle-wrapped deployed
lineup, record what the aircraft actually sees and does, and clone
the executed behavior (mostly FT-v3 passthrough; the oracle's commit
in the terminal metre) into a vision-only moving_gap slot specialist.

**Lineup-coupling surcharge, priced up front (the v3 ordering law):**
a new mgap slot pilot changes slalom's upstream exit distribution —
v3 measured that swap at 17.2 → 43.8 % slalom seam. The coupling
guard below is armed, and ONE slalom re-DAgger round against the new
upstream (the v2 R2 recipe, seeds 152000+) is PRE-AUTHORIZED as the
bounded surcharge if the guard trips. Mitigating prior: the commit
changes behavior only inside mgap terminal windows, and new survivors
exit near the natural survivors' distribution — the coupling may be
mild; the guard decides.

## Protocol (frozen)

- **Collection:** n=400 k=6 courses, seeds **150000+** (fresh; k=6
  maximizes mgap-terminal exposure per flight), flown by
  ThreadCommitOracle(deployed HYBRID). The generalized SeamProbe
  records every moving_gap-stage decision (mirror ObsBuilder vecs +
  executed menu actions; the weave counterfactual is slalom-specific
  and is DISABLED for this target). Cleared-stage filter (only stages
  cleared before any crash feed the pot — the oracle's ~98 % mgap
  clear rate makes this rich). Labels = EXECUTED actions (BC of the
  oracle-wrapped trajectory).
- **Pot floors:** ≥ 10,000 kept mgap decisions, ≥ 2,000 inside the
  terminal metre (x within 1.0 of the fence plane); **BC val floor
  0.94** — frozen BELOW the slalom pots' 0.96 with the reason stated:
  terminal commit labels contain sharp geometry-conditioned switches
  (harder to fit than weave's smooth gate-homing), and the val meter
  is reported per-region (terminal vs approach) for the mechanism
  read.
- **Graduation:** k=3 (the deployment format), n=60 @ **145000**,
  contender = HYBRID with the mgap slot swapped to the new
  specialist. Wins ≥ 45 (42–44 → recheck @146000, pooled ≥ 90/120).
- **Primary campaign read:** pooled mgap SEAM failure across
  graduation blocks ≤ 8 % (true rate 17.2 %; the oracle ceiling ~4 %).
- **Coupling guard (method-consistent conditionals vs the 79-record):
  slalom ≥ 0.867 (0.917 − 0.05), every other type −0.05.** Guard
  trips ⇒ the pre-authorized slalom re-DAgger round fires (bounded,
  once); its own graduation decides.
- **Exam hygiene:** the 110000 formal does NOT fire in this campaign
  — a single +3–4 arm cannot be 0.84-worthy alone; the arm BANKS at
  graduation level as a stack member for the parked 0.84 ambition
  (with slalom RL-from-success as the named partner arm).

## Machinery (defaults bit-identical)

`eval_seam_fidelity`: SeamProbe/capture gain `target_stage`
(default slalom — bit-identical) + `thread_commit` (oracle wrap);
rows gain x/plane_x for terminal accounting; the mirror-fidelity
instrument is asserted only when the oracle is OFF (with it on, the
executed-vs-inner mismatch IS the override rate — reported).
`scripts/build_mgap_commit.py`: pot filter + floors + bc_train.

## K1 results (2026-07-13) — the val floor refused, and the diagnostic names the teacher

Collection delivered (23,792 rows, 19,849 kept, 7,511 terminal —
quantity floors passed; oracle-wrapped k=6 success 0.583). **BC val
0.9143 < the 0.94 floor — the build refused, the graduation never
ran.** The per-region meter localizes it: approach 0.948, **terminal
0.856**.

**The free confusion diagnostic (held-out terminal rows, n=724):
direction confusion is ONE error in 104** — the student knows WHERE
the slot is. The errors are TIMING: 60 % "teacher veers, student
flies forward" + 32 % the reverse, all crowding the oracle's razor
0.10 m threshold. Mechanism: tracking a MOVING slot, |err| oscillates
around 0.10, so the teacher's labels FLICKER (veer/forward/veer)
faster than any visual estimate can resolve ±2 cm — the labels
themselves are inconsistent at the boundary. **The disease is the
teaching, not the student.**

## K2 — the hysteresis teacher (pre-registered)

**One knob: label coherence.** `ThreadCommitOracle` gains commit
HYSTERESIS (opt-in, default bit-identical — the K6 record's oracle is
untouched): once |err| > 0.10 it commits and KEEPS veering until
|err| ≤ 0.04, then flies FORWARD until the 0.10 boundary is crossed
again. Labels become temporally coherent segments instead of boundary
flicker. Everything else identical: same seeds machinery (fresh block
**151000+**, n=400 k=6), same quantity floors, **the same 0.94 val
floor** (the bar does not move; the teacher does), same graduation
plan and coupling guard. Sanity read declared: the hysteresis
oracle's own collection success should stay in the K6 oracle's band
(~0.58–0.61 at k=6) — a smoother commit must not fly worse.

## Status

- [x] Pre-registration (this file, before any number)
- [x] K1: collect + build → **val floor REFUSED (0.9143 < 0.94);
      terminal region 0.856; confusion diagnostic = commit-TIMING at
      the razor threshold, direction known (1/104) — the teacher's
      flickering labels are the disease**
- [x] K2 pre-registered (this section, before any number)
- [ ] K2: hysteresis teacher → re-collect @151000 → build (same
      floors) → graduation @145000 → primary read + coupling guard

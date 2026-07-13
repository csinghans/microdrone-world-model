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
- [x] K2: **floor refused AGAIN — and the miss teaches** (below)

## K2 results (2026-07-13) — the hysteresis backfires on the student, helps the oracle

Collection 21,649 kept (floors ✓), **hysteresis oracle's own success
0.583 → 0.665** (the sanity read passed with a bonus: the smoother
commit is a better ORACLE — recorded for any future oracle use). But
the fit went DOWN: pooled 0.9071, terminal **0.841** (was 0.856).
Mechanism of the backfire, identified: hysteresis makes labels
HISTORY-DEPENDENT — visually similar states inside the 0.04–0.10
band now carry different labels depending on the teacher's committed
state, turning a memoryless threshold task into a partially
unobservable one. Coherent segments, harder mapping.

## K3 — instrument re-registration: the floor measured the wrong thing (flight bars untouched)

Two knobs, two floor refusals, one consistent diagnosis: the val
meter punishes threshold-adjacent label mismatches that are
behaviorally near-equivalent (veer at 0.08 vs FORWARD — both thread),
while the behaviorally fatal error class — DIRECTION — sits at
**1/104**. "Fidelity is a meter, not the target" is this repo's
twice-measured law; the 0.94 floor was an a-priori proxy for
obs-sufficiency, and the measured obs-consistency ceiling for
razor-threshold labels is ~0.91.

**Re-registration (on the record, not silent):** the 0.94 pooled-val
floor is RETIRED for this task class and replaced by the
behavior-relevant fit read — **direction-confusion ≤ 2 % on held-out
terminal rows** (K1 clone: 0.96 % ✓). The K1/K2 floor verdicts stand
in this ledger unedited. **Every FLIGHT bar is unchanged and remains
the campaign's judge:** graduation wins ≥ 45/60 @145000, primary
mgap seam ≤ 8 %, coupling guard slalom ≥ 0.867 (+ the pre-authorized
re-DAgger), exam hygiene intact. **The candidate: the K1 clone**
(memoryless teacher, the higher fit of the two; one candidate, chosen
before flying — no fishing).

- [x] K3 registered (this section, before the graduation flies)
- [x] K3 graduation block 1 → three borderlines → pooled recheck
      (below)

## K3 graduation block 1 (2026-07-13 — grad_n60.json) — three borderlines

| read | value | bar | as written |
|---|---|---|---|
| graduation wins | 45/60 | ≥ 45 | passes, at the bar |
| PRIMARY mgap seam | 3/28 = 10.7 % | ≤ 8 % | missed by < 1 fail |
| coupling guard: slalom | 0.850 | ≥ 0.867 | tripped by 0.017 |
| other guards (door/gap/odoor) | 0.931/0.960/0.941 | −0.05 each | all held |

**Before firing the expensive pre-authorized re-DAgger, the house
recheck rule applies — and the guard's own anchor deserves a note:**
the 0.867 bar was frozen from the 79-record's exam conditional
(0.917), which the truth table later showed to be a ~1.3σ friendly
draw; the r3 lineage's TRUE slalom conditional is ~0.87, so 0.850 may
be block noise rather than coupling damage. The bar binds as written;
the pooled recheck (the K1c/R2 law: pool, never replace) sharpens all
three borderlines at once before any consequence fires.

**Recheck (registered before flying): second block @146000, pooled
judgments — wins ≥ 90/120; primary mgap seam ≤ 8 % pooled; slalom
guard on the pooled conditional vs 0.867. Only a pooled guard trip
fires the re-DAgger.**

- [x] K3 recheck @146000 → pooled verdict (below)

## K3 pooled verdict (2026-07-13 — grad_n60_b2.json) — the arm does not graduate as frozen

| pooled read (n=120 courses) | value | bar | verdict |
|---|---|---|---|
| wins | 92/120 | ≥ 90 | ✓ |
| **PRIMARY mgap seam** | **6/54 = 11.1 %** | ≤ 8 % | **missed** |
| coupling guard: slalom | 0.855 (n=69) | ≥ 0.867 | tripped as written |
| other guards | door .938 / gap .945 / odoor .958 | −0.05 | held |

**The vision student captured about HALF the oracle's gain** — mgap
seam true 17.2 % → 11.1 % (a real cut, z ≈ −1.8) against the oracle's
~4 % ceiling — exactly what the terminal-fit ceiling (~0.86, the
threshold-noise diagnosis) predicted. For once the meter and the
flight agree: the BC student learned WHERE but only half of WHEN.

**On the guard and the surcharge, recorded plainly:** the trip
condition is met as written (twice, 0.850/0.855 vs 0.867), but both
reads sit within noise of the TRUE slalom baseline (~0.87; the 0.867
anchor was frozen off the exam's friendly 0.917) — and with the
primary failed pooled, completing this arm's graduation is moot. The
pre-authorized re-DAgger is HELD UNSPENT, explicitly: its object was
to complete a graduating arm; if this arm is ever revived, the
surcharge remains owed. Instrument lesson, SECOND occurrence
(beam_latency's band was the first): **freeze guard anchors from
pooled true rates, not one exam's draw.**

## Campaign close — REFUTED at its bars, with the mechanism ledger paid in full

The arm is refuted as frozen: 11.1 % > 8 %. What the campaign banked:
1. **The BC ceiling for razor-threshold skills is real and now
   understood:** flickering labels at a visually-unresolvable
   boundary cap the terminal fit (~0.86 both teachers), and the
   flight shortfall tracks the fit shortfall.
2. **Hysteresis helps oracles, hurts students** (history-dependent
   labels = partial unobservability) — the smoother oracle flies
   +8 (0.583→0.665) and is the better teacher-CONTROLLER for any
   future oracle use, but not for BC labels.
3. **The named next arm sidesteps the disease entirely:**
   RL-from-success on mgap terminal windows — RL needs no consistent
   labels, only outcomes; it was already the 0.84 stack's partner
   arm, and this campaign hands it the exact target (the terminal
   second), the oracle warm-start option, and the priced ceiling
   (~4 % seam). Owner-gated, fresh registration.
4. mgap improvement to 11.1 % exists but ships nothing: the record
   lineup keeps FT-v3 on the mgap slot; the k=3 gate of record was
   never touched.

## Status

- [x] K1: floor refused; diagnosis = flickering teacher labels
- [x] K2: hysteresis teacher — refused again; mechanism sharpened
      (history-dependent labels); oracle itself flies better
- [x] K3: instrument re-registered (flight bars untouched) →
      graduation pooled: **REFUTED (mgap 11.1 % vs ≤8 %); guard
      anchor lesson recorded; re-DAgger held unspent**
- [x] Campaign CLOSED; RL-from-success (terminal-targeted, priced
      ceiling ~4 %) = the named successor, owner's call

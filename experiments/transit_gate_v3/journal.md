# transit_gate_v3 — the road past 80 (the owner's direction)

**Opened:** 2026-07-12 · **Owner:** Hans（「Transit 整合門可以再提高到
80 以上嗎」→「go」）· Prior record: `experiments/transit_gate_v2/`
(72 → 79, the seam mechanism measured and paid), gate of record
`experiments/transit_gate_v2/r3_formal_n100.json` (79/100).

## Campaign bars (frozen before any number)

- **Challenger bar: formal n=100 @ the standing 110000 exam, PASS =
  ≥ 0.84** (the 79 record + ~1.3σ, the same meaningful-beat rule that
  produced 0.78 last campaign). Milestone arithmetic: a real +5 lands
  ≥ 0.80 even after any honest discount; a lucky-draw 80 is not a
  result.
- **Guards:** method-consistent per-type conditionals not worse than
  the 79-record's by 0.05 (door 0.980, gap 0.930, moving_gap 0.887,
  opening_door 0.923, slalom 0.917 — the R3 dissection script is the
  method of record).
- **Exam hygiene:** 110000 fires at most once per promoted-stack
  attempt; all intermediate knives are judged on graduation blocks.
- **Seed ledger:** K2 probe 118000 (recheck 119000); lineup graduation
  121000 (recheck 122000); collections 132000+; 110000 exam only.
  (120000/125000/130xxx/131xxx are spent collection blocks.)

## The failure map (the 79 record's own 21 failures + the pooled ledger)

R3 formal: seam fails mgap 4/30 · gap 4/42 · slalom 4/42 · odoor 3/37
· door 1/34, plus 5 cold (stage-0) fails. No dominant edge remains —
the slalom-sized prize is gone; this campaign farms a SPREAD tail.

**Arm 1 (free read, pooled from every record where the FT-v3
generalist flew moving_gap — 10 files, 578 stage instances):**

| entry | fail | conditional |
|---|---|---|
| mgap **seam** (pos ≥ 1) | 64/373 = 17.2 % | **0.828** |
| mgap **cold** (pos 0) | 20/205 = 9.8 % | **0.902** |

Two diseases, not one: a **base-rate problem** (the generalist drops
1-in-10 moving_gap stages even from a cold start — slalom cold was
3 %) and a **seam tax** (×1.75). Killing the seam tax alone buys only
≈ +2.2 composite points (0.074 × ~30 seam instances/100); a lever
that lifts BOTH sides is worth ≈ +4.

## What is NOT re-dug

- The slalom DAgger ladder is CLOSED (v2, frozen at two rounds); the
  slalom residue (9.5 % seam) belongs to the pre-named dagger-weight
  knife (D1, below), not more rounds.
- The mgap champion in-course is NOT a dead end being re-dug: the
  hybrid kept the generalist on moving_gap in v1 because slalom was
  the crisis and the generalist's 0.86 was "good enough" — the
  champion was never flown in-course (integration_ft journal, checked
  2026-07-12). Both zips are plain PPO on the same 576-dim obs; the
  slot swap is mechanically the same move as the slalom specialist.

## K2 — the champion-swap probe (pre-registered)

**Question.** Is moving_gap's failure mass a PILOT problem (the
generalist) or a TASK problem (timing stages entered at random phase
are intrinsically harder)? The cheapest decisive read is an
intervention, not an agreement statistic: fly the solo mgap champion
(`ppo_moving_gap_v2_K3.zip`, gated 0.85–0.93 on its own world) in the
moving_gap slot of the CURRENT deployed lineup, one knob, and read
its stage conditionals against Arm 1.

**Machinery (defaults bit-identical):** `eval_integration` gains
`--swap STAGE=ZIP` (repeatable, hybrid contender only — the generic
form of `--slalom-zip`, which stays).

**The run:** n=100 @ seeds 118000, lineup = deployed (R3 slalom clone
included) with moving_gap → champion. Expected exposure ≈ 37 seam +
20 cold champion instances.

**Branches (frozen):** C_seam = the champion's pooled mgap-seam
conditional; comparator G_seam = 0.828 (Arm 1, n=373).
- **SWAP-WINS**: C_seam ≥ 0.878 (G_seam + 0.05) → the pilot was the
  wall; remedy = promote the champion into the mgap slot (a lineup
  change → graduation @121000 → it joins the promoted-stack attempt).
- **SWAP-NULL**: C_seam ≤ 0.848 (G_seam + 0.02) → the champion buys
  nothing at seams → the wall is the task (random-phase entries);
  remedy re-points at phase-randomized training (fresh registration)
  and D1 becomes the campaign's lead knife.
- GRAY between → pool a second block @119000, judge pooled.
- **Declared side-reads (not barred):** C_cold vs G_cold (0.902) — the
  base-rate lever; task-hardness signature = the champion ITSELF
  degrading ≥ 0.05 from cold to seam; overall success of the swapped
  lineup on 118000 (context only — 118000 is not the exam).

**Interpretation caveat (frozen):** the champion is a learned policy,
not a state-pure oracle; SWAP-NULL does not prove no pilot can do
better — it prices what the best EXISTING pilot buys. Building a
better mgap pilot is a training arm, registered separately if chosen.

## Named later knives (pre-named, each its own registration when reached)

- **D1 — dagger-weighted BC:** student rows are 24 % of the R3 pot;
  slalom residue 9.5 % seam vs 3 % cold. One knob: sample weights.
- **RL-from-success:** the only lever that touches the 5 cold fails
  (R1 measured those as on-teacher-but-dying = teacher/dynamics
  ceiling); expensive, guards carry the regression risk.

## K2 results (2026-07-12 — k2_swap_n100.json)

**The registered read: SWAP-NULL, cleanly.** C_seam **0.818** (6/33)
vs G_seam 0.828 — the champion buys nothing at moving_gap seams
(≤ 0.848 branch). C_cold 0.923 vs 0.902 (noise, n=26). The
task-hardness signature FIRES: the champion itself degrades cold →
seam by 10.5 points. The wall is the task — random-phase entries —
not the pilot.

**The collateral discovery (worth more than the question): lineups
are coupled — "lineup-as-ABI."** The probe block's slalom seam
exploded to **14/32 = 43.8 %**, and the sharpest cut is the
**moving_gap→slalom edge at 6/9**. Cross-block truth table (slalom
seam fail rate, every committed record, by clone lineage):

| lineage | pooled | blocks |
|---|---|---|
| record-clone | 34.6 % (47/136) | 30.0 exam · 35.8 · 40.0 |
| r2-clone | 24.5 % (34/139) | 30.8 grad · 21.4 exam · 23.9 |
| r3-clone | **17.2 % (11/64)** | 31.8 grad · **9.5 exam** |
| r3-clone, mgap→champion | **43.8 % (14/32)** | one block |

Three verdicts fall out at once:
1. **The DAgger ladder's true effect is real and monotone** (34.6 →
   24.5 → 17.2) — but the exam's 9.5 % was the friendly tail (~1.3σ
   lucky draw; the gate of record stands by protocol, planning uses
   17.2 %). Honest correction: the lineup's TRUE composite is
   ~0.775–0.78, so the 0.84 challenger needs **≈ +6.5 true points**,
   not +5.
2. **Swapping any upstream pilot re-opens downstream seams** (17.2 →
   43.8 % behind the swapped mgap, z ≈ 2.8): the R3 clone's DAgger
   adaptation is specific to the exit-state distribution of the
   lineup it was trained under. The behavioural sibling of the
   latent-as-ABI law.
3. K2's swap is therefore **doubly dead**: no mgap gain AND a slalom
   collateral tax. Rejected without a graduation.

**Ordering law (frozen for the rest of the campaign):** any future
arm that changes an upstream pilot (e.g. a phase-trained mgap
specialist) must budget a slalom re-DAgger against the NEW upstream
as part of its price — fix upstreams first, re-adapt downstream last.

**Consequence for the knives:** D1's expected value RISES — the
slalom seam's true rate is 17.2 %, not 9.5 %, so the dagger-weight
knob has ~+3–6 true points of headroom (0.14 × ~42 seam
instances/100 at full kill), the single biggest lever left. The
mgap-phase training arm stays parked pending the owner (it now
carries the re-DAgger surcharge).

## D1 — dagger-weighted BC (pre-registered)

**One knob:** re-BC the R3 pot (persisted, byte-identical) with
sample weight **w = 3 on the dagger rows** (native/oracle-hot stay
1.0; dagger is 24 % of rows → ~49 % of effective gradient mass). One
value, no sweep — a second value is a new arm.

**Floors (frozen):** pooled val ≥ 0.96 (unweighted meter, as ever);
**native-val ≥ 0.975** (rebalance guard — the zoo_transfer lesson:
upweighting must not trade the primary manifold away; R3's was
0.982); dagger-val reported (expect ↑ from 0.918).

**Bars:** graduation n=60 @121000, wins ≥ 45 (42–44 → recheck
@122000, pooled ≥ 90/120). Declared read (not barred alone): the
graduation block's slalom-seam rate joins the lineage truth table
against 17.2 %. The 110000 exam fires ONLY when the accumulated stack
is 0.84-worthy.

**Machinery (defaults bit-identical):** `bc_train` gains
`sample_w=None` (None = the exact current mean-loss path);
`build_bigpot_v2` gains `--dagger-weight` (default 1.0) and can build
from the persisted pot npz.

## Status

- [x] Campaign bars frozen (this file, before any number)
- [x] Arm 1 pooled comparator computed (free, from committed records)
- [x] K2 pre-registered (this file, before any probe number)
- [x] K2 verdict: **SWAP-NULL + task-hardness + the lineup-coupling
      law (slalom 17.2 → 43.8 % behind a swapped upstream); true-rate
      table corrects the exam's friendly draw; swap rejected**
- [x] D1 pre-registered (this section, before any number)
- [ ] D1: weighted re-BC → graduation @121000 → stack arithmetic +
      the owner's RL decision point

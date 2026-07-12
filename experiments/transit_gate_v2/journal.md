# transit_gate_v2 — raising the 72/100 (the owner's direction)

**Opened:** 2026-07-12 · **Owner:** Hans（「我想提高 Transit integration
gate 的成功率」）· Prior record: `experiments/integration_ft/` (the
climb 0.33→0.72), gate of record `hybrid4_n100.json`.

## The failure map (the 72/100 record's own 28 failures, measured first)

| cut | numbers |
|---|---|
| by stage type | slalom 13 · moving_gap 8 · opening_door 5 · gap 2 · door 0 |
| by position | stage0 4 · stage1 13 · stage2 11 → **24/28 (86 %) are SEAM failures** |
| slalom, cold vs seam | cold **1/30 (3 %)** vs seam **12/46 (26 %) — ×8** |
| the worst single edge | **opening_door → slalom: 6 failures** (half of slalom's seam breaks) |
| runner-up | moving_gap seam 6/36 (17 %); door is perfect (0/54) |

Arithmetic headroom: slalom-seam at its own cold rate ≈ **+10 → ~0.82**;
the door→slalom edge alone ≈ +6 → 0.78.

## What is NOT re-dug (measured dead ends, on the record)

- **Entry brake at slalom handoffs: played, exactly null** (v3 era,
  0.645 == 0.645; `eval_integration.PerStageExperts`, the removed-brake
  comment). Its mechanism verdict ("per-decision fidelity, not the
  entry state") was measured on the WEAK specialist; today's ×8
  cold-vs-seam split on the BIG-POT specialist re-opens the entry-state
  question with new evidence, per the house re-opening rule.
- **dense is not in the course pool** — the dense frontier
  (oracle_memory_v1's verdict) is a different wall; nothing here
  touches it.

## The K1 hypothesis — deployment-matched entry states

The big pot's hot seam segments were collected under the **OracleRelay**
(privileged pilots fly the preceding stages — `scripts/distill.py::
collect_hot`). At gate time the specialist inherits the **FT
generalist's** exit states instead. If the two upstreams' exit
distributions differ (a door exit is a wait-then-charge burst; the
oracle's may be cleaner/centred), the specialist reads
out-of-distribution entries exactly at X→slalom seams — which is where
12 of 13 slalom failures live, six of them behind a door.

**K1 (one knob): re-collect the hot slalom segments with the DEPLOYED
upstream.** A mixed relay — the v3 FT generalist flies every non-slalom
stage (creating the real exit states), the oracle Weave flies and
LABELS the slalom stages — cleared-segment filtered, StageLocal
semantics, courses restricted to those with slalom at position ≥ 1
(seam entries guaranteed; the door→slalom mix is REPORTED). Top up the
existing big pot with these deployment-matched segments and re-BC;
everything else in the lineup frozen.

**Floors (frozen):** ≥ 4,000 new slalom decisions; BC val ≥ 0.96 (the
big pot's own fidelity floor — the chain arithmetic that demanded it
has not changed).

**Bars (frozen):** graduation pooled n=60 ≥ 0.75 → formal n=100;
**PASS = ≥ 0.78** (the record + ~1.3σ). Guards: per-type conditional
must not regress more than 0.05 vs the record's (door 1.000, gap 0.966,
odoor 0.906, mgap 0.864, slalom 0.829). Refuted = slalom seam failures
do not shrink → the entry-state story dies a second, better-instrumented
death, and the residue re-points at per-state fidelity (an anchored-FT
arm, pre-named, separately registered).

Ledger note: moving_gap's 6 seam failures are the pool's second seam —
NOT touched by K1 (one knob); pre-named as K2 if K1 lands.

Implementation note (harness fact, recorded before running): the
record pot's raw arrays were never persisted, so "top up" is
implemented as regenerate-the-recipe (native weave chains + oracle-hot
segments) PLUS the deployed-hot component — `scripts/build_bigpot_v2.py`
(native 600 eps / 240 oracle courses / 240 deployed seam-courses,
deployed X→slalom mix reported). The knob remains the added component;
regeneration variance is covered by the val ≥ 0.96 floor and the
graduation gate. Machinery: `collect_hot` gains `teachers`/
`course_filter` (defaults bit-identical); `eval_integration` gains
`--slalom-zip` (swaps only the hybrid's slalom slot).

## K1 results (2026-07-12 — build + graduation, k1_grad_n60{,_b2}.json)

**The pot (floors all green):** 62,276 decisions = native 37,035 +
oracle-hot 7,634 + **deployed-hot 17,607** (≫ the 4,000 floor); pooled
val **0.9658** ≥ 0.96; deployed X→slalom mix healthy (door 48 / odoor
56 / mgap 57 / gap 54 / slalom 57); the deployed upstream clears
courses at 0.825 vs the oracle relay's 0.550.

**The read:** graduation block 1 **0.733** (< 0.75 — the && gate held
the formal); borderline → the house pooled recheck, block 2 (seeds
112000+) **0.717** → **pooled 87/120 = 0.725 < 0.75. The formal n=100
never runs.** Seam dissection, pooled across both blocks:
**slalom seam 16/63 = 25.4 % — bit-identical to the record's 26 %**
(12/46); mgap seam 8/54 = 14.8 % (record 17 %). Graduation level itself
is a null vs the record's own graduation (0.725 vs 0.733, inside
noise): the v2 pot neither helps nor hurts.

## Verdict — K1 REFUTED: the entry-state story dies its second, better-instrumented death

With the fidelity floor HELD (0.9658) and seventeen thousand
deployment-matched seam entries in the diet, the slalom seam rate did
not move a millimetre. Combined with the earlier brake-null (braking
INTO the specialist's native start: exactly null), the seam now has two
independent eliminations from opposite directions — neither recreating
the native entry NOR training on the true deployed entries touches it.
The distribution-matching hypothesis is dead; what survives the two
eliminations is **per-state fidelity in seam-reachable states** (the
pooled val is dominated by native-start states; the clone's accuracy
ON the states a seam actually visits is unmeasured) — or a mechanism
neither knob reaches (StageLocal reset timing, the entry-decision
prev-action context).

**Consequences:** the v2 pot is NOT promoted — the record lineup
(72/100) stays deployed, its graduation twin measured. The pre-named
residue arm is now the only live road and needs its own registration:
**anchored FT of the specialist on composite seam entries** (the crown
recipe pointed at the specialist in-course), judged first by a
per-state-fidelity probe on seam-visited states (measure THAT before
training — the oracle-probe pattern). Owner's call on spending it.

## R1 — the residue probe: per-state fidelity at seam-visited states (pre-registered)

**Question.** K1's verdict named the surviving suspect: the pooled val
(0.9658) is dominated by native-start states — the clone's fidelity ON
the states a seam actually visits is unmeasured. R1 measures exactly
that, before any training money is spent.

**Instrument.** `run_composite_episode` gains `probe=None` (two lines,
bit-identical when None — the C1 trace-hook pattern). A `SeamProbe`
rides the RECORD lineup (PerStageExperts + HYBRID, the deployed
contender) over the standing exam block (seeds 110000..110099, n=100)
and, at every slalom-stage decision, records: the executed action, the
**OracleWeave counterfactual label** at the same state (begin() at
stage entry with the relay's stage-window pillars — weave is a pure
function of (x, y) vs its gate ladder, so counterfactual queries are
exact), and a mirror ObsBuilder vec built with collect_hot's exact
construction (StageLocal reset, executed-prev, stage-local x). No new
gate number is produced: the record lineup flies its own standing exam;
the v2 clone NEVER flies (offline forward passes only — its formal
stays unrun).

**Agreement** = executed menu action == weave label (menu space, the
same space as bc_train's val meter). Caveat, frozen now: agreement is
label-match, not correctness — several actions can be safe at once, so
absolute level is not the read; the CONTRASTS are.

**Instrument checks (before any read):**
- Exam-outcome match: per-seed success vs `hybrid4_n100.json` — expect
  ≥ 0.95 (deterministic re-fly; the env was REBUILT since the record,
  so drift is possible). Below 0.95 → flag loudly as a reproducibility
  finding; the primary read still stands (contrasts are internal to the
  capture) but the "record's 12 seam failures" framing is re-anchored
  to the capture's own outcomes.
- Mirror fidelity: the record clone's OFFLINE predict on mirror vecs
  must equal its executed actions ≥ 0.99 — proves the vec mirror is
  faithful. Below → the v2 secondary is marked unreadable; the primary
  (live agreement) does not depend on vecs.
- Menu-0 identity: `ObsBuilder.ids.index(FORWARD) == 0` asserted at
  capture start (the mirror's entry-prev convention).

**Primary contrast (barred): cold vs seam.** A_cold = pooled
per-decision agreement on slalom stages at position 0; A_seam = same at
position ≥ 1. Stage-clustered means reported alongside; if pooled and
clustered disagree on the branch, treat as GRAY.
- **CONFIRMED** (a broad seam-entry fidelity tax): A_seam ≤ A_cold − 0.03.
- **REFUTED** (no detectable tax): A_seam ≥ A_cold − 0.01.
- GRAY between → pool a fresh block (seeds 113000, n=60), judge pooled.

**Co-primary contrast (barred): within-seam, by outcome.** A 5-point
deficit concentrated on the ~26 % of seam stages that break would
dilute to ~1.3 points pooled and hide under the primary — so it gets
its own bars (wider: fewer decisions, episodes end at the crash).
A_broke = agreement on seam stages where the episode broke AT that
stage; A_cleared = agreement on seam stages cleared.
- **CONFIRMED** (fidelity deficit rides the failures): A_broke ≤ A_cleared − 0.05.
- **REFUTED**: A_broke ≥ A_cleared − 0.02. GRAY between → same recheck.
- Readability floor: ≥ 6 broke seam stages in-sample, else recheck block.

**Verdict synthesis (frozen):** fidelity is the lesion iff EITHER
contrast confirms; the fidelity story dies iff BOTH refute.

**Secondary (declared): the v2 clone, same states.** Offline
teacher-forced predicts on the captured vecs (readable only if mirror
fidelity ≥ 0.99). Interpretation table, frozen:
- Primary/co-primary CONFIRMED and v2 does NOT close the gap → K1's
  diet never transferred to these states; imitation-side repair is
  still unexploited (anchored FT with imitation anchor — owner's call).
- CONFIRMED and v2 CLOSES the gap (yet K1 success was flat) → fidelity
  was raised and success did not follow → **fidelity is non-binding**;
  imitation-side work is dead, the money is saved.
- REFUTED → v2 read is a consistency check only.

**Context reads (declared, not barred):** agreement by upstream stage
type (the door→slalom edge carried 6 of 13 record breaks);
early-window (first 12 decisions post-entry) vs rest; break-step-
after-entry histogram; per-decision agreement in the last 10 decisions
before a break. Interpretation guide, frozen: if REFUTED and
A_broke ≈ A_cleared, the clone is **on-teacher-but-dying** — the named
suspect becomes teacher adequacy at deployed seam states (the oracle
relay's own clean-course rate was 0.550), and the residue arm's shape
becomes RL-from-success (transcend the teacher), not imitation repair.

**What this probe cannot decide (honest scope):** it does not gate
WHETHER anchored FT is the next candidate (pre-named since K1); it
decides the rationale and the training target — imitation top-up vs
RL-from-success — and in exactly one cell (CONFIRMED + v2-closed) it
kills the imitation rationale outright.

**Artifacts:** `experiments/transit_gate_v2/r1_seam_fidelity.json`
(committed record) + capture npz in `artifacts/` (gitignored, replay
corpus). Tool: `eval/eval_seam_fidelity.py` (--capture/--selftest).

## R1 results (2026-07-12 — r1_seam_fidelity.json)

**Instrument, first:** exam-outcome match **1.000** — the rebuilt
environment (fresh miniforge, torch 2.12.1) reproduces the gate of
record per-seed EXACTLY, 72/100 with the same 72. Mirror fidelity
**1.0000** (the offline clone reproduces every executed action from the
mirror vecs — the vec construction is bit-faithful). 608 post-crash
phantom rows excluded. Every read below is fully credentialed.

| contrast | numbers | frozen bar | branch |
|---|---|---|---|
| primary: cold vs seam | **0.9523 vs 0.8573** (−9.5 pts; clustered −12.0) | −0.03 | **CONFIRMED** |
| co-primary: seam broke vs cleared | **0.6667 vs 0.9101** (−24.3 pts, 12 stages) | −0.05 | **CONFIRMED** |

**VERDICT: FIDELITY-IS-THE-LESION.** On the states a seam actually
visits, the clone leaves its teacher at 3× the cold rate — and on the
stages that break, one decision in three is off-teacher. Context reads
all cohere: the deficit concentrates in the entry window (first 12
decisions 0.7625 vs 0.8845 after) and on the worst mapped edge —
**opening_door→slalom agreement 0.6875, the failure map's 6-break edge
found again by a completely different instrument**. Cold breaks stay
on-teacher (0.9333): cold failures are the dynamics tail, not fidelity.

**The money read (secondary, frozen cell fired):** the v2 clone on the
SAME states — seam **0.8666** vs the record's 0.8573. K1's seventeen
thousand deployment-matched teacher-flown seam decisions bought **less
than one point** of fidelity on student-visited states. The registered
interpretation: *the diet never transferred; imitation-side repair is
still unexploited.*

**Mechanism, now named: covariate shift.** Teacher-flown trajectories
— even ones STARTED from true deployed entries (K1's whole design) —
relax back onto the teacher's manifold within a few decisions. The
states that kill the clone are the ones its OWN compounding deviations
create, and no amount of teacher-flown collection can harvest them.
This also retires the brake-null's wording the right way: stilling the
entry (brake) and matching the entry distribution (K1) both failed
because the problem was never the entry POSE — it is the off-manifold
aftermath the student generates from it. The textbook remedy is
DAgger: let the STUDENT fly, label its states with the teacher
counterfactually — which is mechanically exactly what this probe's
instrumentation already does.

## R2 — DAgger round 1 (pre-registered)

**One knob vs the record pot:** pot = the record recipe regenerated
(native 600 weave episodes + oracle-hot 240 courses — K1 already
demonstrated regeneration stability) **plus a DAgger component**:
student-flown slalom states (the RECORD lineup flies fresh courses),
weave-counterfactual labels, post-crash rows excluded. K1's
deployed-hot component is DROPPED (measured null; one knob stays one
knob). Collection: n=200 courses, **seeds 130000+** — disjoint from the
exam (110000), every graduation block, and every prior collection.
**No exam-seed state ever enters a pot: R1's capture npz is
diagnostic-only, permanently.**

**Floors (frozen):** kept DAgger rows ≥ 6,000 with seam rows ≥ 3,000;
pooled BC val ≥ 0.96; per-world val REPORTED (the dagger-val column is
the fit diagnostic: can one head fit both manifolds?).

**Bars (the campaign's standing bars, restated):** graduation n=60 @
seeds 114000 — integer-safe: wins ≥ 45 proceeds; wins 42–44 → recheck
block @115000 and pooled wins ≥ 90/120 proceeds; wins < 42 → dead. The
formal n=100 @ the standing 110000 exam: **PASS = ≥ 0.78** with the
per-type conditional guard (no type worse than record − 0.05: door
1.000, gap 0.966, odoor 0.906, mgap 0.864, slalom 0.829). Guard
failure at any rate = "traded", not a pass; no promotion.

**Pre-named continuation (frozen now, not fished later):** DAgger is
inherently iterative; ONE more round (R3: student = the R2 clone,
seeds 131000+) is auto-authorized iff the formal lands in **[0.72,
0.78)** — visible progress, short of the bar. Formal ≥ 0.78 → stop,
PASS (promotion into the deployed lineup is the OWNER's call — it
swaps a deployment artifact and re-anchors the gate of record). Formal
< 0.72 → R2 refuted: one DAgger round does not lift the composite;
residue re-points at RL-from-success (weave-anchored FT in-course) or
accepting 72 as the architecture's plateau.

**Machinery (defaults bit-identical):** `eval_seam_fidelity --capture`
gains `--out-json/--out-npz` (the exam-match read guards against
zero-overlap seed blocks; npz gains kept/outcome/dec/upstream arrays);
`build_bigpot_v2` gains `--dagger-npz` + `--hot-deployed 0` (deployed
floor applies only when the component is requested) and persists the
assembled pot arrays alongside the zip (R3 stops paying the
regeneration tax). Fresh-block capture diagnostics double as a free
R1 replication on non-exam seeds (reported, not barred).

## Status

- [x] Failure map computed from the gate of record (before any knob)
- [x] K1 pre-registered (this file, before any number)
- [x] Deployment-matched collection + big-pot rebuild + re-BC (floors ✓)
- [x] Graduation blocks 1+2 → pooled 0.725 < 0.75 → **K1 REFUTED;
      formal never runs; record lineup stays; residue = per-state
      fidelity at seam states (fresh registration, owner's call)**
- [x] R1 pre-registered (this file, before any number)
- [x] R1 capture + verdict: **FIDELITY-IS-THE-LESION (both contrasts
      CONFIRMED; v2 diet never transferred; mechanism = covariate
      shift; instrument perfect — exam match 1.000, mirror 1.0000)**
- [x] R2 pre-registered (this section, before any number)
- [x] R2 executed: **PROGRESS, NOT PASS — formal 0.73; the [0.72,
      0.78) cell fires R3** (results below)
- [x] R3 executed: **PASS — formal 0.79 ≥ 0.78, guards all held,
      slalom seam 30 % → 9.5 %. The ladder ends as frozen. Promotion =
      owner's call (not done).**

## R3 results (2026-07-12 — r3_grad_n60.json, r3_formal_n100.json) — PASS

**Collection (the R2 clone flying itself):** 240 courses @131000,
round-2 component kept 6,896 (3,814 seam) — floors ✓; aggregate dagger
14,185 (8,597 seam). Treatment response visible at collection: the R2
clone's own seam agreement 0.8728 vs the record clone's 0.8009 on
fresh seeds, fresh-block success 189/240 = 0.7875. Mirror 1.0000 again.

**Pot:** 58,854 decisions; pooled val 0.9614 ≥ 0.96 ✓; per-world val
**dagger 0.918 — UP from R2's 0.905**: no capacity slide; the head
absorbs the student manifold as it grows. Graduation 45/60 → formal.

**Formal: 0.79 ≥ 0.78 = PASS.** Method-consistent conditionals vs the
record, guard −0.05 ALL HELD:

| type | record | R3 | Δ |
|---|---|---|---|
| slalom | 0.814 | **0.917** | **+0.102** (seam fails 12/40 → **4/42 = 9.5 %**) |
| moving_gap | 0.846 | 0.887 | +0.041 (R2's dip was the draw, not damage) |
| opening_door | 0.900 | 0.923 | +0.023 |
| door | 1.000 | 0.980 | −0.020 ✓ |
| gap | 0.964 | 0.930 | −0.034 ✓ |

Break profile 28 → 21 fails; stage-1 breaks 12 → 5. The failure map's
arithmetic headroom ("slalom seam at its cold rate ≈ +10") is banked
at +7 by this knob; the residual failure mass is now SPREAD (mgap 4 /
gap 4 / odoor 3 / door 1 seam + 5 cold) — no single dominant edge
remains for a successor campaign to farm.

## Campaign verdict — the seam had a mechanism, and two rounds of DAgger bought it down

The arc, every step on the record: failure map (86 % seam; slalom ×8)
→ K1 deployment-matched teacher data REFUTED (0.725, seam unmoved) →
R1 probe names the mechanism (covariate shift; fidelity 0.9523 cold /
0.8573 seam / 0.6667 on breaking stages; K1's diet never transferred)
→ R2 DAgger-1 moves the target (seam 30 → 21.4 %, formal 0.73) → R3
DAgger-2 aggregate lands it (**0.917 conditional, seam 9.5 %, formal
0.79 PASS**). The ladder closes as pre-frozen; no R4.

**What remains the owner's (explicitly NOT done here):**
1. **Promotion** of `ppo_slalom_dagger_r3.zip` into the deployed
   lineup (`eval_integration.HYBRID` slalom slot) and re-anchoring the
   gate of record (72 → 79 in `scripts/gate.py` ingest + scorecard).
   Note: gate-lineup zips live under gitignored `artifacts/` dirs —
   record reproducibility wants the R3 zip published (champions
   release) or rebuilt from the persisted pot npz.
2. Or hold at 72-of-record with the R3 result banked in the journal.

**Named residues (fresh registrations if pursued):** the spread tail
(no dominant edge — diminishing returns priced accordingly),
dagger-weighted BC, RL-from-success. The moving_gap seam recovered on
its own draw (+4.1) — K2's motivation is now thinner than at freeze.

## Promotion (2026-07-12, owner's call — Hans「go 1 then push」)

Executed: `eval_integration.HYBRID["slalom3_fixed"]` →
`ppo_slalom_dagger_r3.zip`; `scripts/gate.py` re-anchored
(TRANSIT_RECORD → `r3_formal_n100.json`, 79/100; re-fly scratch path
split from the record so `--run-transit` can never shadow it; selftest
asserts 0.79); README status + gate section carry the new number with
lineage; CHANGELOG Unreleased updated. Record reproducibility: the R3
zip's sha256 is
`dcb50674a492f4af829bd9980b77a0465e4225ba82eb17f531fc0c4079f7b182`
(recorded here); publishing it to the champions release awaits the
owner's explicit release word (the permission layer correctly held the
upload — releases are owner-gated by house rule), and the assembled
pot npz is persisted locally for deterministic rebuild meanwhile. The
72/100 lineup and its record file stay in the tree untouched as
lineage.

## R2 results (2026-07-12 — r2_grad_n60.json, r2_formal_n100.json)

**Pot & floors:** 51,958 decisions (native 37,035 + oracle-hot 7,634 +
**dagger 7,289**, of which 4,783 seam); pooled val 0.9648 ≥ 0.96 ✓.
**Per-world val — the fit diagnostic: dagger 0.905** vs native 0.983 /
oracle-hot 0.935: the student manifold is measurably harder for the
same head. Graduation 45/60 = 0.750, exactly the integer bar → formal.

**Formal: 0.73** (record 0.72; bar 0.78). Method-consistent per-type
conditionals (same script on both gate files): slalom **0.814 → 0.861
(+4.7 pts; seam failures 12/40 → 9/42, 30 % → 21.4 %)**, odoor 0.900 →
0.920, door 1.000 = 1.000, gap 0.964 → 0.946 (−1.8), moving_gap 0.846
→ 0.815 (−3.1). Guard (≤ −0.05, method-consistent deltas): ALL HELD.

**Reading:** the knob moved its target — the slalom seam shrank by a
third, the first instrument-confirmed lift this campaign — but the
composite banked only +1 because moving_gap (whose seam this knob was
never pointed at; pre-named K2 since the failure map) gave back three.
**The [0.72, 0.78) cell fires: R3 auto-authorized per the frozen tree.**

## R3 — DAgger round 2 (pre-registered; the ladder's last rung)

**One knob:** aggregate DAgger, canon form — pot = R2's pot + a round-2
component collected by the **R2 clone itself** flying the lineup
(students collect their own residual off-manifold states; the record
clone's states stay in — aggregation, not replacement). Collection
n=240 @ **seeds 131000+**; component floors same as R2 (kept ≥ 6,000,
seam ≥ 3,000, asserted on the NEW component alone at merge); pooled
val ≥ 0.96; per-world val watched (a dagger-val slide below ~0.90 is
the capacity-wall signature, reported not barred).

**Bars:** graduation n=60 @116000 (wins ≥ 45; 42–44 → recheck @117000
pooled ≥ 90/120); formal @ the standing 110000 exam, **PASS ≥ 0.78**,
same method-consistent conditional guard. **Exit branches, frozen: ≥
0.78 → PASS, stop (promotion = owner's call); ANYTHING below → the
campaign's imitation-side closes at its measured plateau — no R4, no
ladder.** Residue arms already named: moving_gap seam (K2, a different
knob), dagger-weighted BC (the 7.3k student rows are 14 % of a pot
that is 84 % teacher-manifold — a sample-weight knob, separate
registration), RL-from-success, or accept the plateau.

**Machinery (defaults bit-identical):** `eval_seam_fidelity --capture`
gains `--slalom-zip` (the student slot override, mirroring
eval_integration's) so round-2 states are the R2 clone's own.

**R2 execution notes (recorded as they happened):**
- The n=200 collection under-delivered the frozen floor by 22 rows
  (kept 5,978 < 6,000 — the fresh block breaks more often than the
  exam, so postmortem exclusion bites harder; 1,482 rows excluded of
  7,460). **The floor did its job and the build refused.** Remedy per
  the house rule (bars never move to meet numbers): collection
  EXTENDED within the same pre-named seed block (+40 courses @130200),
  floors and bars untouched. n=200 was dosage, not a bar.
- Free replication: the fresh-block capture reproduces R1 on non-exam
  seeds, stronger — cold 0.9420 vs seam 0.8009 (CONFIRMED), broke
  0.4538 vs cleared 0.9011 over 29 broke stages (CONFIRMED), mirror
  1.0000 (r2_dagger_diag.json).
- Builder gained `--base-cache` (opt-in, defaults bit-identical): the
  native+oracle base is a pure function of its frozen seeds and had
  now been regenerated three times; a downstream floor failure no
  longer burns the ~2 h regeneration.

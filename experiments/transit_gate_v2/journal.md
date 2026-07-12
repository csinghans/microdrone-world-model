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

## Status

- [x] Failure map computed from the gate of record (before any knob)
- [x] K1 pre-registered (this file, before any number)
- [x] Deployment-matched collection + big-pot rebuild + re-BC (floors ✓)
- [x] Graduation blocks 1+2 → pooled 0.725 < 0.75 → **K1 REFUTED;
      formal never runs; record lineup stays; residue = per-state
      fidelity at seam states (fresh registration, owner's call)**
- [x] R1 pre-registered (this section, before any number)
- [ ] R1 capture on the exam block + verdict vs the frozen contrasts

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

## Status

- [x] Failure map computed from the gate of record (before any knob)
- [x] K1 pre-registered (this file, before any number)
- [x] Deployment-matched collection + big-pot rebuild + re-BC (floors ✓)
- [x] Graduation blocks 1+2 → pooled 0.725 < 0.75 → **K1 REFUTED;
      formal never runs; record lineup stays; residue = per-state
      fidelity at seam states (fresh registration, owner's call)**

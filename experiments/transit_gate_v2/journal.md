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

## Status

- [x] Failure map computed from the gate of record (before any knob)
- [x] K1 pre-registered (this file, before any number)
- [ ] Deployment-matched collection + big-pot top-up + re-BC
- [ ] Graduation n=60 → formal n=100 → verdict

# evidence_v1 — detection as sequential evidence (SPRT vs confirm-k)

**Opened:** 2026-07-12 · **Owner:** Hans · **Source:** docs/REVIEW-2026-07.md (C2)

## The question

Every indoor visual mission converts per-frame scores into ONE mission
decision through an ad-hoc rule: consecutive-k debounce (vision_v1
traded FA 0.95→0.35 for miss 0.40 with it) or confirm-2 (yaw_v1,
person_v1). C1 just measured why this is fragile: on moving frames the
scores shift down and a fixed threshold reads almost nothing
(recall@0.65 0.758→0.182) while the RANKING survives (AUC 0.889).
A firing rule that accumulates the score STREAM as evidence — instead
of thresholding single frames — is built for exactly that failure
shape. Does it actually beat the incumbent, on identical data?

## Protocol (frozen before any number)

**Corpus:** C1's recorded in-flight streams — 40 flights, 10,542
labelled frames (`experiments/detect_inflight_v1/artifacts/
streams.npz` block 1, seeds 620000+; `streams_b2.npz` block 2, seeds
620020+; regenerate: `python -m eval.eval_inflight_detect`).

**Contenders, per-flight firing rules:**
- *confirm-k (incumbent):* fire at the first frame where the last k
  consecutive probs ≥ thr. Grid k ∈ {1,2,3,5} × thr ∈ {0.3,0.4,0.5,
  0.65,0.8}.
- *CUSUM-SPRT (challenger):* per-frame calibrated log-likelihood
  ratios, accumulated with reset-at-zero (S ← max(0, S + LLR), the
  change-detection form — a plain cumulative sum drifts negative before
  the target ever appears); fire at S ≥ A, grid A ∈ {1,2,3,4,6,8}.
  LLR calibration: 10 quantile bins fit on the TRAIN block's
  (prob, label) pairs, Laplace-smoothed — deterministic, no learning
  beyond counting.

**Outcome per flight:** fire step s* → CORRECT if label[s*]=1, else
FALSE ALARM; no fire → MISS. (The same semantics the flight harness
scores.)

**Honest replay caveat, stated up front:** the streams came from
flights whose OWN rule fired and turned home — replay is exact for
decisions at or before the original firing step; later fires read
return-leg imagery. Both contenders face the identical corpus, so the
COMPARISON is fair; absolute rates are approximate and the flight
regate (a later sitting) owns them.

**Selection discipline (no eval leakage):** each rule's config is
chosen on the TRAIN block (max correct-find subject to per-flight
FA ≤ 0.10 — the deployed gate's FA bar), then scored frozen on the
EVAL block. Cross-fitted both directions (1→2 and 2→1).

## Pre-registered bars

- **SPRT WINS** if, in BOTH cross-fit directions, at train-selected
  FA ≤ 0.10 configs it scores eval correct-find ≥ the incumbent's AND
  median steps-to-fire (among correct) ≤ 0.8× the incumbent's — OR
  correct-find ≥ incumbent + 0.10 at no worse median steps. → releases
  the flight-regate phase (the winning rule choreographed into the
  yaw-scan mission, judged on the indoor gate bars).
- **Honest negative** if the incumbent matches or beats the challenger
  in either direction: record "the heuristic was already optimal at
  this operating point", export the calibration tables, close at P0's
  price.

## Results (2026-07-12 — `eval_evidence --duel`, duel_results.json)

| direction | rule (train-selected) | correct | FA | miss | med steps |
|---|---|---|---|---|---|
| b1→b2 | confirm-k (k=2, thr=0.4) | 0.200 | 0.250 | 0.550 | 108 |
| b1→b2 | CUSUM-SPRT (A=6) | 0.000 | **0.850** | 0.150 | — |
| b2→b1 | confirm-k (k=1, thr=0.8) | 0.250 | 0.100 | 0.650 | 131 |
| b2→b1 | CUSUM-SPRT (A=6) | 0.150 | **0.600** | 0.250 | 100 |

## Verdict — honest negative: the incumbent holds, and the mechanism rhymes

**SPRT/CUSUM as instantiated is REFUTED on this corpus, both
directions** (the pre-registered negative branch fires). The mechanism
is the campaign's real yield, and it rhymes with B4: reset-at-zero
CUSUM has an UNBOUNDED accumulation horizon — negatives are 94 % of
these moving-frame streams, and any weakly-positive LLR mass in the
mid-bins drifts across the boundary over hundreds of frames, so the
false-alarm rate explodes (0.85 / 0.60). confirm-k's fixed window
BOUNDS the per-decision false-alarm mass. **The horizon's boundedness
is worth more than the accumulation's optimality** — B4's any-trigger
amplification, now measured on the challenger's side of the ledger.

Instrument observation, recorded: config selection transfers poorly
across blocks for BOTH rules (confirm-k's b1-selected config blows the
FA budget on b2: 0.250 vs 0.10) — 20 flights per block is thin for
selection; any future registration should select on pooled flights
with a held-out block.

**Consequences.** The deployed choreography (hover-scan + confirm-2)
stays the config of record. Named candidates for a FRESH registration
(not run): a bounded-horizon evidence window (sum of the last W LLRs —
the middle point between confirm-k and CUSUM); pooled-selection
protocol; or repair per-frame quality first (C1's moving-frame
head-retrain knob) — on a corpus where the best achievable
correct-find is ~0.25, no firing rule can rescue the mission, which is
C1's conclusion restated at the rule layer. Article #9's spine is now
this negative: *per-frame recall is a lie — and so is unbounded
evidence.*

## Status

- [x] Pre-registration committed (this file, before any number)
- [x] `eval/eval_evidence.py` (offline duel) + selftest
- [x] Cross-fit duel → **honest negative both directions; incumbent
      holds; unbounded-horizon mechanism named; flight regate NOT
      released**

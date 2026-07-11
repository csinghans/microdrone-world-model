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

## Status

- [x] Pre-registration committed (this file, before any number)
- [ ] `eval/eval_evidence.py` (offline duel) + selftest
- [ ] Cross-fit duel → verdict

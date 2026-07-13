# integration_k6_v1 — the chain doubled: 6 stages, one read

**Opened:** 2026-07-13 · **Owner:** Hans（「整合飛行測試把關卡從3變到
6，看成功率是多少」）· Prior: the 3-stage gate of record 79/100
(`experiments/transit_gate_v2/r3_formal_n100.json`); the true-rate
table and lineup-coupling law (`experiments/transit_gate_v3/`).

## The question

The deployment gate chains 3 random stages; this read doubles it to 6
with the SAME deployed lineup, judge, and speed. It is a PRICING
measurement, not a new gate — the 3-stage exam remains the gate of
record. The scientific question underneath: **does the chain
arithmetic hold at depth** — is the per-seam failure rate independent
of chain length (StageLocal resets every stage, so nothing should
accumulate), or do longer chains compound something we have not
named?

## Protocol (frozen)

- Lineup: the deployed hybrid (FT-v3 generalist + R3 DAgger slalom
  clone), speed 1.0, judge `integration_success` — everything as the
  standing gate, except `k=6`.
- **n=100, fresh seed block 140000** (never used by any exam,
  graduation, or collection).
- Machinery: `suite()`/CLI gain `k` (default 3, bit-identical; the
  composite builders were k-generic already).

## Declared prediction (frozen before the number; a prediction, not a bar)

From the method-consistent conditionals with the true-rate correction
(door 0.980, gap 0.930, odoor 0.923, mgap 0.887, slalom ~0.88 true),
uniform stage draw, 1 cold + 5 seam positions: mean per-stage
conditional ≈ 0.92 → expected composite ≈ 0.92^6 ≈ **0.55–0.65**.
- Landing inside the band ⇒ chain arithmetic holds; 6-stage success
  is priced and predictable from 3-stage conditionals.
- Materially below ⇒ something compounds with depth (a finding worth
  its own campaign — position-trend dissection is the first cut).
- Materially above ⇒ the conditionals were pessimistic (position-0
  mix, or seam rates improving late in chains) — also a finding.

**Declared reads:** success rate; failure dissection by stage
position (0–5), type, and seam-vs-cold; per-seam rate vs the 3-stage
lineage table (slalom seam true 17.2 %); position trend of seam
failures (flat = no accumulation).

## Status

- [x] Pre-registration (this file, before any number)
- [ ] k=6 read: n=100 @140000 → rate + dissection vs the prediction

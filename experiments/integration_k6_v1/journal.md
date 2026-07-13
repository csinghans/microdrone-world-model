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

## Results (2026-07-13 — k6_n100.json)

**k=6 success: 50/100 = 0.500** — below the frozen 0.55–0.65 band
(borderline as a composite number at ±5 pts, but the declared
position read settles it decisively).

**The finding — depth compounds.** Pooled seam failure rate BY
POSITION: 1→ 3.2 % (3/95), 2→ 9.8 %, 3→ 13.3 %, 4→ 12.5 %, 5→
**20.6 %** (13/63). Position 1 vs position 5 is z ≈ 3.4 — the
per-seam rate is NOT independent of chain depth. In hindsight the
k=3 record already whispered it (r3_formal: stage-1 seams 5.3 %,
stage-2 12.2 %); at k=6 the whisper is a trend. Chain arithmetic
(conditional^k) is REFUTED as a pricing model for deep chains.

Per-type seam rates at k=6: slalom 21.6 % (true 17.2 % at k=3),
moving_gap 15.1 %, **door 10.0 % (≈0–3 % at k=3 — the generalist
suffers at depth too; this is not clone-specific)**, gap 7.2 %,
odoor 2.4 %. Cold (position-0) fails 5/100, unchanged.

**Mechanism hypothesis (recorded, not asserted): the entry-state
random walk.** StageLocal resets the POLICY's memory at every stage
— but nothing resets the AIRCRAFT: exit pose (y offset, velocity,
attitude) carries variance into the next stage, and over depth that
variance accumulates like a random walk. Deeper seams therefore
sample wider, more-OOD entry distributions — and the DAgger diet was
collected on 3-STAGE courses (seam positions 1–2 only), so its
coverage thins exactly where depth begins. Every cut coheres: all
types degrade at depth (not just the clone), and the trend is in
position, not time-in-flight per se.

**Named next arms (owner's call, each a fresh registration):**
1. Cheap probe: record pose-at-entry (y, vy) vs position on a k=6
   re-fly (the SeamProbe hook pattern) — measure the walk directly;
   if entry spread does NOT widen with depth, the hypothesis dies
   and something else compounds (e.g. controller integrator state).
2. Depth-DAgger: collect student states on 6-stage courses (deep
   seam entries enter the diet) — the v2 playbook, one level deeper.
3. Accept: the 3-stage gate remains the gate of record; six stages
   are now priced at 0.500 with the mechanism named.

## K1 — the pose-at-entry probe (pre-registered)

**Question.** Does the entry-state distribution widen with depth —
is the random walk real? Direct measurement, no training.

**Instrument.** `PoseWalkProbe` on the standing `probe` hook: re-fly
the SAME k=6 block (140000, n=100, identical lineup — deterministic),
and at the first decision tick of every stage entry record the
aircraft's pose (y, z, vx, vy) plus position/type. The probe only
reads; per-seed outcomes must match `k6_n100.json` at **1.000**
(probe inertness in vivo — the R1 precedent).

**Frozen reads and branches:**
- Spread ratio R(m) = pooled mean |m| at entry positions 4–5 ÷ pooled
  mean |m| at positions 1–2, for m ∈ {y, vy}.
  **WALK CONFIRMED** iff R(y) ≥ 1.5 or R(vy) ≥ 1.5;
  **REFUTED** iff both < 1.2; between → gray, judged with the
  death-link read.
- **Death link (co-read):** at seam entries, failure rate for
  above-median |y| entries vs below-median. Link ratio ≥ 2 ties wide
  entries to deaths mechanistically.
- Full per-position tables reported (mean, p90 of |y|, |vy|).

**Consequences (frozen):** CONFIRMED + linked → depth-DAgger becomes
the matched remedy (its diet directly covers wide entries), and a
cheaper candidate is named for pricing first: an inter-stage
RECENTER behavior (actively drive y→0 before the next stage — NOT
the refuted brake, which only stilled velocity in place). REFUTED →
the walk dies; next suspects, each needing its own probe: controller
integrator state over long flights, or something time-indexed rather
than position-indexed.

**Machinery:** `eval/eval_pose_walk.py` (probe + runner + verdict;
selftest covers entry detection, spread/link arithmetic, frozen
thresholds). State indices per the kinematic layout: y=state[1],
z=state[2], vx=state[10], vy=state[11].

## Status

- [x] Pre-registration (this file, before any number)
- [x] k=6 read: **0.500, below the band; depth-compounding CONFIRMED
      via the position trend (3.2 % → 20.6 %, z ≈ 3.4); entry-state
      random walk hypothesized; arms named for the owner**
- [x] K1 pre-registered (this section, before any probe number)
- [ ] K1 pose-walk probe: re-fly @140000 with the probe → verdict

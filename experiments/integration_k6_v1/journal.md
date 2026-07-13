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
- [x] K1 executed → **GRAY as written, with the mechanism sharpened**
      (results below)

## K1 results (2026-07-13 — k1_pose_walk.json) — GRAY as written; the walk is real but SATURATING

Instrument 1.000 (599 entries, probe inert in vivo). The frozen reads:

| read | value | bar | as written |
|---|---|---|---|
| spread ratio R(y), deep/early | **1.466** | ≥ 1.5 | GRAY |
| spread ratio R(vy) | 1.173 | ≥ 1.5 | — |
| death link (wide vs narrow \|y\|) | **×1.992** (0.120 vs 0.060) | ≥ 2.0 | not linked, by 0.008 |

Both effects sit a hair under their bars — and both are statistically
solid on their own terms: per-position mean |y| climbs **0.090 →
0.121 → 0.143 → 0.159** (positions 1→4, z ≈ 5 on ~120 entries per
position) then **saturates** (0.150 at position 5), and wide entries
die at twice the rate of narrow ones (z ≈ 2.5). The bars were frozen
as instrument guesses; reality landed at 1.47 and 1.99. The letter
binds: **the walk hypothesis is NOT confirmed as registered.** The
observation stands on file in full.

**The mechanism, sharpened by the miss:** the entry-state process is
not a pure random walk — the corridor-centering prior acts as a
restoring force, so spread grows for ~3 stages and then SATURATES
around |y| ≈ 0.15 (an Ornstein–Uhlenbeck signature, which is exactly
why the deep/early ratio undershoots a pure-walk prediction). The
saturated wide regime is itself the danger zone (×2 death rate), and
within statistical power the failure-vs-position trend is compatible
with the spread trend (positions 4→5: 12.5 % vs 20.6 % is z ≈ 1.2 —
not evidence of a second mechanism).

**Options (owner's call):**
1. Recheck by pooling a second k=6 block (~2 h) — but both point
   estimates sit just under their bars, so pooling most likely buys a
   tighter gray, not a verdict.
2. **Intervention beats observation (recommended):** price the
   RECENTER behavior — actively drive y→0 at stage boundaries — and
   read the position trend under it. If the depth trend flattens, the
   mechanism is confirmed interventionally (stronger than any ratio
   bar) and the remedy is priced in the same run. Fresh registration.
3. Accept: 6 stages priced at 0.500, mechanism recorded as
   "saturating entry-spread, death-linked ×2, formally gray".

## Status

- [x] Pre-registration (this file, before any number)
- [x] k=6 read: **0.500, below the band; depth-compounding CONFIRMED
      via the position trend (3.2 % → 20.6 %, z ≈ 3.4); entry-state
      random walk hypothesized; arms named for the owner**
- [x] K1 pre-registered (this section, before any probe number)
- [x] K1 pose-walk probe: **GRAY as written (R(y) 1.466 vs 1.5, link
      ×1.992 vs 2.0) — the walk is real, saturating (OU signature),
      and death-linked at ×2 within a hair of the bar; intervention
      probe (RECENTER) named as the recommended next arm**

## K2 — the RECENTER intervention (pre-registered)

**One knob.** `RecenterWrap` around the deployed hybrid: at each
stage entry, for a budget of 12 decisions, whenever the inner pilot
would fly FORWARD (no perceived threat) and |y| > 0.05, substitute
the veer toward y=0 instead; any non-FORWARD inner decision (evade /
slow / hover) is always respected — recentering is opportunistic and
never overrides a threat response. Own-odometry only (y), the same
information the W_CENTER prior already uses — flight-plan legal.
This is NOT the refuted brake: the brake stilled velocity in place;
this actively removes the lateral offset K1 measured as ×2 deadly.

**Exam:** the SAME k=6 block (140000, n=100 — paired seeds against
the 0.500 record read). The PoseWalkProbe rides along (read-only).

**Frozen reads, in dependency order:**
1. **Manipulation check (gates everything):** deep-entry (positions
   4–5) mean |y| must drop to ≤ 0.11 (K1 measured 0.155; position-1
   level is 0.090). If recentering fails to actually tighten entry
   pose, the mechanism read is VOID — an intervention that did not
   manipulate the variable proves nothing either way.
2. **Mechanism read:** deep-seam (positions 3–5) pooled failure rate
   ≤ 10 % (the record read: 33/218 = 15.1 %) ⇒ the entry-spread
   mechanism is CONFIRMED interventionally. ≥ 13 % with the
   manipulation check passed ⇒ the mechanism is REFUTED (pose was
   tightened, deaths did not move). Between ⇒ gray.
3. **Remedy price:** overall k=6 success ≥ 0.58 (record 0.500) ⇒ the
   recenter behavior is a real remedy candidate (adoption = a
   separate lineup decision, owner's).
4. **Guard:** early seams (1–2) + cold fails must not worsen by more
   than 3 total (blind-veer risk priced; the opportunistic design
   should make this free).

**Machinery (defaults inert):** `RecenterWrap` + `--recenter` flag on
the hybrid contender in `eval_integration`; selftest pins the
substitution logic (only FORWARD replaced, threats respected, budget
and tolerance honored).

- [x] K2 pre-registered (this section, before any number)
- [x] K2 executed → **mechanism REFUTED interventionally** (below)

## K2 results (2026-07-13 — k2_recenter_pose.json) — the pose story dies at the intervention's hands

| frozen read | value | bar | verdict |
|---|---|---|---|
| manipulation: deep-entry mean \|y\| | **0.1021** (was 0.155; per-position 0.09–0.11, the walk profile GONE) | ≤ 0.11 | **PASSED** |
| mechanism: deep-seam (3–5) fail rate | **15.3 %** (33/215; baseline 15.1 %) | ≤10 confirm / ≥13 refute | **REFUTED** |
| remedy: k=6 success | 0.49 (baseline 0.500) | ≥ 0.58 | no remedy |
| guard: early+cold delta | +1 | ≤ +3 | held |

The intervention did exactly what it was built to do — entry pose
tightened to position-1 levels at every depth — **and the deaths did
not move at all.** Entry offset is a MARKER, not a CAUSE. The
tell-tale: within the recentered arm, relatively-wide entries STILL
die at ×1.8 — the correlation survives the removal of the variance,
the signature of a confounder riding along. K1's correlational
near-miss pointed one way; the intervention settled it the other.
This is why interventions outrank ratio bars.

## The free dissection that names the next suspect

Per-type seam failure, early (1–2) vs deep (3–5), baseline block:
gap (static) **7 % → 7 % flat**; slalom (static) 17 % → 25 %
(z ≈ 0.9, noise); door 9 % → 11 %; opening_door 0 % → 4 %;
**moving_gap 2 % → 27 % (1/45 → 13/48, z ≈ 3.3).**

**The depth tax is essentially ONE type: the timing stage.**
Refined suspect: **arrival-phase scrambling** — moving_gap demands
phase alignment (v3's K2-swap measured that wall: even its own
champion degrades 10.5 pts from cold to seam = random-phase arrival),
and deeper positions are reached later with wider arrival-TIME
variance, scrambling the phase distribution beyond anything the
pilot practiced. This also explains K2's null (recentering pose does
not change arrival time) and K1's death-link confound (late, messy
flights arrive both wider AND phase-scrambled — pose rode along with
time).

Honest anomaly, flagged not resolved: this block's EARLY moving_gap
seam rate (2.2 %) sits well below the k=3 historical 15–17 %
(binomial p ≈ 0.004) — the position-1/2 structure of mgap seams
deserves its own look before any phase campaign freezes bars.

**Named next arm (fresh registration, owner's call): the phase
probe** — persist per-entry arrival times (the pose probe already
captures `t`; it needs only to SAVE rows) plus the moving gap's
oscillation phase at entry, and correlate phase-at-arrival with
death. If deaths concentrate in a phase band, the mechanism is
nailed and the remedy menu is concrete (phase-aware entry timing —
wait for the window — or phase-randomized training, v3's parked arm,
now with a mechanism to aim it).

## Status

- [x] Pre-registration; k=6 read 0.500; depth trend z ≈ 3.4
- [x] K1 pose probe: GRAY as written; walk real but saturating
- [x] K2 recenter intervention: **manipulation PASSED, mechanism
      REFUTED — pose is a marker, not a cause; guard held**
- [x] Free dissection: **the depth tax is moving_gap's (2 % → 27 %,
      z ≈ 3.3); arrival-phase scrambling named; phase probe = the
      next arm (owner's call)**

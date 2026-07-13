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

## K3 — the rendezvous probe (pre-registered)

**Reading the scenario sharpened the suspect before the probe flew.**
`MovingGapFence` does not oscillate — it drifts LINEARLY (vy constant,
0.15–0.35 m/s, no period, no bounce), and it is AIMED with a
cold-start assumption: the gap centre is placed to pass near the
centreline at `t_arr = x_gap / cruise`, computed from the stage's own
origin. In a composite course every fence starts sliding at LAUNCH,
so a stage at position j is reached ≈ 3j/cruise seconds late — the
rendezvous is long past, and the displacement grows LINEARLY with
position (≈ vy·3j/cruise: ~0.5–1.3 m at j=1, ~2.8–6.6 m at j=5,
beyond the fence's ±3.2 m coverage). "Phase scrambling" refines to
**rendezvous displacement**.

**Instrument (read-only, baseline lineup, same block 140000):**
`GapPhaseProbe` records, at every decision inside a moving_gap stage:
t, drone (x, y), the fence plane x, the gap centre y (widest spacing
midpoint among the stage-window pillars — the weave-gate rule, valid
at any slide), and the fence's y-coverage (open-bypass detection).
Rows PERSISTED. Per instance, the crossing tick = first tick with
x ≥ plane (or the last tick if it broke short).

**Frozen reads:**
1. Instrument: per-seed outcomes match `k6_n100.json` at 1.000.
2. **Premise:** mean |gap-centre y| at crossing grows with position —
   CONFIRMED if deep (3–5) ≥ 2× early (1–2). Linear-drift arithmetic
   predicts well above 2×.
3. **Death link (the causal read):** mgap instances that broke vs
   cleared — broke mean |gap offset at crossing/break| ≥ 1.5× cleared
   ⇒ LINKED (deaths ride the displacement). Report the above/below
   median split too (the K1 pattern; K1's boundary lesson noted —
   point estimates govern, borderline goes gray, not fished).
4. Bypass audit (declared): fraction of deep instances where the
   slid fence leaves the corridor edge open (an accidental easy-out
   would CUT deaths at extreme displacement — report, it shapes the
   remedy).

**Consequences (frozen):** premise + link confirmed ⇒ the depth tax
mechanism is NAILED as a scenario-composition artifact (cold-start
rendezvous reused at depth), and the remedy menu is concrete and
CHEAP: re-aim each composite stage's fence at its own expected
arrival (a composite-builder fix — the exam becomes what it was
always meant to be), with "wait-for-the-window entry" and v3's
phase-randomized training as pilot-side alternates. Refuted ⇒ the
displacement is not the killer; back to arrival-time dissection.
NOTE: any change to the composite builder re-defines the exam — the
k=3 gate of record is untouched by this campaign regardless.

- [x] K3 pre-registered (this section, before any number)
- [x] K3 executed → split verdict + the campaign's biggest
      generalization (below)

## K3 results (2026-07-13 — k3_rendezvous.json + rows npz)

Instrument 1.000. **Premise REFUTED — my displacement theory was shot
by the instrument:** gap-centre offset at crossing is FLAT with depth
(0.13 → 0.17 m, ×1.3 vs the 2.0 bar; per-position 0.10–0.24 ≈ the
designed yc_hit ±0.3 expectation). The composite LAZY-STEPS its
stages — `CompositeCourse.step()` advances only the stage the drone
is inside, "its first step() call IS its clock zero, so baked aim
math holds" (the comment was there; I theorized from the skill file
without reading the composite). Bypass 0.00 everywhere.

**Death link LINKED, hard: ×2.52** (broke instances cross at
drone-gap offset 0.38 m vs cleared 0.15 m), and the median split is a
razor — **29.8 % of wide-half instances die, 0.0 % of the narrow
half.** Every mgap death is a failure to ALIGN by crossing time.

## Exploratory addendum (labelled as such; free dissections of the rows)

- **Outward encounters kill:** when the gap drifts AWAY from the
  centreline during approach, fail 35.3 % vs 10.4 % inward (×3.4);
  broke instances' gap sits off-centre at crossing (0.343 vs 0.117).
- **Entry conditions are FLAT at every depth and non-predictive:**
  entry misalignment 0.52–0.58 everywhere (broke entries were
  slightly BETTER aligned, ×0.82); entry |vy| ~0.02; approach time
  2.6–3.0 s. The misalignment develops DURING the approach.
- **★ The gradient was never a k=6 phenomenon:** pooling every k=3
  record on disk (10 files, n=271 mgap seam instances):
  **position 1 = 10.7 %, position 2 = 26.7 % (z ≈ 3.4).** The
  position gradient has been in every gate record since the first
  hybrid — k=6 merely extended the axis (and this block's early
  cells, 2.2 %, were the lucky draw the anomaly flag suspected).
- **Upstream-composition selection ELIMINATED:** per-upstream mgap
  seam rates sit in a modest 10.8–24.6 % band (mgap-after-mgap is
  the SAFEST, curiously), and the upstream mix at position 1 vs 2 is
  nearly identical — survival selection does not build the gradient.
- **Time and position are collinear:** stages take ~4.4 s each with
  tiny within-position arrival variance (late-vs-early split within
  position: 14.9 % vs 13.0 %, no leverage). Observation cannot
  separate flight-time from position; only an intervention can.

## Campaign state — the elimination table

| suspect | verdict | by |
|---|---|---|
| entry pose (y) | eliminated | K2 intervention (manipulated, deaths unmoved) |
| rendezvous displacement | eliminated | K3 premise (flat; composite lazy-steps) |
| open bypass | eliminated | K3 audit (0.00) |
| entry conditions (misalignment, vy, approach time) | eliminated | K3 addendum (flat, non-predictive) |
| upstream-composition selection | eliminated | history dissection (mix flat) |
| **time-accumulated controller state** | **SURVIVING — collinear with position; separable only by intervention** | — |

Positive facts: deaths = failure to align by crossing (×2.52, razor
median split); outward drift ×3.4; the gradient is position/time-
indexed and pre-dates k=6 (10.7 → 26.7 % at k=3, n=271).

**Named next arm (K4, owner's call): the controller-reset
intervention.** A runner flag that resets the VelCommander/PID state
at every stage boundary (costless to deploy if it works), paired k=6
re-fly: if the position gradient flattens, the accumulator is nailed
AND remedied in the same run; if it stands, the last named suspect
falls and the gradient becomes an honest open.

## Status

- [x] k=6 priced: **0.500** (the owner's question, answered)
- [x] K1 pose GRAY → K2 intervention: pose ELIMINATED
- [x] K3: rendezvous ELIMINATED; death = crossing misalignment
      (×2.52); **the gradient generalizes to k=3 (10.7→26.7 %,
      n=271) — a standing property of every gate record**
- [x] Suspects eliminated ×5; survivor: controller-state
      accumulation (collinear, needs intervention)
- [x] K4 approved (owner:「go 修 composite builder」— note: the
      fence-re-aim variant of a "builder fix" is measured moot, K3
      premise refuted; the LIVE fix is the controller layer)

## K4 — the controller-reset intervention (pre-registered)

**The suspect's anatomy.** `VelCommander` carries two time
accumulators: the PID's integrators, and the integrated REFERENCE
position `ref` — during constant-command stretches it integrates the
commanded velocity while the true aircraft lags, re-anchoring only on
command changes. `cmd.reset(pos)` zeroes both. **One knob: reset the
commander at every stage boundary** (`ctrl_reset` flag in the
composite runner) — flight time keeps flowing, the accumulator does
not. This separates the collinear pair.

**Exam:** paired k=6 @140000, deployed lineup, `--ctrl-reset`.

**Frozen reads:**
1. **Mechanism:** deep (3–5) moving_gap seam fail ≤ 13.5 % (half the
   baseline 27 %) ⇒ the accumulator is NAILED; ≥ 20 % ⇒ the last
   named suspect FALLS and the gradient becomes an honest open;
   between ⇒ gray.
2. Remedy price: overall k=6 success ≥ 0.58 (K2's bar, for
   comparability).
3. Guard: early (1–2) + cold fails not worse by > 3 (a mid-flight
   reset can wobble — priced).
4. Declared: the full per-position, per-type table (if controller
   state also taxed deep slalom, the reset should lift it too).

**Consequences (frozen):** nailed ⇒ the remedy is FREE at deployment
(resetting a commander at boundaries costs nothing) — but adopting it
into the composite protocol re-defines the exam, an OWNER decision,
and the k=3 gate of record is untouched regardless. Falls ⇒ five
suspects dead and the survivor too; the gradient stands as a real,
unexplained property, honestly recorded.

- [x] K4 pre-registered (this section, before any number)
- [x] K4 executed → **the last suspect FALLS** (below)

## K4 results (2026-07-13 — k4_ctrlreset_n100.json)

| frozen read | value | bar | verdict |
|---|---|---|---|
| mechanism: deep mgap seam | **21.3 %** (10/47; baseline 27 %) | ≤13.5 nail / ≥20 fall | **FALLS** |
| remedy: k=6 success | 0.570 (baseline 0.500) | ≥ 0.58 | misses by one course |
| guard: early+cold fails | 13 (baseline 17) | ≤ 20 | held, improved |

The controller accumulator is NOT the gradient's cause: zeroing it at
every boundary left deep mgap seams at 21.3 % (vs 27 %, z ≈ 0.65 —
noise). Honest side-note: the reset lifted the composite +7 (0.500 →
0.570, p ≈ 0.16 one-sided — suggestive, free at deployment, but not
the mechanism and short of the remedy bar as frozen).

## Campaign close — six executions, one survivor: the gradient itself

**Eliminated by measurement or intervention:** entry pose (K2),
rendezvous displacement (K3), open bypass (K3), entry conditions
(K3 addendum), upstream-composition selection (history), controller
accumulator (K4). **Established:** k=6 flies at 0.500; every mgap
death is a failure to align by crossing (×2.52, razor median split);
outward-drifting encounters are ×3.4 deadlier; and the position
gradient predates k=6 — **10.7 % → 26.7 % across positions 1→2 in
every k=3 record on disk (n=271)**. The cause is an honest open —
recorded as such, not narrated over.

**What remains if reopened (fresh registrations):** the approach-
window trajectory analysis (the K3 npz holds full per-tick
drone-vs-gap traces — the divergence ONSET during approach is
unexamined); a positions-1-vs-2 paired intervention at k=3 (bigger
per-cell n than k=6 affords); ctrl-reset priced as a free-but-gray
remedy candidate. The k=3 gate of record was never touched by this
campaign.

## Status

- [x] k=6 priced: **0.500** (the owner's question, answered)
- [x] Mechanism arc: pose → rendezvous → controller, all eliminated
      by pre-registered probes/interventions; the mgap position
      gradient (10.7→26.7 % at k=3, n=271) stands REAL and UNSOLVED
- [x] Campaign CLOSED with the open recorded honestly

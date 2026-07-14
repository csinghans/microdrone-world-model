# slalom_depth_v1 — the deep slalom seam: mechanism before medicine

**Opened:** 2026-07-14 · **Priors:** `stack_registration_v1` (the k=6
follow-up read named this frontier: slalom is now the largest single
failure type at depth, 16/99 = 16.2 %, and the position gradient
survives), `slalom_rl_v1` (the honest double negative: the k=3 slalom
seam resists RL under both clean and entry-matched (y/vy) visitation —
open suspect (b) was "entry components beyond the measured y/vy
table"), `integration_k6_v1` (the pose-walk instrument; the y-based
death link 1.992 across all types), the house order: two medicines
failed WITHOUT a mechanism — no third medicine before one.

## P0 — free anatomy (exploratory, recorded honestly, no bar)

From existing records only, no flight:

- **Slalom has its own depth gradient** (k=6 blocks, both lineups
  agree): cold 0–6 %, seam p1–2 10–17 %, deep p3–5 **25.0 % both** —
  depth compounds within the type.
- **The predecessor signature** (pooled over 49 record files,
  n=1210 slalom seam rows — CAVEAT: mixes eras and lineups, absolute
  rates inflated by old weak lineups; the CONTRAST is the read):
  after door **22.8 %** (42/184) · after moving_gap 30.1 % · after
  gap 35.3 % · after slalom 35.4 % · after **opening_door 39.2 %**
  (100/255). door-vs-odoor z ≈ 3.6. The two k=6 blocks alone show
  the same ordering (9 % vs 27–36 %).
- Reading: WHO hands you the baton predicts whether you die — and
  the gentle hand-off (door) vs hostile hand-offs (odoor, slalom,
  gap) differ in exit dynamics. Hypothesis to test: hostile
  predecessors exit with lateral-velocity / off-axis state the y/vy
  ENTRY-MATCH sampler undersampled (it sampled marginals; tails and
  predecessor-conditioning were not in the table).

## P1 (frozen before any number): predecessor-conditioned entry states

**Instrument:** `eval_pose_walk` extended (pred column on every
entry row, per-entry rows dumped to the JSON, `--seed0`, fresh-seed
match guard; defaults bit-identical, selftest green). Two blocks,
n=100 k=6 each, DEPLOYED lineup, read-only probe:

- Block A = replay @**140000** (instrument check: outcome match vs
  `k6_newlineup_n100.json` ≥ 0.95 — read-only probes must not move
  outcomes).
- Block B = fresh @**157000** (fresh randomization of courses;
  match reported as -1 by construction).

**Hypotheses & frozen lines (slalom seam entries, both blocks
pooled):**

- **H1 (the signature is in the state):** mean |vy| at slalom-seam
  entry after {opening_door, slalom, gap} ≥ **1.3×** the mean after
  {door}, z ≥ 2 → CONFIRMED. (|y| reported alongside; vy is the
  named suspect because the entry-match sampler already covered the
  |y| marginal and the disease did not move.)
- **H2 (the state kills):** median split on entry |vy| over slalom
  seam entries → broke_here(wide) / broke_here(narrow) ≥ **2.0**
  (the pose-walk LINK_RATIO convention) → LINKED.

**Branch table (frozen):**

- H1 ✓ H2 ✓ → the entry story revives with the MISSING coordinate:
  medicine = predecessor-conditioned entry sampling (extend
  `entry_match` to sample (y, vy) jointly from hostile-predecessor
  tails) — its own registration, owner-gated (a third slalom
  medicine needs Hans's word).
- H1 ✓ H2 ✗ → the state differs but does not kill → the killer is
  in-stage (weave rhythm / phase); P2 pre-named = SeamProbe
  trajectory-divergence on slalom breaks (the K5 pattern).
- H1 ✗ → the predecessor signature is not in the recorded state at
  all (timing/perceptual) → P2 as above, plus the pooled-history
  confound audit (era mix) before believing the signature.

**Seeds:** 157000 = block B (spent here). 140000 replay = no new
randomness. Exam 110000 untouched.

## P1 verdict — H1 REFUTED, H2 REFUTED; the state vector is exonerated, the predecessor effect survives

**Instrument:** block A outcome match **1.000** vs the frozen
baseline (`k6_newlineup_n100.json`), success rate bit-equal 0.570 —
the read-only probe moved nothing. Ledger note: the probe PRINTED
0.770 because the code's `K6_RECORD` constant still points at the
old-lineup file; the frozen clause named the new record, recomputed
offline. Instrument-print bug, not a probe bug (fix owed with P2).

**The frozen lines (206 slalom seam entries pooled, blocks A+B):**

- **H1 REFUTED:** |vy| after hostile predecessors 0.089 vs after
  door 0.101 — ratio **0.88**, z −0.34. The named suspect (lateral
  velocity) is flatly exonerated; slalom-pred entries carry the
  LOWEST |vy| (0.076).
- **H2 REFUTED, inverted:** entry-|vy| median split death ratio
  **0.71** — wide-vy entries die LESS.

**What the autopsy found instead (recorded, no bar):**

- The |y| signature is real (hostile 0.180 vs door 0.088, z 5.01)
  but **|y| ordering does not match death ordering**: slalom-pred
  hands off WIDEST (0.260) and fastest (vx 0.798) yet dies little
  (0.137); odoor hands off nearly centred (0.118) at ordinary speed
  (0.529) and dies most (**0.333**).
- **The matched-band razor:** within the NARROW |y| band, odoor
  still kills 3.2× door (0.250 vs 0.077) — the predecessor effect
  survives pose matching. Pose is a marker, not the cause — the
  fourth occurrence of this lesson (k6 K2-recenter, terminal-commit
  confusions, mgap phase, now slalom-pred).
- vx, z, entry tick t: none carries it (odoor ≈ door on vx; z flat;
  odoor enters late, t 713 vs 604, but slalom-pred is equally late
  at 711 and dies little).
- **Timeout suspect executed same-turn:** all 32 slalom seam breaks
  in the two k=6 blocks are true crashes (`crash_stage` == break
  stage); no budget-exhaustion misattribution.
- Fresh confound-free replication of P0's ordering (same lineup,
  within-block): odoor 0.333 / mgap 0.163 / gap 0.139 / slalom
  0.137 / door 0.097.

**Verdict:** everything the entry-state recorder can see — y, vy,
vx, z, t — is exonerated as the carrier. The predecessor effect is
real, replicated, and lives in something the first-tick state vector
does not record. Per the frozen branch table (H1 ✗): **P2 fires =
SeamProbe trajectory-divergence on slalom stages by predecessor**
(the K5 pattern), with three named candidates the per-tick view can
discriminate: (a) the settle-brake window — does the entry brake
leave a different POST-brake state by predecessor; (b) early-frame
perceptual content — what the camera sees in the first decisions
after an odoor hand-off; (c) break localization — WHICH fence kills
(entry fence = entry story after all; mid/late = weave rhythm).
Any medicine remains owner-gated.

## Status

- [x] P0 free anatomy (exploratory, caveats recorded)
- [x] P1 pre-registered (this file, before any number) + instrument
      extended (selftest green, defaults bit-identical)
- [x] P1 blocks A+B → **H1/H2 both REFUTED; state vector exonerated;
      predecessor effect survives matching; timeout executed; P2
      (trajectory divergence) is the pre-named next probe**

## P2 (frozen before any number): per-tick divergence by predecessor

**Instrument:** SeamProbe gains y/vy per decision row (both npz
writers), `--collect-rows` routes the slalom target to collection
mode (raw rows + outcomes, no R1 verdict semantics; defaults
bit-identical, selftest green). Two blocks, k=6 n=100, DEPLOYED
lineup, same seeds as P1 (140000 / 157000 — no new randomness);
every decision on every slalom stage recorded with (dec, upstream,
exec, weave, x, plane_x, y, vy) + outcome.

**The three frozen directional calls** (slalom SEAM stages, pooled;
odoor-preceded vs door-preceded is the primary contrast):

- **(a) The settle-brake window:** the entry brake spans the first
  SETTLE_K=5 decisions. If the post-brake state (|y|, |vy| at
  dec 5–7) differs odoor-vs-door at z ≥ 2, the brake fails
  differentially → the entry story revives POST-brake.
- **(b) Decision divergence:** weave-agreement in the early window
  (dec 0–11) for odoor-preceded BROKE stages vs door-preceded
  cleared. Drop ≥ 0.10 confined to the early window → perceptual /
  history contamination at hand-off; drop only late → in-weave
  rhythm story.
- **(c) Fence localization:** death x (last recorded row) vs the
  stage's fence planes. ≥ 0.6 of odoor-preceded deaths at the FIRST
  fence → an entry-adjacent kill (whatever crosses the boundary does
  its damage immediately); majority mid/late → accumulated rhythm.

All three are reported with honest n (expect only ~10–20 odoor
deaths pooled); any medicine stays owner-gated. No new seeds.

- [x] P2 blocks A+B → **(a)/(b)/(c) all REFUTED as frozen; the true
      anatomy below; the carrier remains unidentified**

## P2 verdict — three refutations, and the disease changes shape

**Instrument lesson first (recorded):** the composite flies the FULL
course and judges crash post-hoc by minimum clearance — `crash_t`
precedes the last recorded row by 38–173 ticks. A "last row = death
point" read gives a false boundary-death story (every broke visit's
rows end at stage-frac ~0.99). All death localization below maps
`crash_t` to the nearest row. (My first pass fell into exactly this
trap and printed deaths at x≈2.95 where the world is EMPTY — the
fences sit at 0.9/1.6/2.3.)

**The frozen calls:**

- **(a) REFUTED.** Post-brake (dec 5–7) |y| identical (0.208 vs
  0.205, z 0.17); |vy| slightly LOWER after odoor (z −1.99, wrong
  direction). The settle brake equalizes the hand-off; the entry
  story stays dead post-brake.
- **(b) REFUTED (barely, and instructively).** odoor-broke early
  agreement 0.788 vs door-cleared 0.875 — drop 0.087 < 0.10. The
  honest grid: EVERY predecessor's broke visits show depressed
  agreement in BOTH windows (early 0.72–0.80, late 0.71–0.82) vs
  cleared (0.82–0.88 / 0.91–0.93). Dying pilots are off-oracle-path
  THROUGHOUT the stage — slalom death is not mgap's one-second
  flinch; it has no single commit moment.
- **(c) REFUTED.** True crash points sit ON the fences (±0.21 m of
  a plane, all 36) and are SPREAD: fence1 16 / fence2 9 / fence3 11;
  odoor-preceded 4/4/5 — not entry-adjacent (first-fence share 0.31
  < 0.6). Ordinary missed-gap weave failures.

**What P2 actually established:** the odoor multiplier is a RATE
effect, not a SHAPE effect — odoor-preceded deaths (13/39 = 0.333 vs
23/167 = 0.138 for the rest, z ≈ 3.0) look exactly like everyone
else's deaths (same fences, same y-range, same agreement
depression), there are just MORE of them. Every recorded coordinate
(entry state, post-brake state, fence choice, agreement window) is
now exonerated as the carrier. One thread flagged: the only two
blow-out crashes (|y| 0.57, 0.81 — far outside the gap zone) are
both odoor-preceded; n=2, noted not judged.

**Campaign state:** predecessor effect measured, replicated
(z ≈ 3.0), and — after two probe rounds — carried by nothing the
entry-state recorder or the per-tick trajectory records. Remaining
suspects, honestly unpriced: frame-level perceptual content at the
hand-off (what the camera actually sees, not what the state vector
says), or an untested interaction. Next moves are owner-gated:
(i) paired-geometry A/B (same slalom spawn, odoor vs door
predecessor — the intervention that would settle carrier-vs-noise),
(ii) frame-level diff probe, (iii) park as residual with the k=6
instrument watching it.

## P3 (frozen before any number): the paired-geometry A/B — owner's word「go 1」

**The intervention:** `eval_pred_ab` flies 2-stage courses
`[PRED, slalom3_fixed]` at the SAME course seed with only the
predecessor name swapped (odoor vs door). Mechanism: each stage
consumes exactly ONE course-rng draw, so the slalom stage's geometry
is bit-identical across arms — asserted per pair at runtime, and the
selftest proves the assert has teeth (a different seed fails it).
`register_course` gains `names`/`tag` overrides (defaults
bit-identical; composite selftest green). This kills every
composition/position/geometry confound at once: what survives
pairing lives in the hand-off dynamics.

**Frozen bars:** 160 pairs @**158000**, deployed HYBRID, analysis on
pairs where BOTH arms reach the slalom. **CONFIRMED** = odoor/door
slalom-death ratio ≥ 2.0 AND McNemar z ≥ 2.0 (the carrier is real
and lives in the hand-off). **REFUTED** = ratio < 1.5 (the P1/P2
multiplier was a composition confound wearing a predecessor
costume). GRAY between. Expected under H-carrier: door ~0.05–0.10,
odoor ~0.20–0.30 at seam position 1.

**Seeds:** 158000–158159 spent here. Exam 110000 untouched.

### P3 block 1 (@158000) — GRAY, pooling fires

`p3_pred_ab.json`: both-reached 151/160; slalom death **odoor
24/151 = 0.159 vs door 14/151 = 0.093** — ratio **1.71** (confirm
≥ 2.0), McNemar 21/11, z **1.77** (confirm ≥ 2.0). Direction right,
both lines short → GRAY as frozen. Borderline → pool, never replace:
block 2, 160 pairs @**159000** (spent). Note for the pooled verdict:
the observational multiplier (3.4×, P1) was measured across ALL seam
positions including deep; the paired causal read is at position 1
only — if the pooled ratio settles in [1.5, 2.0) with z ≥ 2, the
honest reading is "roughly half the observational multiplier was
confound, the remainder is a real hand-off carrier, possibly
depth-amplified".

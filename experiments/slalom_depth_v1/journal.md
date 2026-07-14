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

## Status

- [x] P0 free anatomy (exploratory, caveats recorded)
- [x] P1 pre-registered (this file, before any number) + instrument
      extended (selftest green, defaults bit-identical)
- [ ] P1 blocks A (@140000 replay) + B (@157000 fresh) → H1/H2 verdict

# slalom_rl_v1 — RL-from-success on the deployed slalom clone

**Opened:** 2026-07-14 · **Priors:** `transit_gate_v2/v3` (imitation
exhausted twice on the seam residue: the DAgger ladder closed at
17.2 % true seam, the weight knob refuted), `mgap_rl_v1` (the crown
FT recipe runs clean; the perception-tax review; guards must be
true-rate anchored), `hot_start` (its decomposition #2 NAMES
unit-level hot-entry training as the sanctioned next rung — the
forbidden zone covers course-level BC from a weak relay, not this),
`anchor_dial` (KL 1.0 → 0.1 schedule). Owner:「go slalom RL」— the
0.84 stack's other half.

## K1 (cheap knob first): solo-world crown FT

**Recipe (frozen, the mgap_rl_v1 mirror):** warm-start the DEPLOYED
R3 clone (`ppo_slalom_dagger_r3.zip` — untouched on disk, sha-pinned
in the release); AnchoredPPO on `slalom3_fixed`, unmodified success
reward, **KL 1.0 → 0.1 over 450k**, seed 0.

**The honest open question, frozen as the prediction:** the slalom
disease is SEAM-SPECIFIC (cold 3 % vs seam 17.2 % true) and solo
training resets from clean starts — PPO's exploration visits
off-centre states at mid-stage x but never at LOW stage-local x,
which is exactly where seam entries live. Transfer is
uncertain-to-weak; a clean refutation would itself close "solo RL"
for seam diseases and fire the pre-named K2.

**K2, pre-named (fires only on K1 primary refuted):** entry-matched
RL — a pre-roll entry randomizer (the episode starts with pose/
velocity sampled from the MEASURED seam-entry distributions before
control and reward hand over) — the hot_start ledger's own
decomposition #2, now with the k6 campaign's pose data to sample
from. Fresh machinery, its own frozen section when reached.

## Bars (frozen; every guard anchor cites a pooled true rate)

- **Graduation:** k=3, n=60 @ **149000**, deployed HYBRID with the
  slalom slot swapped to the student. Wins ≥ 45 (42–44 → recheck
  @153000; pooled ≥ 90/120; two blocks is the pooling convention).
- **PRIMARY: pooled slalom seam ≤ 12 %** (stack arithmetic: ≥ +2 true
  points from the true 17.2 %; no priced oracle ceiling exists for
  slalom — stated, not implied).
- **Cold guard:** pooled slalom cold fails ≤ 8 % (true ~3 % — the
  97 % cold skill must not be traded away).
- **Coupling guards (pooled-true anchors, n≈390–440 each):** door
  ≥ 0.919 (true 0.969), gap ≥ 0.912 (0.962), moving_gap ≥ 0.805
  (0.855), opening_door ≥ 0.888 (0.938).
- **Exam hygiene:** 110000 untouched. A passing arm banks for the
  0.84 stack registration; a near-miss banks as EVIDENCE (the
  mgap_rl_v1 precedent).

## K1 block 1 (@149000, n=60) — BORDERLINE, pooling fires

FT chain clean (450k, exit 0, `artifacts/ppo_slalom_rl.zip`).
`grad_n60.json`:

- Wins **46/60 = 0.767** (bar ≥45: PASS, and clears the 0.70
  deployment threshold).
- **PRIMARY slalom seam 3/20 = 15.0 %** vs frozen ≤12 % — one block,
  0.6 of one failure over the line. Down from the 17.2 % true rate
  but not through the bar. **Borderline → pool, never replace**: the
  pre-named second block fires @153000.
- Cold guard 0/9 = 0.0 % (bar ≤8 %): the 97 % cold skill was NOT
  traded away — the honest open question of the prereg (does
  solo-world FT transfer to seams without eroding cold?) is at least
  half-answered: no erosion.
- Coupling guards (single-block reads, pooled verdict pending):
  door 32/32 = 1.000 (≥0.919 ✓), gap 33/35 = 0.943 (≥0.912 ✓),
  moving_gap 34/42 = 0.8095 (≥0.805 ✓ by 0.0045 — a squeaker, watch
  the pool), opening_door 28/29 = 0.966 (≥0.888 ✓).

## K1 pooled verdict (n=120) — PRIMARY REFUTED, cleanly

Block 2 @153000 (`grad_n60_recheck.json`): wins 51/60, seam 5/20 =
25.0 %, cold 1/11. Pooled:

- **PRIMARY: seam 8/40 = 20.0 % vs frozen ≤12 % — REFUTED.** Not a
  squeaker this time: the pooled rate sits ABOVE the 17.2 % true
  baseline (within noise of it, z ≈ 0.5 — consistent with zero
  transfer, not with damage). Block 1's 15.0 % was a friendly draw;
  the pool told the truth. The a-block-is-a-draw law, again.
- Wins 97/120 = 0.808 (≥90 ✓) — identical to the mgap arm's pooled
  composite, coincidentally. Cold 1/20 = 5.0 % (≤8 % ✓). All four
  coupling guards pass pooled (door 1.000, gap 0.972, mgap 0.857,
  odoor 0.984 — the block-1 mgap squeaker resolved upward).

**Verdict:** solo-world crown FT does not transfer to seam entries —
the frozen prediction's mechanism confirmed as written: PPO from
clean resets explores off-centre states at mid-stage x, never at low
stage-local x where seam entries live. The policy got better at what
it practised (cold intact, no coupling damage) and never saw what it
needed. **"Solo RL for seam diseases" is closed.** The pre-named K2
(entry-matched RL) fires.

## Status

- [x] Pre-registration (this file, before any number)
- [x] K1: crown FT 450k → pooled n=120 → PRIMARY REFUTED (20 % vs
      ≤12 %); solo RL closed for seam diseases; guards all green
- [ ] K2 (pre-named): entry-matched RL — frozen section below when
      machinery lands

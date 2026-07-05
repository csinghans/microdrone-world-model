# sweep2_noise — the fast-solo cell's sampling distribution

## Pre-registration (2026-07-05, frozen before any batch flies)

**Why.** `guard:sweep@2.0` (one in-path solo pillar, cruise factor 2.0
= 1.6 m/s) has adjudicated three campaigns and reads like a coin:
27/22/8/17 % (moving-gap v1, n=30/60 mixed), 0 % (v2 K3, n=60), 13 %
(opening-door K3, n=60). Budget is measured non-monotone on it; mixture
shape can hold it at zero; every new timing world seems to re-tax it a
few points. Before any future campaign adjudicates this guard again, we
owe the cell an error bar. (Honest scope: the historical spread mixes
TRUE-rate differences across different policies with sampling noise —
this study isolates the sampling component for ONE fixed policy.)

**Design.** One pinned policy — opening-door K3
(`experiments/opening_door/artifacts/ppo_opening_door_K3.zip`, the
artifact whose 13-vs-10 verdict we could not settle), flying with the
G1 world model at `output/world_model.pth`. Ten batches × n=60 episodes
on DISJOINT fresh seed blocks (seed0 = 3000, 4000, …, 12000), via the
standard probe: `python -m eval.eval_policy_cells --zip <K3> --cells
experiments/metric_grounding/m2_cells.json --only sweep@1.6 --n 60
--seed0 <block>` (that spec's `sweep@1.6` IS this cell: factor 2.0
solo). ~600 episodes total, pure eval.

**Frozen interpretive rules.**

- Compute per-batch crash rates, the overall p̂, the observed
  batch-to-batch std, and the binomial-expected std √(p̂(1−p̂)/60).
  Dispersion ratio = observed/expected; significance by parametric
  bootstrap (10k simulated 10-batch sets at p̂).
- **Ratio ≈ 1 (bootstrap p > 0.05):** the cell is honest binomial —
  the historical chaos at n=30 (±11 pt CI half-width at p≈0.15) needed
  no further explanation. Deliverable: an (n, bar-margin) table from
  binomial CIs, and the recommendation that future bars on this cell
  either use n ≥ the table's row for their margin or stop re-litigating
  differences inside it.
- **Ratio > 1.3 and bootstrap p < 0.05:** overdispersed — seed blocks
  carry clustered course difficulty; bigger n alone won't stabilize
  verdicts. Deliverable: recommend a fixed stratified course panel for
  this cell instead of fresh-seed n-inflation.
- No bars, no pass/fail: this is instrument calibration. Whatever the
  numbers say gets recorded and becomes every future campaign's
  inheritance.

## Batches

(appended as they land)

## Batches (10 × n=60, disjoint blocks, policy = opening-door K3)

| seed0 | 3000 | 4000 | 5000 | 6000 | 7000 | 8000 | 9000 | 10000 | 11000 | 12000 |
|---|---|---|---|---|---|---|---|---|---|---|
| crash | .067 | **.133** | .017 | .033 | .083 | .033 | .050 | .033 | .067 | .050 |

Pooled **p̂ = 0.0567** (34/600), 95 % CI ≈ [0.038, 0.075].
Observed batch std 0.0335 vs binomial-expected 0.0298 →
**dispersion ratio 1.12, bootstrap p = 0.251.**

## Verdict (per the frozen rules): the cell is honest binomial

No seed-block clustering. The cell's historical chaos needed no exotic
explanation — n=30 carries a ±8.3 pt CI half-width at these rates and
n=60 carries ±5.9 pt, so readings scattered across 0-27 % from
policies whose true rates differ by a few points are exactly what
honest sampling looks like.

**The sting in the tail.** This study's block 4000 — the single worst
of ten (13.3 %) — is the very block the opening-door campaign's
recheck used (seed0+1000 = 4000), and the campaign's recorded 13 % is
consistent with block 3000 reading ~6.7 % first (a PASS), the ±0.08
borderline rule firing, and the *replacement-style* recheck re-rolling
the die into the one bad block. On a binomial cell, a recheck that
REPLACES the original n=60 with a fresh n=60 does not firm the verdict
up — it tosses the coin again. (Pooled, the two blocks read
12/120 = exactly 0.100 ≤ the bar.)

## The inheritance (what every future campaign gets from this hour)

1. **CI table for this cell** (binomial, at p ≈ 0.06):
   n=30 → ±8.3 pt · n=60 → ±5.9 pt · n=120 → ±4.1 pt ·
   n=200 → ±3.2 pt · n=300 → ±2.6 pt.
   Differences inside these widths are not findings. Bars adjudicated
   on this cell should be judged at pooled n ≥ 200, or carry an
   explicit margin ≥ the table's row.
2. **Protocol recommendation (prospective, needs the maintainer's
   sign-off since it changes gate semantics):** the borderline recheck
   should **pool** the original and fresh blocks (judge at combined n),
   never replace — replacement re-rolls; pooling accumulates. Applies
   to every cell, not just this one.
3. **The opening-door K3 annotation:** the campaign verdict stands as
   gated (bars-as-written at their pre-registered n — honest negatives
   are not retried into passing). But this study's 600-episode
   measurement of the same artifact on the same cell — 5.7 %
   [3.8, 7.5] vs the ≤10 % bar — is strictly stronger evidence, and a
   fresh pre-registered promotion gate under the inheritance rule
   (pooled n ≥ 200) is the legitimate path to settling that title.

Cost of this study: ~600 eval episodes, zero training, one hour.

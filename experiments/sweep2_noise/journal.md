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

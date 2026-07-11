# zoo_transfer_v1 — "both high": swap-invariance without rebalancing

**Opened:** 2026-07-12 · **Owner:** Hans · **Source:** docs/REVIEW-2026-07.md
(K-series); `experiments/slalom_stopobserve_v1`'s named next.

## The question

Two-WM encoder data-augmentation is the measured strongest lever for
surviving a champion→unified encoder swap on the longest chain
(slalom: unified 0 %→75 %), but at 50/50 and 500k it REBALANCES rather
than lifting both (champion 80 %→35 %). Can a champion-weighted mix buy
BOTH columns — the insurance that would make any future WM promotion
(Option B) affordable?

Reference points (measured, `slalom_stopobserve_v1`): continuous
champion 80/0 (champion-WM / unified-WM); 50/50 aug @500k → 35/75.

## K1 (this sitting, one knob)

**The knob:** the per-episode probability of encoding with the AUG
(unified) WM drops 0.50 → **0.34** (champion-weighted 66/34). Everything
else identical to the measured two-WM run: warm-start from the slalom
champion, 500k steps, stop_hover=0, same env recipe, seed 0. Mechanism:
the 50/50 run showed the policy drifting to the aug latent's basin;
weighting episodes toward the PRIMARY latent should hold the champion
column while the 1-in-3 aug episodes keep buying swap tolerance.

**Machinery note:** `WMPolicyEnv` gains `aug_p` (default 0.5 —
bit-identical to every existing recipe; the selftest re-run guards it).

**Bars (frozen, the review's):** raw 2×2 continuous column at n=20,
seeds 22000+ — **champion-WM ≥ 0.70 AND unified-WM ≥ 0.50.**
- PASS both → K2 released: budget 500k→1.0M at this ratio (bars
  ≥ 0.75 / ≥ 0.70).
- Champion holds but unified < 0.50 → the ratio traded too far back;
  record, and K2 may probe 0.42 as ONE further arm (pre-named here, not
  fished).
- Champion < 0.70 → champion-weighting does NOT protect the primary
  column at 500k; the rebalance is not a mixing artifact — record as
  the honest negative and Option B's price stays "a re-distill per
  encoder".

## Status

- [x] Pre-registration committed (this file, before any number)
- [ ] `aug_p` machinery (default-identical) + selftest
- [ ] K1: train 500k @ aug_p 0.34 → 2×2 read → verdict

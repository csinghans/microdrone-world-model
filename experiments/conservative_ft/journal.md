# conservative-ft — can constrained fine-tuning buy repair without corrosion?

## Pre-registration (2026-07-06, before any number exists)

The four erasure datapoints this campaign designs against (all gated
today): FT repairs its own diet (surpass +29.5), corrodes outside it
(bcft-K1 sweep 98 % crash), corrodes RL-unlearnable skills inside it
(bcft-K0 chain 93→0 with slalom IN the diet), and a
strong-but-imperfect prior can bias it below from-scratch
(dodge-distill K1). Headline mechanism: KL-anchoring to the frozen
prior. **But the cheapest axis gets priced first** (the
feasibility-first discipline): if repair happens EARLY in fine-tuning
and corrosion late, a short dose wins without any new machinery.

**Fixed throughout:** prior = the gated BC2 generalist; diet = bcft-K0's
exact five-world uniform recipe; SB3 defaults; judge = the
corridor-slalom-v2 predicates on the STANDARD exam seeds — every
number directly comparable to the bcft table (chain 93.3→0, gap
70→96.7, mgap 43→90 at 450k).

**K0 — the dose curve (measurement knob, not promotion).** Three
doses, one variable: steps ∈ {25k, 75k, 225k} (1/18, 1/6, 1/2 of the
erasing dose). Each measured on three INDEX cells (n=30, standard
seeds): slalom3@1.0 (corrosion axis), gap@1.0 and mgap@1.0 (repair
axes). Frozen graduation rule: a dose qualifies iff chain ≥ 0.70 AND
gap ≥ 0.75 AND mgap ≥ 0.70; if several qualify, the LARGEST qualifying
dose graduates (most repair, still safe).

**K1 — the graduation shot:** the qualifying dose re-examined on the
FULL slalom-v2 gate (all cells + guards, runner semantics). Full pass
= the catalog's first distilled champion, tenth sitting.

**K2 — the KL anchor (built ONLY if no dose qualifies):** PPO with an
added kl_coef · KL(π_prior ‖ π_θ) penalty on rollout states, frozen
prior copy, kl_coef = 1.0, 450k, same recipe → same graduation rule.

**Refuted (campaign):** no dose qualifies AND the KL anchor at 1.0
fails the same rule — conservatism at these altitudes cannot decouple
repair from corrosion; the distilled-champion road then requires
architecture (per-world dispatch / ensembles), recorded and closed.

Cost: K0 = 325k total training (~under one bcft dose) + 9 index
evals; K1 one full exam; K2 only on failure.

## K0 — the dose curve: there is no window (2026-07-06)

| dose | chain (≥0.70) | gap (≥0.75) | mgap (≥0.70) |
|---|---|---|---|
| 25k | **0.00** | 0.90 ✓ | 0.83 ✓ |
| 75k | 0.13 | 0.97 ✓ | 0.93 ✓ |
| 225k | 0.20 | 0.97 ✓ | 0.87 ✓ |
| 450k (bcft K0) | 0.00 | 0.97 | 0.90 |

No dose qualifies — and the failure is maximally informative:
**corrosion is FASTER than repair.** The chain is dead inside 25k
steps (~280 episodes) while the repair is already essentially complete
at that same dose. Early stopping cannot help when the thing you want
to keep is the first thing to go: re-optimization toward RL's
attractor begins immediately, not late. (The 0→0.13→0.20 chain drift
upward across doses sits inside n=30 noise; nowhere near the bar.)

Per the frozen rule, **K2 fires: the KL anchor gets built** —
kl_coef · KL(π_prior ‖ π_θ) on rollout states, frozen prior copy,
kl_coef = 1.0 (one value, no sweep), 450k, same recipe, same index
cells, same graduation rule.

**K2 machinery shipped (2026-07-06):** `AnchoredPPO` in
`scripts/distill.py` — SB3 2.9.0's PPO.train vendored with exactly one
addition (kl_coef · KL(π_prior ‖ π_θ) per minibatch, frozen prior
copy), version-pinned with a loud-fail assert. Wiring smoke on the
record: kl_coef=1e6 pins the policy (max action-prob shift 0.0145
after 768 steps). K2 = BC2 + 450k anchored at kl_coef=1.0 (one value,
no sweep), same recipe, same index cells, same graduation rule.

## K2 — the anchor at 1.0: decoupling is REAL, the budget is not enough (2026-07-06)

| cell | BC2 (prior) | K2 anchored FT | need |
|---|---|---|---|
| slalom3 chain | 93.3 % | **93.3 %** (chain 2.87, frac 0.98) | ≥ 0.70 ✓ |
| gap | 70 % | **80 %** | ≥ 0.75 ✓ |
| mgap | 43 % | 43.3 % | ≥ 0.70 ✗ |

## Campaign verdict: the frozen rule fires REFUTED — with the interpretation amended by the data

No configuration qualified (doses: corrosion outruns repair; anchor at
1.0: mgap unrepaired), so the graduation shot never fires and the
crown stays untaken — **but the refuted clause's mechanism sentence
("conservatism cannot decouple repair from corrosion") is contradicted
by K2's own row**: the anchor held the chain at zero corrosion
(93.3 %, chain_break 2.87 — byte-level BC2 behavior) WHILE repairing
gap past its bar (+10). Decoupling is real and measured. What actually
binds: **mgap's repair lies outside the KL-ball that kl_coef = 1.0
permits** — its closed-loop drift (the campaign-long deep sore) needs
more policy movement than the anchor allows, and the dose curve shows
unconstrained movement destroys the chain first. One value was
pre-registered; dialing the coefficient now would be fishing. The
honest close: conservatism works, its budget is a dial, and the dial
is a NEW campaign (or the architecture road: per-world dispatch /
ensembles — both in the ledger).

**Standing export:** the anchored zip
(`artifacts/ppo_anchor_k1.zip`) strictly dominates BC2 on the measured
axes (93.3 / 80 / 43.3 vs 93.3 / 70 / 43) — the best five-world
single-policy artifact in the catalog (cluttered/sweep unmeasured
here; BC2 read 93/93). AnchoredPPO stays as standing machinery,
version-pinned.

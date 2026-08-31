# temporal_probe_v1 — pricing "the previous glance" on a frozen latent

Opened 2026-08-31, from perception_v3's final verdict (`22ddecf`): the
pincer's residue has a name — **the moving/temporal hypothesis**. Every
96-res arm sits at moving AUC ~0.89 and over-warns in open space; "a
single-frame latent cannot rank what it cannot see move." This probe prices
that information claim at the cheapest honest level — probe heads on the
FROZEN `wm_96d128` latent — before any WM retrain is proposed.

## The question

Does adding latent-level motion (a two-frame difference, or a GRU over the
last 8 frames) to the frozen apex latent recover moving-world ranking that
the single-frame head cannot reach? And if yes, which FORM — diff or
recurrence — so the next campaign flies one arm, not two.

## Re-opening context (three prior negatives, each distinguished)

1. **oracle_memory_v1** (dense, speed 1.5, closed-loop; Δcrash −0.035 vs
   bar −0.050): priced *remembered position of an absent static object* on
   a frozen policy. This probe prices *velocity of a mover currently in
   view* (`sim/scenarios.py`: a MovingCrosser is visually identical to a
   static pillar — only motion betrays it), offline, on the model axis.
   Different quantity, different world, different level, different cost.
   That journal's own reservation applies: "a temporal WM might still buy
   detection elsewhere, but not THIS wall."
2. **v0.2's model-side GRU negative** (dense 0.82→0.74, moving 0.88→0.84;
   re-opening rule at `docs/REVIEW-2026-07.md:165-173`): that judge was
   single-seed model-axis AUC, later measured to spread ~0.5 on dense.
   Here: the encoder is FIXED (zero training variance on the latent), and
   every arm reports a 3-head-seed mean with spread.
3. **perception_v3's stability gate** ("the one-sided variance guard must
   be fixed before any long-memory recipe"): a probe head on a frozen
   encoder never runs the guard — no EMA, no encoder gradients — so this
   campaign is admissible regardless of stability_v1's verdict. The gate
   binds the *next* step (training a temporal WM), for which stability_v1
   runs concurrently.

## Protocol (frozen before any number)

Instrument: `eval.eval_temporal_probe` (committed `ae4d0ca`, selftest
green). Frozen latent: `experiments/perception_v2/artifacts/wm_96d128.pth`
(the offline dense apex: dense 0.9965, veer 1.00/1.00, moving 0.8891).

- Heads train on `output/combined_96.npz` transit worlds; score on
  `output/transit_eval_holdout_96.npz`'s val split at the checkpoint's own
  training seed — the exact sample set behind the moving 0.8891 row.
  Label = collision-within-32 of the flown future (`c_h[:, -1, 0]`).
- Arms: **A0** frozen collision heads (instrument validity); **A** fresh
  head on z_hat32 (head-retrain control — gains must beat A, not A0);
  **B** head on concat[z_hat32, z_t − z_{t−4}] (stride 4 = the planner's
  DECIDE_EVERY; stride-1 mover displacement at 96 px is 0.1–0.8 px,
  sub-pixel — priced out by construction); **C** head on
  concat[z_hat32, GRU_8(z_{t−7..t})] (~167 ms window, GRU + head trained
  jointly, encoder frozen).
- 3 head seeds (0, 1, 2); every read is the mean, spread reported.
- Command of record:
  `python -m eval.eval_temporal_probe --ckpt
  experiments/perception_v2/artifacts/wm_96d128.pth --seeds 0 1 2 --out
  experiments/temporal_probe_v1/probe_results.json`

## Pre-registered bars

| read | consequence |
|---|---|
| A0 reproduces eval_wm_checkpoint's moving row (0.8891) exactly-ish, and A within ±0.02 of A0 on moving | instrument valid; anything else = STOP, fix the harness (rule 6), no science read |
| B or C moving (3-seed mean) ≥ A + 0.03, with dense AND classic ≥ A − 0.02 | **GO** — the polarity names the next campaign: `temporal_v1_diff` (two-frame input) or `temporal_v1_gru` (model-side GRU under the closed guard); both passing → the cheaper B wins the tie |
| neither arm reaches A + 0.03 | **NO-GO** — the moving residue is not recoverable from latent-level motion at 96 px: the temporal hypothesis is refuted AT THIS LEVEL; name what remains (pixel-level motion input, higher frame rate) |
| only C gains, B flat | memory beyond one glance is what matters → the gru arm carries the program |
| gains on moving but veer/classic collapse in the follow-up | not this probe's call — the follow-up campaign inherits the FULL original bar set |

Stated out loud, before any number:

- A + 0.03 ≈ 0.919 still sits BELOW the frozen G4 bar (0.9357). This probe
  arbitrates direction and adopts nothing — general_wm_v2's law holds
  (offline instruments predict, never certify; no closed-loop harness
  exists at 96 px).
- Probe-head budget deltas are reported (B ≈ +8 KB, C ≈ +107 KB int8-ish)
  but do not gate — deployment pricing belongs to the follow-up.
- Honest-negative clause: a NO-GO here is a finding (it would kill the
  cheapest reading of "the previous glance" and push the hypothesis to the
  pixel level), recorded, not retried.
- Head `.pt` artifacts stay journal-side and UNLOCKED (the
  `target_head_{alt,alt_os}` precedent).

## Results

(land below when the run completes)

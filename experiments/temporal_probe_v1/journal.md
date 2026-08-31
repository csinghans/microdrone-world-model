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

---

## Mid-campaign record — 2026-08-31: the validity bar trips (as designed); the fit was under-powered

First run of record (log `output/tp1_run.log`): A0 reproduces the
eval_wm_checkpoint row EXACTLY (all 0.8807 / classic 0.7882 / dense 0.9965
/ moving 0.8891) — the scoring pipeline is right. But A (the fresh-head
control) reads moving 0.8615, which is 0.0276 from A0 — outside the
registered ±0.02 — with dense 0.7494 at a 0.21 head-seed spread. Per the
frozen bar: STOP, no science read.

Root cause (rule 6, harness): `_fit` trained ~96 minibatch steps at
lr 1e-3 — far below the repo's reference frozen-latent head recipe
(`search/target_detector.py`: 600 FULL-batch steps at lr 0.02). The
control head is under-trained, so every arm's read is noise-limited.
Fix: `_fit` moves to the reference power (600 full-batch steps, lr 0.02,
wd 1e-3, unchanged); same registration, same arms, same bars, rerun.
(The first run's numbers are recorded above for the log's sake and carry
no verdict weight.)

---

## Final verdict — 2026-08-31: NO-GO at the latent level — the previous glance is not IN the latent

Rerun at reference fit power (log `output/tp1_run2.log`,
`probe_results.json`; 3 head seeds, mean with spread):

| arm | all | classic | dense | moving | +KB int8 | vs bars |
|---|---|---|---|---|---|---|
| A0 frozen heads | 0.8807 | 0.7882 | 0.9965 | 0.8891 | 0 | reproduces wmck digit-for-digit |
| A single-frame head | 0.8916 | 0.8014 | 0.8284 (spread 0.22) | 0.8986 (0.015) | +4.1 | validity: |A−A0| moving 0.0095 <= 0.02 — **instrument VALID** |
| B diff (z_t − z_{t−4}) | 0.8739 | 0.8258 | 0.9266 | 0.8810 (0.057) | +8.1 | moving −0.018 vs A — FAIL |
| C gru (K=8, ~167 ms) | 0.8941 | 0.8248 | 0.9309 | 0.9015 (0.007) | +104.8 | moving +0.003 vs A — FAIL (needed +0.03) |

**Neither temporal arm reaches A + 0.03 -> NO-GO, per the frozen bar: the
moving residue is NOT recoverable from latent-level motion at 96 px.**

Mechanism reading (recorded, two-tier language): a single-frame encoder
trained with single-frame objectives has already destroyed the motion —
Δz between two encodings of a sub-pixel-shifted scene is encoder noise
(B's moving spread 0.057 is the widest in the table), and the GRU's small,
BROAD gains (dense +0.10, classic +0.02 over A) are it stabilizing a weak
fresh head, not reading velocity. The frozen cheads' dense 0.9965 towering
over every fresh head's dense (0.83–0.93, spreads to 0.22) is the same
lesson from the head side: dense discrimination lives in deep training,
not in the probe.

**What survives, named:** the temporal hypothesis moves DOWN a level — to
the pixels. A two-frame INPUT (e.g. 6-channel stacked frames, or a frame
+ frame-difference channel) lets the ENCODER see motion before the latent
bottleneck discards it. That is an 80-epoch recipe knob and is therefore
NOT gated by the stability arc's open 160-epoch problem; it IS subject to
the draw-noise discipline stability_v2 measured (single-draw spread ~0.02
dense — effects must be large or arms must be >=3 draws). Candidate name:
`temporal_v1_pixel`. The higher-frame-rate axis (finer stride at the
sensor) stays parked behind it.

Probe heads stay journal-side, unlocked; nothing is adopted (the
instruments predict, never certify).

## Status

- [x] Pre-registered before any number (9be8a7b)
- [x] Validity bar tripped once, harness fixed at reference power (rule 6, bf40fef)
- [x] Instrument valid on rerun (A0 exact; |A − A0| moving 0.0095)
- [x] NO-GO recorded — latent-level motion refuted; pixel-level named
- [ ] `temporal_v1_pixel` — awaits its own pre-registration

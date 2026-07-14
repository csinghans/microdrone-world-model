# dense_recal_v1 — the dense frontier: does a deployable context signal unlock conditional recalibration?

**Opened:** 2026-07-14 · **Owner sanction:**「go next」on the roadmap's
deepest open. · **Priors:** `head_calibration` C0 (CLOSED 2026-07-05:
global temperature REFUTED — every fitted T < 1 while the dense slice
over-reports; "the miscalibration lives in the conditioning, not the
scale"; verdict said conditional recalibration "needs a world label
the flying drone doesn't have"), `grounding_mechanism` D0 (the
conditional warn inflation finding), ROADMAP #2/#3 (the dense 17–27 %
frontier; the model-axis instrument lesson — single-seed val spreads
~0.5 on the dense slice, so this campaign judges on CALIBRATION
metrics over big stratified slices, never single-seed val AUC).

**The wedge:** C0's blocking objection has aged. Since 2026-07-13 the
sensor ring is a priced, deployable part of the stack (beam_latency_v1:
σ < 5 cm, missed-returns < 5 %, latency ≲ 500 ms — real multirangers
sit an order inside the pocket). A beams8-style reading is a CONTEXT
SIGNAL the flying drone actually has — no world label needed. If local
clutter (i) separates the dense regime, (ii) orders the conditional
inflation monotonically, and (iii) supports a per-bin temperature that
moves C0's own metric the way C0 could not, then "retraining-class" is
overturned and the frontier gets a cheap, deployable knob candidate.

## K0 (frozen before any number): the clutter-context instrument probe

**No flights.** Corpus: fresh `datasets.generate_rollouts.gen(48, 120,
seed=160, worlds=("classic","dense","moving"))` (pos + pillars are
stored per rollout — the signal is computable offline). Model: the
deployed champion (`output/world_model.pth`, the artifacts-lock
binding). All reads on the seed-0 val split (the training convention),
FOV-masked, k=32 ring probabilities via the `eval_head_calibration`
surface — C0's own instrument.

**The signal (frozen):** per frame, 8 compass rays from the drone's
(x, y) against the rollout's pillar cylinders (radius = the skill
PILLAR_R, max range 3.0 m); **clutter = count of rays returning
< 1.0 m**. Deployability twin: the multiranger. Bins: terciles of the
TRAIN split's clutter distribution (frozen from train, applied to val).

**Hypotheses & bars:**

- **K0a (separation):** AUC(clutter separates dense frames from
  classic+moving) ≥ **0.80**. Below → the signal cannot stand in for
  the world label; campaign closes as an honest negative (C0's
  verdict stands, strengthened).
- **K0b (the inflation is ordered by the signal):** signed warn gap
  (mean p − empirical rate, masked, k=32) rises monotonically across
  clutter bins, with **high-bin gap − low-bin gap ≥ +0.05**. Below →
  the conditioning C0 named is not (mostly) local clutter; recorded,
  campaign closes.
- **K0c (the dry-run fix):** fit one temperature per (ring, clutter
  bin) by masked BCE on the TRAIN split (1-D grid 0.25–4.0, step
  0.05 — deterministic, no learning); apply to val. Bars = C0's own,
  verbatim: dense warn ECE ≤ **0.09**; no world-slice ECE worsens
  > 0.01; per-world AUC drop ≤ 0.005 (MEASURED — binned T is not
  AUC-invariant across bins, unlike C0's global scalar).

**Branch table (frozen):** all three green → C0's "retraining-class"
verdict is OVERTURNED by a deployable signal; what it buys IN FLIGHT
is a separate question for a separate registration (the M2 lesson:
detection wins don't automatically fly; the policy consumes head
features, so any in-flight cash-out is policy-side work) — that step
is owner-gated. Any red → the frontier keeps its crown; the negative
is priced and recorded, and the remaining routes stay representation /
memory at scale.

**Seeds:** corpus gen seed 160 (its own namespace); no exam seeds
touched.

## K0 verdict — all three FAIL as frozen; campaign CLOSED, and the sign flips

**Instrument repair (documented):** the frozen tercile spec
degenerated (the clutter count is mostly 0 — val histogram
684/277/138/101 for 0/1/2/≥3), emptying bin 0 to NaN. Repaired to
fixed integer bins {0}/{1–2}/{≥3} — deterministic, no fitting;
verdict semantics unchanged. A stale-variable crash at the JSON
writer cost one rerun (seeded corpus, bit-reproducible). Per-frame
arrays now persist (`k0_results_repaired_frames.npz`) so every
future recut is free.

- **K0a FAIL (clean):** clutter → dense separation AUC **0.736** vs
  the frozen 0.80. Informative, not label-grade.
- **K0b FAIL — and ANTI-monotone:** signed warn gap by clutter bin =
  **+0.121 / +0.074 / −0.034**. The over-report is largest in OPEN
  space and flips to UNDER-report in high clutter. The conditioning
  C0 named is real but points the OPPOSITE way from the hypothesis.
- **K0c FAIL (the C0 shape again):** dense warn ECE improves
  slightly (0.0414 → 0.0390 — note it was already under C0's 0.09
  target) but the guards trip hard: worst slice worsening +0.0254,
  worst AUC drop +0.0260 (crit ring). A clutter-binned temperature
  buys nothing and breaks ranking.

**Premise update (the campaign's most valuable output):** C0's big
dense warn inflation (ECE 0.1225) was the GROUNDED arm's disease.
The deployed CHAMPION's dense warn is mildly calibrated (0.041);
its crit ring is worse (0.130). The dense 17–27 % crash floor is
NOT primarily a warn-calibration problem on the deployed stack.

**The mechanism note this leaves behind (unpriced, recorded):** the
sign flip — over-warn where the world is empty, under-warn where it
is thickest — is exactly what an information limit predicts: in
clutter, the killer object is often outside or sliding out of the
FOV (the known dense death signature: 13/14 side objects leaving
FOV), so the visual heads go quiet precisely where geometric clutter
peaks. That is another face of the perception tax, not a
recalibration knob: no output-side transform fixes an input that
does not contain the threat. The honest remaining routes for the
dense frontier stay what the ROADMAP says — representation or
memory at scale (the temporal_wm oracle-memory probe is the named
next rung, quarterly-gated).

**Campaign CLOSED (2026-07-14). Cost: two offline corpus passes,
zero flights. C0's verdict stands, now with the champion's own
numbers under it and the conditioning's direction measured.**

## Status

- [x] Pre-registration (this file, before any number)
- [x] K0: corpus + clutter instrument → **K0a/K0b/K0c all FAIL as
      frozen; anti-monotone sign flip measured; premise updated
      (champion warn ≈ calibrated on dense); campaign CLOSED**

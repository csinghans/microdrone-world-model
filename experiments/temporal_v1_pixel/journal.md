# temporal_v1_pixel — the previous glance, fed to the eyes instead of read from the latent

Opened 2026-08-31, from temporal_probe_v1's NO-GO (`4267fd1`): latent-level
motion is refuted — a single-frame encoder destroys motion before any probe
can read it (Δz below the control, GRU +0.003 vs a +0.03 bar). The
surviving form moves DOWN a level: give the ENCODER two frames, so motion
exists before the latent bottleneck. This is an 80-epoch recipe knob — NOT
gated by the stability arc's open 160-epoch problem — but it IS subject to
the arc's measured instrument law: single-draw 96-res reads spread ~0.02
(dense) between fair draws, so this campaign is the tier's first
**pre-registered ≥3-draw** model-axis gate.

## The question

Does stacking the frame from 4 control steps earlier (~83 ms, the
planner's DECIDE_EVERY) as 3 extra input channels buy the moving world
what fifteen single-frame arms never reached — without paying the dense
apex away?

## Prior negatives, distinguished

- `temporal_probe_v1`: read motion FROM the frozen latent — dead. Here the
  encoder sees both frames BEFORE the bottleneck; nothing is frozen.
- v0.2 model-side GRU / perception_v3 e160: recurrence + long training —
  different axis (memory/duration); this is a feed-forward input knob at
  the standard 80 epochs.
- oracle_memory_v1: closed-loop memory of absent objects — different
  quantity, level, world.

## Pre-registration (committed before any number)

### The knob (single)

`--two-frame` (`in_frames=2, frame_stride=4`): the encoder input becomes
6 channels — frame_t stacked with frame_{t-4}, clamped at the rollout
start; the EMA target sees the same format at the target step (the input
FORMAT changes; the JEPA objective, diet, seed schedule, D=128, strips 4,
80 epochs, band-[1,8] guard all stay the frozen 96d128 recipe).
Harness threaded end-to-end this session: `Encoder(in_ch)`, training
frames path + veer probe, meta (`in_frames`/`frame_stride`) + `load_model`
reconstruction, `eval_wm_checkpoint` (channel count inferred from the
encoder itself), `onboard_budget` (bills the 6-channel first conv).

### Arms — 3 draws per recipe (the instrument law applied)

Different seeds are the honest draw mechanism (ROADMAP instrument rule):

- **2f arm**: seeds {0, 1, 2} ->
  `experiments/temporal_v1_pixel/artifacts/wm_96d128_2f_s{0,1,2}.pth`
- **1f control**: seeds {1, 2} trained fresh + the seed-0 apex row of
  record (its tensor-level identity to a same-code rerun was verified in
  stability_v2/C0, so re-training seed 0 would be a waste) ->
  `.../wm_96d128_1f_s{1,2}.pth`

Every arm: `python -m scripts.train --epochs 80 --batch 64 --seed <s>
--latent-d 128 [--two-frame] --data output/combined_96.npz --out <path>`.
Graded by `eval_wm_checkpoint` on `output/transit_eval_holdout_96.npz`
(the split follows each checkpoint's own seed — the leakage rule) and
`eval_latency_budget --ckpt --img-res 96`.

### Bars (frozen; all reads are 3-seed MEANS, spreads reported)

- **Primary**: mean moving(2f) >= mean moving(1f) + 0.03
- Guards (means): dense(2f) >= dense(1f) − 0.02;
  classic(2f) >= classic(1f) − 0.02; veer val mean(2f) >= 0.90
- Budget: <= 512 KB and est ms recorded (the 6-channel first conv adds
  MACs at full 96×96 resolution — the estimate must stay <= 83 ms/decision
  at 12 Hz; the honest number is whatever `onboard_budget` prints)
- Stability sanity (recorded): z-std max <= 8.5 per draw (the shipped
  band's own instrument)

### GO / NO-GO (frozen)

- Primary + guards pass -> **GO**: temporal input works at the pixel
  level; the follow-up (its own registration) prices the full original
  bar set (G1-G4, saturation, gap3) and the deployment story. Nothing is
  adopted here (no closed-loop harness exists at 96 px; instruments
  predict, never certify).
- Primary fails on the mean -> **NO-GO**: pixel-level two-frame motion at
  ~83 ms does not buy moving ranking at this diet — the temporal
  hypothesis is then dead at BOTH levels for this generation, and the
  residue escalates to sensor/frame-rate/dataset axes. Honest negative,
  recorded, not retried.
- Primary passes, a guard breaks -> **NO-GO with a named trade** — the
  moving/dense rotation seen throughout the perception tier; record the
  landscape.
- Per-seed disagreement (moving spread(2f) > 0.05): flagged next to the
  verdict — the mean still decides, but the claim carries the spread.

### Honesty clauses

- 1f seed-0 row = the apex row of record (0.8807/0.7882/0.9965/0.8891,
  veer 1.00/1.00) — not retrained, per the C0 bit-identity result.
- The 2f arms train under the shipped [1,8] guard; the 1f fresh seeds do
  too — every new number in this campaign shares one code path (the op
  graph is part of recipe identity; stability_v2's law).
- Six trains would cost ~72 min; five are flown (see above). No other
  reuse.
- Deviations, if any, get their own registered record before flying.

---

(verdicts land below when the queue completes)

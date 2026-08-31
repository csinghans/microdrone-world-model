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

---

## Final verdict — 2026-08-31: NO-GO — and the 3-draw design turns the bar itself into the finding

Queue clean (logs `output/tvp_*`; sha brackets green; all five arms flew).

| arm (seed) | classic | dense | moving | veer val/widened |
|---|---|---|---|---|
| 2f s0 | 0.8075 | 0.9758 | 0.8727 | 1.000 / 0.972 |
| 2f s1 | 0.8650 | 0.9490 | 0.7466 | **0.267** / 0.706 |
| 2f s2 | 0.7155 | 0.9842 | 0.7504 | 1.000 / 1.000 |
| **2f mean (spread)** | 0.7960 (0.150) | **0.9697 (0.035)** | **0.7899 (0.126)** | 0.756 |
| 1f s0 = apex (record) | 0.7882 | 0.9965 | 0.8891 | 1.000 / 1.000 |
| 1f s1 | 0.7397 | 0.7689 | 0.7459 | 1.000 / 0.958 |
| 1f s2 | 0.8228 | 0.9340 | 0.8143 | 1.000 / 1.000 |
| **1f mean (spread)** | 0.7836 (0.083) | 0.8998 (**0.228**) | 0.8164 (**0.143**) | 1.000 |

- **Primary FAIL**: mean moving(2f) 0.7899 vs bar 0.8464 (1f mean + 0.03) —
  the two-frame arm sits 0.027 BELOW the single-frame mean, well inside
  the measured spread. **Veer guard FAIL** too (2f s1 collapses to 0.267;
  the per-seed-disagreement clause fires: moving spread 0.126 > 0.05).
- Budget, honest: 319.3 KB / 11.4 M MACs / est 23 ms per decision
  (<= 512 KB, <= 83 ms) — affordability was never the blocker.
- z-std sane in every draw (max <= 3.28; the [1,8] band never bound).

**temporal_v1_pixel closes NO-GO: the temporal hypothesis is now dead at
BOTH levels for this generation** — read from the latent
(temporal_probe_v1) and fed to the eyes (here). At ~83 ms of baseline,
96 px, and this diet, a second glance does not buy the moving world.

**The deeper finding is instrumental, and it re-frames the tier.** The
first honest 3-draw measurement of the frozen recipe shows per-world
draw spreads of 0.14 (moving) and 0.23 (dense) — the **apex row of
record (seed 0) is the TOP of its own draw distribution on both dense
and moving**, i.e. partly a lucky draw. A +0.03 question is therefore
UNANSWERABLE by offline per-world AUC at this diet size (160/40
rollouts, 1137 val samples) at any affordable draw count. The
perception tier's LARGE effects survive this re-read (+0.077 pixels,
-0.37 strips, -0.19 at 128 res — all outside even this spread); its
fine-grained residue claims (moving "stuck at ~0.89", classic "by
0.013") do not — "~0.89" was one draw of a 0.75-0.89 distribution.

Post-hoc observation (recorded, no claim): the 2f arms' dense FLOOR is
much higher than 1f's (min 0.949 vs 0.769; spread 0.035 vs 0.228) — the
motion channel may act as a training regularizer for dense ranking.
If anyone returns here, that is the registered-question-shaped thing to
chase — with a diet or gate that can actually resolve it.

### What remains for "time", named
- Offline, this diet: nothing — the axis is measured unanswerable at
  the effect sizes on the table.
- The honest instruments left: a BIGGER holdout/diet (more rollouts =
  tighter means; data is the binding resource, per representation_v1),
  or the closed-loop flight gate (which is what "the instruments
  predict, never certify" always pointed at — but no 96-px flight
  harness exists yet; building one is its own campaign).
- Sensor axes (frame rate, stride) inherit the same instrument problem
  and stay parked behind it.

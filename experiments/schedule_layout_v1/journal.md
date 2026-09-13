# schedule_layout_v1 — registered generator-layout comparison

## Registration — 2026-09-13, before generation or training

Question: does crossing passive/intervention roles within each transit world
improve moving-world prediction without degrading the other worlds? The
machine-readable recipe and bars are in [registration.json](registration.json).
The runner freezes source hashes, environment versions and protected artifact
hashes before its first stage. This is a new 64-pixel study, not a rerun or
replacement of the historical 96-pixel NO-GOs.

The only training recipe knob is `schedule_layout`: `legacy` versus
`world_balanced`. Each uses 96 transit + 96 indoor rollouts, length 120, the
existing unified generator's default-sized diet. Generate the indoor corpus
once and reuse exactly the same arrays in both arms. Transit world weights,
generation seed, architecture, loss, optimizer and 80-epoch budget stay fixed.
Three training seeds (0, 1, 2) give six fits; run all six in the registered
alternating order, regardless of readings. These are fresh matched controls;
the shipped checkpoint has different provenance and is not a control.

Training uses the current Adam 1e-3 / EMA / two-sided std-band [1, 8] recipe,
with D64, four strips, one 64px frame, batch 64, no augmentation, grounding or
temporal encoder. Existing collection speeds and omnidirectional room labels
stay unchanged. The .6–1.0 indoor collection-speed distribution is a training
recipe, not an Indoor Active Search flight evaluation; any later flight gate
must run at the established robust speed 0.6.

Both arms score all 186 independent holdout rollouts: 126 transit (42 per
world, a complete six-visit role cycle) plus 60 room, length 160. Data seeds
are distinct from training data and the earlier metric audit. This common
`world_balanced` exam represents the intended role-complete operating mix;
it does not estimate performance under the old aliased distribution. No
checkpoint sees these courses during fitting. Training's stratified internal
validation remains diagnostic and does not choose checkpoints or verdicts.

Before fitting, the instrument must show nonblank rendered scenes in all
four worlds, with a pixel difference from the same camera after the geometry
is removed. Each corpus must have at least 20 positive and 20 negative
held-command labels per world at horizon 32. Validate realized transit roles
against the exact registered schedule and preserve their counts. A failed
instrument stops the queue; fix a demonstrated harness error with an explicit
append-only note. Never regenerate a valid but unhelpful data draw.

**New offline GO bars:** moving AUC@32 candidate-minus-control must average
at least +.03 across the three seeds and be strictly positive on every seed.
Three AUC points are the preselected minimum useful gain for this study.
On **each** seed, classic, dense and room AUC may lose no more than .02;
pooled danger-now AUC may lose no more than .02; transit veer ranking may
lose no more than .05 (both arms need at least 20 probe samples). Every
candidate must remain within 512 KB and have exactly the control's analytic
memory/MAC bill. These are study-specific guard tolerances, not edits to
existing frozen skill bars. Any failed bar means NO-GO. Missing/nonfinite
readings mean INVALID, never a fabricated pass. No borderline remeasurement
is registered for this fixed six-fit study.

Report every fit and paired delta, plus the three-draw mean/range. Per-seed
2,000-resample paired, world-stratified rollout bootstrap intervals use seed
0; they are descriptive and conditional on fixed trained checkpoints. They
are not confidence intervals for training randomness. No significance or
promotion claim follows from three seeds. Report latent scale and internal
MSE/no-op diagnostics without comparing latent MSE across independently
learned representations. Report the full analytic int8 memory bill and MAC
latency estimate at the existing assumed 0.5 GMAC/s, not hardware timing.

Limits: changing schedule roles also changes generator RNG consumption and
the stratified internal split, so physical courses and optimizer-step counts
can differ. This tests the **whole layout recipe at a fixed rollout/epoch
budget**; it cannot isolate role balance from those consequences. Legacy
moving rollouts lack executed interventions, but the counterfactual oracle
still supplies alternative-action labels. A coverage fix alone is not proof
of a perceptual or policy improvement. GO only permits preregistering a
subsequent closed-loop experiment; neither model replaces a champion here.

## Execution and resumption

Run `bash experiments/schedule_layout_v1/run.sh` in the project environment.
The runner uses a process lock, freezes provenance, executes one subprocess
per stage, writes complete logs and immutable JSON receipts, and verifies
receipt hashes before skipping completed stages. Incomplete stages stop
resumption for inspection instead of silently repeating a training draw.
Large files live under `output/schedule_layout_v1/`; receipts and the final
report live here. `SCHEDULE-LAYOUT-DONE` requires every stage and protection
check to succeed; the shell records the real exit code. A valid NO-GO is a
completed scientific result, not a process failure.

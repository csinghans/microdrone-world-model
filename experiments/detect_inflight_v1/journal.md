# detect_inflight_v1 — is detection still sound when the drone is MOVING?

**Opened:** 2026-07-11 · **Owner:** Hans · **Source:** docs/REVIEW-2026-07.md (C1)

## The debt

Every indoor detection GREEN (yaw_v1 0.982, alt_v1, person_v1) was
measured on STATIONARY-imaging probes: the drone parked at grid
positions, kinematics reset, camera level. Missions then convert
per-frame recall (~0.5–0.76) into mission recall (~0.93) by scan
choreography. What was never measured: per-frame detection on frames
harvested DURING flight — where the quad's attitude tilts with every
translation command, the view wobbles with the control loop, and the
frame distribution is whatever flying actually produces. If in-flight
frames are OOD for the stationary-trained heads, every indoor GREEN
rides an unpriced assumption.

## Protocol (frozen before any number)

Fly the +x sweep mission (`run_vision_search`: Frontier coverage,
beams8, speed 0.6, deployed thr 0.65, the runner that detects EVERY
decision while MOVING — the deployed yaw-scan runner only detects while
hovering in spin-scans, so it cannot answer this question) over n=20
fresh rooms at the vision gate seeds (620000+). Instrumentation only: a
`trace` hook records `(step, prob, label, yaw, fired)` at every detect
call; `trace=None` leaves every runner bit-for-bit unchanged. Labels
are yaw-corrected geometric target-in-FOV (`_in_fov_yaw` at the actual
state yaw). Encoder = the unified WM; detector = the locked
`target_head_yaw.pt` (stationary-trained, test-block AUC 0.9818 — the
reference this read is judged against). Frames after the first firing
are logged too (the return leg adds honest negatives; AUC is
rank-based). Streams saved to `experiments/detect_inflight_v1/
artifacts/streams.npz` (gitignored) — they are also C2's replay corpus
(SPRT vs confirm-k on identical data).

## Pre-registered bars

| read | bar |
|---|---|
| pooled in-flight AUC | **≥ 0.90 → the debt is PAID** (an honest positive worth recording); **< 0.85 → the debt is REAL** — releases ONE knob: retrain the head on moving frames (escalation stops at heads, never the WM); 0.85–0.90 → borderline, pool n=40 before any knob |
| per-frame recall / FA @ thr 0.65 | recorded vs the stationary reference (recall 0.758, obstacle-FA 0.021) — informational, no bar |

## Status

- [x] Pre-registration committed (this file, before any number)
- [ ] Instrumentation (trace hook) + suite
- [ ] n=20 read → verdict

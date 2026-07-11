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

## Results (2026-07-11)

| block | flights | frames | pos rate | in-flight AUC | recall@0.65 | FA@0.65 |
|---|---|---|---|---|---|---|
| 1 (seeds 620000+) | 20 | 5523 | 0.066 | 0.8836 | 0.213 | 0.002 |
| 2 (seeds 620020+) | 20 | 5019 | 0.059 | 0.8941 | 0.143 | 0.001 |
| **pooled** | **40** | **10542** | 0.063 | **0.8888** | **0.182** | 0.002 |

Stationary reference (yaw_v1 test block): AUC 0.9818, recall 0.758.

## Verdict — the debt is PRICED, not paid and not forgiven

Pooled n=40 lands at **0.889 — inside the pre-registered borderline
band both times, with a stable estimate** (blocks 0.884/0.894; at ~660
positives the read is tight). By the letter of the bars the
moving-frame head-retrain knob stays holstered (≥ 0.85). By the
numbers, the stationary-imaging assumption has a real price:

- **−0.093 AUC on moving frames** (0.982 → 0.889) — far outside noise
  at this n. Attitude tilt and control wobble are a genuine
  distribution shift for a head trained on parked-drone imagery.
- **The operating point is broken, not the ranking: recall@0.65
  collapses 0.758 → 0.182** (scores shift DOWN on moving frames; FA
  drops with them, 0.002). A fixed threshold tuned on stationary
  frames reads almost nothing while cruising.

**Why the deployed GREENs survive this:** the shipped yaw-scan search
detects only while HOVERING in spin-scans — its frames are
near-stationary by construction, and the choreography (approach, face,
confirm-2) was measured end-to-end at 0.70–0.93 find rates. The debt
never sat under the deployed missions; it sat under any FUTURE design
that detects while cruising.

**Consequences (named, not run):** any cruise-detection ambition must
either (a) retrain heads on moving frames — the knob, releasable by a
fresh pre-registration if a design needs it — or (b) stop reading fixed
thresholds and accumulate the score STREAM as evidence, which is
exactly C2 (`docs/REVIEW-2026-07.md`): the recorded streams
(`artifacts/streams{,_b2}.npz`, 10542 frames with labels) are its
replay corpus, and "ranking survives, operating point does not" is
precisely the failure mode sequential evidence is built for.

Harness note, on the record: block 1's queue committed through a
failing selftest because its gate was `grep OK`, not `&&`-chained exit
codes — the CLAUDE.md queue trap, re-measured on its author; the
selftest's own arithmetic was the bug (fixed), the suite was sound.

## Status

- [x] Pre-registration committed (this file, before any number)
- [x] Instrumentation (trace hook, behaviour-preserving) + suite
- [x] n=20 read → borderline → pooled n=40 per the bar
- [x] Verdict: debt priced (−0.093 AUC, recall 0.758→0.182 @0.65);
      knob stays holstered by the letter; deployed missions insulated
      (hover-scan); streams handed to C2

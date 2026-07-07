# search-wm v2 — FOV-honest labels: can the WM own FORWARD danger? (Phase 1b, step 3)

## Pre-registration (2026-07-08, before any number exists)

search_wm_v1 closed as an honest negative: the retrained WM predicted
room latents well (MSE@32 0.94) but its collision head sat at chance,
because the danger label was OMNIDIRECTIONAL `clearance()` — mostly
out of the forward 28-degree camera's view, hence not a function of
the observation. The named fix: **FOV-honest labels** — label danger
only for surfaces the forward camera can actually see (the
`metric_labels` visible=0 discipline), so the target IS in the frame.

**Machinery (shipped):** `SearchScenario.forward_clearance()` — nearest
wall/obstacle surface in the +x FOV cone (ray-cast, yaw==0 so
body==world); `search_rollouts --fov-honest` labels `dists` with it;
`eval_search_wm_probe --fov-label` scores against it.

**Protocol:** regenerate the search dataset FOV-honest, retrain the WM
80 epochs, re-probe with `--fov-label`.

**Frozen read:** forward AUC >= 0.75 (vs the FOV-honest label) -> the
WM CAN own forward danger; build the HYBRID safety filter (WM warn for
forward motion + the 4 rangefinders for side/behind) and gate it
against the geometric frontier. forward AUC < 0.65 -> even the
in-view danger is not learnable from this encoder at this scale
(deeper negative: the wall appearance itself, not just the label);
record and stop. Between -> marginal, recorded.

Honest note: FOV-honest labeling means the WM can only ever own
FORWARD danger; lateral/behind danger is out of view by construction
and stays the rangefinders' job. So even a pass does not give the WM
the whole safety signal — it gives it the FORWARD share, which is the
most it can honestly have on a fixed forward camera.

Cost: one FOV-honest dataset + one 80-epoch retrain + one probe.

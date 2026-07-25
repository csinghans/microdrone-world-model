# general_wm_v2 — the parked candidate: is wm_3x the next general WM?

Opened 2026-07-25. representation_v2 (commit 8ab7568) failed its
dense-targeted bars but parked an honest by-product: `wm_3x` (the
unified recipe at uniform 3x data) is the best GENERAL row ever
measured offline — all-world AUC@32 **0.9512** vs the unified's 0.9314,
classic +0.10, veer widened 0.986, high-clutter calibration gap 4.7x
tighter. This campaign asks the parked question properly, through the
SAME gate protocol that crowned the unified WM in v0.8
(`eval/eval_unified_wm_gate`): incumbent = the unified WM, candidate =
wm_3x. Offline first, then the closed-loop and promotion arms in one
pre-registered pass.

This is an EVALUATION campaign — zero training; the candidate artifact
is frozen as trained (`experiments/representation_v2/artifacts/
wm_3x.pth`, seed-0 deterministic).

## Pre-registration (committed before any number)

### Protocol

One run of the v0.8 gate, candidate slots swapped:
`eval_unified_wm_gate --champion output/world_model_unified.pth
--unified <wm_3x> --closed-loop --cl-seeds 60 --speed-sweep
--sweep-seeds 40` — transit offline arm (holdout per-world AUC@32),
indoor arms (det_probe n_rooms=6 seed0=600000; fwd_probe n=12
seed0=130000 fov_label), closed-loop transit (60 in-path seeds:
crash / min-clear / false-evasion / reached / trigger-lead), and the
speed sweep (40 seeds x 0.8-1.6 m/s).

### Bars (frozen from the v0.8 gate's shape + the incumbent's rows)

- **B1 (offline transit, already measured — recorded, not re-fished):**
  candidate all-world AUC@32 >= incumbent + 0.01 (0.9414); dense >=
  incumbent - 0.01 (0.9077) — the general upgrade may not silently
  deepen the dense hole.
- **B2 (indoor detection):** det_probe AUC on the candidate latent >=
  incumbent - 0.01. The three deployed heads are latent-bound and
  would need retraining on adoption; B2 asks whether the latent still
  SUPPORTS detection at the linear-probe level (the unified's own
  adoption logic, reused).
- **B3 (closed-loop transit):** candidate crash <= incumbent crash
  (paired seeds) AND false-evasion <= incumbent + 5 pts AND reached >=
  incumbent - 5 pts.
- **B4 (speed sweep):** candidate crash <= incumbent at every cruise
  speed 0.8-1.6 (the unified's own promotion bar).
- **Guards:** G1 the sacred artifacts untouched (sha bracket); G2 any
  regression on the fwd_probe is REPORTED (indoor forward-collision is
  beams8's job — the honest v0.8 asterisk, inherited).

### What passing buys (and does not)

A full pass opens the ADOPTION campaign (its own prereg): three
detection-head retrains on the new latent + lock refresh + release
assets + `flight_mode` rebinding + zoo checks — the v0.8 checklist.
No adoption happens inside this campaign; a pass here is a
recommendation with evidence, nothing moves in `artifacts.lock.json`.

---

(verdict lands below when the gate completes)

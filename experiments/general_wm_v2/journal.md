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

---

## Verdict — 2026-07-25: REFUSED (B1-dense, B3, B4 FAIL); the record offline row is a far worse flyer

Gate as pre-registered (sha brackets green; log `output/gw2_gate.log`).

| arm | incumbent (unified) | candidate (wm_3x) | bar | verdict |
|---|---|---|---|---|
| offline all / dense AUC@32 | 0.9314 / 0.9177 | **0.9512** / 0.8417 | +0.01 / >= 0.9077 | all pass / **dense FAIL** |
| indoor det_probe / fwd_probe | 0.978 / 0.674 | 0.978 / **0.722** | -0.01 / reported | **B2 PASS** (fwd improved) |
| closed loop (60 paired seeds) | crash 0.214, clear 0.387, FE 0.056, lead 216 ms | **crash 0.524, clear 0.233, FE 1.000**, lead 222 ms | crash <=, FE <= +5 pts | **B3 FAIL** |
| speed sweep 0.8-1.6 | 29/32/29/29/54 % | 46/54/46/32/**25** % | <= everywhere | **B4 FAIL** (worse at 0.8-1.2) |

**The candidate is refused.** No adoption campaign opens; nothing moves
in the lock; wm_3x stays parked as an offline curiosity.

### The lesson, measured at the WM level

The best GENERAL offline row ever (all-world 0.9512) is a
*catastrophically worse flyer*: false-evasion 100 % — the closed-loop
trigger fires on EVERY clear course — halving minimum clearance and
doubling the crash rate. The mechanism was already in the offline
record: wm_3x's warn gaps run +0.12/+0.19 in open/mid clutter (global
over-warn), and WMPolicy's relative margin turns a calibration shift
into constant evasive motion. Offline AUC ranks frames; closed loop
flies distributions. v0.5 banked "a better detector is not a better
flight" for policies; general_wm_v2 banks the same law one level down:
**a better-ranking world model is not a better-flying one — the
instruments predict, they do not certify.** (The one honest positive:
the candidate's indoor forward-collision probe improved 0.674 -> 0.722
and detection held at 0.978 — the 3x latent is not globally worse, it
is mis-calibrated for the deployed trigger idiom.)

The unified WM keeps its crown uncontested.

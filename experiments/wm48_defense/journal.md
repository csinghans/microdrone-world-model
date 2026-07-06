# wm48-defense — same body, same reward, longer eyes

## Pre-registration (2026-07-06, before any number exists)

Full rationale and the frozen signature live in the skill docstring
(`skills/wm48_defense/skill.py`); this journal records the swap
protocol and, before the knob flies, the checksummed provenance:

1. `sha256(output/world_model.pth)` must equal the artifacts.lock.json
   champion entry (G1) — recorded below.
2. Swap: copy `experiments/horizon/artifacts/wm_h48.pth` over
   `output/world_model.pth` (G1 kept aside, checksummed).
3. `research step skills/wm48_defense --knob 0` — train + full exam
   under WM48 (ObsBuilder reads meta: 10 probs/candidate).
4. Restore G1; re-verify sha256 against artifacts.lock.json.
5. Pairing: `ppo_wm48_defense_K1.zip` flies ONLY with `wm_h48.pth`
   (mismatched loads fail loudly at state-dict/obs-dim time — by
   design).

Baseline (v1-K3 under G1, same cells/seeds): success 47/60/20/13 %,
crash 0/27/43/77 %. Support = a fast cell (v1.4/v1.8) over its 0.55
bar; mechanism check = v1.8 crash materially under 77 %; refuted =
fast cells at K3 level with training complete (then the blur — AUC@48
0.75 — or dodge kinematics is the live suspect). Secondary read:
v0.6/v1.0 retention. Guards: structural fails expected (pure diet),
promotion out of scope.

**Swap executed (2026-07-06):** G1 sha256 `1fea88ad…149f80cf` ==
artifacts.lock.json champion entry ✓; backup kept; WM48 in place
(`7cc820856c4b77bb…`). K1 launched under it.

Harness footnote: the first K1 launch tripped the DESIGNED loud-fail —
`WM_HORIZONS` was not set, so `load_model` built a 4-head predictor
against the 5-head checkpoint and refused at state-dict time (no
measurement taken). Relaunched with `WM_HORIZONS=4,8,16,32,48`, as the
H1 queue always ran. The swap protocol above now includes the switch.

## K1 — v1-K3's recipe verbatim, trained and examined under WM48 (2026-07-06 05:05 UTC)
Hypothesis: the single delta is the swapped model (1.0 s horizon): warning 1.06 -> 1.4 s at v1.8. Swap protocol + provenance pairing in the journal; zip flies ONLY with wm_h48.pth
Config: {"worlds": ["dodgeball_v06", "dodgeball_v10", "dodgeball_v14", "dodgeball_v18"], "station_tick": 0.6, "x_progress": true, "edge_bias": true, "timesteps": 900000}

| cell | n | crash | success | clearance | custom |
|---|---|---|---|---|---|
| dodge@v0.6 | 30 | 3% | 20% | 0.39 | survived=0.97 in_box=0.23 disp_x=1.58 y_max=1.30 |
| dodge@v1.0 | 90 | 31% | 37% | 0.26 | survived=0.69 in_box=0.41 disp_x=1.52 y_max=1.24 |
| dodge@v1.4 | 30 | 60% | 27% | 0.20 | survived=0.40 in_box=0.57 disp_x=1.42 y_max=1.16 |
| dodge@v1.8 | 30 | 80% | 17% | 0.15 | survived=0.20 in_box=0.60 disp_x=1.39 y_max=1.17 |
| guard:gap@1.0 | 30 | 80% | 0% | 0.44 |  |
| guard:mgap@1.0 | 30 | 83% | 0% | 0.15 |  |
| guard:cluttered | 60 | 25% | 0% | 0.76 |  |
| guard:sweep@2.0 | 60 | 0% | 0% | 1.15 |  |
- dodge@v0.6 success>=0.65: 0.20 FAIL
- dodge@v1.0 success>=0.55: 0.37 FAIL (rechecked)
- dodge@v1.4 success>=0.55: 0.27 FAIL
- dodge@v1.8 success>=0.55: 0.17 FAIL
- guard:gap@1.0 success>=0.75: 0.00 FAIL
- guard:mgap@1.0 success>=0.7: 0.00 FAIL
- guard:cluttered crash<=0.05: 0.25 FAIL
- guard:sweep@2.0 crash<=0.1: 0.00 PASS

**Gate verdict: guard_regression**

### Researcher notes
(unattended run)

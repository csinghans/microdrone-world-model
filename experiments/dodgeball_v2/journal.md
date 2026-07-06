# dodgeball v2 — the guard-clean defender (the union cell)

## Pre-registration (2026-07-06, before any number exists)

The v1 factorial is one cell short: (diet pure/mixed) x (station pay
distal/dense) measured pure x distal (dodges by yielding), mixed x
distal (station erased, sweep broken 37 %), pure x dense (holds the
station, dodge@v1.0 60 % over bar, transit guards structural-fail).
**K1 plays mixed x dense** — v1-K2's exact 7-world diet +
station_tick=0.6; one delta against each v1 arm. Exam verbatim, bars
frozen (0.65 / 0.55 x3 + the standard guards), seed0 unchanged.

**K2 (reserve)** is conditional on the dilution signature (>= 1 dodge
bar passed AND sweep/cluttered broken) and will be arbitrated with
`research step` — the v1 breach is not getting a sequel. If K1 fails
every dodge bar instead, K2 stays sheathed.

**Frozen signature.** Support = one zip with >= 1 dodge bar AND all
four guards green (the guard-clean defender exists — the ledger's
claim). Crown = the full gate; stated now: v1.4/v1.8 sit behind the
measured k=32 warning arithmetic, so a crown likely needs WM48 and is
not expected from this campaign. Refuted = every played knob fails all
dodge bars or breaks guards — the transit/defense trade is structural
at 900k; escalations go to a fresh pre-registration.

Cost: 1-2 x 900k (~1 h each on this machine) + exams; single knob at a
time via `research step`.

## K1 — the union cell: v1-K2's mixed diet + station_tick=0.6 (2026-07-06 04:10 UTC)
Hypothesis: single delta vs K2 (the tick) and vs K3 (the mixing): per-world reward dispatch lets one policy learn both economies — transit pays progress, ball worlds pay the station
Config: {"worlds": ["classic", "gap", "moving_gap", "dodgeball_v06", "dodgeball_v10", "dodgeball_v14", "dodgeball_v18"], "station_tick": 0.6, "x_progress": true, "edge_bias": true, "timesteps": 900000}

| cell | n | crash | success | clearance | custom |
|---|---|---|---|---|---|
| dodge@v0.6 | 30 | 23% | 0% | 0.31 | survived=0.00 in_box=0.00 disp_x=3.01 y_max=0.82 |
| dodge@v1.0 | 30 | 40% | 0% | 0.27 | survived=0.00 in_box=0.00 disp_x=3.01 y_max=0.76 |
| dodge@v1.4 | 30 | 30% | 0% | 0.26 | survived=0.00 in_box=0.00 disp_x=3.01 y_max=0.71 |
| dodge@v1.8 | 30 | 30% | 0% | 0.29 | survived=0.00 in_box=0.00 disp_x=3.01 y_max=0.78 |
| guard:gap@1.0 | 30 | 10% | 90% | 0.35 |  |
| guard:mgap@1.0 | 90 | 30% | 70% | 0.28 |  |
| guard:cluttered | 60 | 25% | 75% | 0.35 |  |
| guard:sweep@2.0 | 60 | 58% | 42% | 0.19 |  |
- dodge@v0.6 success>=0.65: 0.00 FAIL
- dodge@v1.0 success>=0.55: 0.00 FAIL
- dodge@v1.4 success>=0.55: 0.00 FAIL
- dodge@v1.8 success>=0.55: 0.00 FAIL
- guard:gap@1.0 success>=0.75: 0.90 PASS
- guard:mgap@1.0 success>=0.7: 0.70 PASS (rechecked)
- guard:cluttered crash<=0.05: 0.25 FAIL
- guard:sweep@2.0 crash<=0.1: 0.58 FAIL

**Gate verdict: guard_regression**

### Researcher notes
(unattended run)

# beam_latency_v1 — the sensor spec line's last axis: ring latency

**Opened:** 2026-07-13 · **Prior:** `experiments/beam_noise_v1/` (P1,
closed) — noise and dropout are priced (safety pocket σ ≤ 0.05 m,
missed-return ≤ 5 %; knee at σ=0.10 / p=0.10), and P1's close NAMED
this follow-up: the latency axis, needing runner surgery. A real ToF
ring reports late; every beam the indoor safety case rides has been
instantaneous.

## Protocol (P1's, one axis swapped)

`DelayedBeams` — a delegating scenario proxy in the P1 mould:
`beam_ranges`, and ONLY `beam_ranges`, returns the reading captured k
CALLS ago (a FIFO; readings are captured at their own old positions,
so the proxy models a ring whose report lags the aircraft). The judge
(`clearance`), planner context (`range_sensors`) and beacon stay
clean. Warm-up honesty: the first k calls replay the initial reading.
Instrument note: delay is denominated in BEAM READS; the run reports
reads-per-decision in the control arm so the ms equivalence
(~83 ms/decision at the 12 Hz decide rate) is stated, not assumed.

**Arms (frozen):** k ∈ {0 (control), 1, 2, 4, 8} reads — nominally
0 / 83 / 167 / 333 / 664 ms at one read per decision; at the robust
0.6 m/s that is up to ~40 cm of stale geometry. Identical fresh seeds
per arm, seed block **750000**, n=30, single-room frontier search at
speed 0.6 + beams8 (the P1 mission, verbatim).

## Bars (frozen; P1's pricing shape)

- **Instrument-first:** the control arm must sit in its historical
  band (find ≥ 0.80, collision ≤ 0.05) or there is no pricing read.
- **The footnote:** knee = the first arm whose collision crosses the
  0.05 SEARCH-ROOM bar; pocket = the largest delay inside the bar.
  Deliverable = the BOM spec line completed: "beams8 safety absorbs
  ≤ X ms of ring latency at 0.6 m/s", joining ToF σ < 5 cm and
  missed-return < 5 % from P1.
- Find/return reported per arm (context; P1 saw them barely move
  under noise — whether latency behaves the same is part of the read).

**Machinery:** `eval/eval_beam_latency.py` (proxy + `--price` +
selftest: delay semantics on a scripted fake scenario, d0 passthrough
identity, delegation untouched).

## Status

- [x] Pre-registration (this file, before any number)
- [ ] Price run: 5 arms × n=30 @750000 → knee + pocket + footnote

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

## Block-1 execution note (recorded as it happened)

The instrument-first clause FIRED: control find 0.767 < the 0.80 band
(collision 0.000 ✓). The collision curve itself is textbook
(0/0/0/0.033/0.100; find/return IDENTICAL across arms — delay touches
only the safety veto, as designed, and P1's arms showed the same
flat-find signature). The suspect is the BAND, not the harness: P1's
clean arm read 0.833 on ITS block (740000); 0.767 on a fresh block is
2 missions in 30 (−0.97σ) — a draw, not damage. The session's own law
applies: a block is a draw, not a rate.

**Recheck (frozen before running):**
1. **Instrument exoneration:** the bare runner (no proxy) on the same
   block must reproduce the d0 arm's numbers EXACTLY (deterministic
   seeds; the selftest already proves d0 passthrough in vitro — this
   proves it in vivo). Any mismatch = real harness suspicion → stop.
2. **Pool, never replace:** a second fresh block @760000, all five
   arms, n=60 pooled per arm. The control band (find ≥ 0.80,
   collision ≤ 0.05) is judged on the POOLED control; knee and pocket
   are read on pooled collisions. If the pooled control still misses
   the band, the campaign records "control band unmet across two
   blocks" and the footnote is issued WITH that caveat (the band
   itself encoded P1's single-block draw — stated, not hidden).

## Status

- [x] Pre-registration (this file, before any number)
- [x] Block 1 @750000: instrument-first fired on find 0.767 (band
      0.80); collision curve clean (knee d8, pocket d4 ≈ 517 ms
      provisional) → recheck registered above
- [ ] Exoneration + block 2 @760000 → pooled verdict + footnote

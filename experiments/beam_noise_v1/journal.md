# beam_noise_v1 — pricing the ring (the first noisy beam)

**Opened:** 2026-07-12 · **Owner:** Hans · **Source:** docs/REVIEW-2026-07.md
(P1 — indoor sensor pricing)

## The question

The entire indoor safety case — 91/100 with zero collision missions
included — rides the beams8 rangefinder ring, and every beam ever flown
has been NOISELESS. Real ToF sensors carry range noise and dropout.
This is a PRICING run, not a gate: at what perturbation level does the
deployable configuration's collision bar (≤ 0.05, SEARCH-ROOM) break?

## Protocol (frozen before any number)

**Injection seam:** a delegating scenario proxy whose `beam_ranges` —
and ONLY `beam_ranges` — is perturbed (a seeded rng per mission). The
judge (`clearance` scoring), the planner context (`range_sensors`) and
the beacon stay clean: this sitting prices exactly what the beams8
SAFETY FILTER reads. One axis per sitting: latency injection is
deferred (the veto's call-count-vs-decision ambiguity would make the
delay unit dishonest without runner surgery — named, not smuggled).

**Perturbations, applied per beam reading:**
- *range noise:* r ← max(0, r + N(0, σ)), σ ∈ {0.05, 0.10, 0.20} m
- *dropout-to-max:* with probability p the reading returns the sensor
  max (a missed ToF return), p ∈ {0.05, 0.10}

**Missions:** the M1/search_room_v3 config of record (single room,
frontier, beams8, speed 0.6, 600 decisions), n=30 per arm, fresh seed
block 740000+. Arms: clean baseline + 3 σ-arms + 2 p-arms = 6 × 30 =
180 missions, identical seeds across arms.

**Reads (pricing, no pass/fail bars):** find / return / collision per
arm; the interpretation rule frozen now — the deployable claim gains a
noise footnote of the form "beams8 holds collision ≤ 0.05 up to σ = X /
p = Y; the knee is at Z". If even the clean arm misses its historical
band (find ~0.9, collision ≤ 0.05), the harness is suspect and no
pricing is read (instrument-first).

## Results (2026-07-12 — `eval_beam_noise --price`, price_results.json)

| arm | find | return | collision |
|---|---|---|---|
| clean | 0.833 | 0.733 | 0.000 |
| σ=0.05 m | 0.833 | 0.733 | 0.033 |
| σ=0.10 m | 0.833 | 0.733 | **0.067 ✗** |
| σ=0.20 m | 0.800 | 0.733 | **0.167 ✗** |
| dropout 5 % | 0.833 | 0.700 | 0.000 |
| dropout 10 % | 0.833 | 0.733 | **0.067 ✗** |

Clean arm inside its coded sanity band (find ≥ 0.80, collision ≤ 0.05);
levels on this fresh block sit slightly under the v3 record (0.833 vs
0.917 find at n=30 — block noise), and the identical-seed Δ across arms
is the read, per the pre-registration.

## The footnote (the deliverable)

**beams8 holds the ≤ 0.05 collision bar up to σ = 0.05 m range noise
and 5 % dropout; the knee is at σ = 0.10 m / p = 0.10.** Both failure
directions behave as geometry predicts: noise puts phantom-far readings
on genuinely-near walls (the veto passes a bad action), and
dropout-to-max is pure phantom-far. Find/return barely move across
arms — the price is paid in collisions, exactly where the safety
filter lives.

Bridge-relevant line for the sensor BOM (and writing/#8's sequel):
a ToF ring needs σ < 5 cm and missed-return rate < 5 % at ≤ 3 m —
VL53-class parts sit comfortably inside the pocket. Named follow-ups
(fresh registrations, not run): the latency axis (needs runner surgery
for an honest delay unit); the same pricing on the indoor-gate mission
pool instead of M1-only.

## Status

- [x] Pre-registration committed (this file, before any number)
- [x] Noisy-proxy + pricing tool + selftest
- [x] 6-arm read → **footnote priced: safe pocket σ ≤ 0.05 m, p ≤ 0.05;
      knee at σ = 0.10 / p = 0.10**

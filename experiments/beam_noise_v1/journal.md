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

## Status

- [x] Pre-registration committed (this file, before any number)
- [ ] Noisy-proxy + pricing tool + selftest
- [ ] 6-arm read → the noise footnote

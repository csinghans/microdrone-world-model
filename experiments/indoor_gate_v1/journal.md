# indoor_gate_v1 — one number for the indoor mission

**Opened:** 2026-07-12 · **Owner:** Hans · **Source:** docs/REVIEW-2026-07.md
(INDOOR-GATE v1 — "the missing 72/100")

## The question

Transit earned a single deployment number (72/100) by composing
unit-green skills into seed-drawn composite courses. The indoor track
has six-plus per-experiment GREENs on per-experiment bars — and no
composite. Do the indoor GREENs survive COMPOSITION into one seeded
mission pool, the way a deployed system would actually be exercised?

## Mission families (each config = its unit gate's, verbatim)

Speed **0.6** and **beams8** are HARDCODED in the runner — never
inherited from any API default (the I1 lesson). Fresh seed blocks,
disjoint from every unit gate.

| family | weight (gate) | mission | config of record | seeds |
|---|---|---|---|---|
| M1 | 0.30 | single-room beacon find+return | `single_room`, frontier, 600 decisions (search_room_v3) | 700000+ |
| M2 | 0.30 | multi-room 2/3/4-room find+return | `two_room`/`n_room`, 1000×rooms decisions (eval_room_graph's budget) | 710000+ |
| M3 | 0.20 | **vertical: search the room, then scan heights — the first end-to-end read** | vary-height room (beacon_z ∈ {0.3, 1.0, 2.0}), NEW flown runner: Frontier cruise + periodic 3-D scans (FLY to each altitude 0.4/1.0/1.6/2.0 — no teleports — spin 360°, confirm-2), descend + BFS home | 720000+ |
| M4 | 0.20 | person find+return | `demo_person.record` choreography (sense→approach→face-confirm), snapshots off, 900 decisions | 730000+ |

Composite verdict per mission (transit's shape): **found AND returned
AND zero collisions.** Per-family break histogram reported.

Honest notes, on the record before flying:
- **M3 is new flight glue** — the unit evidence (alt_v1 find 0.50→1.00)
  came from a teleport-pose scan probe at a ground-truth-placed scan
  point; nobody has ever flown search-then-vertical-scan. Its probe
  number is the sitting's first deliverable, whatever it is.
- **M3 rides the journal-side `alt` multi-height head** (z_cams
  0.4–2.0); the LOCKED `low` head is the floor-hugging variant (z_cams
  0.15–0.8) and would be OOD at 1.6–2.0 m scans. The alt/low
  canonicalization is the open G1 owner decision — if `low` stays
  canonical, M3 needs a locked multi-height refit before the formal
  gate.
- Vertical moves happen at the scan spot only (x, y fixed), so the 2-D
  clearance collision model stays consistent at altitude.

## Protocol — feasibility first (the slalom lesson)

**This sitting runs the CEILING PROBE: n=20 per family, no bars.**
Bars are frozen FROM the probe (in a follow-up commit, before the
formal n=100 weighted-draw gate) — never from hope. Non-binding priors
from the unit numbers, for calibration only: composite ≥ 0.80, pooled
collision ≤ 0.02, return|found ≥ 0.90.

## Ceiling probe (2026-07-12 — n=20/family, probe_results.json)

| family | find | return | collision missions | composite |
|---|---|---|---|---|
| M1 single | 0.900 | 0.850 | 0.000 | 0.850 |
| M2 multi | 0.950 | 0.900 | 0.000 | 0.900 |
| **M3 vertical (the first flown read)** | 0.700 | 0.900 | 0.000 | **0.700** |
| M4 person | 1.000 | 0.950 | 0.000 | 0.950 |
| **weighted ceiling** | | | **0.000** | **0.855** |

**Zero collisions in 80 missions** — the beams8 safety case survives
composition, including M3's altitude flying (vertical moves at the safe
scan spot held the 2-D clearance model). M4 beats its unit gate (1.00 /
0.95 vs 0.933). M3's 0.700 is the search-then-vertical-scan mission's
first number ever flown — the pool's load-bearing weak family.

## Bars — FROZEN from the probe (before the formal read)

- **GATE (headline): composite ≥ 0.80 over n=100 missions, split by the
  registered weights (30/30/20/20), FRESH seed blocks (probe seeds
  +100).** Margin note, stated honestly: the probe ceiling 0.855 leaves
  ~1.6σ at n=100 (binomial σ ≈ 0.035) — a modest margin; M3 carries the
  risk.
- **Guard: collision missions ≤ 0.02 pooled** (probe: 0.000).
- Per-family break histogram REPORTED, not gated (probe ceilings on
  record: 0.85 / 0.90 / 0.70 / 0.95).

## Status

- [x] Pre-registration committed (this file, before any number)
- [x] Runner (`eval/eval_indoor_gate.py`) + M3 flight glue + M4
      snapshots/collision patch
- [x] Ceiling probe n=20/family → **weighted ceiling 0.855, zero
      collisions in 80**
- [x] Bars frozen from the probe (this commit, before the formal read)
- [x] Formal gate n=100 weight-split, fresh seeds → **GREEN 91/100**
- [ ] `scripts/gate.py` whole-system scorecard (the named next build)

## The formal read (2026-07-12 — n=100, seeds probe+100, gate_results.json)

| family | n | find | return | collision missions | composite |
|---|---|---|---|---|---|
| M1 single | 30 | 0.933 | 0.933 | 0.000 | 0.933 |
| M2 multi | 30 | 1.000 | 1.000 | 0.000 | **1.000** |
| M3 vertical | 20 | 0.750 | 1.000 | 0.000 | 0.750 |
| M4 person | 20 | 0.950 | 0.900 | 0.000 | 0.900 |
| **GATE** | **100** | | | **0.000** | **0.910** |

**Composite 0.910 ≥ 0.80 ✓ · collision missions 0.000 ≤ 0.02 ✓ →
GREEN.** The indoor track's deployment number is **91/100**, alongside
transit's 72/100.

## Verdict

The indoor GREENs survive composition. Zero collisions across all 180
missions flown today (80 probe + 100 gate) — the beams8 ring's safety
case holds under mission mixing, doorway traversal, altitude flying and
person choreography alike. The pool's honest weak spot stays M3
(vertical search 0.750 formal — its FIRST flown number; misses, never
crashes, never fails to come home: find is the frontier, not safety).
Named next builds, in order: `scripts/gate.py` (one command → transit
gate + indoor gate + budget + safety + lock checks → one JSON per
mode); a vertical-search find-rate campaign if M3's 0.75 is worth
buying up (scan cadence/altitudes are un-tuned first-guess parameters —
priced as a fresh pre-registration, not a knob to fish).

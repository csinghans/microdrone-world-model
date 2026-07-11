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

## Status

- [x] Pre-registration committed (this file, before any number)
- [ ] Runner (`eval/eval_indoor_gate.py`) + M3 flight glue + M4
      snapshots/collision patch
- [ ] Ceiling probe n=20/family → freeze bars (follow-up commit)
- [ ] Formal gate n=100 weighted draw (H2) + `scripts/gate.py` scorecard

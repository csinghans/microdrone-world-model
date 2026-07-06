# integration-v1 — flight TDD's first integration suite

## Pre-registration (2026-07-06, before any number exists)

Hans's directive, made mechanical: unit tests (the existing skill cells
+ frozen bars + guards) get an INTEGRATION layer — randomly composed
3-stage courses flown end to end in one episode — and a **deployment
gate**: integration success ≥ **0.70 at n = 100** random courses is the
standing precondition for any real-hardware deployment (hardware itself
stays parked until separately unfrozen). The repo keeps the LATEST
passing integration flight as videos of record (FPV + simulator god
view GIFs in docs/media/, with a provenance stamp).

**Frozen design** (machinery: `sim/composite.py`,
`eval/eval_integration.py`, both selftested):
- Stage pool (5 transit arenas): gap / slalom3_fixed / moving_gap /
  door / opening_door. Course = seed-drawn 3 stages with replacement;
  seeds 110000+. goal 9 m, tmax 22.5 s.
- Shifting is double-write (bodies + logical coords + meta); movers
  ACTIVATE ON ENTRY (their baked aim math assumes clock-zero at native
  distance — crossing the stage boundary is exactly that instant).
- Integration verdict is composite-level: reach the final goal, never
  crash. Stage-resolution diagnostics (stages_cleared / stage_break_at
  / crash_stage) come from x-crossings — deliberately NO per-stage
  time-aware predicates (the absolute-clock trap, documented in
  sim/composite.py).
- Policies fly through `StageLocal` (stage-local x for the x_progress
  feature; memory reset at stage entry = fresh-corridor semantics).

**Schedule:**
1. **Ceiling probe** (feasibility-first): `PerStageExperts` — the
   PRIVILEGED per-stage solo-holder relay (reads the course
   composition; honestly labelled, never a contender). Its n=30 rate
   prices course flyability with the identification problem removed:
   seams, entry states, mover re-aiming are what it measures.
2. **Red baseline** (TDD red), n=30 each: the anchored generalist
   (93.3/80/43 on chain/gap/mgap, doors unseen), mgap-K3 (all fences,
   no slalom), the slalom clone (chain 96.7, moving worlds unseen),
   dispatch-v3 (best closed-loop classifier). Expectation, stated
   honestly: all far below the gate; failures concentrated at each
   contender's foreign stages — the first measured "units green ≠
   integration green".
3. Any contender within 10 points of the ceiling graduates to the
   n=100 formal suite (+ video on pass).

**Solo-holder expert map** (each gated in its own journal): gap→KD1,
moving_gap/door→mgap-v2 K3, opening_door→odoor K3,
slalom3_fixed→chain-distill clone.

## The ceiling probe and the red baseline — the seam tax (2026-07-06)

| contender | integration success (n=30) | breaks @stage 0/1/2 |
|---|---|---|
| **ceiling relay** (privileged per-stage solo holders) | **13.3 %** | 5/10/11 |
| anchored generalist | 13.3 % | 8/4/14 |
| mgap-K3 | 13.3 % | 12/7/7 |
| **slalom clone** | **33.3 %** | 5/7/8 |

**The headline is the ceiling's own number.** If stages were
independent at the experts' native rates (~0.90 each), the relay would
read ~0.73; it reads 0.133 — per-stage conditional success ≈ 0.51.
**The seams cut every expert's stage rate nearly in half**: mid-flight
entry states (residual velocity, y carried over from the previous
stage's gap, no hover start) are conditions no unit episode ever
produced. Units green, integration red, and the break is in the thing
units never test — the integration layer earned its keep on run one.

**The clone anomaly is the green road's first signpost:** a single
policy beating the privileged specialist relay 2.5×. OracleWeave's BC
repertoire is "steer to the visible gap from wherever you are" — the
teacher handled arbitrary entry states, so its student does too; the
RL specialists only ever saw clean starts. Seam robustness was
DISTILLED, never trained.

Notes on the record: (i) the walk-around loophole was audited (passing
runs at |y| ≤ 0.57) and the corridor clause (|y| ≤ 2.4) added as
hardening — no measured number changed; (ii) dispatch-v3 was dropped
from the red list — its artifact predates the v5 code migration, and
the relay's own seam ceiling dominates whatever learned dispatch could
add; its integration exam waits for seam-competent experts; (iii) the
ceiling probe's job was arena pricing, and what it priced is that
**this arena's binding constraint is the seams, not the stages**.

**Graduation per the frozen rule** (within 10 points of the ceiling —
the clone EXCEEDS it): the slalom clone advances to the n=100 formal
suite. Green roads, seeded for the ledger: hot-start collection
(distill/train with randomized entry velocity and y — make the seam a
training view), and an all-stage oracle-BC generalist (the clone
recipe, extended to every pool teacher, hot starts included).

## The n=100 baseline of record (2026-07-06)

The clone's n=30 reading replicated at scale: **33/100 = 0.330**
(CI ±~9 pt) — the instrument is stable. Break profile 10/28/29 across
stages 0/1/2: a clean start almost always survives its first stage;
57 of 67 failures happen at the seams. **Deployment gate: FAIL**
(0.330 vs 0.70) — the honest TDD red, now with a number and a
mechanism. Videos of record: none yet, by protocol — the repo carries
no integration flight video until an integration suite passes.

Campaign state: integration-v1's measurement phase closes here. The
suite, the gate, the ceiling probe and the baseline are standing
infrastructure; the green roads (hot-start distillation; the all-stage
oracle-BC generalist) are seeded in the ledger as the next unit-layer
campaigns — exactly the red→unit→re-integrate loop docs/TDD-FLIGHT.md
prescribes.

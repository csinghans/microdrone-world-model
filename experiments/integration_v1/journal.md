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

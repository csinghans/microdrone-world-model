# Flight TDD — unit tests, integration tests, and the deployment gate

The software-engineering loop, mapped onto flight research:

| software | this repo |
|---|---|
| unit test | a skill's exam cells with frozen bars (`skills/*`, pre-registered before any number — test-first by construction) |
| regression suite | the guard block every campaign re-flies (gap/mgap/cluttered/sweep) |
| **integration test** | a **randomly composed 3-stage course** flown end to end in ONE episode (`sim/composite.py` + `eval/eval_integration.py`) |
| CI gate | the **deployment gate**: integration success ≥ 0.70 at n = 100 random courses — the standing precondition for real-hardware deployment |
| build artifact of record | the LATEST passing integration flight, kept in-repo as two GIFs (drone FPV + simulator god view) + a provenance stamp (`docs/media/`) |

## The red–green loop

1. Run the integration suite (`python -m eval.eval_integration --suite
   30 --zip <policy>`). It reports the success rate against the gate
   and a **stage-break histogram** — which stage kills you.
2. Red at stage type X → open (or revisit) X's UNIT campaign: the
   normal pre-registered knob loop on that skill.
3. Re-run the integration suite. Repeat.
4. Gate passed at n=100 → `--video-seed <passing seed>` regenerates the
   videos of record; hardware deployment becomes eligible.

## Rules that keep it honest

- The integration verdict is composite-level (reach the final goal,
  never crash); per-stage diagnostics come from x-crossings only. The
  unit predicates stay in the unit layer (their time-aware forms read
  the absolute episode clock and would mis-score rebased stages).
- Courses are seed-drawn from the pool — never hand-picked. The video
  seed must come from a PASSING suite run.
- A new skill joins the pool only after its unit campaign has gated
  bars (no untested stage types).
- `PerStageExperts` (reads the course composition) is a privileged
  ceiling probe for pricing course flyability — never a contender.

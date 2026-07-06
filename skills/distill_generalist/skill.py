"""distill-generalist: one clone, every teacher — can the pot hold?

Pre-registration (written before any number exists). chain-distill
proved the mechanism on one world (96.7 % at the teacher's ceiling)
and left the crown vacant: the clone had only ever seen slalom
corridors, so the moving guard failed (47 %) and sweep read 15 %. The
generalist question: **can ONE supervised student hold five teachers'
worlds at once** — the chain AND the standard guard block? Full pass
would crown the catalog's first distilled champion (for the
corridor-slalom-v2 skill, whose crown five RL attempts left vacant).

Contrast pre-stated: this same day measured what MIXING does under RL
(dodgeball-v2: the majority economy erased the minority behavior).
Supervised mixing has no reward conflict — labels are per-state
consistent — so if the pot holds here, the interference story is
RL-specific; if the pot breaks, multi-task interference is deeper
than reward. Either verdict is a finding.

The frozen data recipe lives in `scripts/distill.py::GENERALIST`
(seeds 41000-45119, disjoint from every exam series):

| world | eps | speed | teacher (all measured) |
|---|---|---|---|
| slalom3_fixed | 300 | 1.0 | OracleWeave (0.97) |
| gap | 100 | 1.0 | OracleWeave |
| moving_gap | 200 | 1.0 | OracleTrack (probe: 27/30 = 0.90) |
| classic | 150 | 1.0 | general champion (measured stack) |
| solo | 120 | 2.0 | general champion (sweep@2.0 ~0-5 % crash) |

Manipulation checks, frozen: every teacher enters the pot only with a
measured record on its own world (table above); BC val top-1 >= 0.80
POOLED **and per-world** — a mixed pot must fit every teacher, not an
average of them. Below any floor -> the campaign closes without
flying that exam (representation verdict, not a flight verdict).

Knobs:

- K0 — zero_shot: the generalist BC zip. Hypothesis: supervised
  multi-task has no gradient war; one 576-input MLP holds five
  mappings; the chain survives the pot and the guards come with it.
- K1 — zero_shot RESERVE (step-arbitrated, never `run`): played ONLY
  if K0 holds the chain (slalom3@1.0 >= 0.70) with >= 1 guard still
  broken — then re-BC with the failing world's share x2 (one delta,
  data-side; minutes, not hours). If K0 loses the chain itself, the
  pot broke: close as supervised-interference measured, no re-mixing.

Frozen campaign signature. **Crown** = the full gate (chain bar + all
four guards). **Support** = chain holds (>= 0.70) — imitation's chain
survives dilution even if a guard lags. **Refuted** = slalom3@1.0
< 0.70: the pot costs the chain — supervised multi-task interference
is real at this capacity, recorded against the RL-mixing result.

Exam: corridor-slalom-v2 cells/criteria VERBATIM (eighth sitting;
bars frozen since the probe). Baseline: the chain-distill specialist
(96.7 % chain / gap 93 % / mgap 47 % / cluttered 92 % / sweep 85 %).
"""

from skills.base import Knob, Skill
from skills.corridor_slalom_v2.skill import SKILL as V2

_BC = "experiments/distill_generalist/artifacts/ppo_distill_generalist_BC.zip"
_BC2 = "experiments/distill_generalist/artifacts/ppo_distill_generalist_BC2.zip"

SKILL = Skill(
    name="distill-generalist",
    version="1",
    scenarios=dict(V2.scenarios),
    cells=V2.cells,  # the slalom-v2 exam, verbatim — eighth sitting
    criteria=V2.criteria,
    knobs=(
        Knob(
            "K0",
            "zero_shot",
            "the five-teacher generalist BC clone",
            "supervised multi-task has no gradient war: one student holds "
            "five mappings — the chain survives the pot, guards included",
            policy_path=_BC,
        ),
        Knob(
            "K1",
            "zero_shot",
            "RESERVE: re-BC with the failing world's share x2 (one delta)",
            "played ONLY if K0 holds the chain (>= 0.70) with >= 1 guard "
            "broken (step-arbitrated); if the chain itself broke, the pot "
            "broke — close, do not re-mix",
            policy_path=_BC2,
        ),
    ),
    max_knobs=3,  # one deviation slot, charter rationale required
    success=V2.success,
    episode_metrics=V2.episode_metrics,
)


def selftest() -> None:
    from scripts.distill import GENERALIST, TEACHERS
    from skills.base import load_skill
    from skills.corridor_slalom_v2 import skill as v2mod

    s = load_skill("distill-generalist")
    assert s.cells == V2.cells and s.criteria == V2.criteria
    assert s.success is v2mod.SKILL.success
    assert s.episode_metrics is v2mod.SKILL.episode_metrics
    assert all(k.kind == "zero_shot" for k in s.knobs)
    # the frozen recipe covers every guard family and stays off exam seeds
    worlds = [b[0] for b in GENERALIST]
    assert {"slalom3_fixed", "gap", "moving_gap", "classic", "solo"} == set(worlds)
    exam_seeds = {c.seed0 for c in s.cells}
    for _w, n, _sp, teacher, seed0 in GENERALIST:
        assert teacher in TEACHERS or teacher == "mgap"
        assert all(abs(seed0 - e) > 5000 for e in exam_seeds), "seed hygiene"
        assert n >= 100
    print(
        "DISTILL-GENERALIST OK: slalom-v2 exam verbatim (eighth sitting), "
        "five-teacher recipe frozen with seed hygiene, both knobs hand-built"
    )


if __name__ == "__main__":
    selftest()

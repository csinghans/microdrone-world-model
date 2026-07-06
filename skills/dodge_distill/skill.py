"""dodge-distill: does fast-ball information exist in the observation at all?

Pre-registration (written before any number exists). wm48-defense
refuted "window length" and left "signal quality at range" as the
fast-ball suspect. This campaign turns the question into a two-layer
meter, per ball speed:

  1. **Representation layer — BC val accuracy per speed world.** The
     teacher (OracleDodge, feasibility records 0.90/0.80/0.80/0.80)
     decides from privileged tracks; the student sees only the G1
     probability stack. If supervised fitting cannot reach 0.80 val on
     the v1.4/v1.8 worlds, the information provably is not in the
     observation — the wm48 suspect CONFIRMED at the representation
     level, and model-side supervision becomes the only road. Closes
     without flying those cells' hopes.
  2. **Closed-loop layer — the dodgeball exam, verbatim.** If the fast
     worlds FIT (val >= 0.80) but their cells still miss the bars, the
     failure is drift/timing, not representation — a different Tier-2
     than wm48 implied.

Recipe frozen in `scripts/distill.py::DODGE`: 200 episodes per ball
speed, each taught by its matched OracleDodge, seeds 51000-54199
(virgin). One pooled student; per-world val is the reading. Station
episodes run the full TMAX — "reached 0/N" in the collection print is
the expected shape, not a broken teacher.

Knobs:

- K0 — zero_shot: the dodge clone. Support = any fast cell (v1.4 or
  v1.8) >= its 0.55 bar. Slow cells read as context vs v1-K3
  (47 / 60 %).
- K1 — zero_shot RESERVE (step-arbitrated): station-reward PPO 450k on
  the clone (the surpass-teacher drift-repair leg, station economy).
  Played ONLY if some fast world FITS (val >= 0.80) while its cell
  misses the bar — the drift case. NOT played on a representation
  negative (nothing to repair), and NOT played to fix slow cells.
  bcft's lesson is pre-acknowledged: RL keeps only what it can learn —
  station-holding IS RL-learnable (dodgeball K3 proved it), so the
  erasure risk here is priced lower than bcft's chain.

Guards: structural failures expected (pure dodge diet; the clone never
transits). Promotion out of scope; the science cells are the four
dodge cells and the four val meters.

Frozen signature. **Support** = a fast cell over its bar (closed
loop). **Representation negative** = val < 0.80 on v1.4 AND v1.8 —
the observation cannot express the teacher's fast-ball policy;
campaign closes at the meter. **Drift verdict** = fast worlds fit but
cells miss → K1 arbitrates; if K1 also misses, the residue is
timing-at-execution, recorded as Tier-2's sharpest pointer yet.
"""

from skills.base import Knob, Skill
from skills.dodgeball.skill import SKILL as V1

_BC = "experiments/dodge_distill/artifacts/ppo_dodge_distill_BC.zip"
_FT = "experiments/dodge_distill/artifacts/ppo_dodge_distill_FT.zip"

SKILL = Skill(
    name="dodge-distill",
    version="1",
    scenarios=dict(V1.scenarios),
    cells=V1.cells,  # the dodgeball exam, verbatim — bars frozen at the probe
    criteria=V1.criteria,
    knobs=(
        Knob(
            "K0",
            "zero_shot",
            "the four-speed OracleDodge clone (pooled BC)",
            "per-speed val is the representation meter; the cells are the "
            "closed loop — the two layers separate wm48's live suspects",
            policy_path=_BC,
        ),
        Knob(
            "K1",
            "zero_shot",
            "RESERVE: station-reward PPO 450k on the clone (drift repair)",
            "played ONLY if a fast world fits (val >= 0.80) while its cell "
            "misses — the drift case; sheathed on a representation negative",
            policy_path=_FT,
        ),
    ),
    max_knobs=3,
    success=V1.success,
    episode_metrics=V1.episode_metrics,
)


def selftest() -> None:
    from scripts.distill import DODGE, TEACHERS
    from skills.base import load_skill
    from skills.dodgeball import skill as v1mod

    s = load_skill("dodge-distill")
    assert s.cells == V1.cells and s.criteria == V1.criteria
    assert s.success is v1mod.dodge_success
    assert s.episode_metrics is v1mod.dodge_metrics
    assert all(k.kind == "zero_shot" for k in s.knobs)
    # the frozen recipe pairs each speed world with its matched teacher
    for world, n, _sp, teacher, seed0 in DODGE:
        assert teacher in TEACHERS and world.split("_v")[1] in teacher
        assert n >= 200 and seed0 >= 51000, "virgin seed series"
    exam_seeds = {c.seed0 for c in s.cells}
    assert all(abs(b[4] - e) > 5000 for b in DODGE for e in exam_seeds)
    print(
        "DODGE-DISTILL OK: dodgeball exam verbatim, matched teachers per "
        "speed, virgin seeds, reserve step-gated on the drift condition"
    )


if __name__ == "__main__":
    selftest()

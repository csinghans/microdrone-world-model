"""corridor-slalom v2: the chaining question, with zero arena alibi.

Pre-registration (written before any number exists). v1 failed every
target and could not say whether the wall was the arena or the
policies. The feasibility probe (`experiments/slalom_feasibility/`)
settled it: at dx = 0.70, cruise, a scripted oracle using the SAME
action set flies the three-gate slalom at **97 %** — while v1's best
learned attempt managed 10 %. So v2 freezes the proven geometry
(dx = 0.70, x0 = 0.9 — v1's spacing, now with a priced ceiling) and
asks the question purely: **can training close a 97-vs-10 gap that has
no arena excuse?**

Bars come from the probe's frozen formula: the single priced target is
slalom3@1.0 ≥ **0.70** (oracle ceiling 0.97 − 0.25). The speed cells'
ceilings are under 0.55 at this spacing (7 %/0 %), so per the frozen
rule they carry **no bar** — slalom2@1.0 and slalom3@1.25 fly as
measured-only diagnostics (recorded, never judged; slalom2 was not
probed, so it gets no bar either — priced bars only).

Per-knob hypotheses (falsifiable, frozen now):

- K0 — v1's best trained artifact (its K2 zip), re-based on the fixed
  geometry with the pooling protocol: expect ≈ its v1 reading (≤10 %);
  this is the "before" of the before/after.
- K1 — fresh training, the fixed-dx slalom3 world in the v2-combination
  diet at 900 k: v1's mixed-dx training could never phase-lock to one
  spacing; a FIXED spacing is learnable rhythm. Expect a real jump;
  whether it clears 0.70 is exactly the open question.
- K2 (reserve, played only if K1 trends right but undershoots) — same
  mixture at 1350 k: v1 never tried the budget dial on this skill
  (its K3 doubled share instead and broke a guard); buy convergence,
  not new variables.

Guards: the standard catalog block (pooled rechecks per the 2026-07-05
protocol).
"""

import numpy as np

from skills.base import Criterion, EvalCell, Knob, Skill
from skills.corridor_slalom.skill import (
    slalom_metrics,
    slalom_success,
    spawn_slalom,
)
from skills.gap_flight.skill import spawn_gap
from skills.moving_gap.skill import spawn_moving_gap
from skills.moving_gap_v2.skill import spawn_solo

DX = 0.70  # frozen from the feasibility probe (oracle ceiling 0.97 @1.0)
X0 = 0.90


def _spawn_slalom3_fixed(env, rng, **kw):
    for k in ("n_fences", "dx", "x0"):
        kw.pop(k, None)
    return spawn_slalom(env, rng, n_fences=3, dx=DX, x0=X0, **kw)


def _spawn_slalom2_fixed(env, rng, **kw):
    for k in ("n_fences", "dx", "x0"):
        kw.pop(k, None)
    return spawn_slalom(env, rng, n_fences=2, dx=DX, x0=1.1, **kw)


_V1_BEST = "experiments/corridor_slalom/artifacts/ppo_corridor_slalom_K2.zip"
_V2_DIET = ("classic", "classic", "dense", "moving", "gap", "moving_gap", "solo")

SKILL = Skill(
    name="corridor-slalom-v2",
    version="2",
    scenarios={
        "slalom3_fixed": _spawn_slalom3_fixed,
        "slalom2_fixed": _spawn_slalom2_fixed,
        "gap": spawn_gap,
        "moving_gap": spawn_moving_gap,
        "solo": spawn_solo,
    },
    cells=(
        # the one priced target (oracle ceiling 0.97)
        EvalCell("slalom3@1.0", "slalom3_fixed", 1.0, 30, 22000),
        # measured-only diagnostics: no criteria reference them (unpriced
        # ceilings — slalom2 unprobed, slalom3@1.25 ceiling 0.07)
        EvalCell("diag:slalom2@1.0", "slalom2_fixed", 1.0, 30, 22000),
        EvalCell("diag:slalom3@1.25", "slalom3_fixed", 1.25, 30, 22000),
        EvalCell("guard:gap@1.0", "gap", 1.0, 30, 9000, {}, "guard"),
        EvalCell("guard:mgap@1.0", "moving_gap", 1.0, 30, 9500, {}, "guard"),
        EvalCell("guard:cluttered", None, 1.0, 60, 1000, {"in_path": True}, "guard"),
        EvalCell(
            "guard:sweep@2.0",
            None,
            2.0,
            60,
            3000,
            {"in_path": True, "solo": True},
            "guard",
        ),
    ),
    criteria=(
        Criterion("slalom3@1.0", "success", ">=", 0.70, "target"),
        Criterion("guard:gap@1.0", "success", ">=", 0.75, "guard"),
        Criterion("guard:mgap@1.0", "success", ">=", 0.70, "guard"),
        Criterion("guard:cluttered", "crash", "<=", 0.05, "guard"),
        Criterion("guard:sweep@2.0", "crash", "<=", 0.10, "guard"),
    ),
    knobs=(
        Knob(
            "K0",
            "zero_shot",
            "v1's best trained artifact, re-based on the fixed geometry",
            "the 'before': expect roughly its v1 reading (<=10 %) — mixed-dx "
            "training never phase-locked to one spacing",
            policy_path=_V1_BEST,
        ),
        Knob(
            "K1",
            "policy",
            "fresh training on the FIXED spacing (v2-combination diet, 900k)",
            "a fixed dx is a learnable rhythm; whether it closes 97-vs-10 is "
            "the whole question",
            train_kwargs=dict(
                worlds=_V2_DIET + ("slalom3_fixed",),
                x_progress=True,
                edge_bias=True,
                timesteps=900_000,
            ),
        ),
        Knob(
            "K2",
            "policy",
            "same mixture at 1350k",
            "reserve: v1 never tried the budget dial here (it doubled share "
            "and broke a guard) — buy convergence, not new variables",
            train_kwargs=dict(
                worlds=_V2_DIET + ("slalom3_fixed",),
                x_progress=True,
                edge_bias=True,
                timesteps=1_350_000,
            ),
        ),
    ),
    max_knobs=3,
    success=slalom_success,
    episode_metrics=slalom_metrics,
)


def selftest() -> None:
    # fixed geometry: every seed spawns dx=0.70 planes at x0=0.9
    for s in range(6):
        sc = _spawn_slalom3_fixed(None, np.random.default_rng(s))
        f = sc.meta["fences"]
        xs = [x for x, _yc, _w in f]
        assert len(f) == 3 and abs(xs[0] - X0) < 1e-9
        assert all(abs((b - a) - DX) < 1e-9 for a, b in zip(xs, xs[1:]))
        sides = [np.sign(yc) for _x, yc, _w in f]
        assert all(a == -b for a, b in zip(sides, sides[1:])), "must alternate"
    sc2 = _spawn_slalom2_fixed(None, np.random.default_rng(3))
    assert len(sc2.meta["fences"]) == 2
    # predicates are v1's, verbatim (v2 changes geometry pricing, not exams)
    from skills.base import load_skill

    s = load_skill("corridor-slalom-v2")
    assert s.name == "corridor-slalom-v2"
    assert s.success is slalom_success and s.episode_metrics is slalom_metrics
    # exactly one priced target; diagnostics carry no criteria
    targets = [c for c in s.criteria if c.kind == "target"]
    assert len(targets) == 1 and targets[0].cell == "slalom3@1.0"
    judged = {c.cell for c in s.criteria}
    assert "diag:slalom2@1.0" not in judged and "diag:slalom3@1.25" not in judged
    from sim.scenario_registry import get

    sc3 = get("slalom3_fixed").spawn(None, np.random.default_rng(5))
    sc4 = get("slalom3_fixed").spawn(None, np.random.default_rng(5))
    assert sc3.meta == sc4.meta, "registered spawn must reproduce per seed"
    print(
        f"CORRIDOR-SLALOM-V2 OK: geometry frozen from the probe (dx={DX}, "
        f"ceiling 0.97), one priced target, diagnostics unjudged, exam "
        f"predicates inherited verbatim"
    )


if __name__ == "__main__":
    selftest()

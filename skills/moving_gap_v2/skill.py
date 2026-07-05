"""moving-gap v2: pay the fast-solo tax with mixture SHAPE, not budget.

Lineage, honestly stated. v1 (`skills/moving_gap`) closed as "capability
yes, promotion no": every trained knob passed the timing targets, and
KD1 (the K1 five-world mixture at 900 k) healed every home-turf guard
except one — **sweep@2.0 confirmed at 17 % vs the ≤10 % bar (n=60)**,
with a *non-monotone* budget response (27/22/8/17 % across 450-900 k).
The budget dial has no measured control over that cell, so v2 attacks
what v1's own verdict pointed at: the **mixture shape**.

Two shape hypotheses, one per knob (single variable each, both on the
proven KD1 chassis — five worlds, x-progress, edge-bias, 900 k):

  * K1 — **classic ×2**: the home-turf tax is share starvation; restore
    classic from 20 % of episodes to 33 % and its fast band heals with it.
  * K2 — **an explicit solo world**: the failing cell is fast + solo
    geometry specifically; edge-bias already over-samples fast episodes,
    so putting a solo-pillar world in the diet aims that fast emphasis
    exactly where the guard bleeds.
  * K3 — the combination (classic ×2 + solo, seven worlds), played only
    if K1/K2 each move the fast cell without clearing it; its accepted
    risk (moving_gap share falls to ~14 %) is priced by v1's target
    headroom (80-97 %).

Two v1 lessons are baked into the bar design rather than re-learned:
the sweep@2.0 cell starts at **n=60** (its n=30 first reads — 27/22/8/17
— were nearly uninformative), and K0 re-measures the v1 best
(`ppo_moving_gap_KD1.zip`) under exactly these cells so the campaign's
baseline and its challengers share one measurement basis.

Scenario code, success predicates and metrics are imported from v1
verbatim — v2 changes the *diet*, never the exam.
"""

from sim.scenario_registry import StaticScenario
from skills.base import Criterion, EvalCell, Knob, Skill
from skills.moving_gap.skill import (
    mgap_metrics,
    mgap_success,
    spawn_gap,
    spawn_moving_gap,
)


def spawn_solo(env, rng, *, speed=1.0, randomize=False, in_path=True):
    """One in-path pillar, nothing else — the speed sweep's course as a
    trainable world. With edge-bias in the recipe, this puts fast-solo
    geometry (the bleeding guard cell) directly into the diet."""
    from sim.scenarios import spawn_pillars

    del speed, in_path
    return StaticScenario(
        spawn_pillars(env, rng, in_path=True, solo=True, randomize=randomize)
    )


_V1_BEST = "experiments/moving_gap/artifacts/ppo_moving_gap_KD1.zip"
_CHASSIS = dict(x_progress=True, edge_bias=True, timesteps=900_000)
_FIVE = ("classic", "dense", "moving", "gap", "moving_gap")

SKILL = Skill(
    name="moving-gap-v2",
    version="2",
    scenarios={
        "moving_gap": spawn_moving_gap,
        "gap": spawn_gap,
        "solo": spawn_solo,
    },
    cells=(
        EvalCell("mgap@1.0", "moving_gap", 1.0, 30, 9500),
        EvalCell("mgap@1.5", "moving_gap", 1.5, 30, 9500),
        EvalCell("guard:gap@1.0", "gap", 1.0, 30, 9000, {}, "guard"),
        EvalCell("guard:cluttered", None, 1.0, 60, 1000, {"in_path": True}, "guard"),
        EvalCell(
            "guard:sweep@1.0",
            None,
            1.0,
            30,
            3000,
            {"in_path": True, "solo": True},
            "guard",
        ),
        EvalCell(
            "guard:sweep@1.5",
            None,
            1.5,
            30,
            3000,
            {"in_path": True, "solo": True},
            "guard",
        ),
        # the v1 lesson: this cell's n=30 reads are noise — start at n=60
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
        Criterion("mgap@1.0", "success", ">=", 0.75, "target"),
        Criterion("mgap@1.5", "success", ">=", 0.60, "target"),
        Criterion("guard:gap@1.0", "success", ">=", 0.75, "guard"),
        Criterion("guard:cluttered", "crash", "<=", 0.05, "guard"),
        Criterion("guard:sweep@1.0", "crash", "<=", 0.05, "guard"),
        Criterion("guard:sweep@1.5", "crash", "<=", 0.10, "guard"),
        Criterion("guard:sweep@2.0", "crash", "<=", 0.10, "guard"),
    ),
    knobs=(
        Knob(
            "K0",
            "zero_shot",
            "the v1 best (KD1), re-measured on v2's cells",
            "one measurement basis for the whole campaign; expected: targets "
            "pass, sweep@2.0 lands near its confirmed 17 %",
            policy_path=_V1_BEST,
        ),
        Knob(
            "K1",
            "policy",
            "classic x2 on the KD1 chassis",
            "share starvation: classic fell from the champion diet's 25 % to "
            "20 %; restoring it to 33 % should heal its fast band with it",
            train_kwargs=dict(worlds=("classic",) + _FIVE, **_CHASSIS),
        ),
        Knob(
            "K2",
            "policy",
            "an explicit solo world on the KD1 chassis",
            "the bleeding cell is fast+solo geometry; edge-bias already "
            "over-samples fast, so a solo world aims it at the wound",
            train_kwargs=dict(worlds=_FIVE + ("solo",), **_CHASSIS),
        ),
        Knob(
            "K3",
            "policy",
            "classic x2 + solo (the combination)",
            "played only if K1/K2 each move the fast cell without clearing "
            "it; the mgap-share dilution risk is priced by v1's target "
            "headroom",
            train_kwargs=dict(worlds=("classic",) + _FIVE + ("solo",), **_CHASSIS),
        ),
    ),
    max_knobs=4,
    success=mgap_success,
    episode_metrics=mgap_metrics,
)


def selftest() -> None:
    import numpy as np

    from skills.base import load_skill

    s = load_skill("moving-gap-v2")
    assert s.name == "moving-gap-v2" and s.version == "2"
    # the v1 lesson must be in the bars: the noisy fast cell starts at n=60
    fast = [c for c in s.cells if c.id == "guard:sweep@2.0"][0]
    assert fast.n_seeds == 60, "sweep@2.0 must start at n=60 (the v1 lesson)"
    # every knob keeps the KD1 chassis; the only variable is the mixture
    for k in s.knobs[1:]:
        kw = k.train_kwargs
        assert kw["timesteps"] == 900_000 and kw["x_progress"] and kw["edge_bias"]
    assert s.knobs[1].train_kwargs["worlds"].count("classic") == 2
    assert "solo" in s.knobs[2].train_kwargs["worlds"]
    k3w = s.knobs[3].train_kwargs["worlds"]
    assert k3w.count("classic") == 2 and "solo" in k3w
    # the solo world spawns exactly one in-path pillar (needs a live env —
    # the training loop is its consumer, so the selftest pays for one)
    from sim.envs import make_env
    from sim.scenario_registry import get

    env = make_env()
    env.reset(seed=3)
    sc = get("solo").spawn(env, np.random.default_rng(3))
    pil = sc.positions()
    env.close()
    assert len(pil) == 1, "solo world must spawn exactly one pillar"
    assert 1.3 <= pil[0][0] <= 2.0 and abs(pil[0][1]) <= 0.2, "pillar not in path"
    assert sc.velocities() == [(0.0, 0.0)]
    # v2 changes the diet, never the exam: predicates are v1's, verbatim
    assert s.success is mgap_success and s.episode_metrics is mgap_metrics
    print(
        "MOVING-GAP-V2 OK: KD1 chassis frozen, mixture is the only variable "
        "(classic x2 / +solo / both), fast cell at n=60, exam unchanged"
    )


if __name__ == "__main__":
    selftest()

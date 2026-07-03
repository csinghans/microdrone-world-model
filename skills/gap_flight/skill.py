"""gap-flight: fly through a narrow gap in a fence, on vision alone.

The scenario is a **fence with one gap**: a line of pillars at x_gap with a
single opening (width w = 0.55-0.85 m edge-to-edge), outer pillars stepping
outward at 0.55 m spacing until |y| >= 2.2 — the 0.55 spacing leaves a
0.11 m channel (impassable at COLLISION_R 0.22), and the training corridor
truncates at |y| > 2.4, so the only rewarded route is the gap. Success is a
statement about the trajectory: reached AND not crashed AND **transited**
(the path crosses x_gap inside the opening).

The physics this skill actually probes: centred transit clearance is
w/2 − 0.04 = 0.235-0.385 m — inside the 0.7 m warn ring of BOTH gap pillars
but outside the 0.35 m critical ring. In-gap, the warn heads saturate and
only the crit heads carry gradient: this is the two-ring design's real
exam. Pre-registered expectation: the v0.3 champion fails K0 zero-shot
honestly (it was never asked to fly *toward* saturated warnings).

Reward: the default (progress/crash/goal) — attempting the gap at even 50 %
crash odds beats stopping, so the decision is already priced; adding a
gap-alignment term would violate the no-hand-tuned-danger-weights rule.
Reserve knobs (researcher may invoke with a written journal rationale):
KR-shaping ONLY if hover-collapse shows up (>30 % of training-cell episodes
truncating at the fence); K4 world-model retrain with gap rollouts
(requires MAX_PIL 8 -> 12 in datasets/generate_rollouts.py).
"""

from functools import partial

import numpy as np

from sim.scenario_registry import StaticScenario
from skills.base import Criterion, EvalCell, Knob, Skill

FENCE_SPACING = 0.55  # outer-pillar spacing: 0.11 m channel = impassable
FENCE_EDGE = 2.2  # fence extends until |y| >= this (corridor truncates 2.4)
PILLAR_R = 0.18


def spawn_gap(
    env, rng, *, speed=1.0, randomize=False, in_path=True, width_range=(0.55, 0.85)
):
    """The fence-with-one-gap scenario. meta carries the gap geometry."""
    del speed, randomize, in_path
    from sim.scenarios import _pillar_body

    x_gap = float(rng.uniform(1.5, 2.1))
    yc = float(rng.uniform(-0.3, 0.3))
    w = float(rng.uniform(*width_range))
    half = (w + 2 * PILLAR_R) / 2.0  # gap-pillar centre offset from yc
    ys = [yc - half, yc + half]
    y = yc - half
    while y > -FENCE_EDGE:
        y -= FENCE_SPACING
        ys.append(y)
    y = yc + half
    while y < FENCE_EDGE:
        y += FENCE_SPACING
        ys.append(y)
    pillars = [(x_gap, float(yy)) for yy in sorted(ys)]
    if env is not None:  # selftest geometry checks run env-free
        for px, py in pillars:
            _pillar_body(env, px, py)
    return StaticScenario(pillars, meta={"x_gap": x_gap, "yc": yc, "w": w})


def _crossing_y(path: np.ndarray, x_gap: float):
    """y at the first crossing of the fence plane, or None."""
    xs = path[:, 0]
    for i in range(len(xs) - 1):
        if xs[i] < x_gap <= xs[i + 1]:
            f = (x_gap - xs[i]) / max(xs[i + 1] - xs[i], 1e-9)
            return float(path[i, 1] + f * (path[i + 1, 1] - path[i, 1]))
    return None


def gap_metrics(ep: dict) -> dict:
    meta = ep.get("scenario_meta", {})
    if "x_gap" not in meta:
        return {}
    half = (meta["w"] + 2 * PILLAR_R) / 2.0
    y_cross = _crossing_y(ep["path"], meta["x_gap"])
    transited = y_cross is not None and abs(y_cross - meta["yc"]) < half
    # edge margin: distance from the crossing point to the nearer gap pillar
    margin = half - abs(y_cross - meta["yc"]) - PILLAR_R if transited else 0.0
    return {"transited": float(transited), "gap_margin": float(max(margin, 0.0))}


def gap_success(ep: dict) -> bool:
    m = gap_metrics(ep)
    return bool(ep["reached"] and not ep["crashed"] and m.get("transited"))


_CHAMPION = "output/ppo_wm_policy_edge_hard_xp.zip"
_BASE_WORLDS = ("classic", "dense", "moving")

SKILL = Skill(
    name="gap-flight",
    version="1",
    scenarios={
        "gap": spawn_gap,
        "gap_narrow": partial(spawn_gap, width_range=(0.55, 0.65)),
    },
    cells=(
        EvalCell("gap@1.0", "gap", 1.0, 30, 9000),
        EvalCell("gap@1.5", "gap", 1.5, 30, 9000),
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
        EvalCell(
            "guard:sweep@2.0",
            None,
            2.0,
            30,
            3000,
            {"in_path": True, "solo": True},
            "guard",
        ),
    ),
    criteria=(
        Criterion("gap@1.0", "success", ">=", 0.85, "target"),
        Criterion("gap@1.5", "success", ">=", 0.70, "target"),
        Criterion("guard:cluttered", "crash", "<=", 0.05, "guard"),
        Criterion("guard:sweep@1.0", "crash", "<=", 0.05, "guard"),
        Criterion("guard:sweep@1.5", "crash", "<=", 0.10, "guard"),
        Criterion("guard:sweep@2.0", "crash", "<=", 0.10, "guard"),
    ),
    knobs=(
        Knob(
            "K0",
            "zero_shot",
            "the v0.3 champion, zero-shot on the gap",
            "expected honest failure: it was never asked to fly toward "
            "saturated warn rings",
            policy_path=_CHAMPION,
        ),
        Knob(
            "K1",
            "policy",
            "gap joins the hard diet",
            "seeing the fence in training teaches crit-ring-guided transit",
            train_kwargs=dict(
                worlds=_BASE_WORLDS + ("gap",),
                x_progress=True,
                edge_bias=True,
                timesteps=300_000,
            ),
        ),
        Knob(
            "K2",
            "policy",
            "gap-weighted diet (2x)",
            "if K1 undertrains the gap cell, double its episode share",
            train_kwargs=dict(
                worlds=_BASE_WORLDS + ("gap", "gap"),
                x_progress=True,
                edge_bias=True,
                timesteps=300_000,
            ),
        ),
        Knob(
            "K3",
            "policy",
            "narrow-gap emphasis",
            "train on the hard end of the width range to buy margin",
            train_kwargs=dict(
                worlds=_BASE_WORLDS + ("gap", "gap_narrow"),
                x_progress=True,
                edge_bias=True,
                timesteps=300_000,
            ),
        ),
    ),
    max_knobs=4,
    success=gap_success,
    episode_metrics=gap_metrics,
)


def selftest() -> None:
    rng = np.random.default_rng(7)
    sc = spawn_gap(None, rng)  # env-free geometry check
    ys = sorted(q[1] for q in sc.pillars)
    meta = sc.meta
    half = (meta["w"] + 2 * PILLAR_R) / 2.0
    gaps = [b - a for a, b in zip(ys, ys[1:])]
    wide = [g for g in gaps if g > FENCE_SPACING + 1e-6]
    assert len(wide) == 1 and abs(wide[0] - 2 * half) < 1e-6, "exactly one gap"
    assert ys[0] <= -FENCE_EDGE and ys[-1] >= FENCE_EDGE, "fence too short"
    assert meta["w"] / 2 - 0.04 >= 0.23, "channel physically too tight"
    # synthetic paths: straight through the gap vs around the fence
    through = np.array([[0, meta["yc"], 1.0], [3.0, meta["yc"], 1.0]])
    around = np.array([[0, 0, 1.0], [1.0, 2.5, 1.0], [3.0, 2.5, 1.0]])
    ep_t = {"path": through, "scenario_meta": meta, "reached": True, "crashed": False}
    ep_a = {"path": around, "scenario_meta": meta, "reached": True, "crashed": False}
    assert gap_success(ep_t) and gap_metrics(ep_t)["gap_margin"] > 0.2
    assert not gap_success(ep_a), "around-the-fence must not count"
    from skills.base import load_skill

    s = load_skill("gap-flight")
    from sim.scenario_registry import get

    # identity check would fail under `python -m` (double import); the
    # behavioral contract is what matters: same name, same geometry per seed
    assert s.name == "gap-flight"
    sc2 = get("gap").spawn(None, np.random.default_rng(7))
    assert sc2.meta == meta, "registered spawn must reproduce the geometry"
    print(
        f"GAP-FLIGHT-SKILL OK: one gap (w={meta['w']:.2f} m), fence to "
        f"|y|>={FENCE_EDGE}, through=success / around=fail, registry round-trip"
    )


if __name__ == "__main__":
    selftest()

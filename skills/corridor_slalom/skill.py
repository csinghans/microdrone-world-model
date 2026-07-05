"""corridor-slalom: sustained weaving — does evasion CHAIN?

Pre-registration (written before any number exists). Every passed skill
so far threads ONE opening. This one asks whether the dodge *chains*:
a corridor of 2 or 3 sequential fences whose gaps alternate sides
(left-right-left), so each transit sets up the next from the wrong side
of the corridor. The physics that makes it a real question: at cruise,
the lateral swing between consecutive gaps (~0.4-0.55 m in ~0.9 s)
sits near the veer authority's edge — a policy must *begin* each dodge
before the previous one has finished paying out. An open arena would
let a single wide sidestep bypass everything, so the slalom is built
from full fence walls (the gap machinery's around-route seal), and
success is trajectory-level: reached, clean, AND every fence crossed
inside its gap. `weave_frac` and `chain_break_at` (index of the first
missed fence) turn "where does the chain snap" into a printed number.

Design math, recorded (v2 of it — the first draft's soul-assert caught
generous gaps overlapping into a straight-line solution, which would
have measured nothing): consecutive gates force a reversal iff their
crash-legal bands are disjoint, i.e. off > w/2 − (COLLISION_R −
PILLAR_R) = w/2 − 0.04. Width is therefore sampled in gap-flight's
proven 0.55-0.62 band and the offset is COUPLED to it (off = w/2 − 0.04
+ U(0.02, 0.10)), giving every seed a 0.02-0.10 m disjointness margin —
asserted numerically in the selftest, not assumed. Swing between gates
≈ 2·off ≈ 0.56-0.74 m over 0.7-0.8 m of corridor; N=3 fills it
(x ≈ 0.9/1.6/2.3), N=4 cannot fit feasibly before the goal line, so the
curve axis is N ∈ {2, 3}. Cells recheck-pool per the 2026-07-05
protocol.

Per-knob hypotheses (falsifiable, frozen now):

- K0 general champion (edge_hard_xp) — trained to dodge *past* things,
  never to re-enter the corridor for a next gate: expect it to clear
  slalom2 marginally and snap early on slalom3
  (chain_break_at ≈ 1-2), or detour around and be caught by `weaved`.
- K1 moving-gap v2 champion — each fence is literally its home skill,
  but chained and alternating: expect the best zero-shot line, passing
  slalom2, degrading on slalom3's third gate (the second direction
  reversal is the new thing).
- K2 (training) — slalom3 joins the v2-combination diet at 900 k:
  the chain becomes a trained behaviour.
- K3 (training, played only if K2 trends right but undershoots) —
  double slalom share: rhythm needs reps, not new variables.

Bars (frozen at v1): slalom2@1.0 ≥ 0.70, slalom3@1.0 ≥ 0.55,
slalom3@1.5 ≥ 0.40 — speed makes the swing window shrink linearly, and
0.40 already demands two direction reversals at 1.2 m/s. Guards: the
standard catalog block.
"""

import numpy as np

from sim.scenario_registry import StaticScenario
from skills.base import Criterion, EvalCell, Knob, Skill
from skills.gap_flight.skill import (
    FENCE_EDGE,
    FENCE_SPACING,
    PILLAR_R,
    _crossing_y,
    gap_metrics,
    gap_success,
    spawn_gap,
)
from skills.moving_gap.skill import (
    mgap_metrics,
    mgap_success,
    spawn_moving_gap,
)
from skills.moving_gap_v2.skill import spawn_solo

W_RANGE = (0.55, 0.62)  # gap width — gap-flight's proven band
DX_RANGE = (0.70, 0.80)  # fence-to-fence spacing
_TRIM = 0.22 - 0.18  # COLLISION_R - PILLAR_R: the crash-legal band trim
# forced weave iff consecutive gates' crash-legal bands are disjoint:
# off > w/2 - _TRIM. Offsets are coupled to the sampled width so every
# seed carries a 0.02-0.10 disjointness margin (asserted in selftest).
OFF_MARGIN = (0.02, 0.10)


def _fence_ys(yc: float, w: float) -> list:
    """One fence's pillar y-centres: the gap pair + outer walls to the
    corridor edge (the gap-flight seal, reused)."""
    half = (w + 2 * PILLAR_R) / 2.0
    ys = [yc - half, yc + half]
    y = yc - half
    while y > -FENCE_EDGE:
        y -= FENCE_SPACING
        ys.append(y)
    y = yc + half
    while y < FENCE_EDGE:
        y += FENCE_SPACING
        ys.append(y)
    return ys


def spawn_slalom(
    env,
    rng,
    *,
    speed=1.0,
    randomize=False,
    in_path=True,
    n_fences=3,
    dx=None,
    x0=None,
):
    """N sequential fences, gaps alternating sides. meta carries the
    fence list [(x, yc, w), ...] the weave predicate needs. `dx`/`x0`
    override the v1 bands for the feasibility probe (defaults keep v1
    semantics bit-for-bit — the skill's frozen cells never pass them)."""
    del speed, randomize, in_path
    side = 1.0 if rng.random() < 0.5 else -1.0
    dx = float(rng.uniform(*DX_RANGE)) if dx is None else float(dx)
    if x0 is None:
        x0 = 0.9 if n_fences >= 3 else 1.1
    x0 = float(x0)
    fences, pillars = [], []
    for i in range(n_fences):
        x = x0 + i * dx
        w = float(rng.uniform(*W_RANGE))
        off = w / 2.0 - _TRIM + float(rng.uniform(*OFF_MARGIN))
        yc = side * ((-1.0) ** i) * off
        fences.append((float(x), float(yc), float(w)))
        pillars += [(float(x), float(yy)) for yy in _fence_ys(yc, w)]
    if env is not None:  # selftest geometry checks run env-free
        from sim.scenarios import _pillar_body

        for px, py in pillars:
            _pillar_body(env, px, py)
    return StaticScenario(pillars, meta={"fences": fences})


def slalom_metrics(ep: dict) -> dict:
    """Dispatch per cell meta ('fences' -> slalom; 'vy' -> moving-gap
    guard; bare 'x_gap' -> static gap guard; else generic)."""
    meta = ep.get("scenario_meta", {})
    if "fences" not in meta:
        if "vy" in meta:
            return mgap_metrics(ep)
        return gap_metrics(ep) if "x_gap" in meta else {}
    n = len(meta["fences"])
    threaded, break_at = 0, -1
    for i, (x, yc, w) in enumerate(meta["fences"]):
        half = (w + 2 * PILLAR_R) / 2.0
        y = _crossing_y(ep["path"], x)
        if y is not None and abs(y - yc) < half:
            threaded += 1
        elif break_at < 0:
            break_at = i
    weaved = threaded == n and ep["reached"] and not ep["crashed"]
    return {
        "weaved": float(weaved),
        "weave_frac": threaded / n,
        # where the chain snaps (mean over episodes reads as a position);
        # n means "never" so clean runs don't drag the average to zero
        "chain_break_at": float(break_at if break_at >= 0 else n),
    }


def slalom_success(ep: dict) -> bool:
    meta = ep.get("scenario_meta", {})
    if "fences" in meta:
        return bool(slalom_metrics(ep).get("weaved"))
    if "vy" in meta:
        return mgap_success(ep)
    if "x_gap" in meta:
        return gap_success(ep)
    return bool(ep["reached"] and not ep["crashed"])


def _spawn_slalom2(env, rng, **kw):
    kw.pop("n_fences", None)
    return spawn_slalom(env, rng, n_fences=2, **kw)


def _spawn_slalom3(env, rng, **kw):
    kw.pop("n_fences", None)
    return spawn_slalom(env, rng, n_fences=3, **kw)


_GENERAL = "output/ppo_wm_policy_edge_hard_xp.zip"
_MGAP = "experiments/moving_gap_v2/artifacts/ppo_moving_gap_v2_K3.zip"
_V2_DIET = ("classic", "classic", "dense", "moving", "gap", "moving_gap", "solo")

SKILL = Skill(
    name="corridor-slalom",
    version="1",
    scenarios={
        "slalom2": _spawn_slalom2,
        "slalom3": _spawn_slalom3,
        "gap": spawn_gap,
        "moving_gap": spawn_moving_gap,
        "solo": spawn_solo,  # K2/K3 diets train on it
    },
    cells=(
        EvalCell("slalom2@1.0", "slalom2", 1.0, 30, 21000),
        EvalCell("slalom3@1.0", "slalom3", 1.0, 30, 21000),
        EvalCell("slalom3@1.5", "slalom3", 1.5, 30, 21000),
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
        Criterion("slalom2@1.0", "success", ">=", 0.70, "target"),
        Criterion("slalom3@1.0", "success", ">=", 0.55, "target"),
        Criterion("slalom3@1.5", "success", ">=", 0.40, "target"),
        Criterion("guard:gap@1.0", "success", ">=", 0.75, "guard"),
        Criterion("guard:mgap@1.0", "success", ">=", 0.70, "guard"),
        Criterion("guard:cluttered", "crash", "<=", 0.05, "guard"),
        Criterion("guard:sweep@2.0", "crash", "<=", 0.10, "guard"),
    ),
    knobs=(
        Knob(
            "K0",
            "zero_shot",
            "the general champion on the slalom",
            "trained to dodge PAST things, never to re-enter for a next "
            "gate: expect slalom2 marginal, slalom3 snapping at gate 1-2, "
            "or a detour caught by `weaved`",
            policy_path=_GENERAL,
        ),
        Knob(
            "K1",
            "zero_shot",
            "the moving-gap v2 champion — its home skill, chained",
            "each fence alone is a solved problem; the second direction "
            "reversal is the new thing — expect best zero-shot, degrading "
            "on slalom3's third gate",
            policy_path=_MGAP,
        ),
        Knob(
            "K2",
            "policy",
            "slalom3 joins the v2-combination diet",
            "the chain becomes a trained behaviour (single variable: the "
            "new world in the proven chassis)",
            train_kwargs=dict(
                worlds=_V2_DIET + ("slalom3",),
                x_progress=True,
                edge_bias=True,
                timesteps=900_000,
            ),
        ),
        Knob(
            "K3",
            "policy",
            "double slalom share",
            "played only if K2 trends right but undershoots: rhythm needs "
            "reps, not new variables",
            train_kwargs=dict(
                worlds=_V2_DIET + ("slalom3", "slalom3"),
                x_progress=True,
                edge_bias=True,
                timesteps=900_000,
            ),
        ),
    ),
    max_knobs=4,
    success=slalom_success,
    episode_metrics=slalom_metrics,
)


def selftest() -> None:
    # geometry: N fences, alternating gap sides, corridor sealed, room to
    # finish — and the arena's THEOREM: consecutive gates' crash-legal
    # bands are disjoint on every seed (no straight line solves a slalom)
    for s in range(8):
        for n in (2, 3):
            sc = spawn_slalom(None, np.random.default_rng(s), n_fences=n)
            f = sc.meta["fences"]
            assert len(f) == n
            sides = [np.sign(yc) for _x, yc, _w in f]
            assert all(a == -b for a, b in zip(sides, sides[1:])), "must alternate"
            assert f[-1][0] <= 2.55, "last fence must leave room to reach goal"
            xs = sorted({round(q[0], 3) for q in sc.pillars})
            assert len(xs) == n, "each fence lives on one plane"
            for x, yc, w in f:
                ys = sorted(q[1] for q in sc.pillars if abs(q[0] - x) < 1e-6)
                assert ys[0] <= -FENCE_EDGE and ys[-1] >= FENCE_EDGE, "sealed"
            bands = [
                (yc - (w + 2 * PILLAR_R) / 2 + 0.22, yc + (w + 2 * PILLAR_R) / 2 - 0.22)
                for _x, yc, w in f
            ]
            for (lo1, hi1), (lo2, hi2) in zip(bands, bands[1:]):
                assert hi2 < lo1 or hi1 < lo2, "a straight line must not exist"
    # the soul: a zigzag that threads every alternating gap succeeds; a
    # straight line and a one-side line snap the chain and fail
    meta = {"fences": [(1.0, 0.30, 0.60), (1.7, -0.30, 0.60), (2.4, 0.30, 0.60)]}
    zig = np.array(
        [
            [0.0, 0.0, 1.0],
            [1.0, 0.30, 1.0],
            [1.7, -0.30, 1.0],
            [2.4, 0.30, 1.0],
            [3.0, 0.0, 1.0],
        ]
    )
    straight = np.array([[0.0, 0.9, 1.0], [3.0, 0.9, 1.0]])  # cruises the wall line
    one_side = np.array([[0.0, 0.30, 1.0], [3.0, 0.30, 1.0]])  # never reverses
    ep = {"scenario_meta": meta, "reached": True, "crashed": False}
    assert slalom_success({**ep, "path": zig}), "the weave must succeed"
    m_zig = slalom_metrics({**ep, "path": zig})
    assert m_zig["weave_frac"] == 1.0 and m_zig["chain_break_at"] == 3.0
    assert not slalom_success({**ep, "path": straight}), "wall-hugging must fail"
    m_one = slalom_metrics({**ep, "path": one_side})
    assert not slalom_success({**ep, "path": one_side}), "no reversal = no weave"
    assert m_one["chain_break_at"] == 1.0, "the snap point must be legible"
    # dispatch: guard cells keep their own skills' predicates
    g = {
        "scenario_meta": {"x_gap": 2.0, "yc": 0.0, "w": 0.7},
        "reached": True,
        "crashed": False,
        "path": np.array([[0.0, 0.0, 1.0], [3.0, 0.0, 1.0]]),
    }
    assert slalom_success(g), "static-gap guard must ride gap-flight rules"
    from skills.base import load_skill

    s = load_skill("corridor-slalom")
    assert s.name == "corridor-slalom"
    from sim.scenario_registry import get

    sc2 = get("slalom3").spawn(None, np.random.default_rng(5))
    sc3 = get("slalom3").spawn(None, np.random.default_rng(5))
    assert sc2.meta == sc3.meta, "registered spawn must reproduce per seed"
    print(
        f"CORRIDOR-SLALOM-SKILL OK: alternating sealed gates (w {W_RANGE}, "
        f"dx {DX_RANGE}), no-straight-line theorem asserted, zigzag=success "
        f"straight/one-side=fail with a legible snap point, registry round-trip"
    )


if __name__ == "__main__":
    selftest()

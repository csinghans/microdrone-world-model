"""moving-gap: transit a gap that is sliding sideways, on vision alone.

The scenario is the gap-flight fence **in lateral motion**: the whole
fence (gap included) slides at vy in [0.15, 0.35] m/s, aimed so the gap
centre sweeps past the corridor centreline around the drone's arrival
time (the MovingCrosser convention — an unaimed mover misses on most
seeds and measures nothing). Success is a statement about *time*, not
just the trajectory: the path must cross the fence plane inside the gap
**where the gap is at the crossing instant**. A policy that flies to
where the gap *was* at first sight fails by exactly the displacement
accumulated during its approach (0.2-0.8 m — up to a full gap width).

What this skill probes that gap-flight could not: the two capabilities
already measured separately — crit-ring-guided transit (gap-flight,
87-90 %) and motion anticipation (the hard diet's moving world, 13/7 %
crash) — composed into one decision: *aim at the future opening*. The
fence extends to |y| >= 3.2 on both sides so the around-route stays
sealed for the whole transit window despite the slide.

Pre-registered expectation: the gap-flight champion fails K0 zero-shot
honestly — its diet never contained a moving fence, and the static-
future assumption puts it at the wrong y by roughly vy x approach-time.

Reward: the default, same argument as gap-flight (the transit is already
priced; hand-tuned aim terms are against house rules).
"""

from functools import partial

import numpy as np

from sim.envs import CTRL_HZ
from skills.base import Criterion, EvalCell, Knob, Skill
from skills.gap_flight.skill import (
    FENCE_SPACING,
    PILLAR_R,
    gap_metrics,
    gap_success,
    spawn_gap,
)

MG_EDGE = 3.2  # fence coverage (static gap uses 2.2; the slide needs margin)
VY_RANGE = (0.15, 0.35)  # fence lateral speed band (m/s)


class MovingGapFence:
    """The whole gap-flight fence, translating laterally as one body.

    `positions()`/`velocities()`/`step()` follow the Scenario protocol;
    every pillar carries the same vy (the label oracle extrapolates them
    coherently). meta carries the *initial* gap geometry + vy — success
    predicates reconstruct the gap's position at any path instant."""

    def __init__(self, env, rng, *, speed=1.0, width_range=(0.55, 0.85)):
        import pybullet as p

        x_gap = float(rng.uniform(1.5, 2.1))
        w = float(rng.uniform(*width_range))
        half = (w + 2 * PILLAR_R) / 2.0
        # aim: the gap centre reaches yc_hit (near the centreline) at the
        # drone's expected arrival, with the crosser's 0.75-1.25 jitter so
        # the encounter is sometimes early, sometimes late
        cruise = 0.8 * float(speed)
        t_arr = x_gap / max(cruise, 1e-6)
        yc_hit = float(rng.uniform(-0.3, 0.3))
        side = 1.0 if rng.random() < 0.5 else -1.0
        vy = side * float(rng.uniform(*VY_RANGE))
        yc0 = yc_hit - vy * t_arr * float(rng.uniform(0.75, 1.25))
        ys = [yc0 - half, yc0 + half]
        y = yc0 - half
        while y > -MG_EDGE:
            y -= FENCE_SPACING
            ys.append(y)
        y = yc0 + half
        while y < MG_EDGE:
            y += FENCE_SPACING
            ys.append(y)
        self.x_gap, self.vy, self.dy = x_gap, vy, 0.0
        self.ys0 = sorted(float(v) for v in ys)
        self.meta = {"x_gap": x_gap, "yc0": yc0, "vy": vy, "w": w}
        self._p, self.env, self.bodies = p, env, []
        if env is not None:  # selftest geometry checks run env-free
            from sim.scenarios import _pillar_body

            self.dt = env.CTRL_TIMESTEP
            self.bodies = [_pillar_body(env, x_gap, yy) for yy in self.ys0]
        else:
            self.dt = 1.0 / CTRL_HZ

    def positions(self) -> list:
        return [(self.x_gap, yy + self.dy) for yy in self.ys0]

    def velocities(self) -> list:
        return [(0.0, self.vy)] * len(self.ys0)

    def step(self) -> None:
        self.dy += self.vy * self.dt
        for body, yy in zip(self.bodies, self.ys0):
            self._p.resetBasePositionAndOrientation(
                body,
                [self.x_gap, yy + self.dy, 0.7],
                [0, 0, 0, 1],
                physicsClientId=self.env.CLIENT,
            )


def spawn_moving_gap(
    env, rng, *, speed=1.0, randomize=False, in_path=True, width_range=(0.55, 0.85)
):
    del randomize, in_path
    return MovingGapFence(env, rng, speed=speed, width_range=width_range)


def _crossing_yt(path: np.ndarray, x_gap: float):
    """(y, t_seconds) at the first crossing of the fence plane, or None.
    The path is recorded once per control step, so the fractional index IS
    the clock — the gap's position at that instant is yc0 + vy*t."""
    xs = path[:, 0]
    for i in range(len(xs) - 1):
        if xs[i] < x_gap <= xs[i + 1]:
            f = (x_gap - xs[i]) / max(xs[i + 1] - xs[i], 1e-9)
            y = float(path[i, 1] + f * (path[i + 1, 1] - path[i, 1]))
            return y, (i + f) / CTRL_HZ
    return None


def mgap_metrics(ep: dict) -> dict:
    """Per-cell dispatch on the scenario meta: sliding fences get the
    time-aware transit, the static-gap guard keeps gap-flight's own
    metrics, generic guard cells contribute none."""
    meta = ep.get("scenario_meta", {})
    if "vy" not in meta:
        return gap_metrics(ep) if "x_gap" in meta else {}
    half = (meta["w"] + 2 * PILLAR_R) / 2.0
    cross = _crossing_yt(ep["path"], meta["x_gap"])
    if cross is None:
        return {"transited": 0.0, "gap_margin": 0.0}
    y, t = cross
    yc_now = meta["yc0"] + meta["vy"] * t  # where the gap IS, not was
    transited = abs(y - yc_now) < half
    margin = half - abs(y - yc_now) - PILLAR_R if transited else 0.0
    return {"transited": float(transited), "gap_margin": float(max(margin, 0.0))}


def mgap_success(ep: dict) -> bool:
    """success must answer for EVERY cell the skill declares (the runner
    applies one predicate per skill): time-aware transit on sliding
    fences, gap-flight's predicate on the static-gap guard, plain
    reached-and-clean on generic guard cells."""
    meta = ep.get("scenario_meta", {})
    if "vy" in meta:
        m = mgap_metrics(ep)
        return bool(ep["reached"] and not ep["crashed"] and m.get("transited"))
    if "x_gap" in meta:
        return gap_success(ep)
    return bool(ep["reached"] and not ep["crashed"])


_GAP_CHAMPION = "experiments/gap_flight/artifacts/ppo_gap_flight_KD1.zip"
_BASE = ("classic", "dense", "moving", "gap")

SKILL = Skill(
    name="moving-gap",
    version="1",
    scenarios={
        "moving_gap": spawn_moving_gap,
        # referenced by cells/knobs; re-registering an existing name is fine
        "gap": spawn_gap,
        "gap_narrow": partial(spawn_gap, width_range=(0.55, 0.65)),
    },
    cells=(
        EvalCell("mgap@1.0", "moving_gap", 1.0, 30, 9500),
        EvalCell("mgap@1.5", "moving_gap", 1.5, 30, 9500),
        # the catalog discipline: the new specialist must keep the old skill
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
            "the gap-flight champion, zero-shot on the sliding fence",
            "expected honest failure: its diet never moved a fence — the "
            "static-future assumption misses by vy x approach-time",
            policy_path=_GAP_CHAMPION,
        ),
        Knob(
            "K1",
            "policy",
            "moving_gap joins the gap champion's diet, at KD1's budget",
            "five worlds dilute harder than the four that already needed "
            "1.5x (the KD1 lesson) — schedule 450k from the start",
            train_kwargs=dict(
                worlds=_BASE + ("moving_gap",),
                x_progress=True,
                edge_bias=True,
                timesteps=450_000,
            ),
        ),
        Knob(
            "K2",
            "policy",
            "moving_gap double share",
            "if K1 undertrains the timing cell, double its episode share",
            train_kwargs=dict(
                worlds=_BASE + ("moving_gap", "moving_gap"),
                x_progress=True,
                edge_bias=True,
                timesteps=450_000,
            ),
        ),
        Knob(
            "K3",
            "policy",
            "K2's mixture at 600k",
            "budget knob: if the double share trends right but undershoots, "
            "buy convergence, not new variables",
            train_kwargs=dict(
                worlds=_BASE + ("moving_gap", "moving_gap"),
                x_progress=True,
                edge_bias=True,
                timesteps=600_000,
            ),
        ),
    ),
    max_knobs=4,
    success=mgap_success,
    episode_metrics=mgap_metrics,
)


def selftest() -> None:
    rng = np.random.default_rng(11)
    # geometry + aiming: across seeds, the gap centre must sweep close to
    # the centreline around arrival time (the aimed-encounter contract)
    for s in range(8):
        sc = spawn_moving_gap(None, np.random.default_rng(s), speed=1.0)
        m = sc.meta
        ys = sorted(q[1] for q in sc.positions())
        gaps = [b - a for a, b in zip(ys, ys[1:])]
        wide = [g for g in gaps if g > FENCE_SPACING + 1e-6]
        assert len(wide) == 1, "exactly one gap"
        assert ys[0] <= -MG_EDGE and ys[-1] >= MG_EDGE, "slide margin too thin"
        t_arr = m["x_gap"] / 0.8
        assert abs(m["yc0"] + m["vy"] * t_arr) < 0.6, "encounter not aimed"
    # the whole fence must move coherently, and velocities must say so
    sc = spawn_moving_gap(None, rng, speed=1.0)
    y_before = [q[1] for q in sc.positions()]
    for _ in range(48):
        sc.step()
    dy = [b - a for a, b in zip(y_before, (q[1] for q in sc.positions()))]
    assert all(abs(d - sc.vy) < 1e-6 for d in dy), "fence must slide as one"
    assert sc.velocities()[0] == (0.0, sc.vy)
    # the skill's whole point, as a predicate assert: a fence that slid
    # 0.6 m by t=2 s — flying through where the gap IS succeeds, flying
    # through where it WAS at t=0 fails
    meta = {"x_gap": 2.0, "yc0": 0.6, "vy": -0.3, "w": 0.7}
    # ~2 s on the clock before crossing; each path holds its aim y the whole
    # way so the interpolated crossing y IS the aim point
    now = np.array([[0.0, 0.0, 1.0]] * 96 + [[2.5, 0.0, 1.0]])  # yc(2s) = 0.0
    was = np.array([[0.0, 0.6, 1.0]] * 96 + [[2.5, 0.6, 1.0]])  # yc(0s) = 0.6
    ep_now = {"path": now, "scenario_meta": meta, "reached": True, "crashed": False}
    ep_was = {"path": was, "scenario_meta": meta, "reached": True, "crashed": False}
    assert mgap_success(ep_now), "aiming at the future gap must succeed"
    assert not mgap_success(ep_was), "the static-future assumption must fail"
    # per-cell dispatch: the static-gap guard rides gap-flight's predicate,
    # generic guard cells succeed on reached-and-clean
    static_meta = {"x_gap": 2.0, "yc": 0.0, "w": 0.7}
    ep_static = {
        "path": np.array([[0, 0, 1.0], [3.0, 0, 1.0]]),
        "scenario_meta": static_meta,
        "reached": True,
        "crashed": False,
    }
    assert mgap_success(ep_static), "static-gap guard must use gap-flight rules"
    ep_plain = {"path": now, "scenario_meta": {}, "reached": True, "crashed": False}
    assert mgap_success(ep_plain), "generic guard cells: reached and clean"
    assert not mgap_success({**ep_plain, "crashed": True})
    from skills.base import load_skill

    s = load_skill("moving-gap")
    assert s.name == "moving-gap"
    from sim.scenario_registry import get

    sc2 = get("moving_gap").spawn(None, np.random.default_rng(3), speed=1.0)
    sc3 = get("moving_gap").spawn(None, np.random.default_rng(3), speed=1.0)
    assert sc2.meta == sc3.meta, "registered spawn must reproduce per seed"
    assert get("gap").spawn is not None, "the skill must register its guards' world"
    print(
        f"MOVING-GAP-SKILL OK: one sliding gap (vy {VY_RANGE}, fence to "
        f"|y|>={MG_EDGE}), aimed encounters, now=success / was=fail, "
        f"registry round-trip"
    )


if __name__ == "__main__":
    selftest()

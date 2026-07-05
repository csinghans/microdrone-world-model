"""closing-door: the reactive-vs-predictive duel, staged where it separates.

**This skill is a benchmark first and a capability second.** The arena is
the gap-flight fence whose two gap-edge pillars **converge**: the door is
invitingly wide at first sight and narrows at 0.25-0.45 m/s. A policy
that reads *distance* ("the opening is still wide, nothing is close")
commits on stale geometry and gets pinched mid-transit, or freezes at a
fence it no longer fits through. A policy that reasons in *time*
("by my arrival the aperture will be w(t_arr); after t_close it will not
exist") threads early or declines honestly. Reaction is a distance
budget; anticipation is a time budget — this scenario is that sentence
built out of pillars.

The width is aimed, not random (the MovingCrosser convention): the door
is sized so an on-time direct transit meets w(t_arr) ~ 0.65-0.95 m
(comfortably flyable — the static gap skill passed 0.55-0.85), and it
closes completely within the episode, so lateness is not merely risky
but physically impossible. Success is a statement about time: the path
must cross the fence plane inside the aperture **as it is at the
crossing instant**.

The duel: knobs K0-K3 fly the SAME cells on the SAME seeds with four
contenders — the privileged-direction reactive baseline (it can only
lose on timing, which is the point), the hand latent-MPC, the general
champion, and the moving-gap v2 champion — so the campaign journal IS
the comparison table. Pre-registered expectations (hypotheses, not
bars): reactive freezes or gets pinched; the hand MPC declines at the
saturated warn wall (the gap-flight K0 signature); the general champion
hard-charges (never dieted on fences); the mgap champion is the best
zero-shot (gap-trained, motion-trained) but has never seen a *shrinking*
aperture. K4 is the one training knob: the door joins the v2-combination
diet, and "before vs after" becomes the final layer of the comparison.

Bars are frozen for the eventual champion (K4, or an earlier knob if
one clears them): door@1.0 >= 0.70, door@1.5 >= 0.55, with the catalog's
regression guards (static gap, moving gap, cluttered, the n=60 fast-solo
cell). Custom metrics make the verdict legible at a glance: threaded /
pinched / froze.
"""

import numpy as np

from sim.envs import CTRL_HZ
from skills.base import Criterion, EvalCell, Knob, Skill
from skills.gap_flight.skill import (
    FENCE_EDGE,
    FENCE_SPACING,
    PILLAR_R,
    gap_metrics,
    gap_success,
    spawn_gap,
)
from skills.moving_gap.skill import (
    _crossing_yt,
    mgap_metrics,
    mgap_success,
    spawn_moving_gap,
)

RATE_RANGE = (0.25, 0.45)  # total closure speed of the door (m/s)
W_HIT_RANGE = (0.65, 0.95)  # aperture at the drone's expected arrival (m)


class ClosingDoorFence:
    """The gap-flight fence with a converging gap: the two edge pillars move
    toward the gap centre at rate/2 each; the outer fence stands still.
    Per-pillar velocities (the oracle extrapolates each pillar by its own
    vp, so heterogeneous motion is already first-class). meta carries the
    initial geometry + rate — the aperture at any instant is
    w(t) = max(w0 - rate*t, 0)."""

    def __init__(self, env, rng, *, speed=1.0, width_hit=W_HIT_RANGE):
        import pybullet as p

        x_gap = float(rng.uniform(1.5, 2.1))
        yc = float(rng.uniform(-0.3, 0.3))
        rate = float(rng.uniform(*RATE_RANGE))
        # aim the WIDTH at the arrival instant (jittered early/late like the
        # crosser): on-time transit meets a flyable door; dawdling meets none
        cruise = 0.8 * float(speed)
        t_arr = x_gap / max(cruise, 1e-6)
        w_hit = float(rng.uniform(*width_hit))
        w0 = w_hit + rate * t_arr * float(rng.uniform(0.85, 1.15))
        half0 = (w0 + 2 * PILLAR_R) / 2.0
        ys = [yc - half0, yc + half0]  # indices 0, 1 = the moving edge pair
        y = yc - half0
        while y > -FENCE_EDGE:
            y -= FENCE_SPACING
            ys.append(y)
        y = yc + half0
        while y < FENCE_EDGE:
            y += FENCE_SPACING
            ys.append(y)
        self.x_gap, self.rate, self.t = x_gap, rate, 0.0
        self.ys0 = list(map(float, ys))  # edge pair first, outers after
        self.meta = {"x_gap": x_gap, "yc": yc, "w0": w0, "rate": rate}
        self._p, self.env, self.bodies = p, env, []
        if env is not None:  # selftest geometry checks run env-free
            from sim.scenarios import _pillar_body

            self.dt = env.CTRL_TIMESTEP
            self.bodies = [_pillar_body(env, x_gap, yy) for yy in self.ys0]
        else:
            self.dt = 1.0 / CTRL_HZ

    def _offsets(self) -> list:
        # edge pillars close symmetrically; the door cannot over-close
        shut = min(self.rate * self.t, self.meta["w0"]) / 2.0
        return [shut, -shut] + [0.0] * (len(self.ys0) - 2)

    def positions(self) -> list:
        return [(self.x_gap, yy + off) for yy, off in zip(self.ys0, self._offsets())]

    def velocities(self) -> list:
        r2 = self.rate / 2.0
        return [(0.0, r2), (0.0, -r2)] + [(0.0, 0.0)] * (len(self.ys0) - 2)

    def step(self) -> None:
        self.t += self.dt
        for body, (x, y) in zip(self.bodies, self.positions()):
            self._p.resetBasePositionAndOrientation(
                body,
                [x, y, 0.7],
                [0, 0, 0, 1],
                physicsClientId=self.env.CLIENT,
            )


def spawn_door(env, rng, *, speed=1.0, randomize=False, in_path=True):
    del randomize, in_path
    return ClosingDoorFence(env, rng, speed=speed)


def door_half_at(meta: dict, t: float) -> float:
    """Half-distance between the edge-pillar centres at time t."""
    w = max(meta["w0"] - meta["rate"] * t, 0.0)
    return (w + 2 * PILLAR_R) / 2.0


def door_metrics(ep: dict) -> dict:
    """Per-cell dispatch (this skill's cells span four scenario kinds):
    'rate' -> the door, judged at the crossing instant; 'vy' -> moving-gap;
    bare 'x_gap' -> static gap; else generic (no custom metrics)."""
    meta = ep.get("scenario_meta", {})
    if "rate" not in meta:
        if "vy" in meta:
            return mgap_metrics(ep)
        return gap_metrics(ep) if "x_gap" in meta else {}
    cross = _crossing_yt(ep["path"], meta["x_gap"])
    crashed = bool(ep["crashed"])
    if cross is None:
        return {
            "threaded": 0.0,
            "pinched": 0.0,  # never even reached the plane
            "froze": float(not crashed and not ep["reached"]),
            "door_margin": 0.0,
        }
    y, t = cross
    half = door_half_at(meta, t)
    inside = abs(y - meta["yc"]) < half
    threaded = inside and ep["reached"] and not crashed
    margin = half - abs(y - meta["yc"]) - PILLAR_R if threaded else 0.0
    return {
        "threaded": float(threaded),
        "pinched": float(crashed),  # crossed the plane and still crashed
        "froze": 0.0,
        "door_margin": float(max(margin, 0.0)),
    }


def door_success(ep: dict) -> bool:
    meta = ep.get("scenario_meta", {})
    if "rate" in meta:
        return bool(door_metrics(ep).get("threaded"))
    if "vy" in meta:
        return mgap_success(ep)
    if "x_gap" in meta:
        return gap_success(ep)
    return bool(ep["reached"] and not ep["crashed"])


_GENERAL = "output/ppo_wm_policy_edge_hard_xp.zip"
_MGAP = "experiments/moving_gap_v2/artifacts/ppo_moving_gap_v2_K3.zip"
_V2_DIET = ("classic", "classic", "dense", "moving", "gap", "moving_gap", "solo")

SKILL = Skill(
    name="closing-door",
    version="1",
    scenarios={
        "door": spawn_door,
        "gap": spawn_gap,
        "moving_gap": spawn_moving_gap,
    },
    cells=(
        EvalCell("door@1.0", "door", 1.0, 30, 9800),
        EvalCell("door@1.5", "door", 1.5, 30, 9800),
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
        Criterion("door@1.0", "success", ">=", 0.70, "target"),
        Criterion("door@1.5", "success", ">=", 0.55, "target"),
        Criterion("guard:gap@1.0", "success", ">=", 0.75, "guard"),
        Criterion("guard:mgap@1.0", "success", ">=", 0.70, "guard"),
        Criterion("guard:cluttered", "crash", "<=", 0.05, "guard"),
        Criterion("guard:sweep@2.0", "crash", "<=", 0.10, "guard"),
    ),
    knobs=(
        Knob(
            "K0",
            "zero_shot",
            "the reactive baseline (privileged direction) on the door",
            "distance-triggered: expected to freeze at the fence or commit "
            "on stale width and get pinched — it can only lose on timing, "
            "which is exactly what the arena prices",
            policy_path="builtin:reactive",
        ),
        Knob(
            "K1",
            "zero_shot",
            "the hand latent-MPC on the door",
            "expected to decline at the saturated warn wall (the gap-flight "
            "K0 signature) — anticipating but margin-bound",
            policy_path="builtin:wm_mpc",
        ),
        Knob(
            "K2",
            "zero_shot",
            "the general champion (edge_hard_xp), zero-shot",
            "never dieted on fences; expected to hard-charge like gap K0",
            policy_path=_GENERAL,
        ),
        Knob(
            "K3",
            "zero_shot",
            "the moving-gap v2 champion, zero-shot",
            "the best predictive contender on paper: gap-trained and "
            "motion-trained — but it has never seen an aperture *shrink*",
            policy_path=_MGAP,
        ),
        Knob(
            "K4",
            "policy",
            "the door joins the v2-combination diet",
            "if no contender clears the bars, teach the door: the v2 chassis "
            "(broad base held every band at once) plus the door world",
            train_kwargs=dict(
                worlds=_V2_DIET + ("door",),
                x_progress=True,
                edge_bias=True,
                timesteps=900_000,
            ),
        ),
    ),
    max_knobs=5,
    success=door_success,
    episode_metrics=door_metrics,
)


def selftest() -> None:
    # geometry + width aiming across seeds: the door is flyable on time,
    # and it closes within the episode (lateness is impossible, not risky)
    for s in range(8):
        sc = spawn_door(None, np.random.default_rng(s), speed=1.0)
        m = sc.meta
        t_arr = m["x_gap"] / 0.8
        w_arr = m["w0"] - m["rate"] * t_arr
        assert 0.45 < w_arr < 1.15, f"arrival width unaimed ({w_arr:.2f})"
        assert m["w0"] / m["rate"] < 7.0, "door must close within the episode"
        ys = sorted(q[1] for q in sc.positions())
        assert ys[0] <= -FENCE_EDGE and ys[-1] >= FENCE_EDGE, "fence too short"
    # motion: only the edge pair moves, symmetrically; outers stand still
    sc = spawn_door(None, np.random.default_rng(3), speed=1.0)
    p0 = sc.positions()
    for _ in range(48):
        sc.step()
    p1 = sc.positions()
    moved = [abs(b[1] - a[1]) for a, b in zip(p0, p1)]
    assert moved[0] > 1e-3 and abs(moved[0] - moved[1]) < 1e-9, "edges converge"
    assert all(d < 1e-9 for d in moved[2:]), "outer fence must not move"
    v = sc.velocities()
    assert v[0][1] > 0 and v[1][1] < 0 and v[2] == (0.0, 0.0)
    # the skill's soul, as a predicate: the SAME off-centre crossing line
    # succeeds on time (aperture half-width 0.53 m at t~2 s) and fails
    # late (0.23 m at t~3.5 s) — "it was open when I looked" is the trap.
    # (A dead-centre late crossing stays between the pillar CENTRES by
    # construction; in real episodes physics settles it via `crashed` —
    # geometry alone judges the off-centre case.)
    meta = {"x_gap": 2.0, "yc": 0.0, "w0": 1.5, "rate": 0.4}
    on_time = np.array([[0.0, 0.35, 1.0]] * 96 + [[2.5, 0.35, 1.0]])  # t~2 s
    late = np.array([[0.0, 0.35, 1.0]] * 168 + [[2.5, 0.35, 1.0]])  # t~3.5 s
    ep = {"scenario_meta": meta, "reached": True, "crashed": False}
    assert door_success({**ep, "path": on_time}), "on-time thread must succeed"
    assert not door_success({**ep, "path": late}), "the late commit must fail"
    frozen = {
        "scenario_meta": meta,
        "reached": False,
        "crashed": False,
        "path": np.array([[0.0, 0.0, 1.0]] * 10),
    }
    dm = door_metrics(frozen)
    assert dm["froze"] == 1.0 and dm["threaded"] == 0.0, "freeze must be legible"
    # dispatch: guard cells keep their own skills' predicates
    g = {
        "scenario_meta": {"x_gap": 2.0, "yc": 0.0, "w": 0.7},
        "reached": True,
        "crashed": False,
        "path": np.array([[0.0, 0.0, 1.0], [3.0, 0.0, 1.0]]),
    }
    assert door_success(g), "static-gap guard must ride gap-flight rules"
    from skills.base import load_skill

    s = load_skill("closing-door")
    assert s.name == "closing-door"
    from sim.scenario_registry import get

    sc2 = get("door").spawn(None, np.random.default_rng(5), speed=1.0)
    sc3 = get("door").spawn(None, np.random.default_rng(5), speed=1.0)
    assert sc2.meta == sc3.meta, "registered spawn must reproduce per seed"
    print(
        f"CLOSING-DOOR-SKILL OK: aimed aperture (rate {RATE_RANGE}, "
        f"w@arrival {W_HIT_RANGE}), edges converge / outers hold, "
        f"on-time=success late=fail frozen=legible, registry round-trip"
    )


if __name__ == "__main__":
    selftest()

"""opening-door: price hesitation — the closing-door duel's mirror.

Pre-registration (written before any number exists). The closing-door
campaign measured that **nobody froze**: that arena prices commitment
errors only. This is the mirror: the fence's gap starts **shut**
(w0 = 0.05 m) and holds shut until t_start, then *opens* at
0.3-0.6 m/s — aimed so the aperture reaches 0.7 m a beat AFTER a
direct-cruise arrival (t07 = t_arr + 0.3-1.5 s; the hold phase keeps
long approaches from eating the wait). The correct flight is therefore:
approach, *hold or slow for about a second*, then thread. An over-eager
policy commits on a still-lethal aperture (pinched); an over-cautious
one wastes the episode at the wall (froze — this metric finally gets to
fire) or detours (reached-without-threading, caught by the transit
check). `wait_time` (crossing instant minus nominal arrival) makes the
hesitation price *visible* per contender.

Per-knob hypotheses (falsifiable, frozen now):

- K0 `builtin:reactive` — sees a wall of close pillars, dodges along it
  or charges the slit: expect pinched or froze at cruise, worse at 1.5x.
  Either failure mode is the point: reaction has no concept of "soon".
- K1 `builtin:wm_mpc` — anticipates ~0.7 s, which sometimes covers the
  wait window: expect partial success at cruise when t07 - t_arr is
  short, collapse when it is long (its margins never learned patience).
- K2 the moving-gap v2 champion — the duel's headline question: it
  learned to aim at *where* a gap will be; does that generalize to
  *when* a gap will exist? Honest expectation: better than K0/K1, still
  under bar — waiting was never in its diet (hover exists in the action
  set but was never the winning move on a fence).
- K3 (training) — door_open joins the v2-combination diet at 900 k: PPO
  must discover hold-then-thread. If K3 also fails, the honest reading
  is that this recipe cannot learn to wait, and that is a finding about
  the action-value of hovering, not a harness error.

Bars (frozen at v1): threaded ≥ 0.60 @1.0, ≥ 0.50 @1.5 — deliberately
below the closing-door champion's 93/87 because waiting is a *new*
behaviour, not a transfer; the catalog guards are the standard block.
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
from skills.moving_gap_v2.skill import spawn_solo

W0 = 0.05  # aperture at spawn: shut for all practical purposes
WAIT_RANGE = (0.3, 1.5)  # how long after nominal arrival the door turns flyable
RATE_RANGE = (0.3, 0.6)  # opening speed once it starts (m/s)
W_FLYABLE = 0.7  # the aperture the aim is denominated in
MAX_TRAVEL = 0.5  # per-edge outward cap (stays clear of the outer fence)


class OpeningDoorFence:
    """The gap-flight fence whose edge pair DIVERGES — piecewise: the
    door holds shut (w0 = 0.05) until t_start, then opens at `rate`.
    Aimed by the *wait*: the aperture reaches W_FLYABLE at
    t07 = t_arr + U(WAIT_RANGE), so patience — not routing — is the
    skill under test (a linear-from-spawn door would be nearly open by
    the time a long approach ends; the hold phase keeps the on-time
    arrival strictly premature). meta carries
    {x_gap, yc, w0, rate, t_start, t_arr}. Honest note: velocities()
    reports the post-start rate for all t — the label oracle would be
    slightly wrong during the hold phase; this campaign is policy-only,
    so nothing consumes it yet.."""

    def __init__(self, env, rng, *, speed=1.0):
        import pybullet as p

        x_gap = float(rng.uniform(1.5, 2.1))
        yc = float(rng.uniform(-0.3, 0.3))
        w0 = W0
        cruise = 0.8 * float(speed)
        t_arr = x_gap / max(cruise, 1e-6)
        t07 = t_arr + float(rng.uniform(*WAIT_RANGE))
        rate = float(rng.uniform(*RATE_RANGE))
        t_start = t07 - (W_FLYABLE - w0) / rate  # >= 0 for all our bands
        half0 = (w0 + 2 * PILLAR_R) / 2.0
        ys = [yc - half0, yc + half0]  # indices 0, 1 = the diverging edge pair
        y = yc - half0
        while y > -FENCE_EDGE:
            y -= FENCE_SPACING
            ys.append(y)
        y = yc + half0
        while y < FENCE_EDGE:
            y += FENCE_SPACING
            ys.append(y)
        self.x_gap, self.rate, self.t = x_gap, rate, 0.0
        self.t_start = t_start
        self.ys0 = list(map(float, ys))
        self.meta = {
            "x_gap": x_gap,
            "yc": yc,
            "w0": w0,
            "rate": rate,
            "t_start": t_start,
            "t_arr": t_arr,
        }
        self._p, self.env, self.bodies = p, env, []
        if env is not None:  # selftest geometry checks run env-free
            from sim.scenarios import _pillar_body

            self.dt = env.CTRL_TIMESTEP
            self.bodies = [_pillar_body(env, x_gap, yy) for yy in self.ys0]
        else:
            self.dt = 1.0 / CTRL_HZ

    def _offsets(self) -> list:
        opened = self.rate * max(self.t - self.t_start, 0.0)
        gape = min(opened / 2.0, MAX_TRAVEL)  # per-edge, outward
        return [-gape, gape] + [0.0] * (len(self.ys0) - 2)

    def positions(self) -> list:
        return [(self.x_gap, yy + off) for yy, off in zip(self.ys0, self._offsets())]

    def velocities(self) -> list:
        r2 = self.rate / 2.0
        return [(0.0, -r2), (0.0, r2)] + [(0.0, 0.0)] * (len(self.ys0) - 2)

    def step(self) -> None:
        self.t += self.dt
        for body, (x, y) in zip(self.bodies, self.positions()):
            self._p.resetBasePositionAndOrientation(
                body,
                [x, y, 0.7],
                [0, 0, 0, 1],
                physicsClientId=self.env.CLIENT,
            )


def spawn_opening_door(env, rng, *, speed=1.0, randomize=False, in_path=True):
    del randomize, in_path
    return OpeningDoorFence(env, rng, speed=speed)


def open_half_at(meta: dict, t: float) -> float:
    """Half-distance between the edge-pillar centres at time t (piecewise
    and capped exactly like the scenario's own offsets)."""
    opened = meta["rate"] * max(t - meta["t_start"], 0.0)
    w = meta["w0"] + 2.0 * min(opened / 2.0, MAX_TRAVEL)
    return (w + 2 * PILLAR_R) / 2.0


def odoor_metrics(ep: dict) -> dict:
    """Dispatch per cell meta ('t_arr' -> opening door; 'vy' -> moving-gap
    guard; bare 'x_gap' -> static gap guard; else generic)."""
    meta = ep.get("scenario_meta", {})
    if "t_arr" not in meta:
        if "vy" in meta:
            return mgap_metrics(ep)
        return gap_metrics(ep) if "x_gap" in meta else {}
    cross = _crossing_yt(ep["path"], meta["x_gap"])
    crashed = bool(ep["crashed"])
    if cross is None:
        return {
            "threaded": 0.0,
            "pinched": 0.0,
            "froze": float(not crashed and not ep["reached"]),
            "door_margin": 0.0,
            "wait_time": 0.0,
        }
    y, t = cross
    half = open_half_at(meta, t)
    threaded = abs(y - meta["yc"]) < half and ep["reached"] and not crashed
    margin = half - abs(y - meta["yc"]) - PILLAR_R if threaded else 0.0
    return {
        "threaded": float(threaded),
        "pinched": float(crashed),
        "froze": 0.0,
        "door_margin": float(max(margin, 0.0)),
        # the hesitation price, visible: seconds held beyond nominal arrival
        "wait_time": float(max(t - meta["t_arr"], 0.0)) if threaded else 0.0,
    }


def odoor_success(ep: dict) -> bool:
    meta = ep.get("scenario_meta", {})
    if "t_arr" in meta:
        return bool(odoor_metrics(ep).get("threaded"))
    if "vy" in meta:
        return mgap_success(ep)
    if "x_gap" in meta:
        return gap_success(ep)
    return bool(ep["reached"] and not ep["crashed"])


_MGAP = "experiments/moving_gap_v2/artifacts/ppo_moving_gap_v2_K3.zip"
_V2_DIET = ("classic", "classic", "dense", "moving", "gap", "moving_gap", "solo")

SKILL = Skill(
    name="opening-door",
    version="1",
    scenarios={
        "opening_door": spawn_opening_door,
        "gap": spawn_gap,
        "moving_gap": spawn_moving_gap,
        "solo": spawn_solo,  # K3's diet trains on it; diets need worlds too
    },
    cells=(
        EvalCell("odoor@1.0", "opening_door", 1.0, 30, 9950),
        EvalCell("odoor@1.5", "opening_door", 1.5, 30, 9950),
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
        Criterion("odoor@1.0", "success", ">=", 0.60, "target"),
        Criterion("odoor@1.5", "success", ">=", 0.50, "target"),
        Criterion("guard:gap@1.0", "success", ">=", 0.75, "guard"),
        Criterion("guard:mgap@1.0", "success", ">=", 0.70, "guard"),
        Criterion("guard:cluttered", "crash", "<=", 0.05, "guard"),
        Criterion("guard:sweep@2.0", "crash", "<=", 0.10, "guard"),
    ),
    knobs=(
        Knob(
            "K0",
            "zero_shot",
            "the reactive baseline on a door that isn't open yet",
            "reaction has no concept of 'soon': expect pinched (charges the "
            "slit) or froze (dodges along the wall all episode)",
            policy_path="builtin:reactive",
        ),
        Knob(
            "K1",
            "zero_shot",
            "the hand latent-MPC",
            "0.7 s of anticipation sometimes covers the wait window: expect "
            "partial success at short waits, collapse at long ones",
            policy_path="builtin:wm_mpc",
        ),
        Knob(
            "K2",
            "zero_shot",
            "the moving-gap v2 champion — does WHERE-timing buy WHEN-timing?",
            "the duel's headline: it aims at where a gap will be; waiting "
            "for a gap to exist was never in its diet — expect best-of-"
            "zero-shot but under bar",
            policy_path=_MGAP,
        ),
        Knob(
            "K3",
            "policy",
            "door_open joins the v2-combination diet",
            "PPO must discover hold-then-thread (hover is in the action "
            "set; it has just never been the winning move at a fence)",
            train_kwargs=dict(
                worlds=_V2_DIET + ("opening_door",),
                x_progress=True,
                edge_bias=True,
                timesteps=900_000,
            ),
        ),
    ),
    max_knobs=4,
    success=odoor_success,
    episode_metrics=odoor_metrics,
)


def selftest() -> None:
    # geometry + aiming: shut at spawn, still premature at an on-time
    # arrival, flyable a 0.3-1.5 s beat later, all with goal-time to spare
    for s in range(8):
        sc = spawn_opening_door(None, np.random.default_rng(s), speed=1.0)
        m = sc.meta
        w_arr = m["w0"] + m["rate"] * max(m["t_arr"] - m["t_start"], 0.0)
        t07 = m["t_start"] + (W_FLYABLE - m["w0"]) / m["rate"]
        assert m["t_start"] >= 0.0, "the hold phase must fit in the episode"
        assert w_arr < 0.62, f"on-time arrival must meet a not-yet door ({w_arr:.2f})"
        assert m["t_arr"] + 0.29 < t07 < m["t_arr"] + 1.51, "wait window unaimed"
        assert t07 < 6.0, "door must open with time left to reach the goal"
        ys = sorted(q[1] for q in sc.positions())
        assert ys[0] <= -FENCE_EDGE and ys[-1] >= FENCE_EDGE, "fence too short"
    # motion: shut through the hold phase, then edges diverge; outers hold
    sc = spawn_opening_door(None, np.random.default_rng(3), speed=1.0)
    w_start = sc.positions()[1][1] - sc.positions()[0][1]
    hold_steps = max(int(sc.t_start * CTRL_HZ) - 2, 0)
    for _ in range(hold_steps):
        sc.step()
    w_hold = sc.positions()[1][1] - sc.positions()[0][1]
    assert abs(w_hold - w_start) < 1e-6, "door must stay shut until t_start"
    for _ in range(int(1.5 * CTRL_HZ)):
        sc.step()
    w_later = sc.positions()[1][1] - sc.positions()[0][1]
    assert w_later > w_start + 0.3, "the door must actually open"
    v = sc.velocities()
    assert v[0][1] < 0 < v[1][1] and v[2] == (0.0, 0.0)
    sc.t = 1e9  # cap check: edges never wander into the outer fence
    w_cap = sc.positions()[1][1] - sc.positions()[0][1]
    assert w_cap <= w_start + 2 * MAX_TRAVEL + 1e-6
    # the soul, mirrored from closing-door: the SAME off-centre line FAILS
    # early (door not open yet) and SUCCEEDS late (patience pays)
    meta = {
        "x_gap": 2.0,
        "yc": 0.0,
        "w0": 0.05,
        "rate": 0.4,
        "t_start": 1.0,
        "t_arr": 2.5,
    }
    early = np.array([[0.0, 0.25, 1.0]] * 48 + [[2.5, 0.25, 1.0]])  # t~1 s
    late = np.array([[0.0, 0.25, 1.0]] * 168 + [[2.5, 0.25, 1.0]])  # t~3.5 s
    ep = {"scenario_meta": meta, "reached": True, "crashed": False}
    assert not odoor_success({**ep, "path": early}), "the eager commit must fail"
    assert odoor_success({**ep, "path": late}), "patience must pay"
    m_late = odoor_metrics({**ep, "path": late})
    assert m_late["wait_time"] > 0.5, "the hesitation price must be visible"
    frozen = {
        "scenario_meta": meta,
        "reached": False,
        "crashed": False,
        "path": np.array([[0.0, 0.0, 1.0]] * 10),
    }
    assert odoor_metrics(frozen)["froze"] == 1.0, "freezing must be legible"
    # dispatch: guard cells keep their own skills' predicates
    g = {
        "scenario_meta": {"x_gap": 2.0, "yc": 0.0, "w": 0.7},
        "reached": True,
        "crashed": False,
        "path": np.array([[0.0, 0.0, 1.0], [3.0, 0.0, 1.0]]),
    }
    assert odoor_success(g), "static-gap guard must ride gap-flight rules"
    from skills.base import load_skill

    s = load_skill("opening-door")
    assert s.name == "opening-door"
    from sim.scenario_registry import get

    sc2 = get("opening_door").spawn(None, np.random.default_rng(5), speed=1.0)
    sc3 = get("opening_door").spawn(None, np.random.default_rng(5), speed=1.0)
    assert sc2.meta == sc3.meta, "registered spawn must reproduce per seed"
    print(
        f"OPENING-DOOR-SKILL OK: shut at spawn (w0 {W0}), opens to "
        f"{W_FLYABLE} m a {WAIT_RANGE}s beat after arrival, early=fail "
        f"late=success frozen=legible wait-time visible, registry round-trip"
    )


if __name__ == "__main__":
    selftest()

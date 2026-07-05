"""dodgeball: hold a station, dodge what is thrown at your face.

The catalog's first DEFENSE arena — success is surviving in place, not
arriving somewhere. The drone hovers at its spawn point; balls (default
pillar bodies, deliberately identical in appearance to every trained
pillar, so the ONLY novelty is radial motion) are launched head-on at
it. Task family: station-keeping survival. The skill's science question
is written in `experiments/dodgeball_feasibility/journal.md`, and the
SKILL object's bars land only after that probe prices the arena per its
frozen selection formula.

Scenario contract (`DodgeballRange`):

  * All ball bodies exist from t=0, PARKED far off-lane (x 1.6-2.8,
    y ±6 — bearing ≥ 71° from any in-box drone pose, far outside the
    28° half-FOV and ≥ 4.7 m from any legal drone position, so parked
    balls can never touch `min_clear` or the camera).
  * The whole launch schedule is pre-drawn in `__init__` from the rng
    (same-seed spawns reproduce exactly — the registry convention).
    Arrival times are fixed per seed at ~{4.0, 5.2, 6.4} s ± 0.25;
    launch time = arrival − LAUNCH_DIST/ball_speed, so the ball_speed
    axis changes warning time, never threat count ("equalize arrivals,
    not launches"). The earliest slow-ball launch stays > 0 by
    construction (4.0 − 0.25 − 2.2/0.6 = 0.08 s).
  * At launch the ball teleports from the parking lot to a point
    LAUNCH_DIST ahead of the drone's position AT THAT INSTANT (read
    from `env.pos`, zero steps stale — both runners step the env before
    the scenario), laterally offset by side·U(0, 0.5), and flies
    STRAIGHT at the drone's launch-instant position + N(0, AIM_SIGMA)
    noise. Aimed once, never homing — the MovingCrosser lesson: aim or
    most seeds measure nothing. Balls that pass 1.2 m behind the
    station re-park.
  * `positions()` is index-stable (ball i lives in slot i forever) —
    the feasibility oracle differentiates consecutive snapshots per
    slot and relies on this.

MINE — do not step on: **dodgeball must never enter a dataset diet**
under the current label oracle. `generate_rollouts` snapshots
positions()/velocities() ONCE at spawn and the intervention labels
extrapolate constant velocity; the parking-lot snapshot plus
mid-episode teleports would poison labels silently. Flight eval and
policy training are unaffected (both read positions() live).

Success/metrics dispatch on the meta key "balls" (chosen to collide
with none of the existing dispatch keys: vy / x_gap / fences / w0 /
rate). The station box converts the action set's dodge cost into a
budget: veers are (0.5, ±0.5), so every ~0.40-0.45 m of lateral dodge
costs the same forward drift and nothing ever comes back (no backward
command) — hence x-budget = 3 arrivals x 0.45 + slack ≈ 1.9 m, well
short of GOAL_X so fleeing forward also ends the episode early and
fails the steps==TMAX clause.
"""

from functools import partial

import numpy as np

from sim.envs import CTRL_HZ
from sim.scenarios import TMAX, _pillar_body
from skills.base import Criterion, EvalCell, Knob, Skill
from skills.gap_flight.skill import spawn_gap
from skills.moving_gap.skill import spawn_moving_gap

N_BALLS = 3
T_ARR = (4.0, 5.2, 6.4)  # seconds; jittered ±ARR_JITTER per seed
ARR_JITTER = 0.25
LAUNCH_DIST = 2.2  # m ahead of the drone at launch (R_MAX is 2.1)
AIM_SIGMA = 0.15  # m of aim error at the target point
LAUNCH_OFF = 0.5  # max lateral launch-point offset (side alternates)
BOX = (1.9, 1.2)  # (forward budget, half-width) around the station
BOX_BACK = 0.3  # rearward tolerance (PID wobble, no backward command)
REPARK_BEHIND = 1.2  # ball re-parks this far behind the station
PARKS = ((1.6, 6.0), (2.0, -6.0), (2.4, 6.0), (2.8, -6.0))


class DodgeballRange:
    """N aimed head-on balls on a pre-drawn schedule; see module doc."""

    def __init__(self, env, rng, *, ball_speed: float, n_balls: int = N_BALLS):
        self.env = env
        self.v = float(ball_speed)
        self.n = int(n_balls)
        self.dt = env.CTRL_TIMESTEP if env is not None else 1.0 / CTRL_HZ
        self.station = (0.0, 0.0)  # the drone spawns at the origin
        # pre-draw everything (fixed draw order => same-seed reproduction)
        self._launch_k, self._side, self._off, self._aim = [], [], [], []
        flight = LAUNCH_DIST / self.v
        for i in range(self.n):
            t_arr = T_ARR[i] + float(rng.uniform(-ARR_JITTER, ARR_JITTER))
            self._launch_k.append(max(1, int(round((t_arr - flight) / self.dt))))
            self._side.append(1.0 if rng.random() < 0.5 else -1.0)
            self._off.append(float(rng.uniform(0.0, LAUNCH_OFF)))
            self._aim.append(rng.normal(0.0, AIM_SIGMA, size=2).astype(float))
        self._pos = [
            np.array(PARKS[i % len(PARKS)], dtype=float) for i in range(self.n)
        ]
        self._vel = [np.zeros(2) for _ in range(self.n)]
        self._flying = [False] * self.n
        self._done = [False] * self.n
        self._k = 0
        self.bodies = (
            [_pillar_body(env, float(p[0]), float(p[1])) for p in self._pos]
            if env is not None
            else []
        )
        self.meta = {
            "balls": self.n,
            "ball_speed": self.v,
            "station": self.station,
            "box": BOX,
        }

    def _drone_xy(self) -> np.ndarray:
        if self.env is not None:
            return np.array(self.env.pos[0][0:2], dtype=float)
        return np.array(self.station, dtype=float)  # env-free selftests

    def positions(self) -> list:
        return [tuple(p) for p in self._pos]

    def velocities(self) -> list:
        return [tuple(v) for v in self._vel]

    def step(self) -> None:
        self._k += 1
        moved = []
        for i in range(self.n):
            if self._flying[i]:
                self._pos[i] = self._pos[i] + self._vel[i] * self.dt
                if self._pos[i][0] < self.station[0] - REPARK_BEHIND:
                    self._pos[i] = np.array(PARKS[i % len(PARKS)], dtype=float)
                    self._vel[i] = np.zeros(2)
                    self._flying[i] = False
                    self._done[i] = True
                moved.append(i)
            elif not self._done[i] and self._k >= self._launch_k[i]:
                d = self._drone_xy()
                launch = np.array(
                    [d[0] + LAUNCH_DIST, d[1] + self._side[i] * self._off[i]]
                )
                heading = d + self._aim[i] - launch
                self._pos[i] = launch
                self._vel[i] = self.v * heading / max(np.linalg.norm(heading), 1e-9)
                self._flying[i] = True
                moved.append(i)
        if self.env is not None and moved:
            import pybullet as p

            for i in moved:
                p.resetBasePositionAndOrientation(
                    self.bodies[i],
                    [float(self._pos[i][0]), float(self._pos[i][1]), 0.7],
                    [0, 0, 0, 1],
                    physicsClientId=self.env.CLIENT,
                )


def spawn_dodgeball(
    env, rng, *, speed=1.0, randomize=False, in_path=True, ball_speed=1.0
):
    """`speed` stays the DRONE's agility knob (envelope discipline);
    ball_speed is baked into registered variants, never mapped from it."""
    del speed, randomize, in_path
    return DodgeballRange(env, rng, ball_speed=ball_speed)


def dodge_metrics(ep: dict) -> dict:
    """Dispatch on the 'balls' meta key; every other cell reports {}."""
    meta = ep.get("scenario_meta", {})
    if "balls" not in meta:
        return {}
    path = np.asarray(ep["path"])
    x0, y0 = meta["station"]
    bx, by = meta["box"]
    in_box = bool(
        (path[:, 0] >= x0 - BOX_BACK).all()
        and (path[:, 0] <= x0 + bx).all()
        and (np.abs(path[:, 1] - y0) <= by).all()
    )
    full = ep["steps"] >= TMAX  # the runner never passes tmax; 360 is pinned
    return {
        "survived": float((not ep["crashed"]) and full),
        "in_box": float(in_box),
        "disp_x": float(path[:, 0].max() - x0),
        "y_max": float(np.abs(path[:, 1] - y0).max()),
    }


def dodge_success(ep: dict) -> bool:
    """Station cells: alive for the whole episode AND never left the box.
    (Fleeing forward trips the GOAL_X early break -> steps < TMAX -> fail,
    so the two clauses agree.) Everything else: the generic transit rule."""
    meta = ep.get("scenario_meta", {})
    if "balls" in meta:
        m = dodge_metrics(ep)
        return bool(m["survived"] and m["in_box"])
    return bool(ep["reached"] and not ep["crashed"])


# bars are the feasibility probe's frozen formula applied to its table
# (experiments/dodgeball_feasibility/ceiling.json: 0.90/0.80/0.80/0.80,
# every cell over the 0.55 floor -> bar = ceiling - 0.25). The selftest
# re-derives them from the committed json so the pre-registration and
# the code cannot drift apart.
_GENERAL = "output/ppo_wm_policy_edge_hard_xp.zip"
_DODGE_WORLDS = ("dodgeball_v06", "dodgeball_v10", "dodgeball_v14", "dodgeball_v18")
_CHASSIS = dict(x_progress=True, edge_bias=True, timesteps=900_000)

SKILL = Skill(
    name="dodgeball",
    version="1",
    scenarios={
        "dodgeball_v06": partial(spawn_dodgeball, ball_speed=0.6),
        "dodgeball_v10": partial(spawn_dodgeball, ball_speed=1.0),
        "dodgeball_v14": partial(spawn_dodgeball, ball_speed=1.4),
        "dodgeball_v18": partial(spawn_dodgeball, ball_speed=1.8),
        "gap": spawn_gap,
        "moving_gap": spawn_moving_gap,
    },
    cells=(
        EvalCell("dodge@v0.6", "dodgeball_v06", 1.0, 30, 23000),
        EvalCell("dodge@v1.0", "dodgeball_v10", 1.0, 30, 23000),
        EvalCell("dodge@v1.4", "dodgeball_v14", 1.0, 30, 23000),
        EvalCell("dodge@v1.8", "dodgeball_v18", 1.0, 30, 23000),
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
        Criterion("dodge@v0.6", "success", ">=", 0.65, "target"),
        Criterion("dodge@v1.0", "success", ">=", 0.55, "target"),
        Criterion("dodge@v1.4", "success", ">=", 0.55, "target"),
        Criterion("dodge@v1.8", "success", ">=", 0.55, "target"),
        Criterion("guard:gap@1.0", "success", ">=", 0.75, "guard"),
        Criterion("guard:mgap@1.0", "success", ">=", 0.70, "guard"),
        Criterion("guard:cluttered", "crash", "<=", 0.05, "guard"),
        Criterion("guard:sweep@2.0", "crash", "<=", 0.10, "guard"),
    ),
    knobs=(
        Knob(
            "K0",
            "zero_shot",
            "the general champion, zero-shot on a task it was never asked",
            "structural 0, pre-registered: its repertoire never hovers "
            "(every command advances >= 0.3 m/s), so it exits the box by "
            "construction — the flee/crash split is the diagnostic",
            policy_path=_GENERAL,
        ),
        Knob(
            "K1",
            "policy",
            "pure dodgeball diet + station reward (the science knob)",
            "does the observation carry a dodgeable warning at all? The "
            "heads are single-frame (motion-blind); the 12-step stacked "
            "history watching the probability ramp is the only mechanism. "
            "Transit guards are expected structural failures for this zip "
            "(promotion impossible by design; the dodge cells are the point)",
            train_kwargs=dict(worlds=_DODGE_WORLDS, **_CHASSIS),
        ),
        Knob(
            "K2",
            "policy",
            "mixed diet: transit worlds + all four ball speeds",
            "CONDITIONAL — played only if K1 reads success >= 0.30 on any "
            "priced cell (else it stays sheathed and the campaign closes "
            "on the perception verdict). The promotion knob: guards regain "
            "meaning; dilution risk on 7 worlds is on the record",
            train_kwargs=dict(
                worlds=("classic", "gap", "moving_gap") + _DODGE_WORLDS, **_CHASSIS
            ),
        ),
    ),
    max_knobs=4,  # one deviation slot, charter rationale required
    success=dodge_success,
    episode_metrics=dodge_metrics,
)


def selftest() -> None:
    # same-seed spawns reproduce the whole schedule (registry convention)
    a = DodgeballRange(None, np.random.default_rng(7), ball_speed=1.0)
    b = DodgeballRange(None, np.random.default_rng(7), ball_speed=1.0)
    assert a._launch_k == b._launch_k and a._side == b._side and a.meta == b.meta
    # arrivals equalized: launch time compensates flight time per speed
    for v in (0.6, 1.0, 1.4, 1.8):
        sc = DodgeballRange(None, np.random.default_rng(3), ball_speed=v)
        for i, k in enumerate(sc._launch_k):
            t_arr = k * sc.dt + LAUNCH_DIST / v
            assert abs(t_arr - T_ARR[i]) <= ARR_JITTER + 2 * sc.dt, (v, i, t_arr)
            assert k >= 1, "slow-ball launches must stay inside the episode"
        assert T_ARR[-1] + ARR_JITTER < TMAX / CTRL_HZ, "last arrival inside tmax"
    # env-free flight: ball launches toward the station, passes, re-parks;
    # slots stay index-stable throughout
    sc = DodgeballRange(None, np.random.default_rng(5), ball_speed=1.4)
    seen_flying = False
    for _ in range(TMAX):
        sc.step()
        if sc._flying[0]:
            seen_flying = True
            assert sc._vel[0][0] < 0, "head-on means vx < 0"
    assert seen_flying and sc._done[0], "ball 0 must launch and re-park"
    assert all(
        tuple(p) == PARKS[i % len(PARKS)] for i, p in enumerate(sc._pos) if sc._done[i]
    )
    # parked balls can never graze the box (min_clear hygiene)
    for px, py in PARKS:
        assert min(abs(py) - BOX[1], 10) >= 4.7, "parking lot too close"
    # predicates: a clean full-length hover succeeds; drifting out of the
    # box fails even uncrashed; a transit guard episode uses the old rule
    hover_path = np.zeros((TMAX + 1, 2))
    ep = {
        "scenario_meta": dict(sc.meta),
        "path": hover_path,
        "steps": TMAX,
        "crashed": False,
        "reached": False,
    }
    assert dodge_success(ep) and dodge_metrics(ep)["in_box"] == 1.0
    flee = hover_path.copy()
    flee[:, 0] = np.linspace(0.0, BOX[0] + 0.4, TMAX + 1)
    assert not dodge_success({**ep, "path": flee})
    assert dodge_metrics({**ep, "path": flee})["disp_x"] > BOX[0]
    assert not dodge_success({**ep, "crashed": True})
    guard_ep = {"scenario_meta": {"x_gap": 2.0}, "reached": True, "crashed": False}
    assert dodge_success(guard_ep) and dodge_metrics(guard_ep) == {}
    # dispatch-key hygiene: none of the other skills' keys appear in meta
    assert not {"vy", "x_gap", "fences", "w0", "rate"} & set(sc.meta)
    # the SKILL loads, registers its worlds, and its bars are EXACTLY the
    # frozen formula applied to the committed probe table (no drift between
    # pre-registration and code)
    import json
    import os

    from skills.base import load_skill

    # compare against the canonical module's objects (under `-m` this file
    # is `__main__`, a second copy — identity must be checked in one module)
    from skills.dodgeball import skill as canon

    s = load_skill("dodgeball")
    assert s.success is canon.dodge_success
    assert s.episode_metrics is canon.dodge_metrics
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    with open(
        os.path.join(root, "experiments", "dodgeball_feasibility", "ceiling.json")
    ) as f:
        grid = {row["ball_speed"]: row["ceiling"] for row in json.load(f)["grid"]}
    bars = {c.cell: c.bar for c in s.criteria if c.kind == "target"}
    for v, cell in (
        (0.6, "dodge@v0.6"),
        (1.0, "dodge@v1.0"),
        (1.4, "dodge@v1.4"),
        (1.8, "dodge@v1.8"),
    ):
        assert grid[v] >= 0.55, "priced cells only"
        assert abs(bars[cell] - (grid[v] - 0.25)) < 1e-9, (cell, grid[v])
    from sim.scenario_registry import get

    sc5 = get("dodgeball_v14").spawn(None, np.random.default_rng(9))
    sc6 = get("dodgeball_v14").spawn(None, np.random.default_rng(9))
    assert sc5.meta == sc6.meta and sc5._launch_k == sc6._launch_k
    assert sc5.v == 1.4, "ball_speed is baked into the variant, not cell speed"
    k0, k1, k2 = s.knobs
    assert k0.policy_path == _GENERAL
    assert set(k1.train_kwargs["worlds"]) == set(_DODGE_WORLDS), "pure diet"
    assert set(k2.train_kwargs["worlds"]) > set(_DODGE_WORLDS), "mixed diet"
    print(
        f"DODGEBALL OK: schedule pre-drawn & reproducible, arrivals equalized "
        f"across speeds (T_ARR={T_ARR}), head-on launch/re-park with stable "
        f"slots, station predicates (box={BOX}) + transit fallback"
    )


if __name__ == "__main__":
    selftest()

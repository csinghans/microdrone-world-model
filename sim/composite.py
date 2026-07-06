"""Composite courses — the integration layer of flight TDD.

Unit tests already exist in this repo (every skill's cells with frozen
bars; guards are the regression suite). What never existed is the
INTEGRATION test: several heterogeneous stages placed one after another
along x and flown in a single episode. This module builds those courses
from the registered single-stage worlds, honestly:

  * **Double-write shifting.** Pillar bodies are visual-only and scoring
    walks `positions()` (eval/episode.py), so a stage shifted by +offset
    must move BOTH the pybullet bodies (body-count snapshot around the
    sub-spawn, then resetBasePositionAndOrientation) and the logical
    coordinates (StaticScenario.pillars, mover `x_gap`/`x` attrs, and
    the meta the predicates read).
  * **Activation on entry.** Every mover's aim math assumes "clock zero
    = the drone is at native x_gap distance, cruising" — so a stage's
    `step()` only runs while the drone is INSIDE that stage. Crossing
    the stage boundary IS clock zero, and the baked aim holds.
  * **Integration verdicts avoid the absolute-clock trap.** The
    time-aware unit predicates (`_crossing_yt` family) read the episode
    path clock and would mis-score rebased stages; the integration
    judgment is deliberately composite-level — reach the final goal
    without ever crashing — plus stage-resolution diagnostics
    (stages_cleared / stage_break_at / crash_stage) from x-crossings.

`StageLocal` wraps any standard policy for composite flight: it feeds
stage-LOCAL x (the experts' x_progress feature is x/GOAL_X, trained in
[0,1]) and resets the policy's memory at stage entry (`begin()` — a
fresh corridor, exactly like a fresh episode).
"""

import numpy as np

from sim.scenario_registry import StaticScenario, get, register

STAGE_LEN = 3.0  # one stage == one native corridor (GOAL_X)
POOL = ("gap", "slalom3_fixed", "moving_gap", "door", "opening_door")


def _shift_logic(sub, off: float) -> None:
    """Shift a sub-scenario's LOGICAL coordinates by +off in x (bodies are
    shifted separately by the body-snapshot loop in CompositeCourse)."""
    if isinstance(sub, StaticScenario):
        sub.pillars = [(float(x) + off, float(y)) for x, y in sub.pillars]
    if hasattr(sub, "x_gap"):
        sub.x_gap = float(sub.x_gap) + off
    if hasattr(sub, "x") and not isinstance(sub, StaticScenario):
        sub.x = float(sub.x) + off
    meta = getattr(sub, "meta", None)
    if isinstance(meta, dict):
        if "x_gap" in meta:
            meta["x_gap"] = float(meta["x_gap"]) + off
        if "fences" in meta:
            meta["fences"] = [
                (float(x) + off, float(yc), float(w)) for x, yc, w in meta["fences"]
            ]


class CompositeCourse:
    """Heterogeneous stages along x; Scenario protocol; see module doc."""

    def __init__(self, env, rng, *, stages, stage_len: float = STAGE_LEN, speed=1.0):
        self.env = env
        self.L = float(stage_len)
        self.names = tuple(stages)
        self.subs, self.offsets = [], []
        stage_meta = []
        for k, name in enumerate(self.names):
            off = k * self.L
            sub_rng = np.random.default_rng(int(rng.integers(2**31 - 1)))
            if env is not None:
                import pybullet as p

                n0 = p.getNumBodies(physicsClientId=env.CLIENT)
            sub = get(name).spawn(env, sub_rng, speed=speed)
            if env is not None:
                n1 = p.getNumBodies(physicsClientId=env.CLIENT)
                for i in range(n0, n1):
                    bid = p.getBodyUniqueId(i, physicsClientId=env.CLIENT)
                    pos, orn = p.getBasePositionAndOrientation(
                        bid, physicsClientId=env.CLIENT
                    )
                    p.resetBasePositionAndOrientation(
                        bid,
                        [pos[0] + off, pos[1], pos[2]],
                        orn,
                        physicsClientId=env.CLIENT,
                    )
            _shift_logic(sub, off)
            self.subs.append(sub)
            self.offsets.append(off)
            stage_meta.append((name, off))
        self.meta = {"stages": stage_meta, "stage_len": self.L}
        # expose the (already shifted) slalom fences so the gate-bonus
        # machinery can pay chain-threading during course fine-tuning —
        # the reward-side chain retention lever (integration-ft v3)
        fences = []
        for sub in self.subs:
            m = getattr(sub, "meta", None)
            if isinstance(m, dict) and "fences" in m:
                fences.extend(m["fences"])
        if fences:
            self.meta["fences"] = fences

    def _drone_x(self) -> float:
        if self.env is not None:
            return float(self.env.pos[0][0])
        return 0.0  # env-free selftests never fly

    def positions(self) -> list:
        out = []
        for sub in self.subs:
            out.extend(sub.positions())
        return out

    def velocities(self) -> list:
        out = []
        for sub in self.subs:
            out.extend(sub.velocities())
        return out

    def step(self) -> None:
        # activation on entry: only the stage the drone is inside advances —
        # its first step() call IS its clock zero, so baked aim math holds
        k = int(np.clip(self._drone_x() // self.L, 0, len(self.subs) - 1))
        self.subs[k].step()


def course_for_seed(seed: int, pool=POOL, k: int = 3) -> tuple:
    """The random course draw: seed -> k stage names (with replacement)."""
    rng = np.random.default_rng(seed)
    return tuple(pool[int(rng.integers(len(pool)))] for _ in range(k))


def register_course(seed: int, pool=POOL, k: int = 3) -> str:
    """Register the seed's course as a throwaway world; returns its name.
    The composition is fixed by the seed; per-episode geometry still draws
    from the episode rng (same-seed spawns reproduce, as everywhere)."""
    names = course_for_seed(seed, pool, k)

    def spawn(env, rng, *, speed=1.0, randomize=False, in_path=True, _names=names):
        del randomize, in_path
        return CompositeCourse(env, rng, stages=_names, speed=speed)

    world = f"_integration_{seed}"
    register(world, spawn)
    return world


class StageLocal:
    """Wrap a standard policy for composite flight: stage-local x (the
    x_progress feature is x/GOAL_X, trained in [0,1]) and a memory reset
    at each stage entry (begin() — a fresh corridor)."""

    def __init__(self, inner, stage_len: float = STAGE_LEN, n_stages: int = 3):
        self.inner = inner
        self.L = float(stage_len)
        self.n = int(n_stages)
        self._stage = 0

    def begin(self, pillars) -> None:
        self._stage = 0
        self.inner.begin(pillars)

    def decide(self, frame, state) -> int:
        k = int(np.clip(float(state[0]) // self.L, 0, self.n - 1))
        if k != self._stage:
            self._stage = k
            self.inner.begin([])  # new corridor: fresh history/LSTM
        s = np.array(state, dtype=float, copy=True)
        s[0] -= k * self.L
        return self.inner.decide(frame, s)


def integration_metrics(ep: dict) -> dict:
    """Stage-resolution diagnostics from x alone — deliberately no
    time-aware per-stage predicates (the absolute-clock trap)."""
    meta = ep.get("scenario_meta", {})
    if "stages" not in meta:
        return {}
    L, n = float(meta["stage_len"]), len(meta["stages"])
    path = np.asarray(ep["path"])
    cleared = int(np.clip(path[:, 0].max() // L, 0, n))
    out = {"stages_cleared": float(cleared)}
    if ep.get("crashed") and "min_clear_step" in ep:
        cx = float(path[int(ep["min_clear_step"]), 0])
        out["crash_stage"] = float(np.clip(cx // L, 0, n - 1))
    out["stage_break_at"] = float(
        n
        if (cleared >= n and not ep.get("crashed"))
        else (
            min(cleared, n - 1)
            if not ep.get("crashed")
            else min(out.get("crash_stage", cleared), n - 1)
        )
    )
    return out


CORRIDOR_Y = 2.4  # the training envelope; fences seal at 2.2/3.2


def integration_success(ep: dict) -> bool:
    """Reach the composite goal without EVER crashing, staying inside the
    corridor (|y| <= 2.4 — closes the walk-around-the-fence loophole;
    audited before hardening: passing runs sat at |y| <= 0.57, so this
    clause changed no measured number)."""
    if not (ep.get("reached") and not ep.get("crashed")):
        return False
    path = np.asarray(ep["path"])
    return bool(np.abs(path[:, 1]).max() <= CORRIDOR_Y)


def selftest() -> None:
    from skills.base import load_skill

    for s in (
        "gap-flight",
        "corridor-slalom-v2",
        "moving-gap",
        "closing-door",
        "opening-door",
    ):
        load_skill(s)
    # the course draw is seed-reproducible and pool-bounded
    a, b = course_for_seed(42), course_for_seed(42)
    assert a == b and len(a) == 3 and all(n in POOL for n in a)
    assert course_for_seed(43) != a or course_for_seed(44) != a
    # env-free composite: logical shift is double-write consistent
    c = CompositeCourse(
        None, np.random.default_rng(7), stages=("gap", "slalom3_fixed", "moving_gap")
    )
    assert [n for n, _ in c.meta["stages"]] == ["gap", "slalom3_fixed", "moving_gap"]
    g_meta = c.subs[0].meta
    assert 1.5 <= g_meta["x_gap"] <= 2.1, "stage 0 stays native"
    f = c.subs[1].meta["fences"]
    assert all(3.0 + 0.9 <= x <= 3.0 + 2.4 for x, _, _ in f), "slalom shifted +3"
    assert 6.0 + 1.5 <= c.subs[2].x_gap <= 6.0 + 2.1, "mover attr shifted +6"
    ps = np.asarray(c.positions())
    assert ps[:, 0].max() > 6.0 and ps[:, 0].min() < 3.0, "coords span stages"
    # positions vs meta agree after the shift (the double-write assert)
    assert abs(c.subs[2].positions()[0][0] - c.subs[2].x_gap) < 1e-9
    # registered throwaway course reproduces per seed
    w = register_course(42)
    s1 = get(w).spawn(None, np.random.default_rng(5))
    s2 = get(w).spawn(None, np.random.default_rng(5))
    assert s1.meta == s2.meta

    # StageLocal: x localization + a begin() reset on entry
    class Probe:
        def __init__(self):
            self.begins, self.xs = 0, []

        def begin(self, pillars):
            self.begins += 1

        def decide(self, frame, state):
            self.xs.append(float(state[0]))
            return 0

    p = Probe()
    sl = StageLocal(p, 3.0, 3)
    sl.begin([])
    for x in (0.5, 2.9, 3.2, 5.9, 6.1, 8.9):
        sl.decide(None, np.array([x, 0.0, 1.0]))
    assert p.begins == 3, "one reset per stage entry (incl. the initial begin)"
    assert max(p.xs) < 3.0 and abs(p.xs[2] - 0.2) < 1e-9, "x is stage-local"
    # metrics: clean full run vs a crash located in stage 1
    meta = {"stages": [("gap", 0.0), ("gap", 3.0), ("gap", 6.0)], "stage_len": 3.0}
    path = np.array([[0, 0, 1], [3.5, 0, 1], [6.5, 0, 1], [9.1, 0, 1]])
    ep = {"scenario_meta": meta, "path": path, "reached": True, "crashed": False}
    m = integration_metrics(ep)
    assert m["stages_cleared"] == 3 and m["stage_break_at"] == 3
    ep2 = {
        "scenario_meta": meta,
        "path": path[:3],
        "reached": False,
        "crashed": True,
        "min_clear_step": 1,
    }
    m2 = integration_metrics(ep2)
    assert m2["crash_stage"] == 1.0 and m2["stage_break_at"] == 1.0
    assert integration_success(ep) and not integration_success(ep2)
    print(
        f"COMPOSITE OK: seeded course draws from {len(POOL)}-world pool, "
        f"double-write shifts verified (coords==meta==attrs), StageLocal "
        f"localizes x and resets memory per stage, metrics locate the break"
    )


if __name__ == "__main__":
    selftest()


def register_random_course(pool=POOL, k: int = 3, name: str = "course_random"):
    """A TRAINING world: every episode draws a fresh k-stage composition
    from the episode rng (exam courses stay seed-pinned via
    register_course; the exam's 110000-series compositions are drawn from
    course seeds, not episode rngs, so train/exam courses never collide
    by construction)."""

    def spawn(env, rng, *, speed=1.0, randomize=False, in_path=True):
        del randomize, in_path
        names = tuple(pool[int(rng.integers(len(pool)))] for _ in range(k))
        return CompositeCourse(env, rng, stages=names, speed=speed)

    register(name, spawn)
    return name

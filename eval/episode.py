"""The unified, registry-dispatched episode runner (skills fly through here).

Generalizes the hard-worlds runner: any registered scenario, per-step
`scenario.step()`, scoring against current geometry, the `.pillars`
privileged-refresh convention — and it **records the flight path**, because
skill success predicates (did it transit the gap?) are statements about the
trajectory, not just the endpoint. The four historical scoreboard files
stay frozen; new work builds on this one.
"""

import numpy as np

from planner.action_set import ACTION_VECS, FORWARD
from planner.latent_mpc import DECIDE_EVERY
from sim.envs import VelCommander, grab_frame, make_ctrl, make_env
from sim.scenario_registry import get as get_scenario
from sim.scenarios import COLLISION_R, GOAL_X, TMAX, nearest_planar


def run_scenario_episode(
    env,
    policy,
    seed: int,
    world: str,
    speed: float = 1.0,
    tmax: int = TMAX,
    goal_x: float = GOAL_X,
    randomize: bool = False,
) -> dict:
    """One START -> goal_x flight through any registered world. Same seed =
    same course. Returns the episode dict plus `path` (N,3) and the
    scenario's `meta` (skill-defined facts for success predicates)."""
    rng = np.random.default_rng(seed)
    obs, _ = env.reset(seed=int(seed))
    cmd = VelCommander(make_ctrl(), env.CTRL_TIMESTEP)
    cmd.reset(obs[0][0:3])
    scenario = get_scenario(world).spawn(env, rng, speed=speed, randomize=randomize)
    pillars0 = scenario.positions()
    policy.begin(pillars0)
    vecs = float(speed) * ACTION_VECS

    state, a_id, trigger = obs[0], FORWARD, -1
    path, min_clear = [state[0:3].copy()], 9.0
    for t in range(tmax):
        cur = scenario.positions()
        if t % DECIDE_EVERY == 0:
            if hasattr(policy, "pillars"):  # privileged baseline: live state
                policy.pillars = [np.array(q) for q in cur]
            a_id = policy.decide(grab_frame(env), state)
            if a_id != FORWARD and trigger < 0:
                trigger = t
        obs, _, _, _, _ = env.step(cmd.rpm(state, vecs[a_id]).reshape(1, 4))
        state = obs[0]
        scenario.step()  # static worlds: no-op
        path.append(state[0:3].copy())
        min_clear = min(min_clear, nearest_planar(state[0:2], scenario.positions()))
        if state[0] >= goal_x:
            break
    return {
        "path": np.array(path),
        "pillars": pillars0,
        "scenario_meta": dict(getattr(scenario, "meta", {}) or {}),
        "min_clear": min_clear,
        "trigger": trigger,
        "crashed": min_clear < COLLISION_R,
        "steps": len(path) - 1,
        "reached": bool(state[0] >= goal_x),
    }


class _Cruise:
    """Selftest stand-in policy: fly straight (no torch needed)."""

    def begin(self, pillars) -> None:
        del pillars

    def decide(self, frame, state) -> int:
        del frame, state
        return FORWARD


def selftest() -> None:
    env = make_env()
    for world in ("classic", "dense", "moving"):
        ep = run_scenario_episode(env, _Cruise(), seed=7, world=world, tmax=96)
        for key in ("path", "pillars", "scenario_meta", "min_clear", "crashed"):
            assert key in ep, f"episode dict missing {key} ({world})"
        assert ep["path"].shape[1] == 3 and len(ep["path"]) == ep["steps"] + 1
        assert np.isfinite(ep["min_clear"]), f"non-finite clearance ({world})"
    env.close()
    print("EPISODE-RUNNER OK: registry-dispatched, path-recorded, 3 builtin worlds")


if __name__ == "__main__":
    selftest()

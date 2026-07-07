"""The mission runner for the Indoor Active Search Track.

Separate from `eval/episode.py` (the forward-transit `goal_x` runner,
kept bit-for-bit so avoidance results reproduce). A search episode is a
2D roam of a `SearchScenario`: cover the room, sense the abstract
beacon, confirm it, and return home — terminating on found-and-returned
or a decision budget, never on a goal line.

Two things kept deliberately simple for Phase 1a:

  * **No teleport.** The env always starts the drone at its origin; we
    fly in env coordinates and map to room coordinates by a constant
    offset (`room = env + start_xy`), so the drone effectively starts at
    the room's entry point without touching pybullet body state.

  * **Privileged geometric safety filter** (`_safe_action`): before
    executing, veto any command whose short lookahead drops clearance
    below a margin, substituting the safest menu action (else hover).
    This isolates the SEARCH-STRATEGY question from perception — the
    strategy layer decides *where*, this filter guarantees *safe*. In
    Phase 1b the clearance estimate comes from the world model instead
    of ground truth; the strategy layer is unchanged.

The policy speaks a small context dict (pos, beacon sense, 4 cardinal
rangefinders, step) and returns a `nav_action_set` id. Homing (the
return leg) is a shared greedy controller so strategies are compared on
SEARCH efficiency, not on how they fly home.
"""

import numpy as np

from planner.latent_mpc import DECIDE_EVERY
from planner.nav_action_set import HOVER, NAV_ACTION_VECS, nav_menu
from sim.envs import START, VelCommander, make_ctrl
from sim.scenarios import COLLISION_R

SAFE_MARGIN = COLLISION_R + 0.12  # veto actions whose lookahead drops below this


def _lookahead(pos_xy, vec, dt, steps):
    return (pos_xy[0] + vec[0] * dt * steps, pos_xy[1] + vec[1] * dt * steps)


def _safe_action(scenario, pos_xy, proposed, dt, steps=DECIDE_EVERY):
    """Privileged geometric veto: keep `proposed` if its lookahead stays
    clear; else pick the menu action with the most lookahead clearance;
    else hover. Returns an action id."""
    vecs = NAV_ACTION_VECS
    if scenario.clearance(_lookahead(pos_xy, vecs[proposed], dt, steps)) >= SAFE_MARGIN:
        return proposed
    best, best_clr = HOVER, scenario.clearance(pos_xy)
    for a in nav_menu():
        clr = scenario.clearance(_lookahead(pos_xy, vecs[a], dt, steps))
        if clr > best_clr:
            best, best_clr = a, clr
    return best


def _greedy_home(scenario, pos_xy, dt, steps=DECIDE_EVERY):
    """Shared homing: the menu action whose lookahead best reduces
    distance to the start point (then safety-filtered by the caller)."""
    vecs, s = NAV_ACTION_VECS, np.asarray(scenario.start_xy, dtype=float)
    best, best_d = HOVER, np.hypot(*(np.asarray(pos_xy) - s))
    for a in nav_menu():
        nxt = np.asarray(_lookahead(pos_xy, vecs[a], dt, steps))
        d = np.hypot(*(nxt - s))
        if d < best_d:
            best, best_d = a, d
    return best


def search_metrics(scenario, path, found_step, returned, collisions, n_decisions):
    """Env-free: assemble the mission scorecard from the recorded path."""
    return {
        "coverage": scenario.coverage(path),
        "target_found": found_step >= 0,
        "steps_to_find": found_step,
        "returned": bool(returned),
        "success": bool(found_step >= 0 and returned),
        "collisions": int(collisions),
        "crashed": bool(collisions > 0),
        "steps": int(n_decisions),
        "path": np.asarray(path),
    }


def run_search_episode(env, scenario, policy, seed, max_decisions=300):
    """One search mission on the real 48 Hz env. Returns the scorecard."""
    obs, _ = env.reset(seed=int(seed))
    cmd = VelCommander(make_ctrl(), env.CTRL_TIMESTEP)
    cmd.reset(obs[0][0:3])
    sx, sy = scenario.start_xy
    dt = env.CTRL_TIMESTEP

    def room_xy(state):  # env origin == the room's start point
        return (float(state[0]) + sx - START[0], float(state[1]) + sy - START[1])

    policy.begin(scenario)
    vecs = NAV_ACTION_VECS
    state = obs[0]
    path = [room_xy(state)]
    found_step, collisions, returned, phase = -1, 0, False, "search"

    for d in range(max_decisions):
        rpos = room_xy(state)
        if found_step < 0 and scenario.found(rpos):
            found_step, phase = d, "return"
        if phase == "return" and scenario.found_home(rpos):
            returned = True
            break
        if phase == "search":
            ctx = {
                "pos": rpos,
                "sense": scenario.sense_beacon(rpos),
                "ranges": scenario.range_sensors(rpos),
                "step": d,
            }
            a = policy.decide(ctx)
        else:
            a = _greedy_home(scenario, rpos, dt)
        a = _safe_action(scenario, rpos, a, dt)
        for _ in range(DECIDE_EVERY):
            obs, _, _, _, _ = env.step(cmd.rpm(state, vecs[a]).reshape(1, 4))
            state = obs[0]
            if scenario.clearance(room_xy(state)) < COLLISION_R:
                collisions += 1
                break
        path.append(room_xy(state))
    return search_metrics(scenario, path, found_step, returned, collisions, d + 1)


class _StraightProbe:
    """Selftest stand-in: always drive +x (no torch, no strategy)."""

    def begin(self, scenario) -> None:
        del scenario

    def decide(self, ctx) -> int:
        del ctx
        return nav_menu()[0]  # forward


def selftest() -> None:
    from sim.indoor.rooms import single_room

    # env-free: the safety filter vetoes a wall-bound command
    sc = single_room(3)
    # a spot 0.2 m from the +x wall, proposing forward -> should be vetoed
    x1 = sc.bounds[1]
    near_wall = (x1 - 0.2, 0.0)
    fwd = nav_menu()[0]
    a = _safe_action(sc, near_wall, fwd, dt=0.021, steps=8)
    assert a != fwd, "forward into the wall must be vetoed"
    assert NAV_ACTION_VECS[a][0] <= 0.0, "the safe substitute backs off / holds"
    # homing points roughly toward start
    home = _greedy_home(sc, (1.0, 1.0), dt=0.021, steps=8)
    v = NAV_ACTION_VECS[home]
    assert v[0] < 0 or v[1] < 0, "home from (1,1) means -x or -y (start is bottom-left)"
    # metrics schema
    m = search_metrics(sc, [sc.start_xy, sc.beacon_xy], 5, True, 0, 6)
    assert set(m) >= {"coverage", "target_found", "success", "returned", "collisions"}
    assert m["success"] and m["target_found"]
    print("SEARCH-EPISODE OK (env-free): safety veto + homing + metrics schema")


def selftest_sim() -> None:
    """Sim group: a few real-env decisions end to end."""
    from sim.envs import make_env
    from sim.indoor.rooms import single_room

    env = make_env()
    sc = single_room(3)
    m = run_search_episode(env, sc, _StraightProbe(), seed=3, max_decisions=6)
    env.close()
    assert m["steps"] >= 1 and m["path"].shape[1] == 2
    assert 0.0 <= m["coverage"] <= 1.0
    print(
        f"SEARCH-EPISODE SIM OK: {m['steps']} decisions, coverage {m['coverage']:.2f}"
    )


if __name__ == "__main__":
    import sys

    selftest()
    if "--sim" in sys.argv:
        selftest_sim()

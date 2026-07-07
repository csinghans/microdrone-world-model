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
return leg) is a shared BFS controller (route home over the safe-cell
graph) so strategies are compared on SEARCH efficiency, not on how they
fly home.
"""

import numpy as np

from planner.latent_mpc import DECIDE_EVERY
from planner.nav_action_set import HOVER, NAV_ACTION_VECS, nav_menu
from sim.envs import START, VelCommander, make_ctrl
from sim.scenarios import COLLISION_R

SAFE_MARGIN = COLLISION_R + 0.13  # veto actions whose braking ray drops below this
# ~the real stopping distance: ~0.05 m travelled per decision + PID overshoot.
# 0.8 m froze the drone (it stopped ~0.8 m short of everything in a cluttered
# room, 16x its per-decision travel — measured: it stalled mid-return)
BRAKE_DIST = 0.35


def _cardinal(dx, dy) -> int:
    """The nav action whose translation best matches direction (dx, dy)."""
    from planner.nav_action_set import FORWARD, REVERSE, STRAFE_L, STRAFE_R

    if abs(dx) >= abs(dy):
        return FORWARD if dx >= 0 else REVERSE
    return STRAFE_L if dy >= 0 else STRAFE_R


def _ray_clearance(scenario, pos_xy, vec, dist=BRAKE_DIST, samples=6):
    """Worst clearance along the command direction out to `dist` — the
    honest safety signal under PID momentum (the endpoint alone vetoes
    too late; the drone coasts). A zero-velocity command just samples
    the current point."""
    speed = float(np.hypot(vec[0], vec[1]))
    if speed < 1e-6:
        return scenario.clearance(pos_xy)
    ux, uy = vec[0] / speed, vec[1] / speed
    worst = 9.0
    for k in range(1, samples + 1):
        d = dist * k / samples
        worst = min(worst, scenario.clearance((pos_xy[0] + ux * d, pos_xy[1] + uy * d)))
    return worst


def _safe_action(scenario, pos_xy, proposed, dt=None, steps=None):
    """Privileged geometric veto with a braking-distance lookahead: keep
    `proposed` if its whole braking ray stays clear; else pick the menu
    action whose ray keeps the most clearance (reverse/hover win near a
    wall — they back off). Returns an action id. dt/steps unused (kept
    for the old call signature)."""
    del dt, steps
    vecs = NAV_ACTION_VECS
    if _ray_clearance(scenario, pos_xy, vecs[proposed]) >= SAFE_MARGIN:
        return proposed
    best, best_clr = HOVER, _ray_clearance(scenario, pos_xy, vecs[HOVER])
    for a in nav_menu():
        clr = _ray_clearance(scenario, pos_xy, vecs[a])
        if clr > best_clr:
            best, best_clr = a, clr
    return best


def _build_safe_grid(scenario, min_clear=0.5):
    """The safe-cell navigation graph (shared shape with the Frontier
    planner) — cells clear enough to occupy, for BFS routing."""
    from search.strategies import scenario_free_cells

    x0, x1, y0, y1 = scenario.bounds
    nx = max(1, int(round((x1 - x0) / scenario.cell)))
    ny = max(1, int(round((y1 - y0) / scenario.cell)))
    safe = set(scenario_free_cells(scenario, nx, ny, x0, y0, scenario.cell, min_clear))
    return {"safe": safe, "nx": nx, "ny": ny, "x0": x0, "y0": y0, "cell": scenario.cell}


def _cell_of(grid, pos):
    i = int((pos[0] - grid["x0"]) / grid["cell"])
    j = int((pos[1] - grid["y0"]) / grid["cell"])
    return (min(max(i, 0), grid["nx"] - 1), min(max(j, 0), grid["ny"] - 1))


def _centre(grid, c):
    return (
        grid["x0"] + (c[0] + 0.5) * grid["cell"],
        grid["y0"] + (c[1] + 0.5) * grid["cell"],
    )


def _bfs_home_path(grid, pos_xy, start_xy):
    """BFS over safe cells from the drone's cell to the start cell; return
    the cell path (start-of-graph excluded). Empty if unreachable. The
    caller CACHES and follows this — recomputing every decision oscillates
    between adjacent cells and stalls (measured: crashes + zero returns)."""
    from collections import deque

    safe = grid["safe"]
    start = _cell_of(grid, pos_xy)
    goal = _cell_of(grid, start_xy)
    if start not in safe or goal not in safe or start == goal:
        return []
    prev, q = {start: None}, deque([start])
    while q:
        c = q.popleft()
        if c == goal:
            break
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nb = (c[0] + di, c[1] + dj)
            if nb in safe and nb not in prev:
                prev[nb] = c
                q.append(nb)
    if goal not in prev:
        return []
    path = [goal]
    while prev[path[-1]] is not None:
        path.append(prev[path[-1]])
    path.reverse()
    return path[1:]  # drop the start-of-graph cell (where we already are)


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


def run_search_episode(env, scenario, policy, seed, max_decisions=300, speed=1.0):
    """One search mission on the real 48 Hz env. Returns the scorecard.
    `speed` scales the executed command velocity (the safety filter's
    lookahead is a fixed DISTANCE, so slower flight overshoots less and
    the same veto margin holds with room to spare)."""
    obs, _ = env.reset(seed=int(seed))
    cmd = VelCommander(make_ctrl(), env.CTRL_TIMESTEP)
    cmd.reset(obs[0][0:3])
    sx, sy = scenario.start_xy

    def room_xy(state):  # env origin == the room's start point
        return (float(state[0]) + sx - START[0], float(state[1]) + sy - START[1])

    policy.begin(scenario)
    grid = _build_safe_grid(scenario)  # for BFS homing on the return leg
    vecs = float(speed) * NAV_ACTION_VECS
    state = obs[0]
    path = [room_xy(state)]
    found_step, collisions, returned, phase = -1, 0, False, "search"
    home_path = []  # cached BFS route home, followed cell by cell

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
            here = _cell_of(grid, rpos)
            while home_path and home_path[0] == here:
                home_path.pop(0)
            if not home_path:
                home_path = _bfs_home_path(grid, rpos, scenario.start_xy)
            if home_path:
                cx, cy = _centre(grid, home_path[0])
                a = _cardinal(cx - rpos[0], cy - rpos[1])
            else:  # already in the start cell (or no route): aim straight
                a = _cardinal(
                    scenario.start_xy[0] - rpos[0], scenario.start_xy[1] - rpos[1]
                )
        a = _safe_action(scenario, rpos, a)
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
    # BFS homing: from the beacon (always clear, far from start) a safe
    # route home exists and its first step heads back toward start (-x)
    grid = _build_safe_grid(sc)
    hp = _bfs_home_path(grid, sc.beacon_xy, sc.start_xy)
    assert hp, "a safe route home exists from the beacon"
    cx, cy = _centre(grid, hp[0])
    a = _cardinal(cx - sc.beacon_xy[0], cy - sc.beacon_xy[1])
    assert a in (nav_menu()), "first home step is a valid nav action"
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

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

from functools import partial

import numpy as np

from planner.latent_mpc import DECIDE_EVERY
from planner.nav_action_set import (
    FORWARD,
    HOVER,
    NAV_ACTION_VECS,
    REVERSE,
    STRAFE_L,
    STRAFE_R,
    nav_menu,
)
from sim.envs import START, VelCommander, grab_frame, make_ctrl
from sim.scenarios import COLLISION_R
from sim.search_scenario import remove_bodies

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


# each cardinal nav action reads exactly one rangefinder beam
_BEAM = {FORWARD: "+x", REVERSE: "-x", STRAFE_L: "+y", STRAFE_R: "-y"}
BEAM_STOP = 0.55  # veto a cardinal whose beam is closer than this (a single
# point beam + PID momentum; a touch more conservative than the geometric ray)


def _safe_action_rf(scenario, pos_xy, proposed, dt=None, steps=None):
    """DEPLOYABLE safety veto: use only the 4 cardinal rangefinders (the
    SGBA sensor suite), not omnidirectional ground truth. Each cardinal
    nav action aligns with one beam; keep it if that beam is clear, else
    take the cardinal whose beam reads farthest (hover if all are close).
    The honest question: do 4 beams suffice where full clearance did?"""
    del dt, steps
    beams = scenario.range_sensors(pos_xy)
    if proposed == HOVER or beams.get(_BEAM.get(proposed), 9.0) >= BEAM_STOP:
        return proposed
    best, best_r = HOVER, 0.0
    for a in nav_menu():
        r = 9.0 if a == HOVER else beams[_BEAM[a]]
        if r > best_r:
            best, best_r = a, r
    return HOVER if best_r < BEAM_STOP else best


# the drone is a disc of radius COLLISION_R; a single beam only checks its
# centerline, so an off-axis corner clips the body while the aligned beam reads
# clear. The N-beam veto protects the whole swept body corridor.
CORRIDOR_HALF = COLLISION_R + 0.08  # 0.30 m — the body half-width the veto guards


def _corridor_clear(beams, ux, uy, max_range=9.0):
    """Nearest along-distance to a beam hit inside the body corridor of a
    move along unit (ux, uy); `max_range` if the corridor is clear. Each
    beam (angle, dist) hit is projected into the motion frame: `along` is
    the forward component, `lateral` the sideways one; a hit counts only
    if it is AHEAD (along > 0) and within the body half-width."""
    best = max_range
    for a, d in beams:
        hx, hy = d * np.cos(a), d * np.sin(a)
        along = hx * ux + hy * uy
        lateral = abs(-hx * uy + hy * ux)
        if along > 0.0 and lateral < CORRIDOR_HALF:
            best = min(best, along)
    return best


def _safe_action_beams(scenario, pos_xy, proposed, dt=None, steps=None, n_beams=8):
    """DEPLOYABLE body-aware veto over an `n_beams` rangefinder ring: keep
    `proposed` if its swept body corridor stays clear past BEAM_STOP, else
    take the menu action whose corridor is clearest (hover if none is).
    Degrades to the single-beam `_safe_action_rf` at n_beams=4 (only the
    aligned cardinal beam lies in a cardinal action's corridor); more beams
    add the off-axis diagonals that catch between-beam corners."""
    del dt, steps
    beams = scenario.beam_ranges(pos_xy, n_beams=n_beams)
    vecs = NAV_ACTION_VECS

    def clear(a):
        v = vecs[a]
        s = float(np.hypot(v[0], v[1]))
        if s < 1e-6:
            return 9.0  # hover: no motion, no corridor to block
        return _corridor_clear(beams, v[0] / s, v[1] / s)

    if proposed == HOVER or clear(proposed) >= BEAM_STOP:
        return proposed
    best, best_c = HOVER, clear(HOVER)
    for a in nav_menu():
        c = clear(a)
        if c > best_c:
            best, best_c = a, c
    return HOVER if best_c < BEAM_STOP else best


_SAFETY = {
    "geometric": _safe_action,
    "rangefinder": _safe_action_rf,
    "beams4": partial(_safe_action_beams, n_beams=4),
    "beams8": partial(_safe_action_beams, n_beams=8),
    "beams16": partial(_safe_action_beams, n_beams=16),
}


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


def run_search_episode(
    env,
    scenario,
    policy,
    seed,
    max_decisions=300,
    speed=1.0,
    safety="geometric",
    on_collision=None,
):
    """One search mission on the real 48 Hz env. Returns the scorecard.
    `speed` scales the executed command velocity (the safety filter's
    lookahead is a fixed DISTANCE, so slower flight overshoots less and
    the same veto margin holds with room to spare). `safety` selects the
    filter: "geometric" (privileged omnidirectional clearance) or
    "rangefinder" (the deployable 4-beam SGBA-style sensor).
    `on_collision`, if given, is called once per collision with a
    forensics dict (executed action, forward-cone clearance, beams) —
    for diagnosing WHICH failure mode the residual collisions are; when
    None (the default) behaviour is bit-for-bit unchanged."""
    safe_fn = _SAFETY[safety]
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
        proposed = a
        a = safe_fn(scenario, rpos, a)
        for _ in range(DECIDE_EVERY):
            obs, _, _, _, _ = env.step(cmd.rpm(state, vecs[a]).reshape(1, 4))
            state = obs[0]
            if scenario.clearance(room_xy(state)) < COLLISION_R:
                collisions += 1
                if on_collision is not None:
                    beams = scenario.range_sensors(rpos)
                    on_collision(
                        {
                            "decision": d,
                            "phase": phase,
                            "proposed": int(proposed),
                            "executed": int(a),
                            "rpos": (float(rpos[0]), float(rpos[1])),
                            "hit": room_xy(state),
                            "beams": {k: float(v) for k, v in beams.items()},
                            "fwd_clear": float(scenario.forward_clearance(rpos)),
                            "clearance_pre": float(scenario.clearance(rpos)),
                        }
                    )
                break
        path.append(room_xy(state))
    return search_metrics(scenario, path, found_step, returned, collisions, d + 1)


def coverage_metrics(
    sc, path, steps_to_cover, returned, collisions, n_dec, thr, hit_threshold=False
):
    """Env-free scorecard for a COMPLETE-COVERAGE mission (distinct from
    search_metrics, which scores beacon find-and-return). `coverage` (the
    fraction actually swept) is the metric of record; `success` = the cover
    phase ended (threshold or plateau) AND the drone made it home."""
    return {
        "coverage": sc.coverage(path),
        "coverage_complete": bool(steps_to_cover >= 0),
        "hit_threshold": bool(hit_threshold),
        "steps_to_cover": int(steps_to_cover),
        "returned": bool(returned),
        # success needs BOTH: finished covering (threshold/plateau) AND home
        "success": bool(steps_to_cover >= 0 and returned),
        "collisions": int(collisions),
        "crashed": bool(collisions > 0),
        "steps": int(n_dec),
        "threshold": float(thr),
        "path": np.asarray(path),
    }


def run_coverage_episode(
    env,
    scenario,
    policy,
    seed,
    max_decisions=800,
    speed=0.6,
    safety="beams8",
    coverage_threshold=0.90,
    plateau=100,
):
    """A COMPLETE-COVERAGE mission: roam until the covered fraction reaches
    `coverage_threshold` OR PLATEAUS (no new cell covered for `plateau`
    decisions — "covered what I can"), THEN fly home (reusing the BFS
    homing). The plateau trigger matters because the deployable-reachable
    ceiling is well below 1.0 (Phase 0: geometric Frontier under beams8
    tops ~0.80 on a clean room — the safety margin leaves wall-hugging /
    behind-obstacle cells unreached), so a fixed high threshold would never
    fire and the drone would never come home.

    The world-model coverage policy's grader; the geometric strategies
    (Frontier/RandomWalk/WallFollow) run here unchanged — they ignore the
    added `frame`/`covered_fraction` ctx keys. `run_search_episode` (beacon
    find-and-return) is left bit-for-bit intact. Coverage is tracked LIVE
    with the SAME definition as `SearchScenario.coverage`. The camera frame
    is grabbed (and the room rendered) only when the policy advertises
    `wants_frame` — so the geometric ceiling probe pays no rendering cost."""
    safe_fn = _SAFETY[safety]
    render = bool(getattr(policy, "wants_frame", False))
    obs, _ = env.reset(seed=int(seed))
    cmd = VelCommander(make_ctrl(), env.CTRL_TIMESTEP)
    cmd.reset(obs[0][0:3])
    sx, sy = scenario.start_xy

    def room_xy(state):
        return (float(state[0]) + sx - START[0], float(state[1]) + sy - START[1])

    body_ids = None
    if render:
        body_ids = scenario.spawn_bodies(env, offset=(sx - START[0], sy - START[1]))
    policy.begin(scenario)
    grid = _build_safe_grid(scenario)
    vecs = float(speed) * NAV_ACTION_VECS
    # live coverage: free-cell centres + a covered mask (== scenario.coverage)
    free = np.asarray(scenario.free_cells(), dtype=float)
    covered = np.zeros(len(free), dtype=bool)
    srange = float(scenario.sensor_range)

    def mark(pos):
        if len(free):
            covered[np.linalg.norm(free - np.asarray(pos), axis=1) <= srange] = True

    def cov_frac():
        return float(covered.mean()) if len(free) else 0.0

    state = obs[0]
    path = [room_xy(state)]
    steps_to_cover, collisions, returned, phase = -1, 0, False, "search"
    home_path = []
    no_gain, prev_cov, hit_threshold = 0, 0.0, False

    for d in range(max_decisions):
        rpos = room_xy(state)
        mark(rpos)
        cf = cov_frac()
        if cf > prev_cov + 1e-9:  # covered a new cell -> reset the plateau clock
            no_gain, prev_cov = 0, cf
        else:
            no_gain += 1
        if steps_to_cover < 0 and (cf >= coverage_threshold or no_gain >= plateau):
            hit_threshold = cf >= coverage_threshold
            steps_to_cover, phase = d, "return"
        if phase == "return" and scenario.found_home(rpos):
            returned = True
            break
        if phase == "search":
            ctx = {
                "pos": rpos,
                # coverage mission ignores the beacon; sense=None keeps the
                # geometric strategies' shared beacon-approach branch dormant
                # so Frontier/RandomWalk/WallFollow run their pure coverage
                "sense": None,
                "ranges": scenario.range_sensors(rpos),
                "frame": grab_frame(env) if render else None,
                "step": d,
                "covered_fraction": cov_frac(),
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
            else:
                a = _cardinal(
                    scenario.start_xy[0] - rpos[0], scenario.start_xy[1] - rpos[1]
                )
        a = safe_fn(scenario, rpos, a)
        for _ in range(DECIDE_EVERY):
            obs, _, _, _, _ = env.step(cmd.rpm(state, vecs[a]).reshape(1, 4))
            state = obs[0]
            if scenario.clearance(room_xy(state)) < COLLISION_R:
                collisions += 1
                break
        path.append(room_xy(state))
    if body_ids is not None:
        remove_bodies(env, body_ids)
    return coverage_metrics(
        scenario,
        path,
        steps_to_cover,
        returned,
        collisions,
        d + 1,
        coverage_threshold,
        hit_threshold,
    )


class _StraightProbe:
    """Selftest stand-in: always drive +x (no torch, no strategy)."""

    def begin(self, scenario) -> None:
        del scenario

    def decide(self, ctx) -> int:
        del ctx
        return nav_menu()[0]  # forward


def selftest() -> None:
    from sim.indoor.rooms import single_room
    from sim.search_scenario import SearchScenario

    # env-free: the safety filter vetoes a wall-bound command
    sc = single_room(3)
    # a spot 0.2 m from the +x wall, proposing forward -> should be vetoed
    x1 = sc.bounds[1]
    near_wall = (x1 - 0.2, 0.0)
    fwd = nav_menu()[0]
    a = _safe_action(sc, near_wall, fwd, dt=0.021, steps=8)
    assert a != fwd, "forward into the wall must be vetoed"
    assert NAV_ACTION_VECS[a][0] <= 0.0, "the safe substitute backs off / holds"
    # the deployable rangefinder filter vetoes the same wall-bound forward
    # using only the 4 beams (its +x beam reads < BEAM_STOP at the wall)
    arf = _safe_action_rf(sc, near_wall, fwd)
    assert arf != fwd, "rangefinder filter also vetoes forward into the wall"
    assert "rangefinder" in _SAFETY and "geometric" in _SAFETY
    # the N-beam body-aware filter vetoes the same wall-bound forward, and at
    # n_beams=4 it must agree with the single-beam rangefinder filter (its
    # corridor sees only the aligned cardinal beam) — the ablation control
    for nb in (4, 8, 16):
        assert (
            _safe_action_beams(sc, near_wall, fwd, n_beams=nb) != fwd
        ), f"beams{nb} filter vetoes forward into the wall"
    assert {"beams4", "beams8", "beams16"} <= set(_SAFETY)
    # an off-axis corner clips the disc body while the +x beam reads clear:
    # a beam ring catches it (corridor blocked) where the single ray cannot
    corner_sc = SearchScenario(
        bounds=(-2.5, 2.5, -2.5, 2.5),
        obstacles=((0.32, 0.32, 0.1),),  # a small disc ~45 deg off +x, close
        beacon_xy=(2.0, 2.0),
        start_xy=(0.0, 0.0),
    )
    origin = (0.0, 0.0)
    assert corner_sc.range_sensors(origin)["+x"] > BEAM_STOP, "the +x ray misses it"
    assert (
        _corridor_clear(corner_sc.beam_ranges(origin, 8), 1.0, 0.0) < BEAM_STOP
    ), "the 8-beam corridor catches the off-axis corner the single ray missed"
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
    # coverage-mission scorecard schema (success needs cover AND return home)
    cm = coverage_metrics(sc, [sc.start_xy, sc.beacon_xy], 4, True, 0, 6, 0.9)
    assert set(cm) >= {"coverage", "coverage_complete", "steps_to_cover", "success"}
    assert cm["success"] and cm["coverage_complete"]
    assert not coverage_metrics(sc, [sc.start_xy], -1, False, 0, 6, 0.9)["success"]
    print("SEARCH-EPISODE OK (env-free): safety veto + homing + metrics schema")


def selftest_sim() -> None:
    """Sim group: a few real-env decisions end to end."""
    from search.strategies import get_strategy
    from sim.envs import make_env
    from sim.indoor.rooms import single_room

    env = make_env()
    sc = single_room(3)
    m = run_search_episode(env, sc, _StraightProbe(), seed=3, max_decisions=6)
    # complete-coverage runner: Frontier runs here unchanged (ignores the
    # added frame ctx key); low threshold so it flips to return quickly
    mc = run_coverage_episode(
        env,
        sc,
        get_strategy("frontier"),
        seed=3,
        max_decisions=6,
        coverage_threshold=0.3,
    )
    env.close()
    assert m["steps"] >= 1 and m["path"].shape[1] == 2
    assert 0.0 <= m["coverage"] <= 1.0
    assert 0.0 <= mc["coverage"] <= 1.0 and mc["path"].shape[1] == 2
    print(
        f"SEARCH-EPISODE SIM OK: search cov {m['coverage']:.2f}, "
        f"coverage-mission cov {mc['coverage']:.2f} (s2c {mc['steps_to_cover']})"
    )


if __name__ == "__main__":
    import sys

    selftest()
    if "--sim" in sys.argv:
        selftest_sim()

"""The wedge, made visible: ONE 512 KB world-model PAIR flying BOTH tasks.

Records two god-view GIFs from the flight-mode stack (planner/flight_mode):
  * transit      — the PINNED CHAMPION WM avoids a pillar corridor (whole-
                   course top-down, reusing eval_integration._god_frame).
  * indoor_search— the UNIFIED WM's stack (frontier + beams8) covers a room,
                   finds the beacon and returns (a drone-following top-down).

Same repo, two resident WMs (~163 KB int8 together), one mode switch. The
point of the picture: avoidance + indoor search from one embedded pair.

  python -m scripts.demo_two_mode                 # writes docs/media/demo_*.gif
  python -m scripts.demo_two_mode --selftest      # wiring only, no sim
"""

import argparse
import os
import sys

import numpy as np

MEDIA = os.path.join("docs", "media")


def _follow_god(env, x, y, span=3.0, res=360):
    """Top-down camera following the drone at (x, y) — for the room, where
    the scene is 2-D (unlike the transit corridor's fixed course view)."""
    import pybullet as p

    vm = p.computeViewMatrix(
        cameraEyePosition=[x, y, span * 1.05],
        cameraTargetPosition=[x, y, 0.5],
        cameraUpVector=[1, 0, 0],
    )
    pm = p.computeProjectionMatrixFOV(fov=60.0, aspect=1.0, nearVal=0.1, farVal=60.0)
    _w, _h, rgb, _d, _s = p.getCameraImage(
        res,
        res,
        viewMatrix=vm,
        projectionMatrix=pm,
        renderer=p.ER_TINY_RENDERER,
        physicsClientId=env.CLIENT,
    )
    return np.reshape(rgb, (res, res, 4))[:, :, :3].astype(np.uint8)


def _record_transit(env, seed, speed=1.0):
    """Champion WM + general transit champion; capture the whole-course view."""
    from eval.eval_integration import _god_frame
    from planner.action_set import ACTION_VECS, FORWARD
    from planner.flight_mode import load_wm_cached
    from planner.latent_mpc import DECIDE_EVERY
    from planner.learned_policy import LearnedPolicy, load_policy, zip_path
    from sim.envs import VelCommander, grab_frame, make_ctrl
    from sim.scenario_registry import get as get_scenario
    from sim.scenarios import GOAL_X, TMAX
    from world_model.training import MODEL

    enc, pred, cheads, _n, meta = load_wm_cached(MODEL)
    pol = LearnedPolicy(
        load_policy(zip_path(hard=True, xp=True, edge=True)),
        enc,
        pred,
        cheads,
        meta,
        speed=speed,
    )
    obs, _ = env.reset(seed=seed)
    cmd = VelCommander(make_ctrl(), env.CTRL_TIMESTEP)
    state = obs[0]
    cmd.reset(state[0:3])
    sc = get_scenario("dense").spawn(env, np.random.default_rng(seed), speed=speed)
    pol.begin(sc.positions())
    frames, a = [], FORWARD
    for t in range(TMAX):
        if t % DECIDE_EVERY == 0:
            a = pol.decide(grab_frame(env), state)
            frames.append(_god_frame(env, GOAL_X))
        obs, *_ = env.step(cmd.rpm(state, speed * ACTION_VECS[a]).reshape(1, 4))
        state = obs[0]
        sc.step()
        if state[0] >= GOAL_X:
            break
    return frames


def _record_indoor(env, seed, speed=0.6, max_decisions=1500, stride=3):
    """Unified WM resident (detection brain); frontier + beams8 fly the room.
    Capture the search leg + the return leg with a drone-following view."""
    from eval.search_episode import (
        _SAFETY,
        _bfs_home_path,
        _build_safe_grid,
        _cardinal,
        _cell_of,
        _centre,
    )
    from planner.flight_mode import UNIFIED_WM, load_wm_cached
    from planner.latent_mpc import DECIDE_EVERY
    from planner.nav_action_set import NAV_ACTION_VECS
    from search.strategies import get_strategy
    from sim.envs import START, VelCommander, make_ctrl
    from sim.indoor.rooms import single_room
    from sim.scenarios import COLLISION_R

    load_wm_cached(UNIFIED_WM)  # the unified WM rides this mode (detection)
    sc = single_room(seed)
    pol = get_strategy("frontier")
    safe_fn = _SAFETY["beams8"]
    obs, _ = env.reset(seed=int(seed))
    cmd = VelCommander(make_ctrl(), env.CTRL_TIMESTEP)
    cmd.reset(obs[0][0:3])
    sx, sy = sc.start_xy

    def room_xy(s):
        return (float(s[0]) + sx - START[0], float(s[1]) + sy - START[1])

    pol.begin(sc)
    sc.spawn_bodies(env, offset=(sx - START[0], sy - START[1]))
    grid = _build_safe_grid(sc)
    vecs = float(speed) * NAV_ACTION_VECS
    state = obs[0]
    frames, phase, home = [], "search", []
    found = -1
    for d in range(max_decisions):
        rpos = room_xy(state)
        if found < 0 and sc.found(rpos):
            found, phase = d, "return"
        if phase == "return" and sc.found_home(rpos):
            break
        if phase == "search":
            a = pol.decide(
                {
                    "pos": rpos,
                    "sense": sc.sense_beacon(rpos),
                    "ranges": sc.range_sensors(rpos),
                    "step": d,
                }
            )
        else:
            here = _cell_of(grid, rpos)
            while home and home[0] == here:
                home.pop(0)
            if not home:
                home = _bfs_home_path(grid, rpos, sc.start_xy)
            if home:
                cx, cy = _centre(grid, home[0])
                a = _cardinal(cx - rpos[0], cy - rpos[1])
            else:
                a = _cardinal(sc.start_xy[0] - rpos[0], sc.start_xy[1] - rpos[1])
        a = safe_fn(sc, rpos, a)
        if d % stride == 0:  # subsample: a room search is long, keep the GIF short
            frames.append(_follow_god(env, float(state[0]), float(state[1])))
        for _ in range(DECIDE_EVERY):
            obs, *_ = env.step(cmd.rpm(state, vecs[a]).reshape(1, 4))
            state = obs[0]
            if sc.clearance(room_xy(state)) < COLLISION_R:
                break
    return frames


def selftest() -> None:
    from planner.flight_mode import get_mode

    assert get_mode("transit") and get_mode("indoor_search")
    assert callable(_follow_god) and callable(_record_transit)
    print("DEMO-TWO-MODE OK: transit + indoor_search capture wired")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--transit-seed", type=int, default=7)
    ap.add_argument("--indoor-seed", type=int, default=130000)
    ap.add_argument("--out-dir", default=MEDIA)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return

    from eval.eval_integration import _gif
    from sim.envs import make_env

    os.makedirs(args.out_dir, exist_ok=True)
    env = make_env()
    try:
        tf = _record_transit(env, args.transit_seed)
        _gif(tf, os.path.join(args.out_dir, "demo_transit.gif"), scale=1)
        print(f"[demo] transit: {len(tf)} frames -> demo_transit.gif")
        inf = _record_indoor(env, args.indoor_seed)
        _gif(inf, os.path.join(args.out_dir, "demo_indoor.gif"), scale=1)
        print(f"[demo] indoor_search: {len(inf)} frames -> demo_indoor.gif")
    finally:
        env.close()
    print(f"DEMO DONE: {args.out_dir}/demo_{{transit,indoor}}.gif")


if __name__ == "__main__":
    sys.exit(main())

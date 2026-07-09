"""v0.8 made visible: finding a target the level camera CANNOT see head-on.

An under-bed target sits at z=0.3 m. At cruise height (1.0 m) the forward
camera looks over it (elevation > the 28 deg FOV), so a flat sweep misses it
entirely. This demo flies the deployable indoor stack — Frontier coverage +
beams8 — until the abstract range sensor says the beacon is near, then does
the v0.8 maneuver: DESCEND to floor level while YAW-scanning, and confirm the
target VISUALLY with the low-altitude detection head (target_head_low.pt) on
the unified WM latent. No WM retrain: the frozen latent sees the target once
the drone drops to its height and turns to face it.

Recorded from an OBLIQUE follow camera (a top-down view would hide the whole
point — the vertical drop). Writes docs/media/demo_indoor_vertical.gif.

  python -m scripts.demo_vertical                 # write the GIF
  python -m scripts.demo_vertical --selftest      # wiring only, no sim
"""

import argparse
import dataclasses
import os
import sys

import numpy as np

OUT = os.path.join("docs", "media", "demo_indoor_vertical.gif")
HEAD = os.path.join("output", "target_head_low.pt")
TARGET_Z = 0.3  # under-bed target height (alt_v1's low regime)


def _follow_oblique(env, x, y, z, res=360):
    """Oblique follow camera (behind + above the drone) so the vertical drop
    and a floor-level target are visible — a top-down view hides altitude."""
    import pybullet as p

    vm = p.computeViewMatrix(
        cameraEyePosition=[x - 2.8, y - 2.0, z + 2.2],
        cameraTargetPosition=[x, y, z - 0.1],
        cameraUpVector=[0, 0, 1],
    )
    pm = p.computeProjectionMatrixFOV(fov=55.0, aspect=1.0, nearVal=0.05, farVal=60.0)
    _w, _h, rgb, _d, _s = p.getCameraImage(
        res,
        res,
        viewMatrix=vm,
        projectionMatrix=pm,
        renderer=p.ER_TINY_RENDERER,
        physicsClientId=env.CLIENT,
    )
    return np.reshape(rgb, (res, res, 4))[:, :, :3].astype(np.uint8)


def record(env, seed, thr=0.5, speed=0.6, max_decisions=900, stride=2):
    import torch

    from eval.eval_alt_detect import _in_fov_alt
    from eval.search_episode import (
        _SAFETY,
        _bfs_home_path,
        _build_safe_grid,
        _cardinal,
        _cell_of,
        _centre,
    )
    from planner.flight_mode import UNIFIED_WM, load_wm_cached
    from planner.latent_mpc import DECIDE_EVERY, _frame_tensor
    from planner.nav_action_set import LIFT_V, NAV_ACTION_VECS, YAW_RATE
    from search.strategies import get_strategy
    from search.target_detector import DetectionHead
    from sim.envs import START, VelCommander, grab_frame, make_ctrl
    from sim.indoor.rooms import single_room
    from sim.scenarios import FOV_HALF_DEG
    from sim.search_scenario import remove_bodies

    enc, _p, _c, _n, _m = load_wm_cached(UNIFIED_WM)
    detector = DetectionHead().load(HEAD)
    # a single room with the beacon forced UNDER-BED (z=0.3), rendered
    sc = dataclasses.replace(single_room(seed, n_obstacles=2), beacon_z=TARGET_Z)
    target = sc.beacon_xy
    safe_fn = _SAFETY["beams8"]

    obs, _ = env.reset(seed=int(seed))
    cmd = VelCommander(make_ctrl(), env.CTRL_TIMESTEP)
    cmd.reset(obs[0][0:3])
    sx, sy = sc.start_xy
    off = (sx - START[0], sy - START[1])

    def room_xy(state):
        return (float(state[0]) + sx - START[0], float(state[1]) + sy - START[1])

    def detect(rpos, z_cam):
        frame = grab_frame(env)
        with torch.no_grad():
            z = enc(_frame_tensor(frame)).numpy().reshape(1, -1)
        p = float(detector.prob(z)[0])
        in_fov = _in_fov_alt(rpos, target, TARGET_Z, z_cam, FOV_HALF_DEG)
        return p, in_fov

    ids = sc.spawn_bodies(env, offset=off)
    tid = sc.spawn_target(env, target, offset=off, target_z=TARGET_Z)
    pol = get_strategy("frontier")
    pol.begin(sc)
    grid = _build_safe_grid(sc)
    vecs = float(speed) * NAV_ACTION_VECS
    down = np.array([0.0, 0.0, -LIFT_V, 0.0])
    up = np.array([0.0, 0.0, LIFT_V, 0.0])
    yaw_cmd = np.array([0.0, 0.0, 0.0, YAW_RATE])

    state = obs[0]
    frames, phase, home_path = [], "search", []
    found, returned, hits = False, False, 0
    d = 0

    def snap():
        if d % stride == 0:
            frames.append(
                _follow_oblique(env, float(state[0]), float(state[1]), float(state[2]))
            )

    while d < max_decisions and phase != "done":
        rpos = room_xy(state)
        z_cam = float(state[2])
        # near the target (abstract range sensor) -> drop + look
        near = sc.sense_beacon(rpos) is not None
        if phase == "search" and near:
            phase = "descend"
        if phase == "descend":  # drop to the target's height, then yaw-scan
            if z_cam > TARGET_Z + 0.1:
                for _ in range(DECIDE_EVERY):
                    obs, *_ = env.step(cmd.rpm(state, down).reshape(1, 4))
                    state = obs[0]
                d += 1
                snap()
                continue
            p, in_fov = detect(rpos, z_cam)
            hits = hits + 1 if p >= thr else 0
            if hits >= 2 and in_fov:
                found, phase = True, "return"
            for _ in range(DECIDE_EVERY):  # slow spin to bring it into the FOV
                obs, *_ = env.step(cmd.rpm(state, yaw_cmd).reshape(1, 4))
                state = obs[0]
            d += 1
            snap()
            if d % 40 == 0 and not found:  # give up the scan, resume coverage
                phase = "search"
            continue
        if phase == "return":  # rise back to cruise, then BFS home
            if z_cam < 0.9:
                for _ in range(DECIDE_EVERY):
                    obs, *_ = env.step(cmd.rpm(state, up).reshape(1, 4))
                    state = obs[0]
                d += 1
                snap()
                continue
            if sc.found_home(rpos):
                returned, phase = True, "done"
                break
            here = _cell_of(grid, rpos)
            while home_path and home_path[0] == here:
                home_path.pop(0)
            if not home_path:
                home_path = _bfs_home_path(grid, rpos, sc.start_xy)
            cx, cy = _centre(grid, home_path[0]) if home_path else sc.start_xy
            a = safe_fn(sc, rpos, _cardinal(cx - rpos[0], cy - rpos[1]))
        else:  # search coverage
            a = safe_fn(
                sc,
                rpos,
                pol.decide(
                    {
                        "pos": rpos,
                        "sense": None,
                        "ranges": sc.range_sensors(rpos),
                        "step": d,
                    }
                ),
            )
        for _ in range(DECIDE_EVERY):
            obs, *_ = env.step(cmd.rpm(state, vecs[a]).reshape(1, 4))
            state = obs[0]
        d += 1
        snap()

    remove_bodies(env, ids + [tid])
    print(
        f"[demo] vertical seed {seed}: found={found} returned={returned} "
        f"frames={len(frames)} decisions={d}"
    )
    return frames, found, returned


def selftest() -> None:
    # wiring-only (CI has no local artifacts: output/ is git-ignored, so the
    # detection head is NOT asserted present here — a real run needs it).
    from planner.flight_mode import UNIFIED_WM

    assert UNIFIED_WM and callable(_follow_oblique) and callable(record)
    assert TARGET_Z < 0.5 and HEAD.endswith("target_head_low.pt")
    print("DEMO-VERTICAL OK: under-bed visual-search capture wired")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=130000)
    ap.add_argument("--thr", type=float, default=0.5)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    from eval.eval_integration import _gif
    from sim.envs import make_env

    env = make_env()
    try:
        frames, found, returned = record(env, args.seed, thr=args.thr)
    finally:
        env.close()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    _gif(frames, args.out, scale=1)
    print(f"DEMO-VERTICAL DONE: {args.out} (found={found}, returned={returned})")


if __name__ == "__main__":
    sys.exit(main())

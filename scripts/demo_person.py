"""SAR made visible: find a PERSON (not an abstract beacon) by SEEING it.

A capsule person stands in the room. The drone flies the deployable indoor
stack (Frontier coverage + beams8) and every few decisions does a 360 deg
hover-yaw scan, confirming the person VISUALLY with the person detection head
(target_head_person.pt) on the frozen unified WM latent. Per-frame recall is
moderate (~0.5), so the scan COMPOUNDS it: a steady target across consecutive
scan yaws (confirm=2) fires, while the head never false-alarms on box clutter
(person_v1: box-FA 0.000). No WM retrain — only the head learned "person".

Recorded from an oblique follow camera. Writes docs/media/demo_person.gif.

  python -m scripts.demo_person                 # write the GIF
  python -m scripts.demo_person --selftest      # wiring only, no sim
"""

import argparse
import os
import sys

import numpy as np

OUT = os.path.join("docs", "media", "demo_person.gif")
HEAD = os.path.join("output", "target_head_person.pt")


def record(env, seed, thr=0.5, speed=0.6, max_decisions=900, scan_every=22, stride=2):
    import torch

    from eval.eval_person_detect import _spawn_person
    from eval.eval_yaw_detect import _in_fov_yaw
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
    from planner.nav_action_set import NAV_ACTION_VECS, YAW_RATE
    from scripts.demo_vertical import _follow_oblique
    from search.strategies import get_strategy
    from search.target_detector import DetectionHead
    from sim.envs import START, VelCommander, grab_frame, make_ctrl
    from sim.indoor.rooms import single_room
    from sim.scenarios import COLLISION_R, FOV_HALF_DEG

    enc, _p, _c, _n, _m = load_wm_cached(UNIFIED_WM)
    detector = DetectionHead().load(HEAD)
    sc = single_room(seed, n_obstacles=2)
    person = sc.beacon_xy
    safe_fn = _SAFETY["beams8"]

    obs, _ = env.reset(seed=int(seed))
    cmd = VelCommander(make_ctrl(), env.CTRL_TIMESTEP)
    cmd.reset(obs[0][0:3])
    sx, sy = sc.start_xy
    off = (sx - START[0], sy - START[1])

    def room_xy(state):
        return (float(state[0]) + sx - START[0], float(state[1]) + sy - START[1])

    def detect():
        with torch.no_grad():
            z = enc(_frame_tensor(grab_frame(env))).numpy().reshape(1, -1)
        return float(detector.prob(z)[0])

    ids = sc.spawn_bodies(env, offset=off)
    pid = _spawn_person(env, person, off, [0.95, 0.10, 0.10, 1])
    pol = get_strategy("frontier")
    pol.begin(sc)
    grid = _build_safe_grid(sc)
    vecs = float(speed) * NAV_ACTION_VECS
    yaw_cmd = np.array([0.0, 0.0, 0.0, YAW_RATE])

    state = obs[0]
    frames, phase, home_path = [], "search", []
    found, returned, since_scan, hits, cooldown, ap_steps, cf_steps = (
        False,
        False,
        0,
        0,
        0,
        0,
        0,
    )
    d = 0

    def snap():
        if d % stride == 0:
            frames.append(
                _follow_oblique(env, float(state[0]), float(state[1]), float(state[2]))
            )

    def drive(cmd_vec):  # one control block; returns updated state
        nonlocal state
        for _ in range(DECIDE_EVERY):
            o, *_ = env.step(cmd.rpm(state, cmd_vec).reshape(1, 4))
            state = o[0]
            if sc.clearance(room_xy(state)) < COLLISION_R:
                break

    while d < max_decisions and phase != "done":
        rpos = room_xy(state)
        br = sc.sense_beacon(rpos)  # {'bearing','range'} within 1.5 m, else None
        # DISCOVERY -> APPROACH: the range sensor says something is near; go
        # CLOSE (translate toward the bearing, never spin in place) so the
        # person fills the frame and per-frame recall is high before confirming
        if phase == "search" and br is not None and cooldown == 0 and not found:
            phase, ap_steps = "approach", 0
        if phase == "approach":
            rng = float(np.hypot(person[0] - rpos[0], person[1] - rpos[1]))
            if rng <= 0.9 or ap_steps > 25:
                phase, cf_steps, hits = "confirm", 0, 0
                continue
            th = br["bearing"] if br else np.arctan2(*(np.array(person) - rpos)[::-1])
            drive(vecs[safe_fn(sc, rpos, _cardinal(np.cos(th), np.sin(th)))])
            ap_steps += 1
            d += 1
            snap()
            continue
        if phase == "confirm":  # face the person (yaw) and CONFIRM with the head
            yaw = float(state[9])
            if detect() >= thr:
                hits += 1
                if hits >= 2 and _in_fov_yaw(rpos, person, yaw, FOV_HALF_DEG):
                    found, phase = True, "return"
            else:
                hits = 0
            if not found:
                drive(yaw_cmd)
                cf_steps += 1
                if cf_steps > 34:  # a full turn, no confirm -> resume + cool down
                    phase, cooldown = "search", 70
            d += 1
            snap()
            continue
        # periodic discovery scan (fallback if the sensor never triggers)
        if phase == "search" and since_scan >= scan_every and not found:
            since_scan = 0
            for _s in range(30):
                yaw = float(state[9])
                if detect() >= thr:
                    hits += 1
                    if hits >= 2 and _in_fov_yaw(rpos, person, yaw, FOV_HALF_DEG):
                        found, phase = True, "return"
                else:
                    hits = 0
                drive(yaw_cmd)
                d += 1
                snap()
                if found:
                    break
            continue
        since_scan += 1
        cooldown = max(0, cooldown - 1)
        if phase == "return":
            if sc.found_home(rpos):
                returned, phase = True, "done"
                break
            here = _cell_of(grid, rpos)
            while home_path and home_path[0] == here:
                home_path.pop(0)
            if not home_path:
                home_path = _bfs_home_path(grid, rpos, sc.start_xy)
            cx, cy = _centre(grid, home_path[0]) if home_path else sc.start_xy
            a = _cardinal(cx - rpos[0], cy - rpos[1])
        else:
            a = pol.decide(
                {
                    "pos": rpos,
                    "sense": None,
                    "ranges": sc.range_sensors(rpos),
                    "step": d,
                }
            )
        drive(vecs[safe_fn(sc, rpos, a)])
        d += 1
        snap()

    from sim.search_scenario import remove_bodies

    remove_bodies(env, ids + [pid])
    print(
        f"[demo] person seed {seed}: found={found} returned={returned} "
        f"frames={len(frames)} decisions={d}"
    )
    return frames, found, returned


def selftest() -> None:
    from planner.flight_mode import UNIFIED_WM

    assert UNIFIED_WM and callable(record)
    assert HEAD.endswith("target_head_person.pt")
    print("DEMO-PERSON OK: person visual-search capture wired")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=11)
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
    print(f"DEMO-PERSON DONE: {args.out} (found={found}, returned={returned})")


if __name__ == "__main__":
    sys.exit(main())

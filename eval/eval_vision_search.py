"""Visual-search flight mission — the vision branch's deployable capstone.

A Frontier coverage-sweep of a rendered room + a bright-red target; each
decision the detection head (search/target_detector.py, on the frozen WM
latent) reads the camera; on the FIRST firing (prob >= thr) the drone
declares "found" and flies home (honest deployable behaviour: it stops on
the first detection, not knowing yet whether it is right). This replaces
the abstract omnidirectional beacon with real vision.

Per-flight outcome: correct_find (first firing WAS a true target-in-FOV),
false_alarm (spurious — target not in view), or miss (never fired). Plus
collision / return. Threshold tuned on a VAL block, gated on FRESH rooms
(pre-reg + bars: experiments/vision_v1/journal.md).

Run:
  python -m eval.eval_vision_search --head experiments/vision_v1/target_head.pt
  python -m eval.eval_vision_search --selftest
"""

import argparse
import sys

import numpy as np


def run_vision_search(
    env,
    sc,
    detector,
    enc,
    seed,
    thr,
    speed=0.6,
    safety="beams8",
    max_decisions=800,
    plateau=100,
    debounce=1,
    trace=None,
):
    import torch

    from eval.eval_target_probe import _in_fov
    from eval.eval_yaw_detect import _in_fov_yaw
    from eval.search_episode import (
        _SAFETY,
        _bfs_home_path,
        _build_safe_grid,
        _cardinal,
        _cell_of,
        _centre,
    )
    from planner.latent_mpc import DECIDE_EVERY, _frame_tensor
    from planner.nav_action_set import NAV_ACTION_VECS
    from search.strategies import get_strategy
    from sim.envs import START, VelCommander, grab_frame, make_ctrl
    from sim.scenarios import COLLISION_R, FOV_HALF_DEG
    from sim.search_scenario import remove_bodies

    safe_fn = _SAFETY[safety]
    target = sc.beacon_xy
    obs, _ = env.reset(seed=int(seed))
    cmd = VelCommander(make_ctrl(), env.CTRL_TIMESTEP)
    cmd.reset(obs[0][0:3])
    sx, sy = sc.start_xy
    off = (sx - START[0], sy - START[1])

    def room_xy(state):
        return (float(state[0]) + sx - START[0], float(state[1]) + sy - START[1])

    ids = sc.spawn_bodies(env, offset=off)
    tid = sc.spawn_target(env, target, offset=off)
    pol = get_strategy("frontier")
    pol.begin(sc)
    grid = _build_safe_grid(sc)
    vecs = float(speed) * NAV_ACTION_VECS
    state = obs[0]
    free = np.asarray(sc.free_cells(), dtype=float)
    covered = np.zeros(len(free), dtype=bool)

    def mark(p):
        if len(free):
            covered[np.linalg.norm(free - np.asarray(p), axis=1) <= sc.sensor_range] = (
                True
            )

    fired = fire_in_fov = returned = False
    steps_to_fire, collisions, phase, streak = -1, 0, "search", 0
    home_path, no_gain, prev_cov = [], 0, 0.0

    for d in range(max_decisions):
        rpos = room_xy(state)
        mark(rpos)
        if not fired or trace is not None:
            frame = grab_frame(env)
            with torch.no_grad():
                z = enc(_frame_tensor(frame)).numpy().reshape(1, -1)
            p = float(detector.prob(z)[0])
            if trace is not None:  # C1 instrumentation — never alters behaviour
                yw = float(state[9])
                trace.append(
                    (
                        d,
                        p,
                        1 if _in_fov_yaw(rpos, target, yw, FOV_HALF_DEG) else 0,
                        yw,
                        1 if fired else 0,
                    )
                )
            if not fired:
                # debounce: fire only after `debounce` CONSECUTIVE frames
                # above thr — a persistent target-in-view fires, isolated
                # spurious frames do not (the fix for first-firing
                # false-alarm compounding)
                streak = streak + 1 if p >= thr else 0
                if streak >= debounce:
                    fired, steps_to_fire, phase = True, d, "return"
                    fire_in_fov = _in_fov(rpos, target, FOV_HALF_DEG)
        cf = float(covered.mean()) if len(free) else 0.0
        if cf > prev_cov + 1e-9:
            no_gain, prev_cov = 0, cf
        else:
            no_gain += 1
        if phase == "search" and no_gain >= plateau:
            phase = "return"  # swept everything, never fired -> go home
        if phase == "return" and sc.found_home(rpos):
            returned = True
            break
        if phase == "search":
            ctx = {
                "pos": rpos,
                "sense": None,
                "ranges": sc.range_sensors(rpos),
                "step": d,
            }
            a = pol.decide(ctx)
        else:
            here = _cell_of(grid, rpos)
            while home_path and home_path[0] == here:
                home_path.pop(0)
            if not home_path:
                home_path = _bfs_home_path(grid, rpos, sc.start_xy)
            if home_path:
                cx, cy = _centre(grid, home_path[0])
                a = _cardinal(cx - rpos[0], cy - rpos[1])
            else:
                a = _cardinal(sc.start_xy[0] - rpos[0], sc.start_xy[1] - rpos[1])
        a = safe_fn(sc, rpos, a)
        for _ in range(DECIDE_EVERY):
            obs, _, _, _, _ = env.step(cmd.rpm(state, vecs[a]).reshape(1, 4))
            state = obs[0]
            if sc.clearance(room_xy(state)) < COLLISION_R:
                collisions += 1
                break
    remove_bodies(env, ids + [tid])
    return {
        "correct_find": bool(fired and fire_in_fov),
        "false_alarm": bool(fired and not fire_in_fov),
        "miss": bool(not fired),
        "steps_to_fire": int(steps_to_fire),
        "returned": bool(returned),
        "crashed": bool(collisions > 0),
    }


def run_yaw_scan_search(
    env,
    sc,
    detector,
    enc,
    seed,
    thr,
    speed=0.6,
    safety="beams8",
    max_decisions=900,
    plateau=100,
    scan_every=25,
    scan_steps=30,
    confirm=2,
    trace=None,
):
    """yaw_v1 flight: Frontier coverage (yaw=0), and every `scan_every`
    decisions a full 360 deg SPIN-SCAN — the drone faces every direction, so
    an off-axis target (which the +x sweep only glimpses) enters the FOV and
    is detected. Declares found only after `confirm` scan-frames fire (a
    target steadily in view across consecutive scan yaws), which suppresses
    the isolated false alarms that sank the +x-lock flight. Uses the unified
    WM encoder + the yaw detection head. `fire_in_fov` is yaw-corrected."""
    import torch

    from eval.eval_yaw_detect import _in_fov_yaw
    from eval.search_episode import (
        _SAFETY,
        _bfs_home_path,
        _build_safe_grid,
        _cardinal,
        _cell_of,
        _centre,
    )
    from planner.latent_mpc import DECIDE_EVERY, _frame_tensor
    from planner.nav_action_set import NAV_ACTION_VECS, YAW_RATE
    from search.strategies import get_strategy
    from sim.envs import START, VelCommander, grab_frame, make_ctrl
    from sim.scenarios import COLLISION_R, FOV_HALF_DEG
    from sim.search_scenario import remove_bodies

    safe_fn = _SAFETY[safety]
    target = sc.beacon_xy
    obs, _ = env.reset(seed=int(seed))
    cmd = VelCommander(make_ctrl(), env.CTRL_TIMESTEP)
    cmd.reset(obs[0][0:3])
    sx, sy = sc.start_xy
    off = (sx - START[0], sy - START[1])

    def room_xy(state):
        return (float(state[0]) + sx - START[0], float(state[1]) + sy - START[1])

    def detect(rpos):
        frame = grab_frame(env)
        with torch.no_grad():
            z = enc(_frame_tensor(frame)).numpy().reshape(1, -1)
        p = float(detector.prob(z)[0])
        if trace is not None:  # C1/C2 instrumentation — never alters behaviour
            yw = float(state[9])
            trace.append(
                (
                    d,
                    p,
                    1 if _in_fov_yaw(rpos, target, yw, FOV_HALF_DEG) else 0,
                    yw,
                    1 if fired else 0,
                )
            )
        return p

    ids = sc.spawn_bodies(env, offset=off)
    tid = sc.spawn_target(env, target, offset=off)
    pol = get_strategy("frontier")
    pol.begin(sc)
    grid = _build_safe_grid(sc)
    vecs = float(speed) * NAV_ACTION_VECS
    yaw_cmd = np.array([0.0, 0.0, 0.0, YAW_RATE], dtype=float)  # raw spin (unscaled)
    state = obs[0]
    free = np.asarray(sc.free_cells(), dtype=float)
    covered = np.zeros(len(free), dtype=bool)

    def mark(p):
        if len(free):
            covered[np.linalg.norm(free - np.asarray(p), axis=1) <= sc.sensor_range] = (
                True
            )

    fired = fire_in_fov = returned = False
    steps_to_fire, collisions, phase = -1, 0, "search"
    home_path, no_gain, prev_cov, since_scan = [], 0, 0.0, 0

    d = 0
    while d < max_decisions and phase != "done":
        rpos = room_xy(state)
        mark(rpos)
        # --- periodic 360 spin-scan (only while still searching) ---
        if phase == "search" and not fired and since_scan >= scan_every:
            since_scan = 0
            hits = 0
            for _s in range(scan_steps):
                yaw = float(state[9])
                if detect(rpos) >= thr:
                    hits += 1
                    if hits >= confirm and not fired:
                        fired, steps_to_fire, phase = True, d, "return"
                        fire_in_fov = _in_fov_yaw(rpos, target, yaw, FOV_HALF_DEG)
                else:
                    hits = 0
                for _ in range(DECIDE_EVERY):
                    obs, _, _, _, _ = env.step(cmd.rpm(state, yaw_cmd).reshape(1, 4))
                    state = obs[0]
                d += 1
                if fired:
                    break
            continue
        since_scan += 1
        cf = float(covered.mean()) if len(free) else 0.0
        if cf > prev_cov + 1e-9:
            no_gain, prev_cov = 0, cf
        else:
            no_gain += 1
        if phase == "search" and no_gain >= plateau:
            phase = "return"
        if phase == "return" and sc.found_home(rpos):
            returned, phase = True, "done"
            break
        if phase == "search":
            a = pol.decide(
                {
                    "pos": rpos,
                    "sense": None,
                    "ranges": sc.range_sensors(rpos),
                    "step": d,
                }
            )
        else:
            here = _cell_of(grid, rpos)
            while home_path and home_path[0] == here:
                home_path.pop(0)
            if not home_path:
                home_path = _bfs_home_path(grid, rpos, sc.start_xy)
            if home_path:
                cx, cy = _centre(grid, home_path[0])
                a = _cardinal(cx - rpos[0], cy - rpos[1])
            else:
                a = _cardinal(sc.start_xy[0] - rpos[0], sc.start_xy[1] - rpos[1])
        a = safe_fn(sc, rpos, a)
        for _ in range(DECIDE_EVERY):
            obs, _, _, _, _ = env.step(cmd.rpm(state, vecs[a]).reshape(1, 4))
            state = obs[0]
            if sc.clearance(room_xy(state)) < COLLISION_R:
                collisions += 1
                break
        d += 1
    remove_bodies(env, ids + [tid])
    return {
        "correct_find": bool(fired and fire_in_fov),
        "false_alarm": bool(fired and not fire_in_fov),
        "miss": bool(not fired),
        "steps_to_fire": int(steps_to_fire),
        "returned": bool(returned),
        "crashed": bool(collisions > 0),
    }


def suite(head_path, thr, n, seed0, speed=0.6, max_decisions=800, debounce=1):
    from eval.eval_closed_loop import load_or_train
    from search.target_detector import DetectionHead
    from sim.envs import make_env
    from sim.indoor.rooms import single_room

    enc, _p, _c, _n, _m = load_or_train(device="cpu")
    detector = DetectionHead().load(head_path)
    env = make_env()
    rows = []
    for i in range(n):
        sc = single_room(seed0 + i)
        rows.append(
            run_vision_search(
                env,
                sc,
                detector,
                enc,
                seed0 + i,
                thr,
                speed,
                max_decisions=max_decisions,
                debounce=debounce,
            )
        )
    env.close()
    agg = {
        "thr": thr,
        "debounce": debounce,
        "n": n,
        "correct_find_rate": float(np.mean([r["correct_find"] for r in rows])),
        "false_alarm_rate": float(np.mean([r["false_alarm"] for r in rows])),
        "miss_rate": float(np.mean([r["miss"] for r in rows])),
        "collision_rate": float(np.mean([r["crashed"] for r in rows])),
        "return_rate": float(np.mean([r["returned"] for r in rows])),
    }
    return agg


def _rates(rows, **extra):
    return {
        **extra,
        "n": len(rows),
        "correct_find_rate": float(np.mean([r["correct_find"] for r in rows])),
        "false_alarm_rate": float(np.mean([r["false_alarm"] for r in rows])),
        "miss_rate": float(np.mean([r["miss"] for r in rows])),
        "collision_rate": float(np.mean([r["crashed"] for r in rows])),
        "return_rate": float(np.mean([r["returned"] for r in rows])),
    }


def suite_yaw(head_path, thr, n, seed0, speed=0.6, max_decisions=900, confirm=2):
    """The yaw_v1 flight suite: unified WM encoder + the yaw detection head +
    the 360 spin-scan runner, over n fresh rooms."""
    from eval.eval_yaw_detect import UNIFIED_WM
    from search.target_detector import DetectionHead
    from sim.envs import make_env
    from sim.indoor.rooms import single_room
    from world_model.training import load_model

    enc, *_ = load_model(UNIFIED_WM, device="cpu")
    detector = DetectionHead().load(head_path)
    env = make_env()
    rows = []
    for i in range(n):
        sc = single_room(seed0 + i)
        rows.append(
            run_yaw_scan_search(
                env,
                sc,
                detector,
                enc,
                seed0 + i,
                thr,
                speed,
                max_decisions=max_decisions,
                confirm=confirm,
            )
        )
    env.close()
    return _rates(rows, thr=thr, confirm=confirm)


def selftest() -> None:
    # env-free: the outcome bookkeeping is exclusive (correct/false/miss)
    assert {"correct_find", "false_alarm", "miss"}
    for fired, in_fov in ((True, True), (True, False), (False, False)):
        cf = fired and in_fov
        fa = fired and not in_fov
        miss = not fired
        assert int(cf) + int(fa) + int(miss) == 1
    print("EVAL-VISION-SEARCH OK: per-flight outcome bookkeeping is exclusive")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--head", help="detection head .pt")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--val-seed0", type=int, default=600000)
    ap.add_argument("--gate-seed0", type=int, default=620000)
    ap.add_argument("--thr", type=float, default=0.65)
    ap.add_argument("--debounces", nargs="+", type=int, default=[2, 3, 5])
    ap.add_argument("--yaw-scan", action="store_true", help="yaw_v1 spin-scan flight")
    ap.add_argument("--confirm", type=int, default=2)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest or not args.head:
        selftest()
        return

    if args.yaw_scan:
        g = suite_yaw(
            args.head, args.thr, args.n, args.gate_seed0, confirm=args.confirm
        )
        ok = (
            g["correct_find_rate"] >= 0.70
            and g["false_alarm_rate"] <= 0.20
            and g["collision_rate"] <= 0.05
            and g["return_rate"] >= 0.80
        )
        print(
            f"[yaw-scan-search] FRESH gate thr={args.thr} confirm={args.confirm} "
            f"n={g['n']} | correct_find {g['correct_find_rate']:.3f} | "
            f"false_alarm {g['false_alarm_rate']:.3f} | miss {g['miss_rate']:.3f} | "
            f"collision {g['collision_rate']:.3f} | return {g['return_rate']:.3f}"
        )
        print("  (+x camera-lock baseline: single-frame FA 0.95 / debounce miss 0.40)")
        print(f"  FLIGHT GATE: {'PASS' if ok else 'FAIL / honest-negative'}")
        return

    # tune the DEBOUNCE (consecutive-firings) on VAL at a fixed threshold;
    # maximize correct_find - false_alarm
    best_db, best_score = args.debounces[0], -9.0
    for db in args.debounces:
        a = suite(args.head, args.thr, max(8, args.n // 2), args.val_seed0, debounce=db)
        score = a["correct_find_rate"] - a["false_alarm_rate"]
        print(
            f"  [val db={db}] correct {a['correct_find_rate']:.3f} "
            f"false-alarm {a['false_alarm_rate']:.3f} miss {a['miss_rate']:.3f}",
            flush=True,
        )
        if score > best_score:
            best_db, best_score = db, score
    print(f"  -> tuned debounce {best_db} (thr {args.thr})")

    g = suite(args.head, args.thr, args.n, args.gate_seed0, debounce=best_db)
    ok = (
        g["correct_find_rate"] >= 0.70
        and g["false_alarm_rate"] <= 0.20
        and g["collision_rate"] <= 0.05
        and g["return_rate"] >= 0.80
    )
    print(
        f"\n[vision-search] FRESH gate thr={args.thr} debounce={best_db} n={g['n']} | "
        f"correct_find {g['correct_find_rate']:.3f} | "
        f"false_alarm {g['false_alarm_rate']:.3f} | miss {g['miss_rate']:.3f} | "
        f"collision {g['collision_rate']:.3f} | return {g['return_rate']:.3f}"
    )
    print(f"  FLIGHT GATE: {'PASS' if ok else 'FAIL / honest-negative'}")


if __name__ == "__main__":
    sys.exit(main())

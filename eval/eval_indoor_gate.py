"""The indoor deployment gate — one number for the indoor mission.

Transit earned its 72/100 by composing unit-green skills into seed-drawn
composite courses. The indoor track has per-experiment GREENs and no
composite. This runner draws missions from four families — each at its
unit gate's config of record — and scores the transit-shaped composite
verdict per mission: **found AND returned AND zero collisions**.

  M1 single-room beacon find+return   (search_room_v3 config, 600 dec)
  M2 multi-room 2/3/4-room            (eval_room_graph's 1000×rooms)
  M3 vertical: search-then-scan-heights — THE FIRST FLOWN READ (the
     unit evidence was a teleport-pose probe); Frontier cruise +
     periodic 3-D scans (fly to 0.4/1.0/1.6/2.0 m — no teleports —
     spin 360°, confirm-2), descend, BFS home
  M4 person find+return               (demo_person choreography)

Speed 0.6 and beams8 are HARDCODED (the I1 lesson: never inherit a
default). Fresh disjoint seed blocks per family. Pre-registration +
the feasibility-first protocol (bars frozen FROM the probe):
experiments/indoor_gate_v1/journal.md.

Run:
  python -m eval.eval_indoor_gate --probe 20      # the ceiling probe
  python -m eval.eval_indoor_gate --selftest
"""

import argparse
import json
import os
import sys

import numpy as np

SPEED = 0.6  # the track's robust speed — hardcoded, never inherited
SAFETY = "beams8"  # the deployment sweet spot — hardcoded
M3_HEAD = os.path.join("output", "target_head_alt.pt")  # journal-side multi-
# height head (z_cams 0.4-2.0); the LOCKED `low` head is the floor-hugging
# variant and would be OOD at 1.6-2.0 m scans — the alt/low canonicalization
# is the open G1 owner decision (stated in the journal before flying)
M4_HEAD = os.path.join("output", "target_head_person.pt")

WEIGHTS = {"M1_single": 0.30, "M2_multi": 0.30, "M3_vertical": 0.20, "M4_person": 0.20}


# --- M3: the first flown search-then-vertical-scan runner --------------------
def run_alt_scan_search(
    env,
    sc,
    detector,
    enc,
    seed,
    thr=0.5,
    speed=SPEED,
    safety=SAFETY,
    max_decisions=1600,
    plateau=100,
    scan_every=25,
    scan_alts=(0.4, 1.0, 1.6, 2.0),
    scan_steps=12,
    confirm=2,
    cruise_z=1.0,
):
    """Frontier coverage at cruise; every `scan_every` decisions a 3-D scan —
    FLY to each altitude (vz commands, x/y held at the safe scan spot, so
    the 2-D clearance model stays consistent) and spin 360° with confirm-k
    detection; on a confirmed fire, descend to cruise and BFS home.
    `found` requires the fire to be TRULY in view (elevation-aware label);
    a false fire flies home empty-handed and the composite counts it."""
    import torch

    from eval.eval_alt_search import _in_view
    from eval.search_episode import (
        _SAFETY,
        _bfs_home_path,
        _build_safe_grid,
        _cardinal,
        _cell_of,
        _centre,
    )
    from planner.latent_mpc import DECIDE_EVERY, _frame_tensor
    from planner.nav_action_set import LIFT_V, NAV_ACTION_VECS, YAW_RATE
    from search.strategies import get_strategy
    from sim.envs import START, VelCommander, grab_frame, make_ctrl
    from sim.scenarios import COLLISION_R, FOV_HALF_DEG
    from sim.search_scenario import remove_bodies

    safe_fn = _SAFETY[safety]
    target, bz = sc.beacon_xy, sc.beacon_z
    obs, _ = env.reset(seed=int(seed))
    cmd = VelCommander(make_ctrl(), env.CTRL_TIMESTEP)
    cmd.reset(obs[0][0:3])
    sx, sy = sc.start_xy
    off = (sx - START[0], sy - START[1])

    def room_xy(state):
        return (float(state[0]) + off[0], float(state[1]) + off[1])

    ids = sc.spawn_bodies(env, offset=off)
    tid = sc.spawn_target(env, target, offset=off, target_z=bz)
    pol = get_strategy("frontier")
    pol.begin(sc)
    grid = _build_safe_grid(sc)
    vecs = float(speed) * NAV_ACTION_VECS
    yaw_cmd = np.array([0.0, 0.0, 0.0, YAW_RATE], dtype=float)
    state = obs[0]
    free = np.asarray(sc.free_cells(), dtype=float)
    covered = np.zeros(len(free), dtype=bool)

    def mark(p):
        if len(free):
            covered[np.linalg.norm(free - np.asarray(p), axis=1) <= sc.sensor_range] = (
                True
            )

    fired = fire_in_fov = returned = False
    collisions, phase = 0, "search"
    home_path, no_gain, prev_cov, since_scan = [], 0, 0.0, 0
    d = 0

    def drive(vec):
        nonlocal state, collisions
        for _ in range(DECIDE_EVERY):
            o, *_ = env.step(cmd.rpm(state, vec).reshape(1, 4))
            state = o[0]
            if sc.clearance(room_xy(state)) < COLLISION_R:
                collisions += 1
                break

    def detect_prob():
        with torch.no_grad():
            z = enc(_frame_tensor(grab_frame(env))).numpy().reshape(1, -1)
        return float(detector.prob(z)[0])

    def fly_to_z(zt, budget=80):
        nonlocal d
        b = 0
        while d < max_decisions and b < budget and abs(float(state[2]) - zt) > 0.08:
            drive(
                np.array(
                    [0.0, 0.0, LIFT_V if zt > float(state[2]) else -LIFT_V, 0.0],
                    dtype=float,
                )
            )
            d += 1
            b += 1

    while d < max_decisions and phase != "done":
        rpos = room_xy(state)
        mark(rpos)
        if phase == "search" and not fired and since_scan >= scan_every:
            since_scan = 0
            for za in scan_alts:
                fly_to_z(za)
                hits = 0
                for _s in range(scan_steps):
                    yaw = float(state[9])
                    if detect_prob() >= thr:
                        hits += 1
                        if hits >= confirm and not fired:
                            fired, phase = True, "return"
                            fire_in_fov = _in_view(
                                rpos, target, bz, float(state[2]), yaw, FOV_HALF_DEG
                            )
                    else:
                        hits = 0
                    drive(yaw_cmd)
                    d += 1
                    if fired or d >= max_decisions:
                        break
                if fired or d >= max_decisions:
                    break
            fly_to_z(cruise_z)
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
        drive(vecs[a])
        d += 1
    remove_bodies(env, ids + [tid])
    return {
        "found": bool(fired and fire_in_fov),
        "false_fire": bool(fired and not fire_in_fov),
        "returned": bool(returned),
        "collisions": int(collisions),
        "steps": int(d),
        "beacon_z": float(bz),
    }


# --- the four families (each = its unit gate's config of record) --------------
def _m1(env, seed):
    from eval.search_episode import run_search_episode
    from search.strategies import get_strategy
    from sim.indoor.rooms import single_room

    m = run_search_episode(
        env,
        single_room(seed),
        get_strategy("frontier"),
        seed=seed,
        max_decisions=600,
        speed=SPEED,
        safety=SAFETY,
    )
    return {
        "found": bool(m["target_found"]),
        "returned": bool(m["returned"]),
        "collisions": int(m["collisions"]),
    }


def _m2(env, seed):
    from eval.search_episode import run_search_episode
    from search.strategies import get_strategy
    from sim.indoor.rooms import n_room, two_room

    nr = int(np.random.default_rng(seed).choice((2, 3, 4)))
    sc = two_room(seed) if nr == 2 else n_room(seed, n_rooms=nr)
    m = run_search_episode(
        env,
        sc,
        get_strategy("frontier"),
        seed=seed,
        max_decisions=1000 * nr,
        speed=SPEED,
        safety=SAFETY,
    )
    return {
        "found": bool(m["target_found"]),
        "returned": bool(m["returned"]),
        "collisions": int(m["collisions"]),
        "rooms": nr,
    }


def _m3(env, seed):
    from planner.flight_mode import UNIFIED_WM, load_wm_cached
    from search.target_detector import DetectionHead
    from sim.indoor.rooms import single_room

    enc, *_ = load_wm_cached(UNIFIED_WM)
    det = DetectionHead().load(M3_HEAD)
    return run_alt_scan_search(env, single_room(seed, vary_height=True), det, enc, seed)


def _m4(env, seed):
    from scripts.demo_person import record

    _frames, found, returned, collisions = record(env, seed, snapshots=False)
    return {
        "found": bool(found),
        "returned": bool(returned),
        "collisions": int(collisions),
    }


FAMILIES = (
    ("M1_single", _m1, 700000),
    ("M2_multi", _m2, 710000),
    ("M3_vertical", _m3, 720000),
    ("M4_person", _m4, 730000),
)


def probe(n=20, only=None):
    """The feasibility ceiling: n missions per family, composite verdict
    per mission, per-family break stats + the weighted composite. Bars are
    frozen FROM this read (journal), never from hope."""
    from sim.envs import make_env

    env = make_env()
    out = {}
    for name, fn, seed0 in FAMILIES:
        if only and name != only:
            continue
        rows = []
        for i in range(n):
            r = fn(env, seed0 + i)
            r["composite"] = bool(r["found"] and r["returned"] and r["collisions"] == 0)
            rows.append(r)
            print(
                f"  [{name}] seed {seed0 + i}: found={int(r['found'])} "
                f"ret={int(r['returned'])} col={r['collisions']} -> "
                f"{'OK' if r['composite'] else 'BREAK'}",
                flush=True,
            )
        out[name] = {
            "n": n,
            "find": float(np.mean([r["found"] for r in rows])),
            "return": float(np.mean([r["returned"] for r in rows])),
            "collision_missions": float(np.mean([r["collisions"] > 0 for r in rows])),
            "composite": float(np.mean([r["composite"] for r in rows])),
        }
        print(
            f"[{name}] "
            + "  ".join(f"{k}={v:.3f}" for k, v in out[name].items() if k != "n"),
            flush=True,
        )
    env.close()
    if not only and len(out) == len(FAMILIES):
        w = sum(WEIGHTS[k] * out[k]["composite"] for k in WEIGHTS)
        out["weighted_composite"] = float(w)
        print(f"[probe] weighted composite {w:.3f} (weights 0.30/0.30/0.20/0.20)")
    return out


def gate(n=100, seed_off=100):
    """The formal read: n missions split by the registered weights (exact
    counts), FRESH seed blocks (probe seeds + seed_off — never the probe's).
    Judged against the bars frozen in the journal AFTER the ceiling probe:
    composite >= 0.80 over the pool AND collision missions <= 0.02."""
    from sim.envs import make_env

    counts = {k: int(round(WEIGHTS[k] * n)) for k in WEIGHTS}
    assert sum(counts.values()) == n, counts
    env = make_env()
    fam, rows_all = {}, []
    for name, fn, seed0 in FAMILIES:
        rows = []
        for i in range(counts[name]):
            r = fn(env, seed0 + seed_off + i)
            r["composite"] = bool(r["found"] and r["returned"] and r["collisions"] == 0)
            rows.append(r)
            print(
                f"  [{name}] seed {seed0 + seed_off + i}: found={int(r['found'])} "
                f"ret={int(r['returned'])} col={r['collisions']} -> "
                f"{'OK' if r['composite'] else 'BREAK'}",
                flush=True,
            )
        fam[name] = {
            "n": counts[name],
            "find": float(np.mean([r["found"] for r in rows])),
            "return": float(np.mean([r["returned"] for r in rows])),
            "collision_missions": float(np.mean([r["collisions"] > 0 for r in rows])),
            "composite": float(np.mean([r["composite"] for r in rows])),
        }
        rows_all += rows
        print(
            f"[{name}] "
            + "  ".join(f"{k}={v:.3f}" for k, v in fam[name].items() if k != "n"),
            flush=True,
        )
    env.close()
    composite = float(np.mean([r["composite"] for r in rows_all]))
    col = float(np.mean([r["collisions"] > 0 for r in rows_all]))
    ok = composite >= 0.80 and col <= 0.02 + 1e-9
    print(
        f"[GATE] composite {composite:.3f}/{n} (bar >= 0.80)  "
        f"collision missions {col:.3f} (guard <= 0.02) -> "
        f"{'GREEN' if ok else 'FAIL'}"
    )
    return {
        "families": fam,
        "composite": composite,
        "collision_missions": col,
        "pass": bool(ok),
    }


def selftest() -> None:
    import inspect

    from scripts.demo_person import record

    # the composite verdict truth table (transit's shape)
    for found, ret, col, ok in (
        (True, True, 0, True),
        (True, True, 1, False),
        (True, False, 0, False),
        (False, True, 0, False),
    ):
        assert (found and ret and col == 0) is ok
    # families: disjoint fresh seed blocks, weights sum to 1
    seeds = [s for _, _, s in FAMILIES]
    assert len(set(seeds)) == len(seeds) and min(seeds) >= 700000
    assert all(b - a >= 10000 for a, b in zip(sorted(seeds), sorted(seeds)[1:]))
    assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9
    # the robust config is hardcoded, and M4's runner exposes snapshots
    assert SPEED == 0.6 and SAFETY == "beams8"
    assert "snapshots" in inspect.signature(record).parameters
    sig = inspect.signature(run_alt_scan_search).parameters
    assert sig["speed"].default == SPEED and sig["safety"].default == SAFETY
    assert sig["scan_alts"].default == (0.4, 1.0, 1.6, 2.0)
    # the gate's weight split lands exactly on n=100, on fresh seeds
    counts = {k: int(round(WEIGHTS[k] * 100)) for k in WEIGHTS}
    assert sum(counts.values()) == 100 and min(counts.values()) >= 20
    assert inspect.signature(gate).parameters["seed_off"].default >= 100
    print(
        "INDOOR-GATE OK: composite truth table, disjoint seed blocks, "
        "weights sum 1, hardcoded robust config, M3/M4 runner seams"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", type=int, default=0, help="n missions per family")
    ap.add_argument("--gate", type=int, default=0, help="formal weight-split read")
    ap.add_argument("--family", default=None, help="run one family only (probe)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    if not (args.probe or args.gate):
        raise SystemExit("--probe N or --gate N (or --selftest)")
    res = gate(args.gate) if args.gate else probe(args.probe, only=args.family)
    if args.out:
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        with open(args.out, "w") as f:
            json.dump(res, f, indent=1)
        print(f"[indoor-gate] wrote {args.out}")


if __name__ == "__main__":
    sys.exit(main())

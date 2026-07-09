"""Indoor height sensing — the GEOMETRIC tool for "how tall is the space".

Measuring ceiling height is a METRIC/geometric job, not the monocular WM's
(the indoor arc's law: the WM wins perception, loses spatial/metric to cheap
geometry — avoidance->rangefinders, coverage->grid). So height gets an
UP-FACING RANGEFINDER: a ray straight up to the ceiling
(`SearchScenario.ceiling_range`, a pybullet ray-test — the deployable analog
of a $5 up-sensor). This gates its accuracy against ground truth over a grid
of room positions, including a LOW BEAM (a lower ceiling patch) so it must
map a NON-FLAT profile, not just read one number.

Method (no flight, no WM): rooms with a ceiling (`single_room(ceiling=True)`,
per-seed height 2.0-3.2 m + a low beam); the coordinate-offset trick parks
the drone at START and shifts the room so the up-ray samples each (x,y);
measured clearance vs `ceiling_at(x,y) - START_z`.

Run:
  python -m eval.eval_height --n-rooms 8
  python -m eval.eval_height --selftest
"""

import argparse
import sys

import numpy as np


def measure_room(env, sc, grid=0.6):
    """Up-ray clearance vs ground truth over the room's free grid. Returns
    list of (x, y, measured, truth, under_beam)."""
    import pybullet as p

    from sim.envs import START
    from sim.search_scenario import remove_bodies

    rows = []
    x0, x1, y0, y1 = sc.bounds
    bx, by, bh = (sc.beam[0], sc.beam[1], sc.beam[2]) if sc.beam else (9, 9, 0)
    for x in np.arange(x0 + 0.6, x1 - 0.6, grid):
        for y in np.arange(y0 + 0.6, y1 - 0.6, grid):
            if sc.clearance((x, y)) <= 0.35:
                continue
            off = (x - START[0], y - START[1])
            ids = sc.spawn_bodies(env, offset=off)
            p.resetBasePositionAndOrientation(
                env.DRONE_IDS[0],
                list(START),
                p.getQuaternionFromEuler([0.0, 0.0, 0.0]),
                physicsClientId=env.CLIENT,
            )
            env._updateAndStoreKinematicInformation()
            meas = sc.ceiling_range(env)
            truth = sc.ceiling_at(x, y) - float(START[2])
            under = abs(x - bx) <= bh and abs(y - by) <= bh
            rows.append((float(x), float(y), meas, truth, bool(under)))
            remove_bodies(env, ids)
    return rows


def probe(n_rooms=8, seed0=700000, grid=0.6):
    from sim.envs import make_env
    from sim.indoor.rooms import single_room

    env = make_env()
    env.reset(seed=seed0)
    err, beam_meas, open_meas = [], [], []
    for i in range(n_rooms):
        sc = single_room(seed0 + i, ceiling=True)
        for _x, _y, meas, truth, under in measure_room(env, sc, grid):
            err.append(abs(meas - truth))
            (beam_meas if under else open_meas).append(meas)
    env.close()
    return {
        "n": len(err),
        "mae": float(np.mean(err)),
        "max_err": float(np.max(err)),
        "n_beam": len(beam_meas),
        "mean_clear_beam": float(np.mean(beam_meas)) if beam_meas else float("nan"),
        "mean_clear_open": float(np.mean(open_meas)) if open_meas else float("nan"),
    }


def selftest() -> None:
    from sim.search_scenario import SearchScenario

    sc = SearchScenario(
        bounds=(-2.5, 2.5, -2.5, 2.5),
        obstacles=(),
        beacon_xy=(1.0, 1.0),
        start_xy=(0.0, 0.0),
        ceiling_h=3.0,
        beam=(1.0, 0.0, 0.6, 2.1),
    )
    assert sc.ceiling_at(-2.0, 2.0) == 3.0, "open area -> room ceiling"
    assert sc.ceiling_at(1.0, 0.0) == 2.1, "under the beam -> lower ceiling"
    assert sc.ceiling_at(1.5, 0.0) == 2.1, "beam half-width 0.6 covers 1.5"
    assert sc.ceiling_at(2.0, 0.0) == 3.0, "past the beam -> room ceiling"
    op = SearchScenario(
        bounds=(-1, 1, -1, 1), obstacles=(), beacon_xy=(0, 0), start_xy=(0, 0)
    )
    assert op.ceiling_at(0, 0) == float("inf"), "open-top default -> inf"
    print("EVAL-HEIGHT OK: ceiling_at (beam < room < open) — geometric truth")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-rooms", type=int, default=8)
    ap.add_argument("--seed0", type=int, default=700000)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    r = probe(args.n_rooms, args.seed0)
    print(
        f"[height] {r['n']} samples | MAE {r['mae']*100:.1f} cm | "
        f"max-err {r['max_err']*100:.1f} cm | clearance under-beam "
        f"{r['mean_clear_beam']:.2f} m vs open {r['mean_clear_open']:.2f} m"
    )
    ok = r["mae"] <= 0.10 and r["mean_clear_beam"] < r["mean_clear_open"] - 0.3
    verdict = (
        "GEOMETRIC HEIGHT SENSING WORKS: up-rangefinder maps the ceiling "
        "profile (incl. the low beam) to cm accuracy — the right tool, not the WM"
        if ok
        else "unexpected: check the up-ray / ceiling spawn"
    )
    print(f"  {verdict}")


if __name__ == "__main__":
    sys.exit(main())

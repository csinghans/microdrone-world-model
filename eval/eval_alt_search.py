"""Multi-altitude search gate — does sweeping ALTITUDE find high/low targets
a single-altitude search misses?

Hans's vision: find a target on a high cabinet (~2 m) or under a bed
(~0.3 m). Vertical lift (vz) is a clean free DOF, and alt_v1 Phase 0/1a-2
showed a retrained head detects a level target across altitudes (0.15-2 m,
no WM retrain). This gate isolates the ALTITUDE contribution: from a scan
point 1.5 m from the target, run a 3-D scan (altitude x yaw) and compare
MULTI-altitude (sweep {0.4,1.0,1.6,2.0}) vs SINGLE-altitude (z=1 only),
by target-height class. Multi should find high + low; single only mid.

(yaw handles azimuth — yaw_v1; altitude handles elevation — alt_v1; both
are in-place scans with the level +x camera, no WM retrain.)

Run:
  python -m eval.eval_alt_search --head output/target_head_low.pt --n 24
  python -m eval.eval_alt_search --selftest
"""

import argparse
import sys

import numpy as np


def _in_view(pos, target_xy, target_h, z_cam, yaw, half_deg, max_range=2.5):
    """Target in the level camera FOV at heading `yaw` + altitude z_cam:
    azimuth (relative to yaw) AND elevation both within +-half_deg, in range."""
    dx, dy = target_xy[0] - pos[0], target_xy[1] - pos[1]
    horiz = float(np.hypot(dx, dy))
    if horiz > max_range:
        return False
    azim = np.degrees((np.arctan2(dy, dx) - yaw + np.pi) % (2 * np.pi) - np.pi)
    elev = np.degrees(np.arctan2(target_h - z_cam, horiz))
    return abs(azim) <= half_deg and abs(elev) <= half_deg


def scan_find(env, sc, detector, enc, scan_xy, altitudes, yaws, thr, half):
    """3-D scan (altitude x yaw) from scan_xy: set each drone pose + detect.
    A discrete scan puts the target in view at ~one pose, so `found` = the
    detector fired at a pose where the target is TRULY in view (a correct
    detection); `false_alarm` = it fired at a pose where it is NOT in view.
    Returns (correct_detect, false_alarm)."""
    import pybullet as p
    import torch

    from planner.latent_mpc import _frame_tensor
    from sim.envs import START, grab_frame
    from sim.search_scenario import remove_bodies

    target, bz = sc.beacon_xy, sc.beacon_z
    sx, sy = scan_xy
    off = (sx - START[0], sy - START[1])  # room shifted so START samples scan_xy
    ids = sc.spawn_bodies(env, offset=off)
    tid = sc.spawn_target(env, target, offset=off, target_z=bz)
    correct, false_alarm = False, False
    for za in altitudes:
        for yw in yaws:
            p.resetBasePositionAndOrientation(
                env.DRONE_IDS[0],
                [START[0], START[1], float(za)],
                p.getQuaternionFromEuler([0.0, 0.0, float(yw)]),
                physicsClientId=env.CLIENT,
            )
            env._updateAndStoreKinematicInformation()
            with torch.no_grad():
                z = enc(_frame_tensor(grab_frame(env))).numpy().reshape(1, -1)
            if float(detector.prob(z)[0]) >= thr:
                if _in_view(scan_xy, target, bz, za, yw, half):
                    correct = True
                else:
                    false_alarm = True
    remove_bodies(env, ids + [tid])
    return correct, false_alarm


def suite(head_path, n, seed0, thr=0.5, single=False):
    from eval.eval_alt_detect import UNIFIED_WM
    from search.target_detector import DetectionHead
    from sim.envs import make_env
    from sim.indoor.rooms import single_room
    from sim.scenarios import FOV_HALF_DEG
    from world_model.training import load_model

    enc, *_ = load_model(UNIFIED_WM, device="cpu")
    det = DetectionHead().load(head_path)
    yaws = [np.radians(d) for d in (-135, -90, -45, 0, 45, 90, 135, 180)]
    alts = [1.0] if single else [0.4, 1.0, 1.6, 2.0]
    env = make_env()
    rows = []
    for i in range(n):
        sc = single_room(seed0 + i, vary_height=True)
        bx, by = sc.beacon_xy
        # a scan point 1.5 m from the target (within the 2.5 m range), inside
        # the room bounds — the drone yaw+altitude-scans to acquire it
        x0, x1, y0, y1 = sc.bounds
        sxy = (
            float(np.clip(bx - 1.5, x0 + 0.6, x1 - 0.6)),
            float(np.clip(by, y0 + 0.6, y1 - 0.6)),
        )
        correct, fa = scan_find(env, sc, det, enc, sxy, alts, yaws, thr, FOV_HALF_DEG)
        rows.append((sc.beacon_z, correct, fa))
    env.close()
    return rows


def _by_height(rows):
    out = {}
    for h in (0.3, 1.0, 2.0):
        sub = [r for r in rows if abs(r[0] - h) < 1e-6]
        cf = np.mean([r[1] for r in sub]) if sub else float("nan")
        out[h] = (len(sub), float(cf))
    return out


def selftest() -> None:
    # _in_view: a target due +y is seen only when yaw faces +y (~90 deg), and
    # a high target only when the elevation is within the cone
    assert _in_view((0, 0), (0, 1.0), 1.0, 1.0, np.radians(90), 28)
    assert not _in_view((0, 0), (0, 1.0), 1.0, 1.0, 0.0, 28), "not facing +y"
    assert _in_view((0, 0), (1.0, 0.0), 2.0, 2.0, 0.0, 28), "high target, matched alt"
    assert not _in_view((0, 0), (1.0, 0.0), 2.0, 1.0, 0.0, 28), "high target, low alt"
    print("EVAL-ALT-SEARCH OK: yaw+elevation view test")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--head", help="detection head .pt (the alt/low head)")
    ap.add_argument("--n", type=int, default=24)
    ap.add_argument("--seed0", type=int, default=620000)
    ap.add_argument("--thr", type=float, default=0.5)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest or not args.head:
        selftest()
        return
    print(f"multi-altitude search gate: {args.n} rooms (varied height), thr {args.thr}")
    for name, single in (
        ("single-altitude (z=1)", True),
        ("multi-altitude sweep", False),
    ):
        rows = suite(args.head, args.n, args.seed0, thr=args.thr, single=single)
        bh = _by_height(rows)
        overall = float(np.mean([r[1] for r in rows]))
        fa = float(np.mean([r[2] for r in rows]))
        print(
            f"  {name:24} correct-find by height: "
            + "  ".join(f"{h}m={cf:.2f}(n{k})" for h, (k, cf) in bh.items())
            + f"  | overall {overall:.2f} | false-alarm {fa:.2f}"
        )


if __name__ == "__main__":
    sys.exit(main())

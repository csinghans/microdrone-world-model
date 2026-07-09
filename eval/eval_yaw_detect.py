"""Yaw-detection feasibility probe — does the FROZEN WM latent still SEE a
target when the camera is YAWED off +x?

The one boundary that blocked deployable visual search is the yaw=0 +x
camera-lock: the drone can only glimpse a target as its forward cone sweeps
past, never turn to face and confirm it (eval_vision_search FAILED on this).
Before paying a yaw WM-retrain, one decisive, cheap question (feasibility-
first): if the drone yaws to face an off-axis target, does the shipped/
unified encoder's latent linearly separate "target in the (yawed) FOV"?

  * GREEN (AUC >= ~0.85 across the yaw sweep, no collapse as |yaw| grows):
    the frozen latent generalises to rotation -> yaw-scan detection needs
    only a retrained head, NO WM retrain.
  * RED  (AUC craters toward 0.5 with |yaw|): the encoder is OOD on rotated
    frames -> a yaw WM-retrain is required (stop + report).

Method (no flight, no training): the coordinate-offset trick renders the
room from grid position (x,y); we ALSO yaw the parked drone (Route B:
reset its orientation + refresh kinematics + the stock body-frame
grab_frame, which then looks along the yawed heading), and label
target-in-FOV with a YAW-CORRECTED bearing (relative to the heading, not
+x). Encode with the unified WM (the detection champion) and linear-probe
per yaw bin + pooled, vs the raw-pixel redness baseline.

Run:
  python -m eval.eval_yaw_detect --n-rooms 6
  python -m eval.eval_yaw_detect --selftest
"""

import argparse
import os
import sys

import numpy as np

from eval.eval_target_probe import _auc, _linear_probe_auc, _redness
from world_model.training import MODEL

UNIFIED_WM = os.path.join(os.path.dirname(MODEL), "world_model_unified.pth")
YAWS_DEG = (-90, -45, 0, 45, 90)  # signed yaw sweep about +x


def _in_fov_yaw(pos, target, yaw_rad, half_deg, max_range=2.5):
    """Target within +-half_deg of the drone's HEADING (yaw), not +x.
    Drops the +x-only `dx<=0` shortcut; wraps the bearing difference."""
    dx, dy = target[0] - pos[0], target[1] - pos[1]
    if np.hypot(dx, dy) > max_range:
        return False
    rel = np.arctan2(dy, dx) - yaw_rad  # bearing relative to the heading
    rel = (rel + np.pi) % (2 * np.pi) - np.pi  # wrap to [-pi, pi]
    return abs(np.degrees(rel)) <= half_deg


def collect_yaw_frames(
    n_rooms=6, seed0=600000, grid=0.45, yaws_deg=YAWS_DEG, half_deg=None, ckpt=None
):
    """Render + encode target/no-target frames over a position grid AND a
    yaw sweep. Route B: park the drone at START, set its yaw, refresh
    kinematics, and use the stock body-frame grab_frame (camera turns with
    the yaw). Returns lat (N,64), label (N,), yaw (N,), red (N,)."""
    import pybullet as p
    import torch

    from eval.eval_closed_loop import load_or_train
    from planner.latent_mpc import _frame_tensor
    from sim.envs import START, grab_frame, make_env
    from sim.indoor.rooms import single_room
    from sim.scenarios import FOV_HALF_DEG
    from sim.search_scenario import remove_bodies
    from world_model.training import load_model

    half = FOV_HALF_DEG if half_deg is None else half_deg
    if ckpt is not None:
        enc, *_ = load_model(ckpt, device="cpu")
    else:
        enc, *_ = load_or_train(device="cpu")
    yaws = [np.radians(d) for d in yaws_deg]
    env = make_env()
    env.reset(seed=seed0)
    lat, label, yaw_col, red, obs_fov = [], [], [], [], []
    for i in range(n_rooms):
        sc = single_room(seed0 + i)
        target = sc.beacon_xy
        x0, x1, y0, y1 = sc.bounds
        for x in np.arange(x0 + 0.6, x1 - 0.6, grid):
            for y in np.arange(y0 + 0.6, y1 - 0.6, grid):
                if sc.clearance((x, y)) <= 0.35:
                    continue
                off = (x - START[0], y - START[1])
                ids = sc.spawn_bodies(env, offset=off)
                tid = sc.spawn_target(env, target, offset=off)
                for yw in yaws:
                    p.resetBasePositionAndOrientation(
                        env.DRONE_IDS[0],
                        [START[0], START[1], START[2]],
                        p.getQuaternionFromEuler([0.0, 0.0, float(yw)]),
                        physicsClientId=env.CLIENT,
                    )
                    env._updateAndStoreKinematicInformation()
                    frame = grab_frame(env)
                    with torch.no_grad():
                        z = enc(_frame_tensor(frame)).numpy().reshape(-1)
                    lat.append(z)
                    red.append(_redness(frame))
                    label.append(1 if _in_fov_yaw((x, y), target, yw, half) else 0)
                    yaw_col.append(float(np.degrees(yw)))
                    # hard-negative flag: an obstacle box in the (yawed) FOV —
                    # a detector must fire on the red target, not orange boxes
                    seen_obs = any(
                        _in_fov_yaw((x, y), (ox, oy), yw, half)
                        for ox, oy, _ in sc.obstacles
                    )
                    obs_fov.append(1 if seen_obs else 0)
                remove_bodies(env, ids + [tid])
    env.close()
    return {
        "lat": np.asarray(lat, dtype=np.float32),
        "label": np.asarray(label, dtype=int),
        "yaw": np.asarray(yaw_col, dtype=float),
        "red": np.asarray(red, dtype=float),
        "obs_in_fov": np.asarray(obs_fov, dtype=int),
    }


def probe(n_rooms=6, seed0=600000, yaws_deg=YAWS_DEG, ckpt=UNIFIED_WM):
    d = collect_yaw_frames(n_rooms, seed0, yaws_deg=yaws_deg, ckpt=ckpt)
    lat, y, yaw = d["lat"], d["label"], d["yaw"]
    out = {
        "n": int(len(y)),
        "positive_rate": float(y.mean()),
        "pooled_auc": _linear_probe_auc(lat, y),
        "pixel_auc": _auc(d["red"], y),
        "by_yaw": {},
    }
    for yd in sorted(set(yaws_deg)):
        m = yaw == yd
        yy = y[m]
        # per-bin AUC needs both classes; a linear probe per small bin is
        # noisy, so score the POOLED probe's separation restricted to the bin
        if yy.min() != yy.max():
            out["by_yaw"][yd] = _linear_probe_auc(lat[m], yy)
        else:
            out["by_yaw"][yd] = float("nan")
    return out


def selftest() -> None:
    # yaw-corrected FOV: a target due +y (bearing 90 deg) is OUT of a +x
    # (yaw=0) FOV but IN view once the drone yaws +90 to face it.
    assert not _in_fov_yaw((0, 0), (0, 1.0), 0.0, 28)
    assert _in_fov_yaw((0, 0), (0, 1.0), np.radians(90), 28)
    # a +x target is in view at yaw 0 and leaves as the drone yaws away
    assert _in_fov_yaw((0, 0), (1.0, 0.0), 0.0, 28)
    assert not _in_fov_yaw((0, 0), (1.0, 0.0), np.radians(90), 28)
    # range gate still applies
    assert not _in_fov_yaw((0, 0), (3.0, 0.0), 0.0, 28)
    print("EVAL-YAW-DETECT OK: yaw-corrected FOV (off-axis target seen once faced)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-rooms", type=int, default=6)
    ap.add_argument("--seed0", type=int, default=600000)
    ap.add_argument("--ckpt", default=UNIFIED_WM, help="WM to probe (default unified)")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    r = probe(args.n_rooms, args.seed0, ckpt=args.ckpt)
    print(
        f"[yaw-detect] {r['n']} frames (in-view {r['positive_rate']:.2f}) | "
        f"pooled WM-latent AUC {r['pooled_auc']:.3f} | pixel-redness "
        f"{r['pixel_auc']:.3f}"
    )
    print(
        "  per-yaw AUC: " + "  ".join(f"{k:+d}={v:.3f}" for k, v in r["by_yaw"].items())
    )
    lo = min(v for v in r["by_yaw"].values() if v == v)
    verdict = (
        "GREEN: latent generalises to yaw -> head-retrain only (no WM retrain)"
        if r["pooled_auc"] >= 0.85 and lo >= 0.75
        else "RED: latent collapses off-axis -> a yaw WM-retrain is needed"
    )
    print(f"  VERDICT: {verdict}")


if __name__ == "__main__":
    sys.exit(main())

"""Altitude-detection feasibility probe — can the FROZEN WM latent SEE a
target at a different HEIGHT when the drone flies to that height (level +x
camera, no pitch)?

Hans's vision: find targets high (a cabinet ~2 m) or low (under a bed
~0.2 m). His insight: use vertical LIFT, not pitch — vz is a clean free DOF
(the camera stays horizontal), so fly to the target's altitude and view it
LEVEL. Before building a multi-altitude search, the decisive cheap question
(feasibility-first, mirroring the yaw probe):

  * GREEN: for a LEVEL target (target height ≈ drone altitude), AUC stays
    high across the whole altitude range -> the frozen latent detects a
    target imaged at any altitude, so multi-altitude search needs only a
    retrained head, NO WM retrain. Plus the elevation tolerance (AUC vs
    |target_h - z_cam|) sets the altitude sweep spacing.
  * RED: detection collapses away from the training altitude (z=1) -> a WM
    retrain is required (stop + report).

Method (no flight, no training): the coordinate-offset trick renders the
room from grid (x,y); the target is spawned at height h; the parked drone is
set to altitude z_cam (level, Route B: reset + refresh kinematics + the
stock horizontal grab_frame); the label is elevation-aware (`_in_fov_alt`,
azimuth AND vertical angle). Encode with the unified WM, linear-probe.

Run:
  python -m eval.eval_alt_detect --n-rooms 6
  python -m eval.eval_alt_detect --selftest
"""

import argparse
import os
import sys

import numpy as np

from eval.eval_target_probe import _linear_probe_auc
from world_model.training import MODEL

UNIFIED_WM = os.path.join(os.path.dirname(MODEL), "world_model_unified.pth")
Z_CAMS = (0.4, 0.8, 1.2, 1.6, 2.0)  # drone altitudes to sweep
TARGET_HS = (0.3, 1.0, 2.0)  # under-furniture / level / high-shelf target heights


def _in_fov_alt(pos, target_xy, target_h, z_cam, half_deg, max_range=2.5):
    """Target in the level +x camera FOV from altitude z_cam: azimuth about
    +x AND elevation atan2(target_h - z_cam, range) both within +-half_deg,
    within max_range. (Adds the vertical angle the planar _in_fov lacked.)"""
    dx, dy = target_xy[0] - pos[0], target_xy[1] - pos[1]
    if dx <= 0:
        return False  # behind/beside — the +x camera (yaw=0) cannot see it
    horiz = float(np.hypot(dx, dy))
    if horiz > max_range:
        return False
    azim = abs(np.degrees(np.arctan2(dy, dx)))
    elev = abs(np.degrees(np.arctan2(target_h - z_cam, horiz)))
    return azim <= half_deg and elev <= half_deg


def collect_alt_frames(
    n_rooms=6,
    seed0=600000,
    grid=0.7,
    z_cams=Z_CAMS,
    target_hs=TARGET_HS,
    half_deg=None,
    ckpt=None,
    return_frames=False,
):
    """Render + encode over grid position x target height x drone altitude.
    Returns lat (N,64), label, z_cam, target_h, elev (deg, signed |h-z|);
    `return_frames` adds the raw uint8 frames (int8_parity_v1)."""
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
    env = make_env()
    env.reset(seed=seed0)
    lat, label, zc, th, elev, obs_fov, raw = [], [], [], [], [], [], []
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
                for h in target_hs:
                    tid = sc.spawn_target(env, target, offset=off, target_z=h)
                    for z in z_cams:
                        p.resetBasePositionAndOrientation(
                            env.DRONE_IDS[0],
                            [START[0], START[1], float(z)],
                            p.getQuaternionFromEuler([0.0, 0.0, 0.0]),
                            physicsClientId=env.CLIENT,
                        )
                        env._updateAndStoreKinematicInformation()
                        frame = grab_frame(env)
                        with torch.no_grad():
                            emb = enc(_frame_tensor(frame)).numpy().reshape(-1)
                        lat.append(emb)
                        if return_frames:
                            raw.append(frame)
                        label.append(
                            1 if _in_fov_alt((x, y), target, h, z, half) else 0
                        )
                        zc.append(float(z))
                        th.append(float(h))
                        elev.append(abs(h - z))
                        # hard-negative: an obstacle box (at wall_h/2=0.5) in
                        # the elevation+azimuth FOV — the detector must not fire
                        seen_obs = any(
                            _in_fov_alt((x, y), (ox, oy), 0.5, z, half)
                            for ox, oy, _ in sc.obstacles
                        )
                        obs_fov.append(1 if seen_obs else 0)
                    remove_bodies(env, [tid])
                remove_bodies(env, ids)
    env.close()
    out = {
        "lat": np.asarray(lat, dtype=np.float32),
        "label": np.asarray(label, dtype=int),
        "z_cam": np.asarray(zc, dtype=float),
        "target_h": np.asarray(th, dtype=float),
        "elev": np.asarray(elev, dtype=float),
        "obs_in_fov": np.asarray(obs_fov, dtype=int),
    }
    if return_frames:
        out["frames"] = np.asarray(raw, dtype=np.uint8)
    return out


def probe(n_rooms=6, seed0=600000, ckpt=UNIFIED_WM):
    d = collect_alt_frames(n_rooms, seed0, ckpt=ckpt)
    lat, y = d["lat"], d["label"]
    out = {
        "n": int(len(y)),
        "positive_rate": float(y.mean()),
        "pooled_auc": _linear_probe_auc(lat, y),
        "level_by_z": {},
    }
    # the decisive cut: LEVEL targets (target height ~ drone altitude); does
    # detection hold across the altitude range (i.e. does fly-to-altitude work)?
    level = d["elev"] <= 0.4
    out["level_auc"] = _linear_probe_auc(lat[level], y[level])
    for z in sorted(set(Z_CAMS)):
        m = level & (d["z_cam"] == z)
        yy = y[m]
        out["level_by_z"][z] = (
            _linear_probe_auc(lat[m], yy) if yy.min() != yy.max() else float("nan")
        )
    return out


def selftest() -> None:
    # a target at +x, 1 m ahead, height 2.0: in FOV from altitude 2.0 (level),
    # OUT from altitude 1.0 (elevation ~45 deg > 28)
    assert _in_fov_alt((0, 0), (1.0, 0.0), 2.0, 2.0, 28), "level high target seen"
    assert not _in_fov_alt((0, 0), (1.0, 0.0), 2.0, 1.0, 28), "1 m below -> out (elev)"
    # low target under furniture: seen from a low hover, not from up high
    assert _in_fov_alt((0, 0), (1.0, 0.0), 0.3, 0.3, 28), "level low target seen"
    assert not _in_fov_alt((0, 0), (1.0, 0.0), 0.3, 1.5, 28), "1.2 m above -> out"
    assert not _in_fov_alt((0, 0), (-1.0, 0.0), 1.0, 1.0, 28), "behind -> out (+x lock)"
    print("EVAL-ALT-DETECT OK: elevation-aware FOV (target seen at matched altitude)")


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
        f"[alt-detect] {r['n']} frames (in-view {r['positive_rate']:.2f}) | "
        f"pooled AUC {r['pooled_auc']:.3f} | LEVEL-target AUC {r['level_auc']:.3f}"
    )
    print(
        "  level AUC by drone altitude: "
        + "  ".join(f"{z:.1f}m={v:.3f}" for z, v in r["level_by_z"].items())
    )
    lo = min(v for v in r["level_by_z"].values() if v == v)
    verdict = (
        "GREEN: fly-to-altitude detection holds across heights -> head-retrain "
        "only (no WM retrain); multi-altitude search is feasible"
        if r["level_auc"] >= 0.85 and lo >= 0.75
        else "RED: detection collapses off the training altitude -> WM retrain"
    )
    print(f"  VERDICT: {verdict}")


if __name__ == "__main__":
    sys.exit(main())

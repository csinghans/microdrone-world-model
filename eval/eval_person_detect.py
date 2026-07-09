"""Person-vs-clutter feasibility probe — can the FROZEN WM latent tell a
PERSON-shaped target from box clutter, with NO WM retrain?

Hans's SAR direction: indoors the WM's home is perception (detection AUC
0.94), while geometry owns the spatial jobs. The next perceptual step past
"a target is in view" is "WHAT is in view" — for search-and-rescue the target
is a PERSON, and "person vs rubble/furniture" is a pure seeing problem a
rangefinder is blind to. Decisive cheap question (feasibility-first, mirroring
yaw/alt):

  * GREEN: person-vs-empty AND person-vs-box both separate at high AUC on the
    FROZEN latent -> a multi-class detection head can recognize a person vs
    clutter with NO WM retrain.
  * RED: the person shape is OOD (person-vs-empty already at chance) -> a WM
    retrain is required (stop + report).

Honesty control: `--shape-control` paints the person the SAME orange as the
box clutter, so the person-vs-box AUC then reflects SHAPE ALONE (capsule vs
box, colour removed) — the test of whether the latent truly sees the person
SHAPE, not just its colour.

Method (no flight, no training): coordinate-offset render of the room (walls +
orange box obstacles), a CAPSULE person spawned at the beacon, the parked
drone imaging it level (Route B), unified-WM encode, linear probe.

Run:
  python -m eval.eval_person_detect --n-rooms 6
  python -m eval.eval_person_detect --shape-control
  python -m eval.eval_person_detect --selftest
"""

import argparse
import os
import sys

import numpy as np

from eval.eval_target_probe import _linear_probe_auc
from world_model.training import MODEL

UNIFIED_WM = os.path.join(os.path.dirname(MODEL), "world_model_unified.pth")
# capsule person. r=0.25 (~0.5 m across) is a realistic shoulder width — the
# first r=0.15 (~0.3 m) was a thin pole that subtended too few pixels at range
# and capped per-frame recall at 0.50 (person_v1 Phase 1). The wider body is
# both more faithful AND more detectable far away.
PERSON_R, PERSON_LEN = 0.25, 0.9  # standing person torso (~1.4 m tall, 0.5 wide)
PERSON_Z = PERSON_R + PERSON_LEN / 2  # centre height ~0.7 m
BOX_ORANGE = [0.80, 0.45, 0.30, 1]  # the obstacle colour (search_scenario)
TARGET_RED = [0.95, 0.10, 0.10, 1]


def _in_fov(pos, target_xy, half_deg, max_range=2.5):
    """A tall body ahead in the level +x camera: azimuth about +x within
    +-half_deg and within max_range (a ~1.1 m person spans the vertical FOV
    at these ranges, so the planar azimuth is the binding cut)."""
    dx, dy = target_xy[0] - pos[0], target_xy[1] - pos[1]
    if dx <= 0:
        return False
    horiz = float(np.hypot(dx, dy))
    if horiz > max_range:
        return False
    return abs(np.degrees(np.arctan2(dy, dx))) <= half_deg


def _spawn_person(env, xy, offset, color):
    import pybullet as p

    ox, oy = offset
    vis = p.createVisualShape(
        p.GEOM_CAPSULE,
        radius=PERSON_R,
        length=PERSON_LEN,
        rgbaColor=color,
        physicsClientId=env.CLIENT,
    )
    return p.createMultiBody(
        baseMass=0,
        baseVisualShapeIndex=vis,
        basePosition=[xy[0] - ox, xy[1] - oy, PERSON_Z],
        physicsClientId=env.CLIENT,
    )


def collect(n_rooms=6, seed0=650000, grid=0.7, shape_control=False, ckpt=UNIFIED_WM):
    """Render + encode over grid positions x rooms. Each frame is labelled by
    what sits in the +x FOV: a person, a box obstacle, or neither."""
    import pybullet as p
    import torch

    from eval.eval_closed_loop import load_or_train
    from planner.latent_mpc import _frame_tensor
    from sim.envs import START, grab_frame, make_env
    from sim.indoor.rooms import single_room
    from sim.scenarios import FOV_HALF_DEG
    from sim.search_scenario import remove_bodies
    from world_model.training import load_model

    color = BOX_ORANGE if shape_control else TARGET_RED
    if ckpt is not None and os.path.exists(ckpt):
        enc, *_ = load_model(ckpt, device="cpu")
    else:
        enc, *_ = load_or_train(device="cpu")
    env = make_env()
    env.reset(seed=seed0)
    lat, person, box = [], [], []
    for i in range(n_rooms):
        sc = single_room(seed0 + i)
        person_xy = sc.beacon_xy
        x0, x1, y0, y1 = sc.bounds
        for x in np.arange(x0 + 0.6, x1 - 0.6, grid):
            for y in np.arange(y0 + 0.6, y1 - 0.6, grid):
                if sc.clearance((x, y)) <= 0.35:
                    continue
                off = (x - START[0], y - START[1])
                ids = sc.spawn_bodies(env, offset=off)
                pid = _spawn_person(env, person_xy, off, color)
                p.resetBasePositionAndOrientation(
                    env.DRONE_IDS[0],
                    [START[0], START[1], 1.0],
                    p.getQuaternionFromEuler([0.0, 0.0, 0.0]),
                    physicsClientId=env.CLIENT,
                )
                env._updateAndStoreKinematicInformation()
                frame = grab_frame(env)
                with torch.no_grad():
                    emb = enc(_frame_tensor(frame)).numpy().reshape(-1)
                lat.append(emb)
                person.append(1 if _in_fov((x, y), person_xy, FOV_HALF_DEG) else 0)
                box.append(
                    1
                    if any(
                        _in_fov((x, y), (ox, oy), FOV_HALF_DEG)
                        for ox, oy, _ in sc.obstacles
                    )
                    else 0
                )
                remove_bodies(env, ids + [pid])
    env.close()
    return {
        "lat": np.asarray(lat, dtype=np.float32),
        "person": np.asarray(person, dtype=int),
        "box": np.asarray(box, dtype=int),
    }


def probe(n_rooms=6, seed0=650000, shape_control=False, ckpt=UNIFIED_WM):
    d = collect(n_rooms, seed0, shape_control=shape_control, ckpt=ckpt)
    lat, person, box = d["lat"], d["person"], d["box"]
    # person-vs-empty: person in FOV (label 1) vs nothing in FOV (label 0)
    empty = (person == 0) & (box == 0)
    m_pe = person.astype(bool) | empty
    # person-vs-box: person in FOV vs a box in FOV with NO person
    box_only = (box == 1) & (person == 0)
    m_pb = person.astype(bool) | box_only
    return {
        "n": int(len(person)),
        "person_rate": float(person.mean()),
        "box_rate": float(box.mean()),
        "person_vs_empty": _linear_probe_auc(lat[m_pe], person[m_pe]),
        "person_vs_box": _linear_probe_auc(lat[m_pb], person[m_pb].astype(int)),
        "shape_control": bool(shape_control),
    }


def selftest() -> None:
    # a person 1 m ahead at +x is in the FOV; behind (+x lock) or off-azimuth is not
    assert _in_fov((0, 0), (1.0, 0.0), 28), "person ahead -> in FOV"
    assert not _in_fov((0, 0), (-1.0, 0.0), 28), "behind -> out (+x lock)"
    assert not _in_fov((0, 0), (1.0, 1.0), 28), "45 deg off-axis -> out"
    assert PERSON_Z > PERSON_R and PERSON_LEN > 0, "capsule is a standing torso"
    print("EVAL-PERSON-DETECT OK: +x FOV label + capsule person wired")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-rooms", type=int, default=6)
    ap.add_argument("--seed0", type=int, default=650000)
    ap.add_argument("--shape-control", action="store_true", help="person = box colour")
    ap.add_argument("--ckpt", default=UNIFIED_WM, help="WM to probe (default unified)")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    r = probe(
        args.n_rooms, args.seed0, shape_control=args.shape_control, ckpt=args.ckpt
    )
    tag = "SHAPE-ONLY (person=box colour)" if r["shape_control"] else "shape+colour"
    print(
        f"[person-detect] {r['n']} frames (person {r['person_rate']:.2f}, "
        f"box {r['box_rate']:.2f}) | {tag}"
    )
    print(
        f"  person-vs-empty AUC {r['person_vs_empty']:.3f} | "
        f"person-vs-box AUC {r['person_vs_box']:.3f}"
    )
    if not r["shape_control"]:
        verdict = (
            "GREEN: the frozen latent detects AND discriminates a person from "
            "clutter -> multi-class head, no WM retrain"
            if r["person_vs_empty"] >= 0.85 and r["person_vs_box"] >= 0.85
            else "RED/NUANCED: see per-cut AUCs (person shape may be OOD)"
        )
        print(f"  VERDICT: {verdict}")


if __name__ == "__main__":
    sys.exit(main())

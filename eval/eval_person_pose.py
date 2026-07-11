"""Person poses vs the level camera — the realism stress probe (person_pose_v1).

person_v1's GREEN stands on ONE pose (an upright capsule). This probe
renders the same rooms with the person standing / sitting / crouching /
lying / half-buried (pose is the ONLY variable — identical room seeds
across poses), and scores two arms per pose on the frozen unified
latent: a cross-block linear probe (the mechanism read) and ONE
deployable multi-pose head (pooled training, per-pose test — the arm
the bars sit on). Bars + the on-record prediction (lying fails from a
level camera): experiments/person_pose_v1/journal.md, committed first.

Run:
  python -m eval.eval_person_pose --probe
  python -m eval.eval_person_pose --selftest
"""

import argparse
import json
import os
import sys

import numpy as np

POSES = ("standing", "sitting", "crouching", "lying", "buried")
TRAIN0, TEST0 = 670000, 680000
BARS = {"standing": 0.90, "sitting": 0.80, "crouching": 0.80, "lying": 0.75}
FA_GUARD = 0.15  # the v1 head-gate obstacle false-alarm guard
# pose -> (capsule length, centre z, horizontal?) — proxies, stated honestly
POSE_GEOM = {
    "standing": (0.90, None, False),
    "sitting": (0.45, None, False),
    "crouching": (0.25, None, False),
    "lying": (0.90, None, True),
    "buried": (0.90, None, True),
}
SLAB_GREY = [0.55, 0.55, 0.57, 1]  # the wall grey of the room palette


def _spawn_posed(env, xy, offset, pose, color):
    import pybullet as p

    from eval.eval_person_detect import PERSON_R

    ox, oy = offset
    ln, _z, flat = POSE_GEOM[pose]
    z = PERSON_R if flat else PERSON_R + ln / 2
    orn = (
        p.getQuaternionFromEuler([np.pi / 2, 0.0, 0.0])  # capsule axis -> y
        if flat
        else [0.0, 0.0, 0.0, 1.0]
    )
    vis = p.createVisualShape(
        p.GEOM_CAPSULE,
        radius=PERSON_R,
        length=ln,
        rgbaColor=color,
        physicsClientId=env.CLIENT,
    )
    bodies = [
        p.createMultiBody(
            baseMass=0,
            baseVisualShapeIndex=vis,
            basePosition=[xy[0] - ox, xy[1] - oy, z],
            baseOrientation=orn,
            physicsClientId=env.CLIENT,
        )
    ]
    if pose == "buried":
        slab = p.createVisualShape(
            p.GEOM_BOX,
            halfExtents=[0.30, 0.30, 0.075],
            rgbaColor=SLAB_GREY,
            physicsClientId=env.CLIENT,
        )
        bodies.append(
            p.createMultiBody(
                baseMass=0,
                baseVisualShapeIndex=slab,
                basePosition=[xy[0] - ox, xy[1] - oy, 0.15],
                physicsClientId=env.CLIENT,
            )
        )
    return bodies


def collect_pose(pose, n_rooms=6, seed0=TRAIN0, grid=0.7, ckpt=None):
    """The person_v1 collect() convention with a posed person: grid
    positions x rooms, +x FOV labels, box hard-negatives."""
    import pybullet as p
    import torch

    from eval.eval_person_detect import TARGET_RED, UNIFIED_WM, _in_fov
    from planner.latent_mpc import _frame_tensor
    from sim.envs import START, grab_frame, make_env
    from sim.indoor.rooms import single_room
    from sim.scenarios import FOV_HALF_DEG
    from sim.search_scenario import remove_bodies
    from world_model.training import load_model

    enc, *_ = load_model(ckpt or UNIFIED_WM, device="cpu")
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
                pids = _spawn_posed(env, person_xy, off, pose, TARGET_RED)
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
                remove_bodies(env, ids + pids)
    env.close()
    return {
        "lat": np.asarray(lat, dtype=np.float32),
        "label": np.asarray(person, dtype=int),
        "obs_in_fov": np.asarray(box, dtype=int),
    }


def _probe_auc(tr_lat, tr_y, te_lat, te_y, steps=400):
    """Cross-block linear probe: fit on the train block, AUC on test."""
    import torch

    from search.target_detector import _auc

    xt = torch.tensor(tr_lat, dtype=torch.float32)
    yt = torch.tensor(tr_y, dtype=torch.float32)
    w = torch.zeros(tr_lat.shape[1], requires_grad=True)
    b = torch.zeros(1, requires_grad=True)
    opt = torch.optim.Adam([w, b], lr=0.05)
    lossf = torch.nn.BCEWithLogitsLoss()
    for _ in range(steps):
        opt.zero_grad()
        loss = lossf(xt @ w + b, yt) + 1e-3 * (w @ w)
        loss.backward()
        opt.step()
    with torch.no_grad():
        s = (torch.tensor(te_lat, dtype=torch.float32) @ w + b).numpy()
    return float(_auc(s, te_y))


def probe(n_rooms=6, thr=0.5, out=None):
    from search.target_detector import DetectionHead, _score

    tr = {pose: collect_pose(pose, n_rooms, TRAIN0) for pose in POSES}
    te = {pose: collect_pose(pose, n_rooms, TEST0) for pose in POSES}
    head = DetectionHead().fit(
        np.concatenate([tr[p]["lat"] for p in POSES]),
        np.concatenate([tr[p]["label"] for p in POSES]),
    )
    res, fas = {}, []
    for pose in POSES:
        frozen = _probe_auc(
            tr[pose]["lat"], tr[pose]["label"], te[pose]["lat"], te[pose]["label"]
        )
        s = _score(head, te[pose], thr)
        bar = BARS.get(pose)
        ok = None if bar is None else bool(s["auc"] >= bar - 1e-9)
        res[pose] = {
            "frozen_probe_auc": frozen,
            "head_auc": float(s["auc"]),
            "head_recall": float(s["recall"]),
            "obstacle_fa": float(s["obstacle_false_alarm"]),
            "bar": bar,
            "pass": ok,
        }
        fas.append(s["obstacle_false_alarm"])
        tag = "--" if ok is None else ("PASS" if ok else "FAIL")
        print(
            f"  [{pose:9s}] probe={frozen:.3f}  head={s['auc']:.3f} "
            f"(bar {bar if bar else '--'}) recall={s['recall']:.2f} "
            f"obsFA={s['obstacle_false_alarm']:.3f} -> {tag}",
            flush=True,
        )
    guard = float(np.mean(fas))
    trigger = res["lying"]["pass"] is False
    msg = (
        "lying FAILS -> the C8 pitch step is ARMED"
        if trigger
        else "lying PASSES -> the pitch retrain loses its cheapest argument"
    )
    print(f"[person-pose] pooled obstacle-FA {guard:.3f} (guard <= {FA_GUARD}) | {msg}")
    res["pooled_obstacle_fa"] = guard
    res["c8_armed"] = bool(trigger)
    if out:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w") as f:
            json.dump(res, f, indent=1)
        print(f"[person-pose] wrote {out}")
    return res


def selftest() -> None:
    rng = np.random.default_rng(0)
    # geometry table: flat poses sit at radius height; uprights at len/2 + r
    assert POSE_GEOM["standing"][0] == 0.90 and not POSE_GEOM["standing"][2]
    assert POSE_GEOM["lying"][2] and POSE_GEOM["buried"][2]
    assert set(BARS) == {"standing", "sitting", "crouching", "lying"}
    assert BARS["lying"] == 0.75  # the C8 go/no-go
    # the cross-block probe recovers a separable toy
    tr = rng.normal(size=(300, 64)).astype(np.float32)
    y_tr = (tr[:, 0] > 0).astype(int)
    te = rng.normal(size=(200, 64)).astype(np.float32)
    y_te = (te[:, 0] > 0).astype(int)
    assert _probe_auc(tr, y_tr, te, y_te) > 0.95
    # fresh seed blocks, disjoint from person_v1's 650000/660000
    assert TRAIN0 >= 670000 and TEST0 >= 680000 and TEST0 - TRAIN0 >= 10000
    print(
        "PERSON-POSE OK: pose geometry table, C8 go/no-go bar, "
        "cross-block probe on a separable toy, fresh seed blocks"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--n-rooms", type=int, default=6)
    ap.add_argument("--out", default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    if not args.probe:
        raise SystemExit("--probe (or --selftest)")
    probe(args.n_rooms, out=args.out)


if __name__ == "__main__":
    sys.exit(main())

"""Select the existing geometric veer exam without pixels or model calls.

The same selector supplies training/checkpoint scoring and preflight support
accounting. This is the yaw-zero transit pillar oracle, not a room oracle or
a check that scene geometry was rendered. Eligibility does not require a
held-command future window; it rolls hypothetical commands forward from
every recorded FORWARD frame, including the end of a rollout.

    python -m world_model.veer_probe
"""

import numpy as np

from datasets.intervention_labels import HORIZONS
from planner.action_set import ACTION_NAMES, ACTION_VECS, FORWARD
from sim.envs import CTRL_HZ
from sim.scenarios import DANGER_R, FOV_HALF_DEG


def select(data, rolls=None):
    """Ordered (rollout, time), safer-side truth and speed; no random draws.

    Arithmetic and strict boundaries are preserved from training.veer_ranking.
    Missing pillar velocity means static; NaN padding (including rooms) is
    skipped. Only metadata is accessed, so callers need not load frames.
    """
    R, L = data["act_id"].shape
    rolls = list(range(R)) if rolls is None else list(rolls)
    if any(not isinstance(r, (int, np.integer)) or not 0 <= r < R for r in rolls):
        raise ValueError("rollouts must be valid integer indices")
    if len(set(rolls)) != len(rolls):
        raise ValueError("duplicate rollout selection")
    tau1 = np.arange(HORIZONS[-1] + 1) / CTRL_HZ
    i_l, i_r = ACTION_NAMES.index("veer_left"), ACTION_NAMES.index("veer_right")
    cos_fov = np.cos(np.radians(FOV_HALF_DEG))
    gt_left_safer, svs, probe_pairs = [], [], []
    all_vel = data["pillar_vel"] if "pillar_vel" in data else None
    for r in rolls:
        pil = data["pillars"][r]
        mask = ~np.isnan(pil[:, 0])
        pil = pil[mask]
        if not len(pil):
            continue
        vp = np.asarray(all_vel[r])[mask] if all_vel is not None else np.zeros_like(pil)
        sv = float(data["speed"][r])
        for t in range(L):
            if data["act_id"][r, t] != FORWARD:
                continue
            p0 = data["pos"][r, t, :2]
            pil_at = pil + (t / CTRL_HZ) * vp
            d_v, q_v = [], []
            for i in (i_l, i_r):
                rel_v = sv * ACTION_VECS[i][:2] - vp
                diff = (p0 - pil_at)[None, :, :] + tau1[:, None, None] * rel_v[None]
                dmat = np.linalg.norm(diff, axis=2)
                d_v.append(float(dmat.min()))
                q_v.append(pil_at[dmat.min(axis=0).argmin()])
            d_l, d_r = d_v
            if not (
                abs(d_l - d_r) > 0.12 and min(d_l, d_r) < DANGER_R <= max(d_l, d_r)
            ):
                continue
            rel = (q_v[0] if d_l < d_r else q_v[1]) - p0
            if rel[0] <= float(np.linalg.norm(rel)) * cos_fov:
                continue
            gt_left_safer.append(d_l > d_r)
            svs.append(sv)
            probe_pairs.append((r, t))
    pairs = np.asarray(probe_pairs, dtype=np.int64).reshape(-1, 2)
    world_ids = np.asarray(data.get("world_id", np.zeros(R, dtype=int)))
    return {
        "veer_pairs": pairs,
        "veer_gt_left": np.asarray(gt_left_safer, dtype=bool),
        "veer_world_id": world_ids[pairs[:, 0]],
        "speed": np.asarray(svs, dtype=np.float32),
    }


def fixture():
    """Hand-built asymmetric/static, symmetric, invisible and room cases."""
    pillars = np.array(
        [[[0.9, 0.2]], [[0.9, -0.2]], [[0.9, 0]], [[0.2, 0.8]], [[np.nan, np.nan]]]
    )
    return {
        "act_id": np.array([[0, 0, 1]] * 5),
        "pillars": pillars,
        "pos": np.zeros((5, 3, 3)),
        "speed": np.ones(5),
        "world_id": np.array([0, 1, 2, 2, 3]),
        "world_names": np.array(["classic", "dense", "moving", "room"]),
    }


def selftest():
    data = fixture()
    sample = select(data)
    assert sample["veer_pairs"].tolist() == [[0, 0], [0, 1], [1, 0], [1, 1]]
    assert sample["veer_gt_left"].tolist() == [False, False, True, True]
    assert sample["veer_world_id"].tolist() == [0, 0, 1, 1]
    assert select(data, [1, 0])["veer_pairs"].tolist() == [
        [1, 0],
        [1, 1],
        [0, 0],
        [0, 1],
    ]
    assert select(data, [4])["veer_pairs"].shape == (0, 2)
    assert select(data, [])["veer_gt_left"].shape == (0,)
    data["pillar_vel"] = np.zeros_like(data["pillars"])
    assert all(np.array_equal(v, select(data)[k]) for k, v in sample.items())
    # A crossing reaches y=.2 at t=48; static geometry never enters the FOV.
    data = {
        "act_id": np.zeros((1, 49), dtype=int),
        "pillars": np.array([[[0.9, 1.2]]]),
        "pillar_vel": np.array([[[0.0, -1.0]]]),
        "pos": np.zeros((1, 49, 3)),
        "speed": np.ones(1),
    }
    assert [0, 48] in select(data)["veer_pairs"].tolist()
    del data["pillar_vel"]
    assert len(select(data)["veer_pairs"]) == 0
    for bad in ([0, 0], [-1], [1], [0.5]):
        try:
            select(data, bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid rollout selection accepted: {bad}")
    print("VEER-PROBE OK: asymmetric truth, FOV, cruise, rooms, motion, ordering")


if __name__ == "__main__":
    selftest()

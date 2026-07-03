"""Metric grounding labels: a polar occupancy grid, FOV-honest by design.

The v0.5 question: does *metric* supervision — "where is stuff, and how
far" — make the latent carry structure the collision heads and the policy
can exploit? The real-world version of this supervision is an offline
4D-Gaussian-Splatting reconstruction (Orin-class, hours of compute, never
on the drone). In sim we can skip the reconstruction and use the privileged
pillar layout directly, which makes these labels the **perfect-reconstruction
upper bound** of that pipeline: if perfect metric supervision buys nothing
here, the offline-reconstruction road is dead at this scale; if it buys X,
X is the ceiling a real 4D-GS pass could reach.

The grid is deliberately tiny and camera-shaped: N_BEAR bearing bins across
the +/-FOV_HALF_DEG wedge x N_RANGE range shells out to R_MAX. Anything the
camera cannot see (behind, beside, beyond R_MAX) is *not labelled* rather
than labelled empty-vs-occupied from privilege — the same honesty rule as
the counterfactual oracle's FOV mask, enforced here by construction: the
grid simply does not have cells outside the wedge.

Deploy-time cost: zero. The head that consumes these labels is a train-only
auxiliary — it is dropped from the flight stack, so the 512 KB budget line
does not move. The bet is entirely "a grounded latent flies better".

Run:
  python -m datasets.metric_labels     # selftest, asserts
"""

import numpy as np

from sim.envs import CTRL_HZ
from sim.scenarios import FOV_HALF_DEG

N_BEAR = 5  # bearing bins across the +/-28 deg camera wedge
N_RANGE = 3  # range shells: [0,0.7) / [0.7,1.4) / [1.4,2.1) m
R_MAX = 2.1  # metres; ~2.5x the k=32 travel at cruise — the actionable zone
N_CELLS = N_BEAR * N_RANGE


def polar_occupancy(data: dict) -> np.ndarray:
    """Per-frame polar occupancy from the privileged layout: uint8
    (R, L, N_BEAR, N_RANGE), cell = 1 when any pillar centre sits in that
    (bearing, range) bin *at that frame*. Moving pillars are extrapolated
    exactly like the counterfactual oracle (pil0 + t*vp). Pillar centres
    only in v1 (radius 0.18 m unmodelled — symmetric across cells, so the
    where-is-stuff signal survives). Camera looks along +x, yaw held at 0,
    same convention as `intervention_labels`."""
    R, L = data["frames"].shape[:2]
    occ = np.zeros((R, L, N_BEAR, N_RANGE), dtype=np.uint8)
    tgrid = np.arange(L) / CTRL_HZ
    all_vel = data["pillar_vel"] if "pillar_vel" in data else None
    for r in range(R):
        pil = data["pillars"][r]
        mask = ~np.isnan(pil[:, 0])
        pil = pil[mask]
        if not len(pil):
            continue
        vp = np.asarray(all_vel[r])[mask] if all_vel is not None else np.zeros_like(pil)
        pil_t = pil[None, :, :] + tgrid[:, None, None] * vp[None, :, :]  # (L,P,2)
        rel = pil_t - data["pos"][r, :, None, :2]  # pillar - drone (L,P,2)
        rng = np.linalg.norm(rel, axis=2)  # (L,P)
        bear = np.degrees(np.arctan2(rel[..., 1], rel[..., 0]))  # (L,P)
        inside = (rng < R_MAX) & (np.abs(bear) < FOV_HALF_DEG)
        bi = ((bear + FOV_HALF_DEG) / (2 * FOV_HALF_DEG) * N_BEAR).astype(int)
        ri = (rng / (R_MAX / N_RANGE)).astype(int)
        t_idx, p_idx = np.where(inside)
        occ[
            r,
            t_idx,
            bi[t_idx, p_idx].clip(0, N_BEAR - 1),
            ri[t_idx, p_idx].clip(0, N_RANGE - 1),
        ] = 1
    return occ


def selftest() -> None:
    def blank(L):
        return {
            "frames": np.zeros((1, L, 2, 2, 3), dtype=np.uint8),
            "pos": np.zeros((1, L, 3), dtype=np.float32),
        }

    # a pillar dead ahead at 1 m: exactly one cell — centre bearing, mid shell
    d = blank(2) | {"pillars": np.array([[[1.0, 0.0]]], dtype=np.float32)}
    occ = polar_occupancy(d)
    assert occ.shape == (1, 2, N_BEAR, N_RANGE)
    assert occ[0, 0].sum() == 1 and occ[0, 0, N_BEAR // 2, 1] == 1
    # behind the camera: the grid must stay silent (FOV honesty by construction)
    d = blank(1) | {"pillars": np.array([[[-1.0, 0.0]]], dtype=np.float32)}
    assert polar_occupancy(d).sum() == 0
    # +20 deg at 0.5 m: leftmost-but-one... compute: bin 4 of 5, innermost shell
    p = np.array([[[0.5 * np.cos(np.radians(20)), 0.5 * np.sin(np.radians(20))]]])
    d = blank(1) | {"pillars": p.astype(np.float32)}
    assert polar_occupancy(d)[0, 0, 4, 0] == 1
    # beyond R_MAX: visible direction, but outside the actionable zone -> silent
    d = blank(1) | {"pillars": np.array([[[R_MAX + 0.5, 0.0]]], dtype=np.float32)}
    assert polar_occupancy(d).sum() == 0
    # motion: a crosser starts outside the wedge and arrives dead ahead —
    # the static view never sees it, the extrapolated view does (same split
    # the counterfactual oracle asserts)
    d = blank(3) | {
        "pillars": np.array([[[1.0, -1.0]]], dtype=np.float32),
        "pillar_vel": np.array([[[0.0, 24.0]]], dtype=np.float32),
    }
    occ_m = polar_occupancy(d)
    occ_s = polar_occupancy({k: v for k, v in d.items() if k != "pillar_vel"})
    assert occ_s.sum() == 0, "static view must never see the off-wedge pillar"
    assert occ_m[0, 0].sum() == 0 and occ_m[0, 2].sum() == 1, "crosser must arrive"
    print(
        f"METRIC-LABELS OK: {N_BEAR}x{N_RANGE} polar grid to {R_MAX} m, "
        f"FOV-honest by construction, static + extrapolated-motion asserts"
    )


if __name__ == "__main__":
    selftest()

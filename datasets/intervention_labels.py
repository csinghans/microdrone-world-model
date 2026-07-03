"""Label machinery: multi-horizon danger labels and the counterfactual oracle.

The simulator's privileged position hands out two kinds of supervision:

  * **Executed-action labels** — "did the flown future get dangerously close
    within k steps?" Valid only where the command was genuinely held for the
    whole window (`window_valid`).
  * **Counterfactual labels** — for *every* frame and *every* candidate
    command, roll the command forward kinematically through the known pillar
    layout and label whether it would get dangerously close. The executed
    action tells the model what *did* happen; the counterfactuals teach it to
    *rank* the actions it did not take, which is exactly what a planner asks.

Honest notes: the oracle is straight-line kinematics — no PID transient —
and it exists only because sim labels are privileged anyway; with real-world
data you would be back to executed-action supervision and need far more of
it. The approximation is symmetric across candidates, so rankings survive.
And a single-frame model cannot know about a pillar beside or behind it, so
positives caused by out-of-FOV threats are marked unanswerable (`visible=0`)
rather than trained on — grading a model on questions it cannot see would
only teach noise.
"""

import numpy as np

from planner.action_set import ACTION_VECS
from sim.envs import CTRL_HZ
from sim.scenarios import FOV_HALF_DEG, RADII

HORIZONS = (4, 8, 16, 32)  # label horizons in control steps (~83..667 ms @ 48 Hz)
H_MAX = HORIZONS[-1]


def window_valid(seg_row, t: int, k: int) -> bool:
    """True when the command really was held over [t, t+k]: the window fits in
    the rollout and stays inside one held segment."""
    return t + k < len(seg_row) and seg_row[t] == seg_row[t + k]


def counterfactual_labels(data: dict) -> tuple:
    """For every frame and candidate command: would holding it get dangerously
    close within each horizon?

    Returns (labels, visible):
      labels  uint8 (R, L, n_actions, n_horizons, n_radii) — one label per
              ring in RADII (warn 0.7 m + critical 0.35 m).
      visible uint8 (R, L, n_actions) — 1 when the label is answerable from
              this frame: either it is negative ("see nothing -> safe"), or
              the threatening pillar sits inside the camera FOV.

    Valid at *every* step, because it never needs the flown future — this is
    what densifies the action-conditioning supervision beyond the executed
    command."""
    R, L = data["frames"].shape[:2]
    taus = np.arange(H_MAX + 1) / CTRL_HZ  # (K+1,)
    cf = np.zeros((R, L, len(ACTION_VECS), len(HORIZONS), len(RADII)), dtype=np.uint8)
    vis = np.ones((R, L, len(ACTION_VECS)), dtype=np.uint8)
    cos_fov = np.cos(np.radians(FOV_HALF_DEG))
    for r in range(R):
        pil = data["pillars"][r]
        pil = pil[~np.isnan(pil[:, 0])]
        if not len(pil):
            continue
        p0 = data["pos"][r, :, :2]  # (L, 2)
        for i, v in enumerate(float(data["speed"][r]) * ACTION_VECS):
            # paths: (L, K+1, 2) -> distances to every pillar: (L, K+1, P)
            path = p0[:, None, :] + taus[None, :, None] * v[:2]
            d = np.linalg.norm(path[:, :, None, :] - pil[None, None], axis=3)
            for j, k in enumerate(HORIZONS):
                dmin = d[:, : k + 1].min(axis=(1, 2))
                for q, rad in enumerate(RADII):
                    cf[r, :, i, j, q] = (dmin < rad).astype(np.uint8)
            # visibility of the threat (camera looks along +x, yaw held at 0):
            # a positive label caused by an out-of-FOV pillar is unanswerable
            threat = pil[d.min(axis=1).argmin(axis=1)]  # (L, 2)
            rel = threat - p0
            in_fov = rel[:, 0] > np.linalg.norm(rel, axis=1) * cos_fov
            vis[r, :, i] = np.where(cf[r, :, i, :, 0].any(axis=1) & ~in_fov, 0, 1)
    return cf, vis


def selftest() -> None:
    # a hand-built 2-step "rollout" heading straight at one pillar
    R, L = 1, 2
    data = {
        "frames": np.zeros((R, L, 2, 2, 3), dtype=np.uint8),
        "pillars": np.array([[[1.0, 0.0], [np.nan, np.nan], [np.nan, np.nan]]]),
        "pos": np.zeros((R, L, 3), dtype=np.float32),
        "speed": np.array([1.25], dtype=np.float32),
    }
    cf, vis = counterfactual_labels(data)
    fwd, hover = 0, 5
    assert cf[0, 0, fwd, -1, 0] == 1, "forward at a 1 m pillar must warn at k=32"
    assert cf[0, 0, hover, -1, 1] == 0, "hover must not trip the critical ring"
    assert vis[0, 0, fwd] == 1, "an in-FOV threat must stay answerable"
    seg = np.array([0, 0, 1, 1, 1])
    assert window_valid(seg, 2, 2) and not window_valid(seg, 1, 2)
    print(f"LABELS OK: horizons {HORIZONS}, rings {RADII}, oracle + FOV mask assert")


if __name__ == "__main__":
    selftest()

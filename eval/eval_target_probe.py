"""Visual-detection feasibility probe — can the WM latent SEE a target?

The owner's next direction after coverage: the visual-detection branch —
find a target by SIGHT (a rendered object), not the abstract omnidirec-
tional beacon. Before building a detector / widening the observation
channel / paying a yaw-retrain, one decisive, cheap question:

  Does the shipped WM encoder's 64-d latent linearly separate
  "a visual target is in the +x camera FOV" from "it is not"?

If YES -> the existing encoder already carries target information; a small
detection head suffices (no retrain). If NO (but a trivial pixel feature
CAN) -> the collision-trained encoder discards target appearance; the
branch needs a new/wider perception path. This is the architecture fork.

Method (no flight, no training of the WM): render a `single_room` with a
bright-red target (`spawn_target`) at its hidden-target spot; via the
coordinate-offset trick, render the +x camera from a grid of room
positions (yaw==0 -> camera looks +x); encode each frame; label
target-in-FOV from geometry; fit a linear probe on the latent and report
a held-out AUC, against a raw-pixel "redness ahead" baseline.

Run:
  python -m eval.eval_target_probe --n-rooms 6
  python -m eval.eval_target_probe --selftest
"""

import argparse
import sys

import numpy as np


def _auc(scores, labels):
    s, y = np.asarray(scores, float), np.asarray(labels, int)
    pos, neg = s[y == 1], s[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty(len(s), float)
    ranks[order] = np.arange(1, len(s) + 1)
    return float(
        (ranks[y == 1].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))
    )


def _in_fov(pos, target, half_deg, max_range=2.5):
    dx, dy = target[0] - pos[0], target[1] - pos[1]
    if dx <= 0:
        return False  # behind / beside — the +x-locked camera cannot see it
    if np.hypot(dx, dy) > max_range:
        return False
    return abs(np.degrees(np.arctan2(dy, dx))) <= half_deg


def _redness(frame):
    """Raw-pixel baseline: mean red-dominance (R - max(G,B)) over the
    central FOV band — how much bright red is straight ahead."""
    f = frame.astype(np.float32)
    band = f[:, 20:44, :]  # central vertical band (the +x look direction)
    red = band[:, :, 0] - np.maximum(band[:, :, 1], band[:, :, 2])
    return float(red.mean())


def _linear_probe_auc(X, y, seed=0):
    """Held-out AUC of a logistic linear probe on the latent (torch)."""
    import torch

    n = len(y)
    rng = np.random.default_rng(seed)
    idx = rng.permutation(n)
    cut = int(0.7 * n)
    tr, te = idx[:cut], idx[cut:]
    Xt = torch.tensor(X[tr], dtype=torch.float32)
    yt = torch.tensor(y[tr], dtype=torch.float32)
    w = torch.zeros(X.shape[1], requires_grad=True)
    b = torch.zeros(1, requires_grad=True)
    opt = torch.optim.Adam([w, b], lr=0.05)
    lossf = torch.nn.BCEWithLogitsLoss()
    for _ in range(400):
        opt.zero_grad()
        loss = lossf(Xt @ w + b, yt) + 1e-3 * (w @ w)
        loss.backward()
        opt.step()
    with torch.no_grad():
        st = (torch.tensor(X[te], dtype=torch.float32) @ w + b).numpy()
    return _auc(st, y[te])


def collect_target_frames(n_rooms=6, seed0=600000, grid=0.35, half_deg=None, ckpt=None):
    """Render target/no-target frames over a position grid and encode each
    with the shipped WM. Returns dict of arrays: `lat` (N,64) latents,
    `label` (N,) target-in-FOV, `red` (N,) pixel redness, `obs_in_fov`
    (N,) an obstacle box is in the +x FOV (the hard-negative flag — a
    detector must NOT fire on these). Shared by the linear probe and the
    detection-head trainer/gate.

    `ckpt` overrides the encoder with an explicit checkpoint (the
    unified-WM gate passes `output/world_model_unified.pth`), so a
    candidate WM is graded WITHOUT swapping the pinned champion artifact."""
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
        enc, _pred, _ch, _n, _meta = load_model(ckpt, device="cpu")
    else:
        enc, _pred, _ch, _n, _meta = load_or_train(device="cpu")
    env = make_env()
    env.reset(seed=seed0)
    lat, red, label, obs_fov = [], [], [], []
    for i in range(n_rooms):
        sc = single_room(seed0 + i)
        target = sc.beacon_xy  # the hidden spot becomes a VISUAL target
        x0, x1, y0, y1 = sc.bounds
        for x in np.arange(x0 + 0.6, x1 - 0.6, grid):
            for y in np.arange(y0 + 0.6, y1 - 0.6, grid):
                if sc.clearance((x, y)) <= 0.35:
                    continue
                off = (x - START[0], y - START[1])
                ids = sc.spawn_bodies(env, offset=off)
                tid = sc.spawn_target(env, target, offset=off)
                frame = grab_frame(env)
                remove_bodies(env, ids + [tid])
                with torch.no_grad():
                    z = enc(_frame_tensor(frame)).numpy().reshape(-1)
                lat.append(z)
                red.append(_redness(frame))
                label.append(1 if _in_fov((x, y), target, half) else 0)
                seen_obs = any(
                    _in_fov((x, y), (ox, oy), half) for ox, oy, _ in sc.obstacles
                )
                obs_fov.append(1 if seen_obs else 0)
    env.close()
    return {
        "lat": np.asarray(lat, dtype=np.float32),
        "red": np.asarray(red, dtype=float),
        "label": np.asarray(label, dtype=int),
        "obs_in_fov": np.asarray(obs_fov, dtype=int),
    }


def probe(n_rooms=6, seed0=600000, grid=0.35, half_deg=None, ckpt=None):
    d = collect_target_frames(n_rooms, seed0, grid, half_deg, ckpt=ckpt)
    y = d["label"]
    return {
        "n": len(y),
        "positive_rate": float(y.mean()),
        "wm_latent_auc": _linear_probe_auc(d["lat"], y),
        "pixel_redness_auc": _auc(d["red"], y),
    }


def selftest() -> None:
    assert abs(_auc([0.1, 0.2, 0.8, 0.9], [0, 0, 1, 1]) - 1.0) < 1e-9
    assert _in_fov((0, 0), (1, 0), 28) and not _in_fov((0, 0), (-1, 0), 28)
    assert not _in_fov((0, 0), (0, 3), 28)  # 90 deg off-axis, unseeable
    print("EVAL-TARGET-PROBE OK: AUC + FOV-label logic")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-rooms", type=int, default=6)
    ap.add_argument("--seed0", type=int, default=600000)
    ap.add_argument("--ckpt", default=None, help="grade this WM (default: champion)")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    r = probe(args.n_rooms, args.seed0, ckpt=args.ckpt)
    verdict = (
        "FEASIBLE on the WM latent (>=0.80)"
        if r["wm_latent_auc"] >= 0.80
        else (
            "weak (<0.65) — needs a new/wider perception path"
            if r["wm_latent_auc"] < 0.65
            else "borderline"
        )
    )
    print(
        f"[target-probe] {r['n']} frames (target-in-FOV {r['positive_rate']:.2f}) | "
        f"WM-latent AUC {r['wm_latent_auc']:.3f} | pixel-redness AUC "
        f"{r['pixel_redness_auc']:.3f}  [{verdict}]"
    )


if __name__ == "__main__":
    sys.exit(main())

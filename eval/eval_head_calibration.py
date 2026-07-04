"""Compare two checkpoints' collision-probability *landscapes* — the D0 probe.

The v0.5 campaign ended on a split verdict: the grounded model detects
strictly better (AUC, a ranking statistic) and flies strictly worse. The
recorded hypothesis: the policy does not consume rankings — it consumes
the heads' raw probability surfaces (8 sigmoids per candidate, see
`ObsBuilder`), and grounding recalibrated their *shape*. This probe
measures that shape, per world, on the same held-out frames, for two
checkpoints side by side:

  * **contrast** — per-frame std of P across the 6 speed-scaled candidate
    commands (mean over frames). This is the decision signal: a policy
    can only differentiate options that score differently.
  * **saturation** — fraction of (frame, candidate) pairs with P > 0.95
    or P < 0.05: how much of the surface is pinned to the rails.
  * **ECE** — 10-bin expected calibration error against the
    counterfactual oracle's labels, FOV-honesty masked (unanswerable
    pairs excluded) — is the probability *number* still a probability?
  * **mean P** — the overall bias of the surface.

All four are reported for the warn and critical rings at the longest
horizon (k=32 — the anticipation the campaign was about). Diagnostic
only: no bars. The interpretive rules are pre-registered in the campaign
journal *before* the numbers exist.

Run:
  python -m eval.eval_head_calibration --ckpt-a output/world_model_g1.pth \
      --ckpt-b experiments/metric_grounding/artifacts/wm_m1_ground.pth
  python -m eval.eval_head_calibration --selftest
"""

import argparse
import json
import sys

import numpy as np
import torch

from datasets.generate_rollouts import OUT as DATA
from datasets.intervention_labels import counterfactual_labels
from planner.action_set import A_NORM, ACTION_VECS
from world_model.training import _split_rollouts, load_model

RINGS = {"warn": 0, "crit": 1}


def _surface(ckpt_path: str, data: dict, rolls, device) -> np.ndarray:
    """P[k=32] for every (frame, candidate, ring) on the given rollouts:
    float (n_frames, n_actions, 2). Candidates are speed-scaled per rollout
    and normalized — the ObsBuilder/veer-ranking convention."""
    enc, pred, cheads, _nhead, _meta = load_model(ckpt_path, device)
    if getattr(enc, "temporal", None) is not None:
        raise SystemExit("temporal checkpoints need a windowed probe")
    L = data["frames"].shape[1]
    n_a = len(ACTION_VECS)
    out = []
    with torch.no_grad():
        for r in rolls:
            x = (
                torch.tensor(
                    data["frames"][r], dtype=torch.float32, device=device
                ).permute(0, 3, 1, 2)
                / 255.0
            )
            z = enc(x)  # (L, D)
            cands = torch.tensor(
                float(data["speed"][r]) * ACTION_VECS / A_NORM,
                dtype=torch.float32,
                device=device,
            )  # (n_a, 4)
            z_rep = z.repeat_interleave(n_a, dim=0)
            a_rep = cands.repeat(L, 1)
            logits = cheads(pred(z_rep, a_rep, base=z_rep))  # (L*n_a, H, 2)
            out.append(torch.sigmoid(logits[:, -1, :]).reshape(L, n_a, 2).cpu())
    return np.concatenate([o.numpy() for o in out])  # (sum_L, n_a, 2)


def _ece(p: np.ndarray, y: np.ndarray, bins: int = 10) -> float:
    edges = np.linspace(0.0, 1.0, bins + 1)
    n, err = len(p), 0.0
    for i in range(bins):
        m = (p >= edges[i]) & (p < edges[i + 1] if i < bins - 1 else p <= 1.0)
        if m.any():
            err += m.sum() / n * abs(p[m].mean() - y[m].mean())
    return float(err)


def evaluate(ckpt_a: str, ckpt_b: str, data: dict, seed: int = 0) -> dict:
    """Landscape stats per world for both checkpoints, on the seed-`seed`
    val rollouts (the same split the training runs report)."""
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    rng = np.random.default_rng(seed)
    _tr, va_rolls = _split_rollouts(data, rng)
    L = data["frames"].shape[1]
    cf, vis = counterfactual_labels(data)  # labels + FOV honesty mask
    lbl = np.concatenate([cf[r, :, :, -1, :] for r in va_rolls])  # (F, n_a, 2)
    msk = np.concatenate([vis[r] for r in va_rolls]).astype(bool)  # (F, n_a)
    frame_world = np.concatenate(
        [np.full(L, int(data["world_id"][r])) for r in va_rolls]
    )
    wn = (
        [str(x) for x in np.asarray(data["world_names"])]
        if "world_names" in data
        else ["classic", "dense", "moving"]
    )

    report: dict = {}
    for tag, path in (("a", ckpt_a), ("b", ckpt_b)):
        P = _surface(path, data, va_rolls, device)  # (F, n_a, 2)
        per_world: dict = {}
        for w in sorted(set(frame_world.tolist())):
            fm = frame_world == w
            stats = {}
            for ring, q in RINGS.items():
                p = P[fm][:, :, q]
                pv, yv = p[msk[fm]], lbl[fm][:, :, q][msk[fm]]
                stats[ring] = {
                    "contrast": float(p.std(axis=1).mean()),
                    "saturation": float(((p > 0.95) | (p < 0.05)).mean()),
                    "ece": _ece(pv, yv),
                    "mean_p": float(p.mean()),
                }
            per_world[wn[w] if w < len(wn) else str(w)] = stats
        report[tag] = {"ckpt": path, "worlds": per_world}
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt-a", help="baseline checkpoint (e.g. the champion)")
    ap.add_argument("--ckpt-b", help="candidate checkpoint")
    ap.add_argument("--data", default=DATA)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        import os
        import tempfile

        from datasets.generate_rollouts import gen
        from world_model.training import train

        data = gen(6, 80, seed=5, worlds=("classic", "dense", "moving"))
        ckpt, _m = train(data, epochs=2, batch=64, seed=0)
        path = os.path.join(tempfile.mkdtemp(), "wm_cal_selftest.pth")
        torch.save(ckpt, path)
        r = evaluate(path, path, data, seed=0)
        for w, s in r["a"]["worlds"].items():
            for ring in RINGS:
                assert r["a"]["worlds"][w][ring] == r["b"]["worlds"][w][ring]
                assert 0.0 <= s[ring]["saturation"] <= 1.0
                assert 0.0 <= s[ring]["ece"] <= 1.0
                assert s[ring]["contrast"] >= 0.0
        print(
            f"HEAD-CAL OK: identical ckpts -> identical landscapes "
            f"({len(r['a']['worlds'])} worlds x {len(RINGS)} rings, "
            f"contrast/saturation/ECE/mean all in range)"
        )
        return

    if not (args.ckpt_a and args.ckpt_b):
        raise SystemExit("--ckpt-a and --ckpt-b required (or --selftest)")
    blob = np.load(args.data)
    data = {k: blob[k] for k in blob.files}
    r = evaluate(args.ckpt_a, args.ckpt_b, data, seed=args.seed)
    print(f"HEAD-CAL OK: a={args.ckpt_a}  b={args.ckpt_b}")
    for w in r["a"]["worlds"]:
        for ring in RINGS:
            sa, sb = r["a"]["worlds"][w][ring], r["b"]["worlds"][w][ring]
            print(
                f"  {w:8s} {ring:4s} | contrast {sa['contrast']:.4f} -> "
                f"{sb['contrast']:.4f} | sat {sa['saturation']:.3f} -> "
                f"{sb['saturation']:.3f} | ECE {sa['ece']:.4f} -> "
                f"{sb['ece']:.4f} | meanP {sa['mean_p']:.3f} -> "
                f"{sb['mean_p']:.3f}"
            )
    if args.out:
        with open(args.out, "w") as f:
            json.dump(r, f, indent=1)


if __name__ == "__main__":
    main()
    sys.exit(0)

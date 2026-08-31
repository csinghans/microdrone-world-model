"""temporal_probe_v1's instrument: can "the previous glance" rank the moving world?

Probe heads on a FROZEN checkpoint's latent — no encoder gradients, no EMA,
no variance guard: this prices the INFORMATION claim (perception_v3: "a
single-frame latent cannot rank what it cannot see move") without touching
the recipe that destabilized at 160 epochs.

Arms (features per (rollout, t) sample; label = collision-within-32 of the
flown future, the same c_h[:, -1, 0] every AUC@32 claim in the repo uses):

  A0  the frozen collision heads on z_hat (no new head) — must reproduce
      eval_wm_checkpoint's row on the same split, or the instrument is
      invalid (rule 6: fix the tool before reading anything else)
  A   a fresh probe head on z_hat32 alone (controls for the head-retrain
      effect: any temporal gain must beat THIS, not A0)
  B   head on concat[z_hat32, z_t - z_{t-4}] — two-frame diff at stride 4
      (= the planner's DECIDE_EVERY; stride-1 mover displacement at 96 px
      is sub-pixel, priced in the campaign journal)
  C   head on concat[z_hat32, GRU_8(z_{t-7..t})] — recurrence over the
      K_WIN=8 window (~167 ms), GRU trained jointly with the head; the
      encoder stays frozen. The GRU is instantiated directly because
      TemporalEncoder.selftest's param bar was written for D=64.

Heads train on the TRAIN diet's transit worlds and score on the score
dataset's val split — the exact sample set behind the wm_96d128 moving
0.8891 row (same _split_rollouts seed as the checkpoint's training).

Run:
  python -m eval.eval_temporal_probe \
      --ckpt experiments/perception_v2/artifacts/wm_96d128.pth \
      --train-data output/combined_96.npz \
      --score-data output/transit_eval_holdout_96.npz \
      --seeds 0 1 2 --out experiments/temporal_probe_v1/probe_results.json
  python -m eval.eval_temporal_probe --selftest
"""

import argparse
import json
import os

import numpy as np
import torch
import torch.nn as nn

from world_model.losses import roc_auc
from world_model.training import (
    A_NORM,
    _index_samples,
    _split_rollouts,
    load_model,
)

DIFF_STRIDE = 4  # frames between the two glances (= planner DECIDE_EVERY)
K_WIN = 8  # GRU window, matching world_model.temporal


class MLPProbe(nn.Module):
    """The repo's standard frozen-latent head shape (target_detector)."""

    def __init__(self, d_in, hidden=32):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_in, hidden), nn.ReLU(), nn.Linear(hidden, 1)
        )

    def forward(self, feats):
        return self.net(feats["x"]).squeeze(-1)


class GRUProbe(nn.Module):
    """GRU over the latent window, concatenated with z_hat32, then the head."""

    def __init__(self, d=128, hidden=32):
        super().__init__()
        self.gru = nn.GRU(d, d, batch_first=True)
        self.head = nn.Sequential(
            nn.Linear(2 * d, hidden), nn.ReLU(), nn.Linear(hidden, 1)
        )

    def forward(self, feats):
        h, _ = self.gru(feats["win"])
        return self.head(torch.cat([h[:, -1], feats["x"]], dim=1)).squeeze(-1)


def _encode_all(enc, frames, device, batch=512):
    """Per-frame latents for a whole dataset: (R, L, D) on cpu."""
    R, L = frames.shape[:2]
    flat = frames.reshape(R * L, *frames.shape[2:])
    zs = []
    with torch.no_grad():
        for i in range(0, len(flat), batch):
            x = torch.tensor(flat[i : i + batch], dtype=torch.float32, device=device)
            zs.append(enc(x.permute(0, 3, 1, 2) / 255.0).cpu())
    return torch.cat(zs).reshape(R, L, -1)


def _zhat(pred, z, actions, pairs, device, batch=1024):
    """pred(z_t, a_t, base=z_t) for each sample: (n, H, D) on cpu."""
    outs = []
    with torch.no_grad():
        for i in range(0, len(pairs), batch):
            p = pairs[i : i + batch]
            zt = z[p[:, 0], p[:, 1]].to(device)
            a = torch.tensor(
                np.stack([actions[r, t] for r, t in p]) / A_NORM,
                dtype=torch.float32,
                device=device,
            )
            outs.append(pred(zt, a, base=zt).cpu())
    return torch.cat(outs)


def _features(z, pairs):
    """dz (stride DIFF_STRIDE) and the K_WIN latent window, both clamped at
    the rollout start (frame 0 repeats) — the training-side convention."""
    r = torch.tensor(pairs[:, 0])
    t = torch.tensor(pairs[:, 1])
    z_t = z[r, t]
    dz = z_t - z[r, torch.clamp(t - DIFF_STRIDE, min=0)]
    win = torch.stack(
        [z[r, torch.clamp(t - (K_WIN - 1) + j, min=0)] for j in range(K_WIN)],
        dim=1,
    )
    return z_t, dz, win


def _fit(model, feats, y, device, epochs=8, batch=512, lr=1e-3, wd=1e-3):
    model.to(device).train()
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=wd)
    lossf = nn.BCEWithLogitsLoss()
    yt = torch.tensor(y, dtype=torch.float32)
    n = len(yt)
    for _ in range(epochs):
        order = torch.randperm(n)
        for i in range(0, n, batch):
            b = order[i : i + batch]
            fb = {k: v[b].to(device) for k, v in feats.items()}
            opt.zero_grad()
            loss = lossf(model(fb), yt[b].to(device))
            loss.backward()
            opt.step()
    model.eval()
    return model


def _score(model, feats, device, batch=2048):
    outs = []
    with torch.no_grad():
        n = len(feats["x"])
        for i in range(0, n, batch):
            fb = {k: v[i : i + batch].to(device) for k, v in feats.items()}
            outs.append(torch.sigmoid(model(fb)).cpu().numpy())
    return np.concatenate(outs)


def _auc_by_world(scores, y, wid, wn):
    out = {"all": roc_auc(scores, y)}
    for w in sorted({int(x) for x in wid}):
        m = wid == w
        if int(m.sum()) >= 20:
            out[wn[w] if w < len(wn) else str(w)] = roc_auc(scores[m], y[m])
    return out


def _world_names(data):
    if "world_names" in data:
        return [str(x) for x in np.asarray(data["world_names"])]
    return ["classic", "dense", "moving"]


def run(ckpt, train_data, score_data, seeds, device, fit_epochs=8):
    """Grade all arms; returns the results dict (the campaign's record)."""
    enc, pred, cheads, nhead, meta = load_model(ckpt, device=device)
    dtr = train_data if hasattr(train_data, "keys") else np.load(train_data)
    dsc = score_data if hasattr(score_data, "keys") else np.load(score_data)

    # train samples: the diet's transit worlds only (the score set is transit)
    wn_tr = _world_names(dtr)
    idx_tr, ch_tr = _index_samples(dtr)
    transit = [i for i, n in enumerate(wn_tr) if n in ("classic", "dense", "moving")]
    keep = np.isin(np.asarray(dtr["world_id"])[idx_tr[:, 0]], transit)
    pairs_tr, y_tr = idx_tr[keep], ch_tr[keep][:, -1, 0]

    # score samples: the val split at the checkpoint's own training seed —
    # the exact sample set eval_wm_checkpoint grades (leakage rule inherited)
    seed_split = int(meta.get("seed", 0))
    wn_sc = _world_names(dsc)
    idx_sc, ch_sc = _index_samples(dsc)
    _, va_rolls = _split_rollouts(dsc, np.random.default_rng(seed_split))
    va = np.isin(idx_sc[:, 0], va_rolls)
    pairs_sc, y_sc = idx_sc[va], ch_sc[va][:, -1, 0]
    wid_sc = np.asarray(dsc["world_id"])[pairs_sc[:, 0]]

    z_tr = _encode_all(enc, np.asarray(dtr["frames"]), device)
    z_sc = _encode_all(enc, np.asarray(dsc["frames"]), device)
    zh_tr = _zhat(pred, z_tr, np.asarray(dtr["actions"]), pairs_tr, device)
    zh_sc = _zhat(pred, z_sc, np.asarray(dsc["actions"]), pairs_sc, device)
    _, dz_tr, win_tr = _features(z_tr, pairs_tr)
    _, dz_sc, win_sc = _features(z_sc, pairs_sc)
    x_tr, x_sc = zh_tr[:, -1], zh_sc[:, -1]
    d = x_tr.shape[1]

    # A0: the frozen heads themselves, no new parameters
    with torch.no_grad():
        a0 = torch.sigmoid(cheads(zh_sc.to(device))).cpu().numpy()[:, -1, 0]
    results = {
        "config": {
            "ckpt": str(ckpt),
            "diff_stride": DIFF_STRIDE,
            "k_win": K_WIN,
            "seeds": list(seeds),
            "split_seed": seed_split,
            "n_train": int(len(pairs_tr)),
            "n_score": int(len(pairs_sc)),
            "fit_epochs": fit_epochs,
        },
        "a0_frozen_heads": _auc_by_world(a0, y_sc, wid_sc, wn_sc),
        "arms": {},
    }

    arms = {
        "A_single_frame": (
            lambda: MLPProbe(d),
            {"x": x_tr},
            {"x": x_sc},
        ),
        "B_diff": (
            lambda: MLPProbe(2 * d),
            {"x": torch.cat([x_tr, dz_tr], dim=1)},
            {"x": torch.cat([x_sc, dz_sc], dim=1)},
        ),
        "C_gru": (
            lambda: GRUProbe(d),
            {"x": x_tr, "win": win_tr},
            {"x": x_sc, "win": win_sc},
        ),
    }
    for name, (mk, feats_tr, feats_sc) in arms.items():
        per_seed = {}
        for s in seeds:
            torch.manual_seed(s)
            model = _fit(mk(), feats_tr, y_tr, device, epochs=fit_epochs)
            per_seed[str(s)] = _auc_by_world(
                _score(model, feats_sc, device), y_sc, wid_sc, wn_sc
            )
        worlds = per_seed[str(seeds[0])].keys()
        mean = {w: float(np.mean([per_seed[str(s)][w] for s in seeds])) for w in worlds}
        spread = {
            w: float(
                max(per_seed[str(s)][w] for s in seeds)
                - min(per_seed[str(s)][w] for s in seeds)
            )
            for w in worlds
        }
        n_extra = sum(p.numel() for p in mk().parameters())
        results["arms"][name] = {
            "per_seed": per_seed,
            "mean": mean,
            "spread": spread,
            "extra_params": int(n_extra),
            "extra_int8_kb": n_extra / 1024,
        }
        print(
            f"[probe] {name}: "
            + " ".join(f"{w}={v:.4f}" for w, v in mean.items())
            + f" (spread moving {spread.get('moving', 0.0):.4f}, "
            f"+{n_extra / 1024:.1f} KB int8)"
        )
    return results


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default=None)
    ap.add_argument("--train-data", default="output/combined_96.npz")
    ap.add_argument("--score-data", default="output/transit_eval_holdout_96.npz")
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--fit-epochs", type=int, default=8)
    ap.add_argument("--out", default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    device = "mps" if torch.backends.mps.is_available() else "cpu"

    if args.selftest:
        import tempfile

        from datasets.generate_rollouts import gen
        from world_model.training import train

        data_tr = gen(8, 90, seed=3, worlds=("classic", "dense", "moving"))
        data_sc = gen(6, 90, seed=4, worlds=("classic", "dense", "moving"))
        ckpt, _ = train(data_tr, epochs=2, batch=64, seed=0)
        path = os.path.join(tempfile.mkdtemp(), "wm_tprobe_selftest.pth")
        torch.save(ckpt, path)
        r = run(path, data_tr, data_sc, seeds=[0], device=device, fit_epochs=2)
        for arm, rec in r["arms"].items():
            for w, v in rec["mean"].items():
                assert 0.0 <= v <= 1.0, f"{arm}/{w} AUC out of range ({v})"
        assert 0.0 <= r["a0_frozen_heads"]["all"] <= 1.0
        assert (
            r["arms"]["C_gru"]["extra_params"]
            > r["arms"]["A_single_frame"]["extra_params"]
        ), "GRU arm must actually carry the GRU"
        assert r["config"]["n_score"] > 0, "empty score split"
        print(
            "TEMPORAL-PROBE OK: A0 + 3 arms graded on a disjoint draw, "
            f"n_score={r['config']['n_score']}, all AUCs in range"
        )
        return

    if not args.ckpt:
        raise SystemExit("--ckpt is required (the frozen latent under test)")
    results = run(
        args.ckpt,
        args.train_data,
        args.score_data,
        seeds=args.seeds,
        device=device,
        fit_epochs=args.fit_epochs,
    )
    if args.out:
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        with open(args.out, "w") as f:
            json.dump(results, f, indent=1)
        print(f"[probe] wrote {args.out}")


if __name__ == "__main__":
    main()

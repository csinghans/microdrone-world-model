"""Visual target detector — a small head on the frozen WM latent.

vision_v1's feasibility probe found the shipped WM latent linearly
separates "target in the +x FOV" at AUC 0.94 (> a color-only pixel
baseline). This trains a small MLP head on that frozen latent to turn it
into a deployable detector, and gates it on FRESH rooms — the decisive
metric being the OBSTACLE FALSE-ALARM: does it fire only on the red
target, or also on the orange obstacle boxes? (If the latter, the 0.94
was riding "a box ahead," not target identity.)

No WM retrain: the encoder is frozen; only the head learns. The head is
the visual-search mission's "found" signal, replacing the abstract
beacon's omnidirectional magic sensing.

Run:
  python -m search.target_detector --train output/target_head.pt
  python -m search.target_detector --selftest
"""

import numpy as np


class DetectionHead:
    """MLP (64 -> 32 -> 1) on the frozen WM latent. Plain torch; trained by
    `fit`, scored by `prob`."""

    def __init__(self, d_in=64, hidden=32):
        import torch

        self.torch = torch
        self.net = torch.nn.Sequential(
            torch.nn.Linear(d_in, hidden),
            torch.nn.ReLU(),
            torch.nn.Linear(hidden, 1),
        )

    def fit(self, X, y, steps=600, lr=0.02, wd=1e-3):
        torch = self.torch
        Xt = torch.tensor(X, dtype=torch.float32)
        yt = torch.tensor(y, dtype=torch.float32)
        opt = torch.optim.Adam(self.net.parameters(), lr=lr, weight_decay=wd)
        lossf = torch.nn.BCEWithLogitsLoss()
        self.net.train()
        for _ in range(steps):
            opt.zero_grad()
            loss = lossf(self.net(Xt).squeeze(-1), yt)
            loss.backward()
            opt.step()
        self.net.eval()
        return self

    def prob(self, X):
        torch = self.torch
        with torch.no_grad():
            return torch.sigmoid(
                self.net(torch.tensor(X, dtype=torch.float32)).squeeze(-1)
            ).numpy()

    def save(self, path):
        self.torch.save(self.net.state_dict(), path)

    def load(self, path):
        self.net.load_state_dict(self.torch.load(path, weights_only=True))
        self.net.eval()
        return self


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


def _score(head, te, thr):
    """Detection scorecard on a held-out block: AUC, precision, recall, and
    the decisive obstacle false-alarm (fire rate on obstacle-facing frames)."""
    p = head.prob(te["lat"])
    y = te["label"]
    pred = (p >= thr).astype(int)
    tp = int(((pred == 1) & (y == 1)).sum())
    fp = int(((pred == 1) & (y == 0)).sum())
    fn = int(((pred == 0) & (y == 1)).sum())
    hard = (y == 0) & (te["obs_in_fov"] == 1)
    obs_fa = float(pred[hard].mean()) if hard.sum() else 0.0
    return {
        "n_test": int(len(y)),
        "positive_rate": float(y.mean()),
        "auc": _auc(p, y),
        "precision": tp / (tp + fp) if (tp + fp) else 0.0,
        "recall": tp / (tp + fn) if (tp + fn) else 0.0,
        "obstacle_false_alarm": obs_fa,
        "n_hard_neg": int(hard.sum()),
    }


def train_and_gate(out=None, n_rooms=6, train_seed0=600000, test_seed0=610000, thr=0.5):
    """Train the head on one room block, gate on a disjoint fresh block
    (yaw=0 +x frames — the vision_v1 detector)."""
    from eval.eval_target_probe import collect_target_frames

    tr = collect_target_frames(n_rooms, train_seed0)
    te = collect_target_frames(n_rooms, test_seed0)
    head = DetectionHead().fit(tr["lat"], tr["label"])
    if out:
        head.save(out)
    return _score(head, te, thr)


def train_and_gate_yaw(
    out=None, n_rooms=6, train_seed0=600000, test_seed0=610000, thr=0.5
):
    """The yaw_v1 detector: train on YAW-swept frames encoded by the unified
    WM, gate on a fresh yaw-swept block. Fires on a target seen at ANY
    heading, so the hover-yaw-scan can confirm off-axis targets (Phase 0
    showed the frozen latent is yaw-invariant, so no WM retrain — only this
    head learns on rotated frames)."""
    from eval.eval_yaw_detect import UNIFIED_WM, collect_yaw_frames

    tr = collect_yaw_frames(n_rooms, train_seed0, ckpt=UNIFIED_WM)
    te = collect_yaw_frames(n_rooms, test_seed0, ckpt=UNIFIED_WM)
    head = DetectionHead().fit(tr["lat"], tr["label"])
    if out:
        head.save(out)
    return _score(head, te, thr)


def selftest() -> None:
    # env-free: the head learns a linearly-separable toy latent
    rng = np.random.default_rng(0)
    X = rng.normal(size=(400, 64)).astype(np.float32)
    y = (X[:, 0] + 0.5 * X[:, 1] > 0).astype(int)
    head = DetectionHead().fit(X, y, steps=300)
    auc = _auc(head.prob(X), y)
    assert auc > 0.9, f"head learns a separable toy (auc {auc:.2f})"
    assert head.prob(X[:3]).shape == (3,)
    print(f"TARGET-DETECTOR OK: head fits a separable toy (auc {auc:.2f})")


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--train", default=None, help="output head .pt (else selftest)")
    ap.add_argument("--n-rooms", type=int, default=6)
    ap.add_argument("--yaw", action="store_true", help="train on yaw-swept frames")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest or not args.train:
        selftest()
        return
    fn = train_and_gate_yaw if args.yaw else train_and_gate
    r = fn(args.train, args.n_rooms)
    print(
        f"[target-detector] test n={r['n_test']} (pos {r['positive_rate']:.2f}, "
        f"hard-neg {r['n_hard_neg']}) | AUC {r['auc']:.3f} | "
        f"precision {r['precision']:.3f} recall {r['recall']:.3f} | "
        f"obstacle-FA {r['obstacle_false_alarm']:.3f}"
    )
    ok = (
        r["auc"] >= 0.85
        and r["recall"] >= 0.80
        and r["precision"] >= 0.75
        and r["obstacle_false_alarm"] <= 0.15
    )
    print(f"  DETECTION GATE: {'PASS' if ok else 'FAIL / honest-negative'}")


if __name__ == "__main__":
    main()

"""In-flight detection — pricing the stationary-imaging debt (C1).

Every indoor detection GREEN was measured on parked-drone probes
(kinematics reset, camera level); missions convert per-frame recall into
mission recall by scan choreography. This eval harvests per-frame head
scores DURING flight — attitude tilt, control wobble, whatever flying
actually produces — via the behaviour-preserving `trace` hook on
`run_vision_search` (the +x sweep runner is the only one that detects
while MOVING; the deployed yaw-scan runner detects only while hovering
in spin-scans). Pooled in-flight AUC is judged against the frozen bars
in experiments/detect_inflight_v1/journal.md (committed first):
>= 0.90 debt paid; < 0.85 releases ONE moving-frame head-retrain knob.
The recorded streams are also C2's replay corpus (SPRT vs confirm-k on
identical data).

Run:
  python -m eval.eval_inflight_detect --n 20
  python -m eval.eval_inflight_detect --selftest
"""

import argparse
import os
import sys

import numpy as np

HEAD = "output/target_head_yaw.pt"
STREAMS = os.path.join("experiments", "detect_inflight_v1", "artifacts", "streams.npz")
REF_AUC, REF_RECALL, REF_FA = 0.9818, 0.758, 0.021  # yaw_v1 stationary test block


def suite(n=20, seed0=620000, thr=0.65, head_path=HEAD, out=STREAMS):
    from eval.eval_vision_search import run_vision_search
    from eval.eval_yaw_detect import UNIFIED_WM
    from search.target_detector import DetectionHead, _auc
    from sim.envs import make_env
    from sim.indoor.rooms import single_room
    from world_model.training import load_model

    enc, *_ = load_model(UNIFIED_WM, device="cpu")
    det = DetectionHead().load(head_path)
    env = make_env()
    cols = {k: [] for k in ("flight", "step", "prob", "label", "yaw", "fired")}
    for i in range(n):
        tr = []
        run_vision_search(
            env, single_room(seed0 + i), det, enc, seed0 + i, thr, trace=tr
        )
        for d, p, y, yw, f in tr:
            cols["flight"].append(i)
            cols["step"].append(d)
            cols["prob"].append(p)
            cols["label"].append(y)
            cols["yaw"].append(yw)
            cols["fired"].append(f)
        print(
            f"  flight {i:2d}: {len(tr):4d} frames, "
            f"positives {sum(t[2] for t in tr):3d}",
            flush=True,
        )
    env.close()
    probs = np.asarray(cols["prob"], dtype=float)
    labels = np.asarray(cols["label"], dtype=int)
    auc = _auc(probs, labels)
    pos = labels == 1
    recall = float((probs[pos] >= thr).mean()) if pos.any() else float("nan")
    fa = float((probs[~pos] >= thr).mean()) if (~pos).any() else float("nan")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    np.savez(out, **{k: np.asarray(v) for k, v in cols.items()})
    verdict = (
        "DEBT PAID (>= 0.90)"
        if auc >= 0.90
        else (
            "DEBT REAL (< 0.85) — moving-frame head-retrain knob released"
            if auc < 0.85
            else "borderline (0.85-0.90) — pool n=40 before any knob"
        )
    )
    print(
        f"[inflight-detect] n={n} frames={len(labels)} "
        f"pos_rate={float(labels.mean()):.3f}"
    )
    print(f"  pooled in-flight AUC {auc:.4f} (stationary ref {REF_AUC}) -> {verdict}")
    print(
        f"  per-frame @thr {thr}: recall {recall:.3f} (ref {REF_RECALL})  "
        f"FA {fa:.3f} (ref {REF_FA}; base differs — all negatives, informational)"
    )
    print(f"  streams -> {out}")
    return {
        "n": n,
        "frames": int(len(labels)),
        "pos_rate": float(labels.mean()),
        "auc": float(auc),
        "recall": recall,
        "fa": fa,
        "verdict": verdict,
    }


def selftest() -> None:
    import inspect

    from eval.eval_vision_search import run_vision_search, run_yaw_scan_search
    from search.target_detector import _auc

    # both runners expose the behaviour-preserving trace hook
    assert "trace" in inspect.signature(run_vision_search).parameters
    assert "trace" in inspect.signature(run_yaw_scan_search).parameters
    assert inspect.signature(run_vision_search).parameters["trace"].default is None
    # pooled math on a synthetic stream: separable scores -> AUC 1.0,
    # recall/FA at the threshold count the right frames (one positive is
    # deliberately below thr: recall 2/3, FA 0)
    probs = np.array([0.9, 0.8, 0.3, 0.2, 0.1, 0.05])
    labels = np.array([1, 1, 1, 0, 0, 0])
    assert abs(_auc(probs, labels) - 1.0) < 1e-9
    thr = 0.65
    pos = labels == 1
    assert abs(float((probs[pos] >= thr).mean()) - 2 / 3) < 1e-9
    assert abs(float((probs[~pos] >= thr).mean()) - 0.0) < 1e-9
    print(
        "INFLIGHT-DETECT OK: trace hooks present (default None), "
        "pooled AUC/recall/FA math"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--seed0", type=int, default=620000)
    ap.add_argument("--thr", type=float, default=0.65)
    ap.add_argument("--head", default=HEAD)
    ap.add_argument("--out", default=STREAMS)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    suite(args.n, args.seed0, args.thr, args.head, args.out)


if __name__ == "__main__":
    sys.exit(main())

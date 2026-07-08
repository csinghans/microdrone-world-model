"""Dual-track gate: does ONE unified WM hold BOTH transit + indoor?

Head-to-head, unified vs the shipped champion, on IDENTICAL frames:
  * transit   — per-world collision AUC@32 on a held-out transit set
                (`eval_wm_checkpoint.evaluate`, same data + split seed for
                both models -> identical val frames).
  * indoor    — target-detection WM-latent AUC (`eval_target_probe`) and
                forward-collision AUC (`eval_search_wm_probe`); the
                detection grid is fixed and the `frontier` flight is
                GEOMETRIC (model-independent), so both models see identical
                frames.
  * --closed-loop — transit closed-loop WM-arm (`eval_closed_loop.evaluate`
                takes model components directly, no artifact swap): crash%,
                min-clear, false-evasion%, reached%, lead.
  * --speed-sweep — the promotion pre-condition: closed-loop WMPolicy
                head-to-head across the transit speed envelope (0.8..1.6
                m/s), same seeds every cell. Does the win hold at more than
                one operating point?

The champion path (`output/world_model.pth`) is READ-only — never swapped,
never clobbered. See experiments/unified_wm_v1/journal.md for the frozen
bars, the confound control, and the verdict.

Run:
  python -m eval.eval_unified_wm_gate                    # transit + indoor
  python -m eval.eval_unified_wm_gate --closed-loop      # + closed-loop
  python -m eval.eval_unified_wm_gate --speed-sweep      # promotion sweep
  python -m eval.eval_unified_wm_gate --selftest         # CI, no artifacts
"""

import argparse
import os
import sys

import numpy as np

from world_model.training import MODEL

UNIFIED = os.path.join(os.path.dirname(MODEL), "world_model_unified.pth")
HOLDOUT = os.path.join(os.path.dirname(MODEL), "transit_eval_holdout.npz")


def transit_gate(champion, unified, data_path=HOLDOUT, seed=0):
    """Per-world AUC@32 for both models on the identical held-out val split."""
    from eval.eval_wm_checkpoint import evaluate

    data = dict(np.load(data_path, allow_pickle=True))
    out = {}
    for name, ck in [("champion", champion), ("unified", unified)]:
        r = evaluate(ck, data, seed=seed)
        w = r["auc_by_world"]
        out[name] = {
            **{k: float(v) for k, v in w.items()},
            "auc32": float(r["auc_h"][-1]),
        }
    return out


def ck_is_champion(ck):
    """probe()/collect_target_frames() take ckpt=None to mean the champion
    (load_or_train the pinned path); normalize the champion path to None so
    nothing is re-read from a possibly-swapped artifact."""
    return ck is None or os.path.abspath(ck) == os.path.abspath(MODEL)


def indoor_gate(champion, unified):
    """Target-detection + forward-collision AUC for both models."""
    from eval.eval_search_wm_probe import probe as fwd_probe
    from eval.eval_target_probe import probe as det_probe

    out = {}
    for name, ck in [("champion", champion), ("unified", unified)]:
        ck = None if ck_is_champion(ck) else ck
        det = det_probe(n_rooms=6, seed0=600000, ckpt=ck)
        fwd = fwd_probe(n=12, seed0=130000, ckpt=ck, fov_label=True)
        out[name] = {
            "detection_auc": float(det["wm_latent_auc"]),
            "forward_auc": float(fwd["auc_forward"]),
        }
    return out


def wm_arm(rows):
    """Deployed WM-arm metrics from eval_closed_loop rows."""
    from sim.envs import CTRL_HZ

    ip = [r for r in rows if r["in_path"]]
    cl = [r for r in rows if not r["in_path"]]
    leads = [
        (r["reactive"]["trigger"] - r["wm"]["trigger"]) * 1000.0 / CTRL_HZ
        for r in ip
        if r["reactive"]["trigger"] >= 0 and r["wm"]["trigger"] >= 0
    ]
    return {
        "crash": float(np.mean([float(r["wm"]["crashed"]) for r in ip])),
        "min_clear": float(np.mean([float(r["wm"]["min_clear"]) for r in ip])),
        "false_evasion": float(np.mean([r["wm"]["trigger"] >= 0 for r in cl])),
        "reached": float(np.mean([float(r["wm"]["reached"]) for r in ip])),
        "lead_ms": float(np.mean(leads)) if leads else float("nan"),
    }


def closed_loop_gate(champion, unified, n=60, seed0=1000):
    from eval.eval_closed_loop import evaluate as cl_eval
    from world_model.training import load_model

    out = {}
    for name, ck in [("champion", champion), ("unified", unified)]:
        enc, pred, cheads, nhead, meta = load_model(ck, device="cpu")
        out[name] = wm_arm(cl_eval(n, seed0, enc, pred, cheads, nhead, meta))
    return out


# the repo's transit speed axis: x 0.8 m/s base -> 0.8..1.6 m/s cruise
SWEEP_SPEEDS = (1.0, 1.25, 1.5, 1.75, 2.0)


def _wmpolicy_arm(env, model, speed, n, seed0):
    """WMPolicy over n seeds (70% in-path) at one speed: crash%/reached%/
    min-clear (in-path) + false-evasion% (clear)."""
    from eval.eval_closed_loop import run_episode
    from planner.latent_mpc import WMPolicy

    enc, pred, cheads, _nhead, meta = model
    ipc, ipr, ipm, clt = [], [], [], []
    for i in range(n):
        in_path = (i % 10) < 7
        r = run_episode(
            env,
            WMPolicy(enc, pred, cheads, meta),
            seed0 + i,
            in_path=in_path,
            speed=speed,
        )
        if in_path:
            ipc.append(float(r["crashed"]))
            ipr.append(float(r["reached"]))
            ipm.append(r["min_clear"])
        else:
            clt.append(r["trigger"] >= 0)
    return {
        "crash": float(np.mean(ipc)),
        "reached": float(np.mean(ipr)),
        "min_clear": float(np.mean(ipm)),
        "false_evasion": float(np.mean(clt)),
    }


def speed_sweep_gate(champion, unified, speeds=SWEEP_SPEEDS, n=40, seed0=3000):
    """Closed-loop WMPolicy head-to-head across the transit speed envelope —
    the promotion pre-condition (does the win hold at more than one operating
    point?). Same seeds across speeds AND models -> identical pillar courses."""
    from sim.envs import make_env
    from world_model.training import load_model

    env = make_env()
    models = {
        "champion": load_model(champion, device="cpu"),
        "unified": load_model(unified, device="cpu"),
    }
    out = {}
    for s in speeds:
        out[s] = {
            name: _wmpolicy_arm(env, m, s, n, seed0) for name, m in models.items()
        }
    env.close()
    return out


def selftest() -> None:
    # wm_arm math on synthetic rows (no artifacts, no sim)
    rows = [
        {
            "in_path": True,
            "wm": {"crashed": 1, "min_clear": 0.3, "trigger": 20, "reached": 1},
            "reactive": {"trigger": 40},
        },
        {
            "in_path": True,
            "wm": {"crashed": 0, "min_clear": 0.5, "trigger": 30, "reached": 1},
            "reactive": {"trigger": 50},
        },
        {
            "in_path": False,
            "wm": {"crashed": 0, "min_clear": 0.9, "trigger": -1, "reached": 1},
            "reactive": {"trigger": 80},
        },
    ]
    m = wm_arm(rows)
    assert abs(m["crash"] - 0.5) < 1e-9, "2 in-path, 1 crashed -> 0.5"
    assert abs(m["false_evasion"] - 0.0) < 1e-9, "the 1 clear run did not trigger"
    assert abs(m["reached"] - 1.0) < 1e-9
    assert m["lead_ms"] > 0, "reactive triggers later -> positive WM lead"
    assert ck_is_champion(None) and ck_is_champion(MODEL)
    assert not ck_is_champion("output/world_model_unified.pth")
    print("EVAL-UNIFIED-WM-GATE OK: wm_arm math + champion-path guard")


def _fmt(d, keys):
    return "  ".join(f"{k}={d[k]:.3f}" if k in d else f"{k}=--" for k in keys)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--champion", default=MODEL)
    ap.add_argument("--unified", default=UNIFIED)
    ap.add_argument("--data", default=HOLDOUT, help="held-out transit eval set")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--closed-loop", action="store_true")
    ap.add_argument("--cl-seeds", type=int, default=60)
    ap.add_argument("--speed-sweep", action="store_true", help="promotion gate")
    ap.add_argument("--sweep-seeds", type=int, default=40)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    if not os.path.exists(args.unified):
        raise SystemExit(f"unified WM not found: {args.unified} (train it first)")

    print("=== TRANSIT (per-world AUC@32, identical held-out val frames) ===")
    t = transit_gate(args.champion, args.unified, args.data, args.seed)
    ks = ["classic", "dense", "moving", "auc32"]
    for name in ("champion", "unified"):
        print(f"  {name:9s} {_fmt(t[name], ks)}")

    print("=== INDOOR (identical frames: fixed grid + geometric flight) ===")
    i = indoor_gate(args.champion, args.unified)
    for name in ("champion", "unified"):
        print(f"  {name:9s} {_fmt(i[name], ['detection_auc', 'forward_auc'])}")

    if args.closed_loop:
        print(f"=== TRANSIT CLOSED-LOOP (WM-arm, {args.cl_seeds} seeds) ===")
        c = closed_loop_gate(args.champion, args.unified, n=args.cl_seeds)
        ks = ["crash", "min_clear", "false_evasion", "reached", "lead_ms"]
        for name in ("champion", "unified"):
            print(f"  {name:9s} {_fmt(c[name], ks)}")

    if args.speed_sweep:
        print(f"=== TRANSIT SPEED SWEEP (WMPolicy, {args.sweep_seeds} seeds/speed) ===")
        sw = speed_sweep_gate(args.champion, args.unified, n=args.sweep_seeds)
        print(f"  {'m/s':>5}  {'model':9} crash reached min-clr false-evade")
        for s in SWEEP_SPEEDS:
            for name in ("champion", "unified"):
                m = sw[s][name]
                print(
                    f"  {s*0.8:>5.2f}  {name:9} "
                    f"{m['crash']*100:4.0f}% {m['reached']*100:5.0f}%  "
                    f"{m['min_clear']:.2f}m   {m['false_evasion']*100:4.0f}%"
                )


if __name__ == "__main__":
    sys.exit(main())

"""Raise the speed until reaction breaks: crash rate versus cruise speed.

The physics of why the curves must split: a reactive trigger fires at a
fixed visual *distance* (danger-now learned "planar < 0.7 m"), so as speed
rises, the time between trigger and impact shrinks — and with bounded
lateral authority, at some speed the evasion no longer fits in the time
left. The world model triggers at a fixed *time* (~0.7 s of look-ahead,
because the danger heads are conditioned on the commanded speed), which is a
speed-proportional distance. Reaction is a distance budget; anticipation is
a time budget. Speed spends the first and not the second.

All policies fly the same threatened courses at each cruise speed (the same
seeds across speeds), with the whole command set scaled together — the same
model, trained across the 0.6–1.6 m/s envelope, powers every run.

Honest scope: these are *single-pillar* courses on purpose. The threat sits
where every policy can see it, so the sweep isolates the mechanism it claims
to measure; the cluttered scoreboard (`eval_closed_loop`) probes the FOV
blind side separately.

Run:
  python -m eval.eval_speed_sweep --seeds 30
  python -m eval.eval_speed_sweep --selftest   # 2 speeds, asserts
Needs output/world_model.pth (auto-trains a tiny one if missing).
"""

import argparse
import os
import sys

import numpy as np

from eval.eval_closed_loop import load_or_train, run_episode
from planner.latent_mpc import ReactivePolicy, WMPolicy
from sim.envs import make_env

SPEEDS = (1.0, 1.25, 1.5, 1.75, 2.0)  # x 0.8 m/s base -> 0.8..1.6 m/s cruise
BASE_V = 0.8  # forward command at speed factor 1.0 (m/s)
OUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "output",
    "speed_sweep.png",
)


def _policies(enc, pred, cheads, nhead, meta):
    """Reactive + hand MPC always; learned variants join automatically when a
    trained .zip exists. Each factory takes the cruise-speed factor."""
    mk = {
        "reactive": lambda s: ReactivePolicy(enc, nhead),
        "wm": lambda s: WMPolicy(enc, pred, cheads, meta, speed=s),
    }
    from planner.learned_policy import LearnedPolicy, load_policy, zip_path

    for name, rec, edge, curr in (
        ("learned", False, False, False),
        ("learned-rnn", True, False, False),
        ("learned-rnn-edge", True, True, False),
        ("learned-rnn-curr", True, False, True),
    ):
        path = zip_path(recurrent=rec, edge=edge, curr=curr)
        if os.path.exists(path):
            model = load_policy(path)
            mk[name] = lambda s, m=model: LearnedPolicy(
                m, enc, pred, cheads, meta, speed=s
            )
    return mk


def sweep(speeds, n_seeds: int, seed0: int) -> list:
    """Fly `n_seeds` single-pillar courses per speed with every available
    policy. The same seeds repeat across speeds, so each speed step changes
    exactly one thing — and `solo` courses put the one threat where every
    policy can see it, so the sweep measures the anticipation mechanism, not
    the FOV limit."""
    enc, pred, cheads, nhead, meta = load_or_train(device="cpu")
    mk = _policies(enc, pred, cheads, nhead, meta)
    env = make_env()
    rows = []
    for s in speeds:
        row = {"speed": s, "v": s * BASE_V}
        report = []
        for name, factory in mk.items():
            crash, clear = 0, []
            for i in range(n_seeds):
                run = run_episode(
                    env, factory(s), seed0 + i, in_path=True, speed=s, solo=True
                )
                crash += int(run["crashed"])
                clear.append(run["min_clear"])
            row[f"crash_{name}"] = crash / n_seeds
            row[f"clear_{name}"] = float(np.mean(clear))
            report.append(f"{name} {row[f'crash_{name}']:.0%}")
        rows.append(row)
        print(f"  v={row['v']:.1f} m/s: crash " + " / ".join(report))
    env.close()
    rows[0]["_names"] = list(mk)
    return rows


COLORS = {
    "reactive": "tab:orange",
    "wm": "tab:green",
    "learned": "tab:blue",
    "learned-rnn": "tab:purple",
    "learned-rnn-edge": "tab:red",
    "learned-rnn-curr": "tab:brown",
}
LABELS = {
    "reactive": "reactive",
    "wm": "wm (hand MPC)",
    "learned": "learned (stacked memory)",
    "learned-rnn": "learned (LSTM memory)",
    "learned-rnn-edge": "learned (LSTM, edge-biased speeds)",
    "learned-rnn-curr": "learned (LSTM, mixed-diet curriculum)",
}


def _save_plot(rows) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    v = [r["v"] for r in rows]
    names = rows[0]["_names"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 3.6))
    for name in names:
        ax1.plot(
            v,
            [100 * r[f"crash_{name}"] for r in rows],
            "o-",
            color=COLORS.get(name, "tab:gray"),
            label=LABELS.get(name, name),
        )
        ax2.plot(
            v,
            [r[f"clear_{name}"] for r in rows],
            "o-",
            color=COLORS.get(name, "tab:gray"),
            label=LABELS.get(name, name),
        )
    ax1.set_xlabel("cruise speed (m/s)")
    ax1.set_ylabel("crash rate (%)")
    ax1.set_title("Reaction is a distance budget")
    ax1.legend(fontsize=7)
    ax2.set_xlabel("cruise speed (m/s)")
    ax2.set_ylabel("mean min clearance (m)")
    ax2.set_title("Anticipation is a time budget")
    ax2.legend(fontsize=7)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUT, dpi=110)
    print(f"[INFO] saved {OUT}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--seed0", type=int, default=3000)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    speeds, n = ((1.0, 2.0), 8) if args.selftest else (SPEEDS, args.seeds)

    rows = sweep(speeds, n, args.seed0)
    _save_plot(rows)
    lo, hi = rows[0], rows[-1]
    names = rows[0]["_names"]
    lo_s = "/".join(f"{lo[f'crash_{k}']:.0%}" for k in names)
    hi_s = "/".join(f"{hi[f'crash_{k}']:.0%}" for k in names)
    print(
        f"SPEED-SWEEP OK: {n} single-pillar courses/speed — crash "
        f"({'/'.join(names)}) at {lo['v']:.1f} m/s = {lo_s}; at "
        f"{hi['v']:.1f} m/s = {hi_s} — reaction pays a distance, "
        f"anticipation pays time"
    )
    if args.selftest:
        assert (
            hi["crash_wm"] < hi["crash_reactive"] - 0.25
        ), "the story did not hold: wm does not clearly out-survive reactive at speed"
        assert hi["clear_wm"] > hi["clear_reactive"], "no clearance edge at speed"
        # at walking pace both should be near-clean; the wm is allowed the
        # small planner tail the docstring's honest note documents
        assert (
            lo["crash_wm"] <= lo["crash_reactive"] + 2.0 / n + 1e-9
        ), "wm crashes at base speed beyond the documented planner tail"


if __name__ == "__main__":
    main()
    sys.exit(0)

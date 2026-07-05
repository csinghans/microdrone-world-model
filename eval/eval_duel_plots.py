"""Render a duel campaign's verdict as pictures — the obvious eval.

Reads a campaign's `results.json` (every knob flew the same cells on the
same seeds, so the knobs ARE the contenders) and draws:

  * **the outcome bars** — per door cell, one stacked bar per contender:
    threaded / pinched / froze / other. The whole argument of the
    reactive-vs-predictive duel in one glance.
  * **the trajectory overlay** (`--trajectories`) — re-flies ONE shared
    seed per contender through the same door and overlays the paths,
    with the aperture drawn where it was at each contender's crossing
    instant. This is the article figure.

Run:
  python -m eval.eval_duel_plots --exp experiments/closing_door
  python -m eval.eval_duel_plots --exp experiments/closing_door --trajectories
  python -m eval.eval_duel_plots --selftest
"""

import argparse
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BAR_KEYS = ("threaded", "pinched", "froze")
COLORS = {"threaded": "tab:green", "pinched": "tab:red", "froze": "tab:blue"}


def outcome_bars(results: dict, out_png: str) -> list:
    """One subplot per duel cell (cells that carry the 'threaded' metric),
    one stacked bar per knob. Returns the duel cell ids."""
    knobs = results["knobs"]
    duel_cells = sorted(
        {
            cid
            for k in knobs
            for cid, c in k["cells"].items()
            if "threaded" in c.get("custom", {})
        }
    )
    if not duel_cells:
        raise SystemExit("no duel cells (custom metric 'threaded') in results")
    fig, axes = plt.subplots(
        1, len(duel_cells), figsize=(1.2 + 3.2 * len(duel_cells), 3.8), squeeze=False
    )
    for ax, cid in zip(axes[0], duel_cells):
        labels, bottoms = [], np.zeros(len(knobs))
        for key in BAR_KEYS:
            vals = np.array(
                [k["cells"].get(cid, {}).get("custom", {}).get(key, 0.0) for k in knobs]
            )
            ax.bar(
                range(len(knobs)),
                vals,
                bottom=bottoms,
                color=COLORS[key],
                label=key,
                width=0.7,
            )
            bottoms += vals
        other = np.clip(1.0 - bottoms, 0.0, 1.0)
        ax.bar(
            range(len(knobs)),
            other,
            bottom=bottoms,
            color="lightgray",
            label="other",
            width=0.7,
        )
        labels = [k["id"] for k in knobs]
        ax.set_xticks(range(len(knobs)), labels, fontsize=8)
        ax.set_ylim(0, 1.0)
        ax.set_title(cid, fontsize=10)
    axes[0][0].set_ylabel("episode share")
    axes[0][-1].legend(loc="upper right", fontsize=7)
    fig.suptitle("closing-door duel — outcomes per contender", fontsize=11)
    fig.tight_layout()
    fig.savefig(out_png, dpi=120)
    plt.close(fig)
    print(f"[INFO] saved {out_png}")
    return duel_cells


def trajectory_overlay(results: dict, out_png: str, seed: int, world="door") -> None:
    """Re-fly one shared seed per contender; overlay paths + the aperture
    at each crossing instant. Needs the sim + the contenders' artifacts."""
    from eval.episode import run_scenario_episode
    from scripts.research import ROOT, _policy_factory
    from sim.envs import make_env
    from skills.base import load_skill  # registers the duel's worlds

    load_skill("closing-door")
    env = make_env()
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    cmap = plt.get_cmap("tab10")
    meta = None
    for i, k in enumerate(results["knobs"]):
        art = k.get("artifacts", {})
        ref = art.get("policy") or art.get("policy_zip")
        path_ref = ref if str(ref).startswith("builtin:") else os.path.join(ROOT, ref)
        pol = _policy_factory(path_ref)(1.0)
        ep = run_scenario_episode(env, pol, seed, world, 1.0)
        meta = ep["scenario_meta"]
        p = ep["path"]
        tag = "threaded" if ep_metrics_threaded(ep) else "failed"
        ax.plot(p[:, 0], p[:, 1], color=cmap(i), label=f"{k['id']} ({tag})")
    env.close()
    if meta:
        from skills.closing_door.skill import PILLAR_R, door_half_at

        for frac, alpha in ((0.0, 0.15), (2.0, 0.45)):  # door at t=0 and t=2s
            half = door_half_at(meta, frac)
            for side in (-1, 1):
                ax.plot(
                    meta["x_gap"],
                    meta["yc"] + side * half,
                    "s",
                    color="red",
                    alpha=alpha,
                    markersize=7,
                )
        ax.axvline(meta["x_gap"], color="red", linestyle=":", alpha=0.3)
        del PILLAR_R
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_title(f"closing-door duel — same seed ({seed}), every contender")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out_png, dpi=120)
    plt.close(fig)
    print(f"[INFO] saved {out_png}")


def ep_metrics_threaded(ep: dict) -> bool:
    from skills.closing_door.skill import door_metrics

    return bool(door_metrics(ep).get("threaded"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp", default="experiments/closing_door")
    ap.add_argument("--trajectories", action="store_true")
    ap.add_argument("--seed", type=int, default=9800)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        import tempfile

        fake = {
            "knobs": [
                {
                    "id": "K0",
                    "cells": {
                        "door@1.0": {
                            "custom": {"threaded": 0.1, "pinched": 0.4, "froze": 0.4}
                        }
                    },
                },
                {
                    "id": "K4",
                    "cells": {
                        "door@1.0": {
                            "custom": {"threaded": 0.8, "pinched": 0.1, "froze": 0.0}
                        }
                    },
                },
            ]
        }
        out = os.path.join(tempfile.mkdtemp(), "duel_selftest.png")
        cells = outcome_bars(fake, out)
        assert cells == ["door@1.0"] and os.path.getsize(out) > 10_000
        print("DUEL-PLOTS OK: stacked outcome bars render from a results dict")
        return

    with open(os.path.join(args.exp, "results.json")) as f:
        results = json.load(f)
    outcome_bars(results, os.path.join(args.exp, "duel_outcomes.png"))
    if args.trajectories:
        trajectory_overlay(
            results, os.path.join(args.exp, "duel_trajectories.png"), args.seed
        )


if __name__ == "__main__":
    main()
    sys.exit(0)

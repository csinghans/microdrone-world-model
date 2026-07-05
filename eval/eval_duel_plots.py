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


OUTCOME_COLORS = {
    "threaded": "tab:green",
    "pinched": "tab:red",
    "froze": "tab:blue",
    "other": "lightgray",
}


def _episode_outcome(skill, ep: dict) -> tuple:
    """(outcome, t_cross|None) for one episode: outcome from the skill's
    own metrics when they speak the duel vocabulary, generic otherwise;
    t_cross from the fence-plane clock (None if the plane was never
    crossed — frozen or detoured episodes park in the no-cross band)."""
    m = skill.episode_metrics(ep) if skill.episode_metrics else {}
    if m.get("threaded"):
        outcome = "threaded"
    elif m.get("pinched") or ep["crashed"]:
        outcome = "pinched"
    elif m.get("froze"):
        outcome = "froze"
    else:
        outcome = "other"  # e.g. reached without threading: the detour
    t_cross = None
    x_gap = ep.get("scenario_meta", {}).get("x_gap")
    if x_gap is not None:
        from skills.moving_gap.skill import _crossing_yt

        cross = _crossing_yt(ep["path"], x_gap)
        t_cross = cross[1] if cross else None
    return outcome, t_cross


def render_timeline(records: dict, cell_id: str, out_png: str) -> None:
    """Two panels from per-episode records {knob_id: [(outcome, t|None)]}:
    the outcome grid (which seeds kill whom) and the crossing-time strip
    (when each contender commits, coloured by how it ended)."""
    knobs = list(records)
    n_seeds = max(len(v) for v in records.values())
    fig, (ax_g, ax_t) = plt.subplots(
        2, 1, figsize=(1.5 + 0.22 * n_seeds, 2.2 + 0.55 * len(knobs)), sharex=False
    )
    idx = {k: i for i, k in enumerate(OUTCOME_COLORS)}
    grid = np.full((len(knobs), n_seeds), idx["other"], dtype=float)
    for r, kid in enumerate(knobs):
        for c, (outcome, _t) in enumerate(records[kid]):
            grid[r, c] = idx[outcome]
    cmap = plt.matplotlib.colors.ListedColormap(list(OUTCOME_COLORS.values()))
    ax_g.imshow(grid, cmap=cmap, vmin=0, vmax=len(OUTCOME_COLORS) - 1, aspect="auto")
    ax_g.set_yticks(range(len(knobs)), knobs, fontsize=8)
    ax_g.set_xlabel("seed index", fontsize=8)
    ax_g.set_title(f"{cell_id} — outcome per seed", fontsize=10)

    times = [t for v in records.values() for _o, t in v if t is not None]
    park = (max(times) if times else 1.0) * 1.12  # the no-cross band
    for r, kid in enumerate(knobs):
        for outcome, t in records[kid]:
            x = t if t is not None else park
            marker = "o" if t is not None else "x"
            ax_t.plot(
                x,
                r + (np.random.default_rng(0).uniform() - 0.5) * 0.0,
                marker,
                color=OUTCOME_COLORS[outcome],
                alpha=0.65,
                markersize=5,
            )
    ax_t.axvline(park, color="gray", linestyle=":", linewidth=1, alpha=0.5)
    ax_t.text(park, -0.45, " no cross", fontsize=7, color="gray")
    ax_t.set_yticks(range(len(knobs)), knobs, fontsize=8)
    ax_t.set_ylim(len(knobs) - 0.5, -0.5)
    ax_t.set_xlabel("fence-plane crossing time (s)", fontsize=8)
    ax_t.set_title("when each contender commits", fontsize=10)
    handles = [
        plt.Line2D([], [], marker="o", ls="", color=c, label=k)
        for k, c in OUTCOME_COLORS.items()
    ]
    ax_t.legend(handles=handles, fontsize=6, loc="center left")
    fig.tight_layout()
    fig.savefig(out_png, dpi=120)
    plt.close(fig)
    print(f"[INFO] saved {out_png}")


def duel_timelines(results: dict, exp_dir: str) -> None:
    """Re-fly every duel cell's seeds for every contender and render the
    per-seed timelines. The skill (and its worlds) come from results.json."""
    from eval.episode import run_scenario_episode
    from scripts.research import ROOT, _policy_factory
    from sim.envs import make_env
    from skills.base import load_skill

    skill = load_skill(results["skill"])
    duel_cells = [c for c in skill.cells if c.role == "target" and c.world is not None]
    env = make_env()
    for cell in duel_cells:
        records: dict = {}
        for k in results["knobs"]:
            art = k.get("artifacts", {})
            ref = art.get("policy") or art.get("policy_zip")
            path_ref = (
                ref if str(ref).startswith("builtin:") else os.path.join(ROOT, ref)
            )
            factory = _policy_factory(path_ref)
            eps = []
            for i in range(cell.n_seeds):
                ep = run_scenario_episode(
                    env, factory(cell.speed), cell.seed0 + i, cell.world, cell.speed
                )
                eps.append(_episode_outcome(skill, ep))
            records[k["id"]] = eps
        safe = cell.id.replace("@", "_").replace(".", "")
        render_timeline(
            records, cell.id, os.path.join(exp_dir, f"duel_timeline_{safe}.png")
        )
    env.close()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp", default="experiments/closing_door")
    ap.add_argument("--trajectories", action="store_true")
    ap.add_argument("--timelines", action="store_true")
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
        tmp = tempfile.mkdtemp()
        out = os.path.join(tmp, "duel_selftest.png")
        cells = outcome_bars(fake, out)
        assert cells == ["door@1.0"] and os.path.getsize(out) > 10_000
        # the timeline renderer is pure given records — assert it too
        recs = {
            "K0": [("pinched", 2.1), ("froze", None), ("threaded", 2.6)],
            "K4": [("threaded", 3.1), ("threaded", 3.4), ("other", None)],
        }
        out2 = os.path.join(tmp, "duel_timeline_selftest.png")
        render_timeline(recs, "door@1.0", out2)
        assert os.path.getsize(out2) > 10_000
        print(
            "DUEL-PLOTS OK: stacked outcome bars + per-seed timeline render "
            "from plain records"
        )
        return

    with open(os.path.join(args.exp, "results.json")) as f:
        results = json.load(f)
    outcome_bars(results, os.path.join(args.exp, "duel_outcomes.png"))
    if args.trajectories:
        trajectory_overlay(
            results, os.path.join(args.exp, "duel_trajectories.png"), args.seed
        )
    if args.timelines:
        duel_timelines(results, args.exp)


if __name__ == "__main__":
    main()
    sys.exit(0)

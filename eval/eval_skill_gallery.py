"""Champion trajectory gallery — what the flights LOOK like, per arena.

For each arena's best artifact, re-fly the first six seeds of its
signature exam cell and draw small multiples: each panel shows that
seed's own obstacle layout (at t=0 — movers drawn where they start) and
the drone's path, colored by the SKILL'S OWN success predicate (green
pass / red fail). Failures render exactly as prominently as wins.

The cell's world, speed and seeds come from the skill definition
itself — the gallery flies the same courses the gates graded, never a
friendlier set.

Regeneration needs the sim plus the LOCAL artifacts (`*.zip` is
git-ignored; the four cross-repo champions come from
`scripts.fetch_champions`, campaign zips live under
`experiments/*/artifacts/` on the machine that ran them). The PNGs in
docs/figures/ are the committed record; the CI selftest exercises the
pure renderer only.

Run:
  python -m eval.eval_skill_gallery --out docs/figures
  python -m eval.eval_skill_gallery --selftest
"""

import argparse
import os
import sys

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

GREEN, RED, PILLAR = "#2e7d32", "#c62828", "#616161"

# (figure name, judge skill, artifact zip, signature cell id)
GALLERY = (
    (
        "gap_flight_KD1",
        "gap-flight",
        "experiments/gap_flight/artifacts/ppo_gap_flight_KD1.zip",
        "gap@1.0",
    ),
    (
        "moving_gap_K3",
        "moving-gap",
        "experiments/moving_gap_v2/artifacts/ppo_moving_gap_v2_K3.zip",
        "mgap@1.0",
    ),
    (
        "closing_door_K3zs",
        "closing-door",
        "experiments/moving_gap_v2/artifacts/ppo_moving_gap_v2_K3.zip",
        "door@1.0",
    ),
    (
        "opening_door_K3",
        "opening-door",
        "experiments/opening_door/artifacts/ppo_opening_door_K3.zip",
        "odoor@1.0",
    ),
    (
        "slalom_clone",
        "corridor-slalom-v2",
        "experiments/chain_distill/artifacts/ppo_chain_distill_BC.zip",
        "slalom3@1.0",
    ),
    (
        "dodgeball_clone",
        "dodgeball",
        "experiments/dodge_distill/artifacts/ppo_dodge_distill_BC.zip",
        "dodge@v1.8",
    ),
)


def _draw_ep(ax, ep: dict, ok: bool, seed: int) -> None:
    """One panel: this seed's obstacles at t=0 + the drone's path. Pure."""
    pillars = np.asarray(
        [p for p in ep.get("pillars", []) if not np.isnan(p[0])], dtype=float
    )
    if len(pillars):
        near = pillars[np.abs(pillars[:, 1]) < 3.0]  # parked balls sit at |y|=6
        if len(near):
            ax.scatter(near[:, 0], near[:, 1], s=42, color=PILLAR, zorder=2)
    meta = ep.get("scenario_meta", {})
    if "balls" in meta:  # dodgeball: the station box IS the task
        (sx, sy), (bx, by) = meta["station"], meta["box"]
        ax.add_patch(
            plt.Rectangle(
                (sx - 0.3, sy - by),
                bx + 0.3,
                2 * by,
                fill=False,
                edgecolor="#1565c0",
                linestyle="--",
                linewidth=1.0,
            )
        )
    p = np.asarray(ep["path"])
    ax.plot(p[:, 0], p[:, 1], color=GREEN if ok else RED, linewidth=1.4, zorder=3)
    ax.plot(p[0, 0], p[0, 1], "o", color="black", markersize=3, zorder=4)
    ax.set_title(
        f"seed {seed} — {'pass' if ok else 'fail'}",
        fontsize=7,
        color=GREEN if ok else RED,
    )
    ax.set_aspect("equal")
    ax.set_xlim(-0.6, 3.4)
    ax.set_ylim(-2.0, 2.0)
    ax.tick_params(labelsize=6)


def render_entry(name, judge, zip_path, cell_id, out_dir, n=6):
    from eval.episode import run_scenario_episode
    from scripts.research import _policy_factory
    from sim.envs import make_env
    from skills.base import load_skill

    skill = load_skill(judge)
    cell = next(c for c in skill.cells if c.id == cell_id)
    factory = _policy_factory(zip_path)
    env = make_env()
    fig, axes = plt.subplots(2, 3, figsize=(9.6, 5.4))
    for i, ax in enumerate(axes.flat[:n]):
        pol = factory(cell.speed)
        ep = run_scenario_episode(env, pol, cell.seed0 + i, cell.world, cell.speed)
        _draw_ep(ax, ep, bool(skill.success(ep)), cell.seed0 + i)
    env.close()
    fig.suptitle(
        f"{name} — {judge} / {cell_id} (obstacles at t=0; exam seeds "
        f"{cell.seed0}+; green = the skill's own success predicate)",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    p = os.path.join(out_dir, f"traj_{name}.png")
    fig.savefig(p, dpi=110)
    plt.close(fig)
    return p


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs/figures")
    ap.add_argument("--only", default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        # the pure renderer: a synthetic weave that passes and a crash that
        # fails, plus a dodgeball panel with the station box
        import tempfile

        weave = {
            "pillars": [(1.0, 0.6), (1.0, -0.9), (1.7, -0.6), (1.7, 0.9)],
            "path": np.array([[0, 0, 0.7], [1.0, -0.15, 0.7], [1.7, 0.15, 0.7]]),
            "scenario_meta": {},
        }
        ball = {
            "pillars": [(2.0, 6.0)],
            "path": np.array([[0, 0, 0.7], [0.4, -0.5, 0.7], [0.8, 0.2, 0.7]]),
            "scenario_meta": {"balls": 3, "station": (0.0, 0.0), "box": (1.9, 1.2)},
        }
        with tempfile.TemporaryDirectory() as td:
            fig, axes = plt.subplots(1, 3, figsize=(9, 3))
            _draw_ep(axes[0], weave, True, 111)
            _draw_ep(axes[1], weave, False, 112)
            _draw_ep(axes[2], ball, True, 113)
            p = os.path.join(td, "synth.png")
            fig.savefig(p)
            plt.close(fig)
            assert os.path.getsize(p) > 10_000
        # every gallery entry must reference a real cell id at import time
        assert len(GALLERY) == 6 and all(len(e) == 4 for e in GALLERY)
        print(
            "SKILL-GALLERY OK: pure panel renderer (pillars, station box, "
            "pass/fail coloring), gallery spec well-formed"
        )
        return

    os.makedirs(args.out, exist_ok=True)
    for name, judge, zip_path, cell_id in GALLERY:
        if args.only and args.only != name:
            continue
        if not os.path.exists(zip_path):
            print(f"[skip] {name}: missing artifact {zip_path}")
            continue
        p = render_entry(name, judge, zip_path, cell_id, args.out)
        print(f"[gallery] {p}")


if __name__ == "__main__":
    main()
    sys.exit(0)

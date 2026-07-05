"""The two-policy demo: one course, reactive vs the latent MPC, one plot.

Run:
  python -m scripts.demo             # saves output/wm_closed_loop.png
  python -m scripts.demo --gui       # watch it fly
  python -m scripts.demo --selftest  # asserts the anticipation story
Needs output/world_model.pth (auto-trains a tiny one if missing).
"""

import argparse
import os
import sys

from eval.eval_closed_loop import load_or_train, run_episode
from planner.latent_mpc import ReactivePolicy, WMPolicy
from sim.envs import CTRL_HZ, make_env
from sim.scenarios import COLLISION_R, DANGER_R, GOAL_X

SCENARIO_SEED = 11  # the demo course (the scoreboards sweep many seeds)
OUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "output",
    "wm_closed_loop.png",
)


def _save_plot(reactive: dict, wm: dict) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6, 4))
    runs = ((reactive, "tab:orange", "reactive"), (wm, "tab:green", "wm (latent MPC)"))
    for run, color, name in runs:
        px = run["path"]
        ax.plot(px[:, 0], px[:, 1], "-", color=color, label=name)
        if run["trigger"] >= 0:
            ax.plot(*px[run["trigger"], :2], "o", color=color, markersize=6)
    ax.plot(0, 0, "ko", markersize=8, label="start")
    ax.axvline(GOAL_X, color="k", linestyle=":", linewidth=1)
    for q in wm["pillars"]:
        ax.add_patch(plt.Circle(q, COLLISION_R, color="red", alpha=0.6))
        ax.add_patch(plt.Circle(q, DANGER_R, color="red", alpha=0.10))
    ax.set_aspect("equal")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_title("Closed loop from vision: latent-MPC world model vs reactive")
    ax.legend(loc="best", fontsize=8)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUT, dpi=110)
    print(f"[INFO] saved {OUT}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gui", action="store_true")
    ap.add_argument("--seed", type=int, default=SCENARIO_SEED)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    enc, pred, cheads, nhead, meta = load_or_train(device="cpu")
    env = make_env(gui=args.gui)
    reactive = run_episode(env, ReactivePolicy(enc, nhead), args.seed)
    wm = run_episode(env, WMPolicy(enc, pred, cheads, meta), args.seed)
    env.close()
    _save_plot(reactive, wm)

    lead = reactive["trigger"] - wm["trigger"]
    print(
        f"WM-CLOSED-LOOP OK: reactive min-clear={reactive['min_clear']:.2f} m "
        f"(trigger@{reactive['trigger']}), wm min-clear={wm['min_clear']:.2f} m "
        f"(trigger@{wm['trigger']}), lead=+{lead} steps "
        f"(~{lead * 1000 / CTRL_HZ:.0f} ms earlier), crashes reactive/wm = "
        f"{int(reactive['crashed'])}/{int(wm['crashed'])}, goal steps = "
        f"{reactive['steps']}/{wm['steps']} — danger signal from camera alone "
        f"(no privileged look-ahead in control)"
    )
    if args.selftest:
        if meta.get("autotrained_tiny"):
            # artifact-less runner: load_or_train built a 12-rollout stand-in,
            # and the anticipation story is a claim about a *real* checkpoint
            # (judged at the gates). A smoke can only assert the wiring.
            for ep in (reactive, wm):
                assert {"trigger", "min_clear", "crashed", "reached"} <= set(ep)
            assert isinstance(lead, int), "lead not computed"
            print(
                "DEMO OK (wiring only): auto-trained tiny checkpoint — the "
                "anticipation-story asserts need a real model"
            )
            return
        assert wm["trigger"] >= 0, "wm never deviated from cruise"
        assert reactive["trigger"] >= 0, "reactive never triggered"
        assert lead > 0, "wm did not trigger earlier than reactive"
        assert wm["min_clear"] > reactive["min_clear"], "no clearance gain"
        assert not wm["crashed"], "wm crashed"
        assert wm["reached"], "wm never reached the goal line"


if __name__ == "__main__":
    main()
    sys.exit(0)

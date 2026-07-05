"""The two-policy demo: one course, reactive vs the anticipating stack.

The anticipating seat belongs to the *measured champion*: the learned
policy riding the world model's outputs (v0.2 G3 settled this — the hand
latent-MPC's fixed margins broke on every model recalibration, three
strikes, and the demo must tell the repo's current true story). When the
champion zip is absent (fresh checkout, CI), the hand MPC flies the seat
so the demo stays self-contained — labelled as such, wiring-scope
asserts only.

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

CHAMPION_ZIP = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "output",
    "ppo_wm_policy_edge_hard_xp.zip",
)

SCENARIO_SEED = 11  # the demo course (the scoreboards sweep many seeds)
OUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "output",
    "wm_closed_loop.png",
)


def _save_plot(reactive: dict, wm: dict, wm_name: str = "wm (latent MPC)") -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6, 4))
    runs = ((reactive, "tab:orange", "reactive"), (wm, "tab:green", wm_name))
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
    champion = os.path.exists(CHAMPION_ZIP) and not meta.get("autotrained_tiny")
    if champion:
        from planner.learned_policy import LearnedPolicy, load_policy

        anticipator = LearnedPolicy(
            load_policy(CHAMPION_ZIP), enc, pred, cheads, meta, speed=1.0
        )
    else:  # self-contained fallback: the hand MPC flies, wiring-scope only
        anticipator = WMPolicy(enc, pred, cheads, meta)
    env = make_env(gui=args.gui)
    reactive = run_episode(env, ReactivePolicy(enc, nhead), args.seed)
    wm = run_episode(env, anticipator, args.seed)
    env.close()
    _save_plot(
        reactive,
        wm,
        "champion (learned policy)" if champion else "wm (latent MPC, fallback)",
    )

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
        if not champion:
            # artifact-less runner: a tiny stand-in model and/or no champion
            # zip. The anticipation story is a claim about the *measured
            # champion stack* (judged at the gates); a smoke without one can
            # only assert the wiring.
            for ep in (reactive, wm):
                assert {"trigger", "min_clear", "crashed", "reached"} <= set(ep)
            assert isinstance(lead, int), "lead not computed"
            print(
                "DEMO OK (wiring only): no champion stack on this runner — "
                "the anticipation-story asserts need the measured champion"
            )
            return
        assert wm["trigger"] >= 0, "champion never deviated from cruise"
        assert not wm["crashed"], "champion crashed the demo course"
        assert wm["reached"], "champion never reached the goal line"
        assert wm["min_clear"] > COLLISION_R + 0.1, "champion shaved the pillar"


if __name__ == "__main__":
    main()
    sys.exit(0)

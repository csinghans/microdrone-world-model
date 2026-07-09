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
  python -m scripts.demo --gif       # also writes docs/media/demo_single_course.gif
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
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output", "wm_closed_loop.png")
GIF_OUT = os.path.join(ROOT, "docs", "media", "demo_single_course.gif")


def _record_course(env, policy, seed: int, speed: float = 1.0) -> list:
    """Fly the demo course once under `policy`, capturing a top-down god
    view per decision — the frames for the single-course demo GIF. Mirrors
    eval_closed_loop.run_episode's spawn so the GIF is the SAME course the
    scoreboard flies (reused god-view + writer from eval_integration)."""
    import numpy as np

    from eval.eval_integration import _god_frame
    from planner.action_set import ACTION_VECS, FORWARD
    from planner.latent_mpc import DECIDE_EVERY
    from sim.envs import VelCommander, grab_frame, make_ctrl
    from sim.scenarios import GOAL_X, TMAX, spawn_pillars

    rng = np.random.default_rng(seed)
    obs, _ = env.reset(seed=int(seed))
    cmd = VelCommander(make_ctrl(), env.CTRL_TIMESTEP)
    cmd.reset(obs[0][0:3])
    pillars = spawn_pillars(env, rng, in_path=True)
    policy.begin(pillars)
    vecs = float(speed) * ACTION_VECS
    state, a = obs[0], FORWARD
    frames = []
    for t in range(TMAX):
        if t % DECIDE_EVERY == 0:
            a = policy.decide(grab_frame(env), state)
            frames.append(_god_frame(env, GOAL_X))
        obs, *_ = env.step(cmd.rpm(state, vecs[a]).reshape(1, 4))
        state = obs[0]
        if state[0] >= GOAL_X:
            break
    return frames


def _save_gif(env, policy, seed: int) -> None:
    from eval.eval_integration import _gif

    frames = _record_course(env, policy, seed)
    os.makedirs(os.path.dirname(GIF_OUT), exist_ok=True)
    _gif(frames, GIF_OUT, scale=1)
    print(f"[INFO] saved {GIF_OUT} ({len(frames)} frames)")


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
    ap.add_argument("--gif", action="store_true", help="write the single-course GIF")
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
    if args.gif:  # a top-down god view of the anticipating seat on this course
        _save_gif(env, anticipator, args.seed)
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

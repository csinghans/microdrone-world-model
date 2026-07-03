"""v0.2 baseline: how badly does the static-world stack fail in harder worlds?

Measured BEFORE any model change, on two new stress tests:

  * **dense** — 5-7 pillars, two forced into the corridor, tight side
    clutter both sides. Every evasion steers toward somewhere the camera has
    not looked recently: this is the FOV/memory limit, turned up.
  * **moving** — one pillar crosses the corridor laterally while static
    clutter watches. The world model trained on a static world; its danger
    heads assume pillars stay put. This measures what that assumption costs.

Pre-registered expectations (written before the first run): all three
policies degrade on dense (the memoryless MPC worst); the moving crosser
hurts anticipation more than reaction whenever it invalidates the "static
future" the predictor imagines. Whatever the numbers say, they are the
baseline the v0.2 model work (model-side memory, motion-aware labels) must
beat — no asserts on outcomes here, only on harness sanity.

Honest protocol notes: the reactive baseline keeps its privileged evasion
direction and (on moving courses) reads *current* pillar positions — the
same generous-opponent convention as everywhere else. The learned policy is
the stacked PPO from this repo's draw-2 training, flown as-is (zero-shot on
both worlds).

Run:
  python -m eval.eval_hard_worlds --seeds 30
  python -m eval.eval_hard_worlds --selftest   # 3 seeds, harness asserts
Needs output/world_model.pth (+ output/ppo_wm_policy.zip for the learned row).
"""

import argparse
import os
import sys

import numpy as np

from eval.eval_closed_loop import load_or_train
from planner.action_set import ACTION_VECS, FORWARD
from planner.latent_mpc import DECIDE_EVERY, ReactivePolicy, WMPolicy
from sim.envs import VelCommander, grab_frame, make_ctrl, make_env
from sim.scenarios import (
    COLLISION_R,
    GOAL_X,
    TMAX,
    MovingCrosser,
    nearest_planar,
    spawn_dense_pillars,
)

SPEEDS = (1.0, 1.5)  # x 0.8 m/s -> 0.8 and 1.2 m/s cruise


def run_hard_episode(env, policy, seed: int, world: str, speed: float) -> dict:
    """One START -> GOAL_X flight through a `dense` or `moving` course. Same
    contract as `eval_closed_loop.run_episode`, plus the scenario hooks: the
    moving world advances every control step, scoring always uses the
    *current* geometry, and a policy that owns privileged pillar state
    (the reactive baseline) gets it refreshed each decision."""
    rng = np.random.default_rng(seed)
    obs, _ = env.reset(seed=int(seed))
    cmd = VelCommander(make_ctrl(), env.CTRL_TIMESTEP)
    cmd.reset(obs[0][0:3])
    mover = None
    if world == "moving":
        mover = MovingCrosser(env, rng, cruise=0.8 * speed)
        pillars = mover.positions()
    else:
        pillars = spawn_dense_pillars(env, rng)
    policy.begin(pillars)
    vecs = float(speed) * ACTION_VECS

    state, a_id, trigger = obs[0], FORWARD, -1
    min_clear, steps = 9.0, 0
    for t in range(TMAX):
        cur = mover.positions() if mover else pillars
        if t % DECIDE_EVERY == 0:
            if hasattr(policy, "pillars"):  # privileged baseline: live state
                policy.pillars = [np.array(q) for q in cur]
            a_id = policy.decide(grab_frame(env), state)
            if a_id != FORWARD and trigger < 0:
                trigger = t
        obs, _, _, _, _ = env.step(cmd.rpm(state, vecs[a_id]).reshape(1, 4))
        state = obs[0]
        if mover:
            mover.step()
        steps = t + 1
        min_clear = min(min_clear, nearest_planar(state[0:2], cur))
        if state[0] >= GOAL_X:
            break
    return {
        "min_clear": min_clear,
        "trigger": trigger,
        "crashed": min_clear < COLLISION_R,
        "steps": steps,
        "reached": bool(state[0] >= GOAL_X),
    }


def _policies(enc, pred, cheads, nhead, meta):
    mk = {
        "reactive": lambda s: ReactivePolicy(enc, nhead),
        "wm": lambda s: WMPolicy(enc, pred, cheads, meta, speed=s),
    }
    from planner.learned_policy import LearnedPolicy, load_policy, zip_path

    for name, hard, xp, edge in (
        ("learned", False, False, False),
        ("learned-hard", True, False, False),
        ("learned-hard-xp", True, True, False),
        ("learned-hard-xp-eb", True, True, True),
    ):
        path = zip_path(hard=hard, xp=xp, edge=edge)
        if os.path.exists(path):
            model = load_policy(path)
            mk[name] = lambda s, m=model: LearnedPolicy(
                m, enc, pred, cheads, meta, speed=s
            )
    return mk


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--seed0", type=int, default=7000)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    n = 3 if args.selftest else args.seeds
    speeds = (1.0,) if args.selftest else SPEEDS

    enc, pred, cheads, nhead, meta = load_or_train(device="cpu")
    mk = _policies(enc, pred, cheads, nhead, meta)
    env = make_env()
    lines = []
    for world in ("dense", "moving"):
        for s in speeds:
            rep = []
            for name, factory in mk.items():
                crash, clear = 0, []
                for i in range(n):
                    r = run_hard_episode(env, factory(s), args.seed0 + i, world, s)
                    assert np.isfinite(r["min_clear"]), "non-finite clearance"
                    crash += int(r["crashed"])
                    clear.append(r["min_clear"])
                rep.append(f"{name} {crash / n:.0%} ({np.mean(clear):.2f} m)")
            line = f"{world}@{s * 0.8:.1f} m/s: " + " / ".join(rep)
            lines.append(line)
            print("  " + line)
    env.close()
    print(
        f"HARD-WORLDS OK: {n} seeds/world/speed, crash (mean clearance) — "
        + "; ".join(lines)
        + " — the hard-worlds scoreboard"
    )


if __name__ == "__main__":
    main()
    sys.exit(0)

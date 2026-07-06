"""Oracle distillation: behavior-clone a scripted oracle onto the vision obs.

The chain-distill campaign's machinery (P2 on the queue). A privileged
oracle (OracleWeave, 97 % on the fixed slalom with the SAME action set)
flies collection episodes while an `ObsBuilder` computes, in parallel,
exactly what a vision policy would have seen at each decision. The
(obs, oracle_action) pairs then supervise the action head of a standard
SB3 PPO policy, which is saved as a normal zip — `load_policy`, the
research runner and every exam fly it unchanged.

Two honest properties, by construction:

  * **Alignment is exam-exact.** The obs is built with the same
    push-then-decide ordering as `WMPolicyEnv.step` and
    `LearnedPolicy.decide` (frame -> push -> stacked obs -> action), so
    the student is trained on precisely the observation stream it will
    be examined on. x_progress matches the champion convention.
  * **BC validation accuracy is an obs-sufficiency meter.** The teacher
    decides from privileged geometry; the student sees only collision
    probabilities. If held-out accuracy cannot clear the pre-registered
    floor, the observation provably cannot represent the teacher's
    decision function — a finding, not a failure to converge.

Collection seeds live in their own series (default 40000+): the exam's
courses (seed0 22000) stay unseen by training.

Run:
  python -m scripts.distill --collect 400 --out <zip>       # BC
  python -m scripts.distill --finetune <bc_zip> --steps 450000 --out <zip>
  python -m scripts.distill --selftest
"""

import argparse
import sys

import numpy as np

SEED0 = 40000  # collection series — disjoint from every exam seed


def collect(n_episodes: int, world: str, speed: float, seed0: int = SEED0):
    """Fly the oracle; record (stacked_obs, oracle_menu_action) per decision."""
    import torch  # noqa: F401  (torch must exist before SB3 policies)

    from eval.episode import run_scenario_episode  # noqa: F401 (doc: same loop)
    from eval.eval_arena_ceiling import OracleWeave
    from eval.eval_closed_loop import load_or_train
    from planner.action_set import ACTION_VECS
    from planner.latent_mpc import DECIDE_EVERY
    from planner.learned_policy import ObsBuilder
    from sim.envs import VelCommander, grab_frame, make_ctrl, make_env
    from sim.scenario_registry import get as get_scenario
    from sim.scenarios import GOAL_X, TMAX

    env = make_env()
    enc, pred, cheads, _nhead, meta = load_or_train()
    X, Y, reached = [], [], 0
    spec = get_scenario(world)
    for i in range(n_episodes):
        seed = seed0 + i
        obs0, _ = env.reset(seed=seed)
        cmd = VelCommander(make_ctrl(), env.CTRL_TIMESTEP)
        state = obs0[0]
        cmd.reset(state[0:3])
        scenario = spec.spawn(env, np.random.default_rng(seed), speed=speed)
        oracle = OracleWeave()
        oracle.begin(scenario.positions())
        ob = ObsBuilder(enc, pred, cheads, meta, speed, x_progress=True)
        prev_menu = 0
        a_global = ob.ids[prev_menu]
        for t in range(TMAX):
            if t % DECIDE_EVERY == 0:
                # push-then-decide: the exact LearnedPolicy.decide ordering
                vec = ob.push(
                    grab_frame(env), float(state[1]), prev_menu, x=float(state[0])
                )
                a_global = oracle.decide(None, state)
                prev_menu = ob.ids.index(a_global)
                X.append(vec)
                Y.append(prev_menu)
            rpm = cmd.rpm(state, float(speed) * ACTION_VECS[a_global])
            obs, _, _, _, _ = env.step(rpm.reshape(1, 4))
            state = obs[0]
            scenario.step()
            if state[0] >= GOAL_X:
                reached += 1
                break
    env.close()
    print(
        f"[collect] {len(X)} decisions from {n_episodes} episodes on {world} "
        f"(oracle reached {reached}/{n_episodes})"
    )
    return np.asarray(X, dtype=np.float32), np.asarray(Y, dtype=np.int64)


def bc_train(X, Y, out: str, epochs: int = 40, lr: float = 3e-4, val_frac=0.1):
    """Supervise a fresh PPO policy's action head; save a runner-ready zip.
    Returns held-out top-1 accuracy — the obs-sufficiency meter."""
    import torch
    from stable_baselines3 import PPO
    from stable_baselines3.common.env_util import make_vec_env

    from planner.learned_policy import WMPolicyEnv

    venv = make_vec_env(
        lambda: WMPolicyEnv(worlds=("slalom3_fixed",), x_progress=True), n_envs=1
    )
    model = PPO("MlpPolicy", venv, seed=0, verbose=0)
    rng = np.random.default_rng(0)
    idx = rng.permutation(len(X))
    n_val = max(1, int(len(X) * val_frac))
    vi, ti = idx[:n_val], idx[n_val:]
    dev = model.policy.device
    Xt = torch.as_tensor(X, device=dev)
    Yt = torch.as_tensor(Y, device=dev)
    opt = torch.optim.Adam(model.policy.parameters(), lr=lr)
    for ep in range(epochs):
        model.policy.train()
        for k in range(0, len(ti), 256):
            b = ti[k : k + 256]
            dist = model.policy.get_distribution(Xt[b])
            loss = -dist.log_prob(Yt[b]).mean()
            opt.zero_grad()
            loss.backward()
            opt.step()
    model.policy.eval()
    with torch.no_grad():

        def _top1(ix):
            p = model.policy.get_distribution(Xt[ix]).distribution.probs
            return float((p.argmax(1) == Yt[ix]).float().mean())

        acc, train_acc = _top1(vi), _top1(ti)
    model.save(out)
    venv.close()
    print(
        f"[bc] saved {out}  val_top1={acc:.3f}  train_top1={train_acc:.3f}  "
        f"(n={len(X)}, val={n_val})"
    )
    return acc, train_acc


def finetune(bc_zip: str, steps: int, out: str):
    """PPO fine-tune from the BC init on the same pure slalom diet."""
    from stable_baselines3 import PPO
    from stable_baselines3.common.env_util import make_vec_env

    from planner.learned_policy import WMPolicyEnv

    venv = make_vec_env(
        lambda: WMPolicyEnv(worlds=("slalom3_fixed",), x_progress=True), n_envs=1
    )
    model = PPO.load(bc_zip, env=venv)
    model.learn(total_timesteps=steps)
    model.save(out)
    venv.close()
    print(f"[finetune] saved {out} after {steps} steps on the BC init")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--collect", type=int, default=0)
    ap.add_argument("--world", default="slalom3_fixed")
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--seed0", type=int, default=SEED0)
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--finetune", default=None)
    ap.add_argument("--steps", type=int, default=450_000)
    ap.add_argument("--out", default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        # end-to-end wiring on a shoestring: 3 oracle episodes, overfit BC,
        # zip round-trips through load_policy into a flyable LearnedPolicy
        from skills.base import load_skill

        load_skill("corridor-slalom-v2")  # registers slalom3_fixed
        X, Y = collect(3, "slalom3_fixed", 1.0, seed0=90000)
        assert len(X) >= 60 and set(np.unique(Y)) <= set(range(5))
        assert X.dtype == np.float32 and X.ndim == 2
        out = "output/ppo_distill_selftest.zip"
        # 146 train samples < one 256-batch => one gradient step per epoch;
        # overfitting the tiny set needs the epoch count to BE the step count
        _val, train_acc = bc_train(X, Y, out, epochs=400, val_frac=0.2)
        # the wiring assert is TRAIN overfit (does the optimizer move the
        # policy at all?); val floors are a full-scale manipulation check,
        # not a 36-sample coin flip
        assert train_acc >= 0.8, f"tiny-set BC must overfit train, got {train_acc}"
        from eval.eval_closed_loop import load_or_train
        from planner.learned_policy import LearnedPolicy, load_policy

        enc, pred, cheads, _n, meta = load_or_train()
        pol = LearnedPolicy(load_policy(out), enc, pred, cheads, meta, speed=1.0)
        a = pol.decide(np.zeros((48, 64, 3), dtype=np.uint8), np.zeros(12))
        assert 0 <= int(a) < len(meta["action_names"])
        print(
            "DISTILL OK: oracle collection aligned push-then-decide, BC fits "
            "and saves a runner-ready zip, LearnedPolicy flies it"
        )
        return

    if args.finetune:
        finetune(args.finetune, args.steps, args.out or "output/ppo_distill_ft.zip")
        return
    if args.collect:
        from skills.base import load_skill

        load_skill("corridor-slalom-v2")
        X, Y = collect(args.collect, args.world, args.speed, seed0=args.seed0)
        acc, _ = bc_train(X, Y, args.out or "output/ppo_distill_bc.zip", args.epochs)
        print(f"[distill] manipulation check: val_top1={acc:.3f} (floor 0.80)")


if __name__ == "__main__":
    main()
    sys.exit(0)

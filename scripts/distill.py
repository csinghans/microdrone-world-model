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


class OracleTrack:
    """Privileged mover-tracking teacher: the moving-gap twin of
    OracleWeave. Reads the fence's CURRENT pillar positions (live
    `.pillars` refresh from the collection loop), infers the gap as the
    widest y-spacing NOW, and bang-bang steers to its centre. It can
    only lose to dynamics — a teacher, never a contender."""

    def __init__(self):
        self.pillars: list = []  # live-refreshed each decision

    def begin(self, pillars) -> None:
        self.pillars = [np.array(q, dtype=float) for q in pillars]

    def decide(self, frame, state) -> int:
        from eval.eval_arena_ceiling import DEADBAND, VEER_L, VEER_R
        from planner.action_set import FORWARD

        del frame
        x, y = float(state[0]), float(state[1])
        ahead = sorted(float(p[1]) for p in self.pillars if float(p[0]) > x - 0.05)
        if len(ahead) < 2:
            return FORWARD  # fence passed: cruise out
        width, yc = max((b - a, (a + b) / 2.0) for a, b in zip(ahead, ahead[1:]))
        err = yc - y
        if abs(err) < DEADBAND:
            return FORWARD
        return VEER_L if err > 0 else VEER_R


def _teacher_weave(speed, stack):
    from eval.eval_arena_ceiling import OracleWeave

    del speed, stack
    return OracleWeave()


def _teacher_track(speed, stack):
    del speed, stack
    return OracleTrack()


def _teacher_champion(speed, stack):
    from planner.learned_policy import LearnedPolicy, load_policy

    enc, pred, cheads, meta = stack
    return LearnedPolicy(
        load_policy("output/ppo_wm_policy_edge_hard_xp.zip"),
        enc,
        pred,
        cheads,
        meta,
        speed=speed,
    )


def _teacher_mgap_champion(speed, stack):
    from planner.learned_policy import LearnedPolicy, load_policy

    enc, pred, cheads, meta = stack
    return LearnedPolicy(
        load_policy("experiments/moving_gap_v2/artifacts/ppo_moving_gap_v2_K3.zip"),
        enc,
        pred,
        cheads,
        meta,
        speed=speed,
    )


# The generalist recipe, frozen at pre-registration: per-world blocks of
# (world, episodes, drone speed, teacher, seed0). Seeds are disjoint from
# every exam series. The moving_gap teacher slot is decided by the
# pre-registered teacher probe (OracleTrack if >= 0.80 on its own world,
# else the measured mgap champion) — see the campaign journal.
GENERALIST = (
    ("slalom3_fixed", 300, 1.0, "weave", 41000),
    ("gap", 100, 1.0, "weave", 42000),
    ("moving_gap", 200, 1.0, "mgap", 43000),
    ("classic", 150, 1.0, "champion", 44000),
    ("solo", 120, 2.0, "champion", 45000),
)
# K1 remedy (distill-generalist reserve): the two failing single-fence
# worlds get their shares doubled; everything else byte-identical.
GENERALIST2 = GENERALIST + (
    ("gap", 100, 1.0, "weave", 46000),
    ("moving_gap", 200, 1.0, "mgap", 47000),
)
TEACHERS = {
    "weave": _teacher_weave,
    "track": _teacher_track,
    "champion": _teacher_champion,
    "mgap_champion": _teacher_mgap_champion,
}


def collect(
    n_episodes: int,
    world: str,
    speed: float,
    seed0: int = SEED0,
    teacher: str = "weave",
):
    """Fly a teacher; record (stacked_obs, teacher_menu_action) per decision.
    Teachers share the standard policy interface (begin/decide); anything
    with a `.pillars` attribute gets the live privileged refresh, exactly
    like eval/episode.py's runner."""
    import torch  # noqa: F401  (torch must exist before SB3 policies)

    from eval.eval_closed_loop import load_or_train
    from planner.action_set import ACTION_VECS
    from planner.latent_mpc import DECIDE_EVERY
    from planner.learned_policy import ObsBuilder
    from sim.envs import VelCommander, grab_frame, make_ctrl, make_env
    from sim.scenario_registry import get as get_scenario
    from sim.scenarios import GOAL_X, TMAX

    env = make_env()
    enc, pred, cheads, _nhead, meta = load_or_train()
    stack = (enc, pred, cheads, meta)
    X, Y, reached = [], [], 0
    spec = get_scenario(world)
    for i in range(n_episodes):
        seed = seed0 + i
        obs0, _ = env.reset(seed=seed)
        cmd = VelCommander(make_ctrl(), env.CTRL_TIMESTEP)
        state = obs0[0]
        cmd.reset(state[0:3])
        scenario = spec.spawn(env, np.random.default_rng(seed), speed=speed)
        pilot = TEACHERS[teacher](speed, stack)
        pilot.begin(scenario.positions())
        ob = ObsBuilder(enc, pred, cheads, meta, speed, x_progress=True)
        prev_menu = 0
        a_global = ob.ids[prev_menu]
        for t in range(TMAX):
            if t % DECIDE_EVERY == 0:
                frame = grab_frame(env)
                # push-then-decide: the exact LearnedPolicy.decide ordering
                vec = ob.push(frame, float(state[1]), prev_menu, x=float(state[0]))
                if hasattr(pilot, "pillars"):  # privileged live refresh
                    pilot.pillars = [np.array(q) for q in scenario.positions()]
                a_global = pilot.decide(frame, state)
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
        f"(teacher={teacher}, reached {reached}/{n_episodes})"
    )
    return np.asarray(X, dtype=np.float32), np.asarray(Y, dtype=np.int64)


def bc_train(X, Y, out: str, epochs: int = 40, lr: float = 3e-4, val_frac=0.1, W=None):
    """Supervise a fresh PPO policy's action head; save a runner-ready zip.
    Returns held-out top-1 accuracy — the obs-sufficiency meter. With `W`
    (per-sample world tags) the meter is also reported PER WORLD: a mixed
    pot must fit every teacher, not an average of them."""
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
        per_world = {}
        if W is not None:
            W = np.asarray(W)
            for w in sorted(set(W)):
                wi = vi[W[vi] == w]
                if len(wi):
                    per_world[w] = round(_top1(wi), 3)
    model.save(out)
    venv.close()
    print(
        f"[bc] saved {out}  val_top1={acc:.3f}  train_top1={train_acc:.3f}  "
        f"(n={len(X)}, val={n_val})" + (f"  per_world={per_world}" if per_world else "")
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
    ap.add_argument("--probe-track", type=int, default=0, metavar="N")
    ap.add_argument("--generalist", choices=("track", "mgap_champion"), default=None)
    ap.add_argument("--recipe2", action="store_true", help="K1 remedy recipe")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.probe_track:
        # teacher probe: is OracleTrack a fit teacher on its own world?
        from eval.episode import run_scenario_episode
        from sim.envs import make_env
        from skills.base import load_skill

        judge = load_skill("moving-gap")
        env = make_env()
        ok = 0
        for i in range(args.probe_track):
            ep = run_scenario_episode(env, OracleTrack(), 43900 + i, "moving_gap", 1.0)
            ok += int(judge.success(ep))
        env.close()
        print(f"[probe-track] OracleTrack on moving_gap@1.0: {ok}/{args.probe_track}")
        return

    if args.generalist:
        from skills.base import load_skill

        load_skill("corridor-slalom-v2")  # slalom3_fixed + gap + mgap + solo
        parts, tags = [], []
        recipe = GENERALIST2 if args.recipe2 else GENERALIST
        for world, n, speed, teacher, seed0 in recipe:
            t = args.generalist if teacher == "mgap" else teacher
            X, Y = collect(n, world, speed, seed0=seed0, teacher=t)
            parts.append((X, Y))
            tags += [world] * len(X)
        X = np.concatenate([p[0] for p in parts])
        Y = np.concatenate([p[1] for p in parts])
        out = args.out or "output/ppo_distill_generalist.zip"
        acc, _ = bc_train(X, Y, out, epochs=args.epochs, W=np.asarray(tags))
        print(f"[distill] generalist manipulation check: pooled val={acc:.3f}")
        return

    if args.selftest:
        # end-to-end wiring on a shoestring: 3 oracle episodes, overfit BC,
        # zip round-trips through load_policy into a flyable LearnedPolicy
        from skills.base import load_skill

        # OracleTrack steering, env-free: track the gap where it is NOW
        trk = OracleTrack()
        trk.begin([(2.0, -1.5), (2.0, -0.9), (2.0, 0.1), (2.0, 0.7)])
        s0 = np.array([0.5, 0.0, 1.0])
        from eval.eval_arena_ceiling import VEER_L, VEER_R
        from planner.action_set import FORWARD

        assert trk.decide(None, s0) == VEER_R, "gap centre -0.4: steer -y"
        trk.pillars = [np.array([2.0, y + 0.5]) for y in (-1.5, -0.9, 0.1, 0.7)]
        assert trk.decide(None, s0) == VEER_L, "fence moved +0.5: follow it"
        assert trk.decide(None, np.array([2.2, 0.0, 1.0])) == FORWARD, "past: cruise"

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

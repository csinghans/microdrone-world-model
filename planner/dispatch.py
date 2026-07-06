"""Skill dispatch: a tiny world-classifier chooses which specialist flies.

The dispatch campaign's machinery (`experiments/dispatch/journal.md`).
The catalog's measured lesson is that merging skills into one network
taxes or destroys them (RL confiscates, supervised pots pay boundary
tax, fine-tuning corrodes); dispatch keeps every specialist FROZEN and
adds only a small classifier head over the same observation stream:

    frame -> shared world model -> stacked obs (12 decisions)
                                     |-> classifier: which arena is this?
                                     '-> the chosen specialist's action

Hysteresis rule (frozen at pre-registration): majority class over the
last 5 decisions, switch only when a challenger wins >= 3/5; until any
majority exists the dispatcher flies the DODGEBALL specialist — the
hover-biased default, because the costs are asymmetric (waiting is
recoverable; advancing out of a station box is not — the measured
dodgeball-v2 identifiability failure, designed against).

Specialists never retrain here; their internal observation stacks stay
warm (every expert's decide() runs each step; only the dispatched
action is executed). Embedded note: this costs N encoder passes in
this prototype; a deployment shares the single encoder pass across
heads — the budget argument survives.

Run:
  python -m planner.dispatch --train            # phase 1: fit + meters
  python -m planner.dispatch --exam             # phase 2: the union exam
  python -m planner.dispatch --selftest
"""

import argparse
import json
import os
import sys
from collections import Counter, deque
from functools import lru_cache

import numpy as np

# v2 roster (the v1 six-class config and its meter verdict are frozen in
# the journal): the single-fence family was the measured confusable set,
# and one artifact already holds every fence bar — so it becomes ONE class.
CLASSES = ("classic", "fence", "slalom", "dodgeball")
DEFAULT = "dodgeball"  # hover-biased: waiting is recoverable
EXPERTS = {
    "classic": "output/ppo_wm_policy_edge_hard_xp.zip",
    "fence": "experiments/moving_gap_v2/artifacts/ppo_moving_gap_v2_K3.zip",
    "slalom": "experiments/chain_distill/artifacts/ppo_chain_distill_BC.zip",
    "dodgeball": "experiments/dodge_distill/artifacts/ppo_dodge_distill_BC.zip",
}
WORLD2CLASS = {
    "classic": "classic",
    "gap": "fence",
    "moving_gap": "fence",
    "door": "fence",
    "opening_door": "fence",
    "slalom3_fixed": "slalom",
    "dodgeball_v06": "dodgeball",
    "dodgeball_v10": "dodgeball",
    "dodgeball_v14": "dodgeball",
    "dodgeball_v18": "dodgeball",
}
# phase-2 union exam: every cell some catalog artifact holds solo (its own
# skill's frozen bar) + dodge@v1.0 as a measured diagnostic (no artifact
# holds it — the dodgeball crown is vacant there)
EXAM_CELLS = (
    ("gap-flight", "gap@1.0"),
    ("moving-gap", "mgap@1.0"),
    ("closing-door", "door@1.0"),
    ("opening-door", "odoor@1.0"),
    ("corridor-slalom-v2", "slalom3@1.0"),
    ("dodgeball", "dodge@v1.8"),
    ("dodgeball", "dodge@v1.0"),  # diagnostic: solo-vacant
    ("gap-flight", "guard:cluttered"),
    ("gap-flight", "guard:sweep@2.0"),
)
CLF_PATH = "experiments/dispatch/artifacts/dispatch_classifier_v5.pth"
SEED0 = 100000  # v5 collection series — virgin (v1-v4: 60-90k blocks)
Z_DIM = 64  # the encoder latent the classifier taps (asserted on first use)
# v4: the probe gait. A FIXED window of forced "slow" — not "probe until
# switched": the default class is a real class (dodgeball), so an
# until-switched rule would probe forever exactly when the default is
# CORRECT. Eight decisions = 0.67 s = 0.15-0.4 m at factor 1.0-2.0,
# priced harmless in every arena (box 1.9 m, balls at 4 s, doors 2 s+).
PROBE_K = 8


class Hysteresis:
    """Majority-of-5 with a hover-biased default; pure and selftestable."""

    def __init__(self, default: str = DEFAULT, window: int = 5, need: int = 3):
        self.buf: deque = deque(maxlen=window)
        self.current = default
        self.need = need

    def update(self, cls: str) -> str:
        self.buf.append(cls)
        top, n = Counter(self.buf).most_common(1)[0]
        if n >= self.need and top != self.current:
            self.current = top
        return self.current


def _mlp(n_in: int, n_out: int):
    import torch

    return torch.nn.Sequential(
        torch.nn.Linear(n_in, 64), torch.nn.ReLU(), torch.nn.Linear(64, n_out)
    )


@lru_cache(maxsize=None)
def _stack():
    from eval.eval_closed_loop import load_or_train

    enc, pred, cheads, _n, meta = load_or_train()
    return enc, pred, cheads, meta


@lru_cache(maxsize=None)
def _model(zip_path: str):
    from planner.learned_policy import load_policy

    return load_policy(zip_path)


def _expert(cls: str, speed: float):
    from planner.learned_policy import LearnedPolicy

    enc, pred, cheads, meta = _stack()
    return LearnedPolicy(_model(EXPERTS[cls]), enc, pred, cheads, meta, speed=speed)


class DispatchPolicy:
    """The standard policy interface; one classifier, six frozen experts."""

    def __init__(self, speed: float = 1.0, clf_path: str = CLF_PATH):
        import torch

        from planner.learned_policy import ObsBuilder

        enc, pred, cheads, meta = _stack()
        self.ob = ObsBuilder(enc, pred, cheads, meta, speed, x_progress=True)
        self._zbuf = deque(
            [np.zeros(Z_DIM, dtype=np.float32)] * self.ob.history,
            maxlen=self.ob.history,
        )
        self.clf = _mlp(Z_DIM * self.ob.history, len(CLASSES))
        self.clf.load_state_dict(torch.load(clf_path, weights_only=True))
        self.clf.eval()
        self.experts = {c: _expert(c, speed) for c in CLASSES}
        self.hyst = Hysteresis()
        self.trace: list = []
        self._prev_menu = 0

    def begin(self, pillars) -> None:
        for e in self.experts.values():
            e.begin(pillars)
        self.ob.reset()
        self._zbuf = deque(
            [np.zeros(Z_DIM, dtype=np.float32)] * self.ob.history,
            maxlen=self.ob.history,
        )
        self.hyst = Hysteresis()
        self.trace = []
        self._prev_menu = 0

    def decide(self, frame, state) -> int:
        import torch

        from planner.action_set import ACTION_NAMES

        self.ob.push(frame, float(state[1]), self._prev_menu, x=float(state[0]))
        self._zbuf.append(self.ob.last_z.astype(np.float32))
        vec = np.concatenate(self._zbuf)
        with torch.no_grad():
            logits = self.clf(torch.as_tensor(vec)[None])
        cls = self.hyst.update(CLASSES[int(logits.argmax())])
        self.trace.append(cls)
        # every expert sees every frame (their stacks stay warm); only the
        # dispatched one's action is executed
        actions = {c: e.decide(frame, state) for c, e in self.experts.items()}
        # the probe gait: a fixed window of forced slow advance — evidence
        # generation is an action; a hovering observer cannot identify a
        # static world (the v3 verdict)
        if len(self.trace) <= PROBE_K:
            a = ACTION_NAMES.index("slow")
        else:
            a = actions[cls]
        self._prev_menu = self.ob.ids.index(a)
        return a


def collect_streams(world: str, cls: str, n_eps: int, seed0: int, speed=1.0):
    """Fly the PROBE GAIT (forced "slow") for the first PROBE_K decisions,
    then the designated expert — the exact runtime distribution under v4
    dispatch: every world is first seen by a slowly advancing observer,
    whose parallax is the evidence a hovering one never generates.
    Returns per-episode obs streams."""
    from planner.action_set import ACTION_NAMES, ACTION_VECS
    from planner.latent_mpc import DECIDE_EVERY
    from planner.learned_policy import ObsBuilder
    from sim.envs import VelCommander, grab_frame, make_ctrl, make_env
    from sim.scenario_registry import get as get_scenario
    from sim.scenarios import GOAL_X, TMAX

    enc, pred, cheads, meta = _stack()
    env = make_env()
    spec = get_scenario(world)
    episodes = []
    for i in range(n_eps):
        seed = seed0 + i
        obs0, _ = env.reset(seed=seed)
        cmd = VelCommander(make_ctrl(), env.CTRL_TIMESTEP)
        state = obs0[0]
        cmd.reset(state[0:3])
        scenario = spec.spawn(env, np.random.default_rng(seed), speed=speed)
        pilot = _expert(cls, speed)
        pilot.begin(scenario.positions())
        ob = ObsBuilder(enc, pred, cheads, meta, speed, x_progress=True)
        slow = ACTION_NAMES.index("slow")
        prev = 0
        a = ob.ids[prev]
        rows = []
        zbuf = deque(
            [np.zeros(Z_DIM, dtype=np.float32)] * ob.history, maxlen=ob.history
        )
        decision = 0
        for t in range(TMAX):
            if t % DECIDE_EVERY == 0:
                frame = grab_frame(env)
                ob.push(frame, float(state[1]), prev, x=float(state[0]))
                assert ob.last_z.shape == (Z_DIM,)
                zbuf.append(ob.last_z.astype(np.float32))
                rows.append(np.concatenate(zbuf))
                a_pilot = pilot.decide(frame, state)
                a = slow if decision < PROBE_K else a_pilot
                decision += 1
                prev = ob.ids.index(a)
            rpm = cmd.rpm(state, float(speed) * ACTION_VECS[a])
            o, _, _, _, _ = env.step(rpm.reshape(1, 4))
            state = o[0]
            scenario.step()
            if state[0] >= GOAL_X:
                break
        episodes.append(np.asarray(rows, dtype=np.float32))
    env.close()
    return episodes


def train_and_meter(n_train=40, n_val=15, epochs=25):
    """Phase 1 (v3): fit on hover-start streams, then meter the TRUE
    closed loop — DispatchPolicy itself flies the validation episodes
    and its own trace is judged (the v2 lesson: a component whose
    inputs are shaped by its outputs must be metered in its own loop)."""
    import torch

    from skills.base import load_skill

    for s in (
        "gap-flight",
        "closing-door",
        "opening-door",
        "corridor-slalom-v2",
        "dodgeball",
    ):
        load_skill(s)
    train_eps, val_eps = {}, {}
    for wi, (world, cls) in enumerate(sorted(WORLD2CLASS.items())):
        eps = collect_streams(world, cls, n_train + n_val, SEED0 + 1000 * wi)
        train_eps[world], val_eps[world] = eps[:n_train], eps[n_train:]
        print(f"[streams] {world}: {len(eps)} episodes (expert={cls})")
    X = np.concatenate([np.concatenate(v) for v in train_eps.values() if len(v)])
    Y = np.concatenate(
        [
            np.full(sum(len(e) for e in v), CLASSES.index(WORLD2CLASS[w]))
            for w, v in train_eps.items()
        ]
    )
    clf = _mlp(X.shape[1], len(CLASSES))
    opt = torch.optim.Adam(clf.parameters(), lr=1e-3)
    Xt, Yt = torch.as_tensor(X), torch.as_tensor(Y)
    idx = np.random.default_rng(0).permutation(len(X))
    for _ in range(epochs):
        for k in range(0, len(idx), 512):
            b = idx[k : k + 512]
            loss = torch.nn.functional.cross_entropy(clf(Xt[b]), Yt[b])
            opt.zero_grad()
            loss.backward()
            opt.step()
    clf.eval()
    os.makedirs(os.path.dirname(CLF_PATH), exist_ok=True)
    torch.save(clf.state_dict(), CLF_PATH)
    # closed-loop meter: the dispatcher itself flies fresh episodes; its
    # own trace is the evidence (val streams above only sized the split)
    from eval.episode import run_scenario_episode
    from sim.envs import make_env

    env = make_env()
    report = {}
    for world in sorted(WORLD2CLASS):
        truth = WORLD2CLASS[world]
        finals, lats = [], []
        for i in range(n_val):
            pol = DispatchPolicy(1.0)
            run_scenario_episode(env, pol, SEED0 + 500 + i, world, 1.0)
            picks = pol.trace
            finals.append(bool(picks) and picks[-1] == truth)
            stable = next(
                (
                    k
                    for k in range(len(picks))
                    if picks[k] == truth and all(p == truth for p in picks[k:])
                ),
                None,
            )
            lats.append(stable)
        ok = [x for x in lats if x is not None]
        report[world] = {
            "final_acc": round(float(np.mean(finals)), 3),
            "latency_median_decisions": (float(np.median(ok)) if ok else None),
            "never_stable": n_val - len(ok),
        }
        print(f"[meter] {world}: {report[world]}")
    env.close()
    with open("experiments/dispatch/phase1_meters.json", "w") as f:
        json.dump(report, f, indent=1)
    print(f"[phase1] saved experiments/dispatch/phase1_meters.json  clf={CLF_PATH}")
    return report


def union_exam():
    """Phase 2: the dispatcher flies every cell some artifact holds solo,
    judged by each cell's OWN skill predicates and frozen bar."""
    from scripts.research import run_cell
    from sim.envs import make_env
    from skills.base import load_skill

    env = make_env()
    rows = {}
    for skill_name, cell_id in EXAM_CELLS:
        skill = load_skill(skill_name)
        cell = next(c for c in skill.cells if c.id == cell_id)
        crit = next((c for c in skill.criteria if c.cell == cell_id), None)
        res = run_cell(lambda speed: DispatchPolicy(speed), cell, skill, env)
        measured = res[crit.metric] if crit else res["success"]
        verdict = crit.check(measured) if crit else None
        rows[f"{skill_name}/{cell_id}"] = {
            "n": res["n"],
            "success": round(res["success"], 3),
            "crash": round(res["crash"], 3),
            "bar": f"{crit.metric}{crit.op}{crit.bar}" if crit else "diagnostic",
            "pass": verdict,
        }
        print(f"[exam] {skill_name}/{cell_id}: {rows[f'{skill_name}/{cell_id}']}")
    env.close()
    with open("experiments/dispatch/union_exam.json", "w") as f:
        json.dump(rows, f, indent=1)
    print("[phase2] saved experiments/dispatch/union_exam.json")
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", action="store_true")
    ap.add_argument("--exam", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        # hysteresis: default holds without a majority; a majority switches;
        # flicker does not
        h = Hysteresis()
        assert h.update("gap") == DEFAULT and h.update("slalom") == DEFAULT
        for _ in range(3):
            got = h.update("gap")
        assert got == "gap", "3/5 majority must switch"
        assert (
            h.update("slalom") == "gap" and h.update("mover") == "gap"
        ), "flicker must not switch"
        # classifier machinery separates synthetic clusters
        import torch

        rng = np.random.default_rng(0)
        X = np.concatenate(
            [rng.normal(i, 0.3, size=(200, 8)) for i in range(len(CLASSES))]
        ).astype(np.float32)
        Y = np.repeat(np.arange(len(CLASSES)), 200)
        clf = _mlp(8, len(CLASSES))
        opt = torch.optim.Adam(clf.parameters(), lr=1e-2)
        for _ in range(60):
            loss = torch.nn.functional.cross_entropy(
                clf(torch.as_tensor(X)), torch.as_tensor(Y)
            )
            opt.zero_grad()
            loss.backward()
            opt.step()
        acc = float((clf(torch.as_tensor(X)).argmax(1).numpy() == Y).mean())
        assert acc > 0.95, f"synthetic clusters must separate, got {acc}"
        # spec sanity: every exam cell's skill exists in the expert roster's
        # coverage and every class has an artifact path
        assert set(EXPERTS) == set(CLASSES)
        assert set(WORLD2CLASS.values()) == set(CLASSES)
        print(
            "DISPATCH OK: hysteresis (hover default, majority switch, "
            "flicker-proof), classifier fits, roster covers every class"
        )
        return

    if args.train:
        train_and_meter()
        return
    if args.exam:
        union_exam()
        return


if __name__ == "__main__":
    main()
    sys.exit(0)

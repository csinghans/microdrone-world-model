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


class OracleTrackW(OracleTrack):
    """OracleTrack with a width gate: if the tracked aperture is too
    narrow to pass AND we are close to the plane, hold (hover) instead
    of pressing in — the wait-capable door teacher. Probed on both door
    worlds before entering any pot (the teacher-floor discipline)."""

    SPACING_MIN = 0.75  # centre-spacing ~= aperture + 2*PILLAR_R; pass needs ~0.55+
    NEAR = 0.9  # only gate the width when the plane is this close

    def decide(self, frame, state) -> int:
        from eval.eval_arena_ceiling import DEADBAND, VEER_L, VEER_R
        from planner.action_set import ACTION_NAMES, FORWARD

        del frame
        x, y = float(state[0]), float(state[1])
        ahead = [p for p in self.pillars if float(p[0]) > x - 0.05]
        if len(ahead) < 2:
            return FORWARD
        plane_x = min(float(p[0]) for p in ahead)
        ys = sorted(float(p[1]) for p in ahead if float(p[0]) < plane_x + 0.3)
        if len(ys) < 2:
            return FORWARD
        width, yc = max((b - a, (a + b) / 2.0) for a, b in zip(ys, ys[1:]))
        err = yc - y
        if width < self.SPACING_MIN and (plane_x - x) < self.NEAR:
            if abs(err) >= DEADBAND:  # line up while waiting
                return VEER_L if err > 0 else VEER_R
            return ACTION_NAMES.index("hover")
        if abs(err) < DEADBAND:
            return FORWARD
        return VEER_L if err > 0 else VEER_R


# per-stage ORACLE teachers for composite courses (privileged, labelled)
STAGE_ORACLE = {
    "gap": "weave",
    "slalom3_fixed": "weave",
    "moving_gap": "trackw",
    "door": "trackw",
    "opening_door": "trackw",
}

# v2 mixed relay: oracles where geometry suffices, LEARNED artifacts where
# timing does (the measured law: scripted pilots lose timing tasks). Every
# teacher carries a gated record on its own world.
STAGE_TEACHER_V2 = {
    "gap": ("oracle", "weave"),  # OracleWeave 0.97
    "slalom3_fixed": ("oracle", "weave"),
    "moving_gap": ("oracle", "track"),  # OracleTrack 0.90 (probe 27/30)
    "door": ("zip", "experiments/moving_gap_v2/artifacts/ppo_moving_gap_v2_K3.zip"),
    "opening_door": (
        "zip",
        "experiments/opening_door/artifacts/ppo_opening_door_K3.zip",
    ),
}


class OracleRelay:
    """Privileged per-stage teacher relay over a composite course (the
    hot-start TEACHER). v2: mixed — oracles fly the geometry stages,
    gated LEARNED artifacts fly the timing stages (doors). Zip teachers
    get stage-LOCAL x (their x_progress convention) and a begin() reset
    at their stage entry; oracles read global geometry."""

    def __init__(self, names, stage_len: float = 3.0, teachers=None):
        self.names = tuple(names)
        self.L = float(stage_len)
        self.teachers = teachers or STAGE_TEACHER_V2
        self.pillars: list = []
        self._stage = -1
        self._pilot = None
        self._kind = None

    def begin(self, pillars) -> None:
        self.pillars = [np.array(q, dtype=float) for q in pillars]
        self._stage = -1
        self._pilot = None
        self._kind = None

    def _stage_pillars(self, k):
        lo, hi = k * self.L - 0.2, (k + 1) * self.L + 0.2
        return [p for p in self.pillars if lo <= float(p[0]) < hi]

    def _make(self, name):
        from eval.eval_arena_ceiling import OracleWeave

        kind, ref = self.teachers[name]
        if kind == "oracle":
            pilot = {
                "weave": OracleWeave,
                "track": OracleTrack,
                "trackw": OracleTrackW,
            }[ref]()
        else:
            pilot = _teacher_zip(ref)
        return kind, pilot

    def decide(self, frame, state) -> int:
        k = int(np.clip(float(state[0]) // self.L, 0, len(self.names) - 1))
        if k != self._stage:
            self._stage = k
            self._kind, self._pilot = self._make(self.names[k])
            self._pilot.begin(self._stage_pillars(k))
        if hasattr(self._pilot, "pillars"):
            self._pilot.pillars = self._stage_pillars(k)
        if self._kind == "zip":  # learned teachers fly in stage-local x
            s = np.array(state, dtype=float, copy=True)
            s[0] -= k * self.L
            return self._pilot.decide(frame, s)
        return self._pilot.decide(frame, state)


def _teacher_zip(zip_path: str, speed: float = 1.0):
    from eval.eval_closed_loop import load_or_train
    from planner.learned_policy import LearnedPolicy, load_policy

    enc, pred, cheads, _n, meta = load_or_train()
    return LearnedPolicy(load_policy(zip_path), enc, pred, cheads, meta, speed=speed)


class OracleDoorLive(OracleTrack):
    """The door teacher, live-pillar edition of the 0.90 meta oracle:
    measure the aperture from the innermost pillar pair, line up on its
    centre, stage the approach by distance (forward -> slow -> hover),
    and charge the moment the half-aperture admits the drone. No meta,
    no privileged clock — everything from the runner's live `.pillars`
    refresh, so it fits the standard collection protocol."""

    NEED_HALF = 0.30  # half-aperture ~ COLLISION_R + margin
    SLOW_AT = 1.0
    HOLD_AT = 0.45

    def decide(self, frame, state) -> int:
        from eval.eval_arena_ceiling import DEADBAND, VEER_L, VEER_R
        from planner.action_set import ACTION_NAMES, FORWARD

        del frame
        x, y = float(state[0]), float(state[1])
        ahead = [p for p in self.pillars if float(p[0]) > x - 0.05]
        if len(ahead) < 2:
            return FORWARD
        plane_x = min(float(p[0]) for p in ahead)
        ys = sorted(float(p[1]) for p in ahead if float(p[0]) < plane_x + 0.3)
        if len(ys) < 2:
            return FORWARD
        spacing, yc = max((b - a, (a + b) / 2.0) for a, b in zip(ys, ys[1:]))
        half = (spacing - 0.36) / 2.0  # centre spacing -> half-aperture
        err = yc - y
        if abs(err) >= DEADBAND:
            return VEER_L if err > 0 else VEER_R
        dist = plane_x - x
        if half >= self.NEED_HALF or dist > self.SLOW_AT:
            return FORWARD
        if dist > self.HOLD_AT:
            return ACTION_NAMES.index("slow")
        return ACTION_NAMES.index("hover")


def _teacher_weave(speed, stack):
    from eval.eval_arena_ceiling import OracleWeave

    del speed, stack
    return OracleWeave()


def _teacher_track(speed, stack):
    del speed, stack
    return OracleTrack()


def _teacher_dodge(ball_speed):
    def make(speed, stack):
        from eval.eval_dodge_ceiling import OracleDodge

        del speed, stack
        return OracleDodge(ball_speed)

    return make


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
    "dodge06": _teacher_dodge(0.6),
    "dodge10": _teacher_dodge(1.0),
    "dodge14": _teacher_dodge(1.4),
    "dodge18": _teacher_dodge(1.8),
    "doorlive": lambda speed, stack: OracleDoorLive(),
}

# dodge-distill recipe (frozen at pre-registration): the four ball-speed
# worlds, each taught by its matched OracleDodge (feasibility-probe records
# 0.90/0.80/0.80/0.80). Station episodes never reach GOAL_X — "reached 0/N"
# is the expected print, not a broken teacher.
DODGE = (
    ("dodgeball_v06", 200, 1.0, "dodge06", 51000),
    ("dodgeball_v10", 200, 1.0, "dodge10", 52000),
    ("dodgeball_v14", 200, 1.0, "dodge14", 53000),
    ("dodgeball_v18", 200, 1.0, "dodge18", 54000),
)


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


class OracleDoorMeta:
    """The 0.90 opening-door teacher (probed 27/30, seeds 123000): reads
    the door's TRUE aperture from scenario meta on its own decision
    clock — hold centered, stage the approach by distance, charge when
    the half-aperture admits. Privileged by design (teachers are);
    used ONLY by the odoor unit collection, which attaches the meta."""

    NEED_HALF = 0.30
    SLOW_AT = 1.0
    HOLD_AT = 0.45

    def __init__(self):
        self.t = 0.0
        self.meta = None

    def begin(self, pillars) -> None:
        self.t = 0.0

    def decide(self, frame, state) -> int:
        from eval.eval_arena_ceiling import DEADBAND, VEER_L, VEER_R
        from planner.action_set import ACTION_NAMES, FORWARD
        from planner.latent_mpc import DECIDE_EVERY
        from sim.envs import CTRL_HZ
        from skills.opening_door.skill import open_half_at

        del frame
        self.t += DECIDE_EVERY / CTRL_HZ
        x, y = float(state[0]), float(state[1])
        m = self.meta
        err = m.get("yc", 0.0) - y
        if abs(err) >= DEADBAND:
            return VEER_L if err > 0 else VEER_R
        half = open_half_at(m, self.t)
        dist = m["x_gap"] - x
        if half >= self.NEED_HALF or dist > self.SLOW_AT:
            return FORWARD
        if dist > self.HOLD_AT:
            return ACTION_NAMES.index("slow")
        return ACTION_NAMES.index("hover")


def collect_odoor(n_episodes: int, seed0: int = 125000):
    """odoor-v2 unit collection: the meta oracle (0.90) flies
    opening_door@1.0; the student's obs is the standard exam-exact
    stream. Native unit starts (this is a UNIT campaign)."""
    from eval.eval_closed_loop import load_or_train
    from planner.action_set import ACTION_VECS
    from planner.latent_mpc import DECIDE_EVERY
    from planner.learned_policy import ObsBuilder
    from sim.envs import VelCommander, grab_frame, make_ctrl, make_env
    from sim.scenario_registry import get as get_scenario
    from sim.scenarios import GOAL_X, TMAX

    enc, pred, cheads, _n, meta = load_or_train()
    env = make_env()
    X, Y, reached = [], [], 0
    spec = get_scenario("opening_door")
    for i in range(n_episodes):
        seed = seed0 + i
        obs0, _ = env.reset(seed=seed)
        cmd = VelCommander(make_ctrl(), env.CTRL_TIMESTEP)
        state = obs0[0]
        cmd.reset(state[0:3])
        scenario = spec.spawn(env, np.random.default_rng(seed), speed=1.0)
        pilot = OracleDoorMeta()
        pilot.meta = scenario.meta
        pilot.begin(None)
        ob = ObsBuilder(enc, pred, cheads, meta, 1.0, x_progress=True)
        prev = 0
        a = ob.ids[prev]
        for t in range(TMAX):
            if t % DECIDE_EVERY == 0:
                frame = grab_frame(env)
                vec = ob.push(frame, float(state[1]), prev, x=float(state[0]))
                a = pilot.decide(frame, state)
                prev = ob.ids.index(a)
                X.append(vec)
                Y.append(prev)
            rpm = cmd.rpm(state, 1.0 * ACTION_VECS[a])
            o, _r, _te, _tr, _i = env.step(rpm.reshape(1, 4))
            state = o[0]
            scenario.step()
            if state[0] >= GOAL_X:
                reached += 1
                break
    env.close()
    print(
        f"[odoor] {len(X)} decisions from {n_episodes} episodes "
        f"(teacher reached {reached}/{n_episodes})"
    )
    return np.asarray(X, dtype=np.float32), np.asarray(Y, dtype=np.int64)


def collect_hot(n_courses: int, seed0: int = 120000, k: int = 3):
    """Hot-start collection v2: the MIXED RELAY flies random composite
    courses; the student's observation is recorded with StageLocal
    semantics (stage-local x, memory reset at stage entry) — the
    exam-exact view. **Cleared-segment filtering**: a decision is kept
    only if its stage was subsequently cleared BEFORE any crash — weak
    teachers still yield clean demonstrations. Returns (X, Y, tags,
    relay_success_rate)."""
    from eval.eval_closed_loop import load_or_train
    from planner.action_set import ACTION_VECS
    from planner.latent_mpc import DECIDE_EVERY
    from planner.learned_policy import ObsBuilder
    from sim.composite import STAGE_LEN, course_for_seed, register_course
    from sim.envs import VelCommander, grab_frame, make_ctrl, make_env
    from sim.scenario_registry import get as get_scenario
    from sim.scenarios import TMAX

    enc, pred, cheads, _n, meta = load_or_train()
    env = make_env()
    X, Y, T, wins = [], [], [], 0
    for i in range(n_courses):
        seed = seed0 + i
        names = course_for_seed(seed)
        world = register_course(seed)
        obs0, _ = env.reset(seed=seed)
        cmd = VelCommander(make_ctrl(), env.CTRL_TIMESTEP)
        state = obs0[0]
        cmd.reset(state[0:3])
        scenario = get_scenario(world).spawn(
            env, np.random.default_rng(seed), speed=1.0
        )
        relay = OracleRelay(names)
        relay.begin(scenario.positions())
        ob = ObsBuilder(enc, pred, cheads, meta, 1.0, x_progress=True)
        goal_x, tmax = k * STAGE_LEN, k * TMAX
        stage, prev, a = -1, 0, 0
        ep_rows = []  # (vec, label, stage_idx)
        clear_step: dict = {}
        min_clear, crash_step = 9.0, None
        from sim.scenarios import COLLISION_R, nearest_planar

        for t in range(tmax):
            if t % DECIDE_EVERY == 0:
                x = float(state[0])
                k_now = int(np.clip(x // STAGE_LEN, 0, k - 1))
                if k_now != stage:
                    stage = k_now
                    ob.reset()  # StageLocal semantics: fresh corridor
                    prev = 0
                frame = grab_frame(env)
                vec = ob.push(frame, float(state[1]), prev, x=x - stage * STAGE_LEN)
                relay.pillars = [np.array(q) for q in scenario.positions()]
                a = relay.decide(frame, state)
                prev = ob.ids.index(a)
                ep_rows.append((vec, prev, stage))
            rpm = cmd.rpm(state, 1.0 * ACTION_VECS[a])
            o, _r, _te, _tr, _i = env.step(rpm.reshape(1, 4))
            state = o[0]
            scenario.step()
            d = nearest_planar(state[0:2], scenario.positions())
            if d < min_clear:
                min_clear = d
                if d < COLLISION_R and crash_step is None:
                    crash_step = t
            for kk in range(k):
                if kk not in clear_step and float(state[0]) >= (kk + 1) * STAGE_LEN:
                    clear_step[kk] = t
            if state[0] >= goal_x:
                if crash_step is None:
                    wins += 1
                break
        # cleared-segment filter: keep a stage's decisions only if that
        # stage was cleared BEFORE any crash — weak teachers still yield
        # clean demonstrations
        keep = {
            kk for kk, cs in clear_step.items() if crash_step is None or cs < crash_step
        }
        for vec, lab, st in ep_rows:
            if st in keep:
                X.append(vec)
                Y.append(lab)
                T.append(names[st])
        if (i + 1) % 25 == 0:
            print(f"[hot] {i + 1}/{n_courses} courses, {len(X)} kept decisions")
    env.close()
    rate = wins / n_courses
    print(
        f"[hot] {len(X)} KEPT decisions from {n_courses} courses "
        f"(relay clean-course rate {wins}/{n_courses} = {rate:.3f})"
    )
    return (
        np.asarray(X, dtype=np.float32),
        np.asarray(Y, dtype=np.int64),
        np.asarray(T),
        rate,
    )


def bc_train(X, Y, out: str, epochs: int = 40, lr: float = 3e-4, val_frac=0.1, W=None):
    """Supervise a fresh PPO policy's action head; save a runner-ready zip.
    Returns held-out top-1 accuracy — the obs-sufficiency meter. With `W`
    (per-sample world tags) the meter is also reported PER WORLD: a mixed
    pot must fit every teacher, not an average of them."""
    import torch
    from stable_baselines3 import PPO
    from stable_baselines3.common.env_util import make_vec_env

    from planner.learned_policy import WMPolicyEnv

    # spaces only — the builtin classic world is always registered
    venv = make_vec_env(
        lambda: WMPolicyEnv(worlds=("classic",), x_progress=True), n_envs=1
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


class AnchoredPPO:
    """Deferred-import namespace: `make(env_or_zip)` returns a PPO subclass
    instance with a KL anchor to a FROZEN copy of the loaded prior policy.

    The `train()` body is a faithful copy of SB3 **2.9.0**'s PPO.train with
    exactly ONE addition — `kl_coef * KL(pi_prior || pi_theta)` on each
    minibatch, inserted after the standard loss assembly. The version is
    pinned on purpose: the selftest asserts it, so an SB3 upgrade fails
    loudly instead of silently drifting from the copied internals (the
    checkpoint-meta-is-truth philosophy, applied to vendored code)."""

    @staticmethod
    def build():
        import copy

        import numpy as np
        import stable_baselines3
        import torch as th
        from gymnasium import spaces
        from stable_baselines3 import PPO
        from stable_baselines3.common.utils import explained_variance
        from torch.nn import functional as F

        assert stable_baselines3.__version__ == "2.9.0", (
            "AnchoredPPO.train is a vendored copy of SB3 2.9.0's — re-verify "
            f"the copy against {stable_baselines3.__version__} before trusting it"
        )

        class _AnchoredPPO(PPO):
            kl_coef = 0.0

            def set_anchor(self, kl_coef: float) -> None:
                self.kl_coef = float(kl_coef)
                self.prior_policy = copy.deepcopy(self.policy)
                self.prior_policy.set_training_mode(False)
                for prm in self.prior_policy.parameters():
                    prm.requires_grad_(False)

            def train(self) -> None:
                self.policy.set_training_mode(True)
                self._update_learning_rate(self.policy.optimizer)
                clip_range = self.clip_range(self._current_progress_remaining)
                if self.clip_range_vf is not None:
                    clip_range_vf = self.clip_range_vf(self._current_progress_remaining)

                entropy_losses = []
                pg_losses, value_losses = [], []
                anchor_losses = []
                clip_fractions = []

                continue_training = True
                for epoch in range(self.n_epochs):
                    approx_kl_divs = []
                    for rollout_data in self.rollout_buffer.get(self.batch_size):
                        actions = rollout_data.actions
                        if isinstance(self.action_space, spaces.Discrete):
                            actions = rollout_data.actions.long().flatten()

                        values, log_prob, entropy = self.policy.evaluate_actions(
                            rollout_data.observations, actions
                        )
                        values = values.flatten()
                        advantages = rollout_data.advantages
                        if self.normalize_advantage and len(advantages) > 1:
                            advantages = (advantages - advantages.mean()) / (
                                advantages.std() + 1e-8
                            )

                        ratio = th.exp(log_prob - rollout_data.old_log_prob)
                        policy_loss_1 = advantages * ratio
                        policy_loss_2 = advantages * th.clamp(
                            ratio, 1 - clip_range, 1 + clip_range
                        )
                        policy_loss = -th.min(policy_loss_1, policy_loss_2).mean()

                        pg_losses.append(policy_loss.item())
                        clip_fraction = th.mean(
                            (th.abs(ratio - 1) > clip_range).float()
                        ).item()
                        clip_fractions.append(clip_fraction)

                        if self.clip_range_vf is None:
                            values_pred = values
                        else:
                            values_pred = rollout_data.old_values + th.clamp(
                                values - rollout_data.old_values,
                                -clip_range_vf,
                                clip_range_vf,
                            )
                        value_loss = F.mse_loss(rollout_data.returns, values_pred)
                        value_losses.append(value_loss.item())

                        if entropy is None:
                            entropy_loss = -th.mean(-log_prob)
                        else:
                            entropy_loss = -th.mean(entropy)
                        entropy_losses.append(entropy_loss.item())

                        loss = (
                            policy_loss
                            + self.ent_coef * entropy_loss
                            + self.vf_coef * value_loss
                        )

                        # === the ONE addition: anchor to the frozen prior ===
                        if self.kl_coef > 0.0:
                            with th.no_grad():
                                prior_dist = self.prior_policy.get_distribution(
                                    rollout_data.observations
                                ).distribution
                            cur_dist = self.policy.get_distribution(
                                rollout_data.observations
                            ).distribution
                            anchor = th.distributions.kl_divergence(
                                prior_dist, cur_dist
                            ).mean()
                            anchor_losses.append(float(anchor.item()))
                            loss = loss + self.kl_coef * anchor
                        # =====================================================

                        with th.no_grad():
                            log_ratio = log_prob - rollout_data.old_log_prob
                            approx_kl_div = (
                                th.mean((th.exp(log_ratio) - 1) - log_ratio)
                                .cpu()
                                .numpy()
                            )
                            approx_kl_divs.append(approx_kl_div)

                        if (
                            self.target_kl is not None
                            and approx_kl_div > 1.5 * self.target_kl
                        ):
                            continue_training = False
                            if self.verbose >= 1:
                                print(
                                    f"Early stopping at step {epoch} due to "
                                    f"reaching max kl: {approx_kl_div:.2f}"
                                )
                            break

                        self.policy.optimizer.zero_grad()
                        loss.backward()
                        th.nn.utils.clip_grad_norm_(
                            self.policy.parameters(), self.max_grad_norm
                        )
                        self.policy.optimizer.step()

                    self._n_updates += 1
                    if not continue_training:
                        break

                explained_var = explained_variance(
                    self.rollout_buffer.values.flatten(),
                    self.rollout_buffer.returns.flatten(),
                )
                self.logger.record("train/entropy_loss", np.mean(entropy_losses))
                self.logger.record("train/policy_gradient_loss", np.mean(pg_losses))
                self.logger.record("train/value_loss", np.mean(value_losses))
                if anchor_losses:
                    self.logger.record("train/anchor_kl", np.mean(anchor_losses))
                self.logger.record("train/approx_kl", np.mean(approx_kl_divs))
                self.logger.record("train/clip_fraction", np.mean(clip_fractions))
                self.logger.record("train/loss", loss.item())
                self.logger.record("train/explained_variance", explained_var)
                self.logger.record(
                    "train/n_updates", self._n_updates, exclude="tensorboard"
                )
                self.logger.record("train/clip_range", clip_range)
                if self.clip_range_vf is not None:
                    self.logger.record("train/clip_range_vf", clip_range_vf)

        return _AnchoredPPO


def finetune(
    bc_zip: str,
    steps: int,
    out: str,
    world: str = "slalom3_fixed",
    station_tick: float = 0.0,
    anchor: float = 0.0,
    gate_bonus: float = 0.0,
    anchor_end: float = None,
    edge_bias: bool = False,
):
    """PPO fine-tune from the BC init; `world` may be a comma-separated
    diet (round-robin, the training-env convention). station_tick passes
    through to the env for ball worlds (the measured-good station economy).
    anchor_end (with anchor > 0) drives the KL coefficient linearly from
    anchor to anchor_end across the run, updated at each rollout start."""
    from stable_baselines3 import PPO
    from stable_baselines3.common.env_util import make_vec_env

    from planner.learned_policy import WMPolicyEnv

    diet = tuple(world.split(","))
    venv = make_vec_env(
        lambda: WMPolicyEnv(
            worlds=diet,
            x_progress=True,
            station_tick=station_tick,
            gate_bonus=gate_bonus,
            edge_bias=edge_bias,
        ),
        n_envs=1,
    )
    cls = AnchoredPPO.build() if anchor > 0.0 else PPO
    model = cls.load(bc_zip, env=venv)
    callback = None
    if anchor > 0.0:
        model.set_anchor(anchor)
        if anchor_end is not None:
            from stable_baselines3.common.callbacks import BaseCallback

            class _AnchorSchedule(BaseCallback):
                def _on_rollout_start(self):
                    frac = min(1.0, self.model.num_timesteps / float(steps))
                    # coefficient ONLY — set_anchor would re-freeze the
                    # prior to the CURRENT policy (and deepcopy a live
                    # grad graph); the prior snapshot stays the load-time
                    # BC2, which is the whole point of the anchor
                    self.model.kl_coef = anchor + (anchor_end - anchor) * frac

                def _on_step(self) -> bool:
                    return True

            callback = _AnchorSchedule()
    model.learn(total_timesteps=steps, callback=callback)
    if anchor > 0.0 and anchor_end is not None:
        print(f"[finetune] anchor schedule landed at kl_coef={model.kl_coef:.4f}")
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
    ap.add_argument("--probe-trackw", type=int, default=0, metavar="N")
    ap.add_argument("--hot-ceiling", type=int, default=0, metavar="N")
    ap.add_argument("--hot", type=int, default=0, metavar="N_COURSES")
    ap.add_argument("--odoor", type=int, default=0, metavar="N_EPS")
    ap.add_argument("--probe-seed0", type=int, default=43900)
    ap.add_argument("--teacher", default="weave", choices=tuple(TEACHERS))
    ap.add_argument("--generalist", choices=("track", "mgap_champion"), default=None)
    ap.add_argument("--recipe2", action="store_true", help="K1 remedy recipe")
    ap.add_argument("--dodge", action="store_true", help="dodge-distill recipe")
    ap.add_argument("--ft-tick", type=float, default=0.0)
    ap.add_argument("--anchor", type=float, default=0.0)
    ap.add_argument("--anchor-end", type=float, default=None)
    ap.add_argument("--ft-edge-bias", action="store_true")
    ap.add_argument("--ft-gate-bonus", type=float, default=0.0)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.probe_trackw:
        # teacher probe: the width-gated tracker on BOTH door worlds
        from eval.episode import run_scenario_episode
        from sim.envs import make_env
        from skills.base import load_skill

        env = make_env()
        for skill_name, world, cell_speed in (
            ("closing-door", "door", 1.0),
            ("opening-door", "opening_door", 1.0),
        ):
            judge = load_skill(skill_name)
            ok = 0
            for i in range(args.probe_trackw):
                ep = run_scenario_episode(
                    env, OracleTrackW(), 121000 + i, world, cell_speed
                )
                ok += int(judge.success(ep))
            print(
                f"[probe-trackw] {world}@1.0: {ok}/{args.probe_trackw} "
                f"= {ok / args.probe_trackw:.3f}"
            )
        env.close()
        return

    if args.hot_ceiling:
        # the TRUE integration ceiling: the oracle relay on random courses
        from eval.eval_integration import suite
        from skills.base import load_skill

        for sk in (
            "gap-flight",
            "corridor-slalom-v2",
            "moving-gap",
            "closing-door",
            "opening-door",
        ):
            load_skill(sk)
        suite(
            lambda names: OracleRelay(names),
            args.hot_ceiling,
            110000,
            args.out,
        )
        return

    if args.odoor:
        from skills.base import load_skill

        load_skill("opening-door")
        X, Y = collect_odoor(args.odoor)
        out = args.out or "output/ppo_odoor_v2.zip"
        acc, _ = bc_train(X, Y, out, epochs=args.epochs)
        print(f"[odoor] manipulation meter: val_top1={acc:.3f} (floor 0.80)")
        return

    if args.hot:
        from skills.base import load_skill

        for sk in (
            "gap-flight",
            "corridor-slalom-v2",
            "moving-gap",
            "closing-door",
            "opening-door",
        ):
            load_skill(sk)
        X, Y, T, rate = collect_hot(args.hot)
        out = args.out or "output/ppo_hot_start.zip"
        acc, _ = bc_train(X, Y, out, epochs=args.epochs, W=T)
        print(f"[hot] teacher-relay line {rate:.3f}; pooled val {acc:.3f}")
        return

    if args.probe_track:
        # teacher probe: is OracleTrack a fit teacher on its own world?
        from eval.episode import run_scenario_episode
        from sim.envs import make_env
        from skills.base import load_skill

        judge = load_skill("moving-gap")
        env = make_env()
        ok = 0
        for i in range(args.probe_track):
            ep = run_scenario_episode(
                env, OracleTrack(), args.probe_seed0 + i, "moving_gap", 1.0
            )
            ok += int(judge.success(ep))
        env.close()
        print(f"[probe-track] OracleTrack on moving_gap@1.0: {ok}/{args.probe_track}")
        return

    if args.dodge:
        from skills.base import load_skill

        load_skill("dodgeball")
        parts, tags = [], []
        for world, n, speed, teacher, seed0 in DODGE:
            X, Y = collect(n, world, speed, seed0=seed0, teacher=teacher)
            parts.append((X, Y))
            tags += [world] * len(X)
        X = np.concatenate([p[0] for p in parts])
        Y = np.concatenate([p[1] for p in parts])
        out = args.out or "output/ppo_distill_dodge.zip"
        acc, _ = bc_train(X, Y, out, epochs=args.epochs, W=np.asarray(tags))
        print(f"[distill] dodge-clone manipulation meter: pooled val={acc:.3f}")
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
        # not a 36-sample coin flip. On artifact-less runners load_or_train
        # self-trains a TINY model whose near-degenerate probabilities cap
        # fit at the label entropy (identical obs, different oracle actions)
        # — the autotrained_tiny stamp downgrades the bar honestly, exactly
        # like the demo's behavior asserts.
        from eval.eval_closed_loop import load_or_train

        tiny = load_or_train()[4].get("autotrained_tiny", False)
        floor = 0.35 if tiny else 0.8
        assert train_acc >= floor, f"BC train acc {train_acc} < {floor} (tiny={tiny})"
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
        from skills.base import load_skill

        for sk in (
            "corridor-slalom-v2",
            "dodgeball",
            "moving-gap",
            "closing-door",
            "opening-door",
        ):
            load_skill(sk)  # any --world must be resolvable
        from sim.composite import register_random_course

        register_random_course()  # the integration-FT training world
        finetune(
            args.finetune,
            args.steps,
            args.out or "output/ppo_distill_ft.zip",
            world=args.world,
            station_tick=args.ft_tick,
            anchor=args.anchor,
            gate_bonus=args.ft_gate_bonus,
            anchor_end=args.anchor_end,
            edge_bias=args.ft_edge_bias,
        )
        return
    if args.collect:
        from skills.base import load_skill

        load_skill("corridor-slalom-v2")
        X, Y = collect(
            args.collect, args.world, args.speed, seed0=args.seed0, teacher=args.teacher
        )
        acc, _ = bc_train(X, Y, args.out or "output/ppo_distill_bc.zip", args.epochs)
        print(f"[distill] manipulation check: val_top1={acc:.3f} (floor 0.80)")


if __name__ == "__main__":
    main()
    sys.exit(0)

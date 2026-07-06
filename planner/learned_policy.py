"""Learn the policy: RL over the world model's eyes.

Eight hand-tuned MPC configurations each fixed one failure mode and exposed
the next, while the model's rankings were already perfect (veer-ranking
1.00). The measured verdict: the hand-crafted cost function is the
bottleneck — so stop tuning it and learn it.

  * **Observation** — not pixels, and not privileged pillar positions: the
    world model's own outputs. For each of the five candidate commands, the
    8 collision probabilities (4 horizons x warn/crit rings), plus the
    drone's own y, cruise factor and previous command — 47 numbers per
    decision.
  * **Memory, two flavours** — default: the last 12 decisions stacked (~1 s
    at 12 Hz). `recurrent=True`: sb3-contrib's RecurrentPPO — a single
    decision per observation and an LSTM carries the memory.
  * **Reward** — progress toward the goal line, a small time cost, a crash
    penalty, a goal bonus. No hand-tuned danger weights anywhere — that is
    the point.

Speed-diet knobs (the measured lesson: *you get what you sample*):
`edge_bias` draws half the episodes from the fast edge of the envelope —
uniform sampling starves the edge twice over (the top band is a sliver of
the range, and fast episodes end sooner). `train_curriculum` runs one budget
through three diets in sequence. Both were measured against the same fair
budget: the edge diet closes the fast hole and reopens the cluttered one;
the ordered curriculum loses both bands (on-policy learning has no
yesterday). The stacked policy needed neither and has yet to lose anywhere.

Saves output/ppo_wm_policy[_recurrent][_rand][_edge][_curr].zip (git-ignored).
"""

import os
from collections import deque

import gymnasium as gym
import numpy as np
import torch

from datasets.intervention_labels import HORIZONS  # noqa: F401  (obs layout doc)
from planner.action_set import ACTION_VECS, FORWARD, SPEED_RANGE
from planner.latent_mpc import DECIDE_EVERY, _frame_tensor
from sim.domain_randomization import jitter
from sim.envs import VelCommander, grab_frame, make_ctrl, make_env
from sim.scenario_registry import get as get_scenario
from sim.scenario_registry import resolve_worlds
from sim.scenarios import COLLISION_R, GOAL_X, TMAX, nearest_planar

HISTORY = 12  # stacked-memory depth (~1 s @ 12 Hz); recurrent uses 1 + LSTM
# edge_bias: uniform sampling starves the envelope edge twice over — the top
# band is a sliver of the range AND fast episodes end sooner, so the edge's
# share of *decisions* is smaller still. Bias half the episodes into the edge.
EDGE_RANGE = (1.5, 2.0)  # the envelope edge: 1.2–1.6 m/s cruise
EDGE_P = 0.5  # with edge_bias, this fraction of episodes trains at the edge
# curriculum: one budget, three diets — natural, edge-drilled, then mixed.
# (edge_p, share of the budget) per phase. Measured: it backfires.
CURRICULUM = ((0.0, 1 / 3), (0.5, 1 / 3), (0.25, 1 / 3))
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def zip_path(
    recurrent: bool = False,
    randomize: bool = False,
    edge: bool = False,
    curr: bool = False,
    hard: bool = False,
    xp: bool = False,
) -> str:
    suffix = (
        ("_recurrent" if recurrent else "")
        + ("_rand" if randomize else "")
        + ("_edge" if edge else "")
        + ("_curr" if curr else "")
        + ("_hard" if hard else "")
        + ("_xp" if xp else "")
    )
    return os.path.join(_ROOT, "output", f"ppo_wm_policy{suffix}.zip")


def _menu(meta):
    """The five-command menu (climb off, as in WMPolicy) -> original ids."""
    names = list(meta["action_names"])
    return [i for i, n in enumerate(names) if n != "climb"]


class ObsBuilder:
    """One decision's observation: the world model's 8 collision probabilities
    per candidate command + own y + cruise factor + previous command one-hot,
    stacked over the last `history` decisions (history=1 for the recurrent
    policy — its LSTM is the memory). Shared verbatim by the training env and
    the deployed LearnedPolicy, so train and fly see the same thing."""

    def __init__(
        self,
        enc,
        pred,
        cheads,
        meta,
        speed: float,
        history: int = HISTORY,
        x_progress: bool = False,
    ):
        self.enc, self.pred, self.cheads = enc, pred, cheads
        self.ids = _menu(meta)
        vecs = float(speed) * np.array(meta["action_vecs"], dtype=np.float32)
        a_norm = np.array(meta["a_norm"], dtype=np.float32)
        self.cands = torch.tensor(vecs[self.ids] / a_norm)
        self.speed = float(speed)
        self.n_act = len(self.ids)
        # x_progress: the map pin. The stacked history is only a *map* if its
        # snapshots can be spatially registered — own corridor progress (pure
        # odometry, the drone's knowledge of itself) is the anchor that lets
        # "danger seen 0.8 s ago" mean "danger BEHIND me" vs "danger ahead".
        self.x_progress = bool(x_progress)
        # collision probabilities per candidate: one per (horizon, ring),
        # sized from the LOADED model's meta — 8 for the classic 4x2 stack,
        # more for horizon-extended variants; old zips keep their layout
        n_probs = len(meta["horizons"]) * len(meta["radii"])
        self.per_step = self.n_act * n_probs + 2 + self.n_act + (1 if x_progress else 0)
        self.history = int(history)
        self.hist = deque(maxlen=self.history)
        self.h_gru = None  # model-side memory state (v3 checkpoints)
        self.reset()

    def reset(self) -> None:
        self.hist.clear()
        self.h_gru = None
        for _ in range(self.history):
            self.hist.append(np.zeros(self.per_step, dtype=np.float32))

    def push(
        self, frame: np.ndarray, y: float, prev_menu_idx: int, x: float = 0.0
    ) -> np.ndarray:
        with torch.no_grad():
            z = self.enc(_frame_tensor(frame))
            cond = z
            tem = getattr(self.enc, "temporal", None)
            if tem is not None:
                cond, self.h_gru = tem.step(z, self.h_gru)
            z_hat = self.pred(
                cond.expand(len(self.cands), -1),
                self.cands,
                base=z.expand(len(self.cands), -1),
            )
            p = torch.sigmoid(self.cheads(z_hat)).numpy()  # (n_act, H, 2)
        # write-only tap: the raw scene encoding, for consumers that need
        # identity rather than threat (the dispatch classifier) — the policy
        # observation below stays byte-identical
        self.last_z = z.detach().squeeze(0).cpu().numpy()
        prev = np.zeros(self.n_act, dtype=np.float32)
        prev[prev_menu_idx] = 1.0
        own = [y / 2.5, self.speed / SPEED_RANGE[1]]
        if self.x_progress:
            own.append(x / GOAL_X)  # corridor progress: the map pin
        step = np.concatenate(
            [p.reshape(-1), np.array(own, dtype=np.float32), prev]
        ).astype(np.float32)
        self.hist.append(step)
        return np.concatenate(self.hist)


def gate_bonus_hits(prev_xy, xy, fences, spent, pillar_r) -> list:
    """Fence indices newly threaded on the segment prev_xy -> xy.

    Mirrors the slalom exam predicate EXACTLY (same half-band
    (w + 2*pillar_r)/2, same linear interpolation of y at the plane,
    same first-crossing-only semantics): a training-time gate reward
    must pay for precisely what the exam metric counts as "through the
    gap", or shaping teaches a different task than the one judged.
    Any first crossing of a plane — inside or outside the gap — spends
    that fence (`spent` is mutated), so a detour can never bank the
    bonus by circling back."""
    (x0, y0), (x1, y1) = prev_xy, xy
    hits = []
    for i, (fx, yc, w) in enumerate(fences):
        if i in spent or not (x0 < fx <= x1):
            continue
        spent.add(i)
        f = (fx - x0) / max(x1 - x0, 1e-9)
        y = y0 + f * (y1 - y0)
        if abs(y - yc) < (w + 2.0 * pillar_r) / 2.0:
            hits.append(i)
    return hits


class WMPolicyEnv(gym.Env):
    """Gymnasium wrapper around the project's own closed-loop harness: the sim
    steps at 48 Hz under the PID VelCommander, the agent decides at 12 Hz, and
    everything the agent sees comes from the camera through the world model —
    pillar positions only stage and score, exactly like `run_episode`.
    `randomize=True` trains inside the storm (random pillar shapes, command
    latency, actuation noise, appearance jitter)."""

    metadata = {"render_modes": []}

    def __init__(
        self,
        seed0: int = 0,
        history: int = HISTORY,
        randomize: bool = False,
        edge_bias: bool = False,
        worlds: tuple = ("classic",),
        x_progress: bool = False,
        gate_bonus: float = 0.0,
        station_tick: float = 0.0,
    ):
        super().__init__()
        # station-mode reward shape (dodgeball K3 deviation): 0.0 keeps the
        # distal +50 survival bonus (K1); > 0 replaces it with a dense
        # per-decision tick paid only INSIDE the box — the mission pays
        # where it is held, not at a distal finish line.
        self.station_tick = float(station_tick)
        # per-gate task-structure reward (chain-learning campaign). 0.0 keeps
        # every existing recipe bit-identical; > 0 pays `gate_bonus` once per
        # fence threaded, judged by the SAME predicate as the slalom exam.
        self.gate_bonus = float(gate_bonus)
        self.env = make_env()
        # lazy import (planner <-> eval would cycle at module level); on a
        # fresh checkout / CI runner there is no output/world_model.pth, and
        # the self-contained rule is load_or_train, not FileNotFoundError
        from eval.eval_closed_loop import load_or_train

        self.enc, self.pred, self.cheads, self.nhead, self.meta = load_or_train()
        self.rng = np.random.default_rng(seed0)
        self.history = int(history)
        self.randomize = bool(randomize)
        self.edge_p = EDGE_P if edge_bias else 0.0
        self.worlds = resolve_worlds(worlds)
        self.x_progress = bool(x_progress)
        self._ep = 0
        self.scenario = None
        probe = ObsBuilder(
            self.enc,
            self.pred,
            self.cheads,
            self.meta,
            1.0,
            history=self.history,
            x_progress=self.x_progress,
        )
        self.obs_dim = probe.per_step * self.history
        self.observation_space = gym.spaces.Box(
            low=-np.inf, high=np.inf, shape=(self.obs_dim,), dtype=np.float32
        )
        self.action_space = gym.spaces.Discrete(probe.n_act)
        self.max_decisions = TMAX // DECIDE_EVERY

    def set_edge_p(self, p: float) -> None:
        """Curriculum hook: change the speed diet between training phases
        (called through the VecEnv, so it reaches past the Monitor wrapper)."""
        self.edge_p = float(p)

    def _frame(self) -> np.ndarray:
        frame = grab_frame(self.env)
        if self.randomize:  # appearance DR, per frame
            out = jitter(frame[None].astype(np.float32) / 255.0, self.rng)
            frame = (out[0] * 255.0).astype(np.uint8)
        return frame

    def reset(self, seed=None, options=None):
        if seed is not None:
            self.rng = np.random.default_rng(seed)
        scenario = int(self.rng.integers(2**31 - 1))
        obs, _ = self.env.reset(seed=scenario)
        self.cmd = VelCommander(make_ctrl(), self.env.CTRL_TIMESTEP)
        self.cmd.reset(obs[0][0:3])
        rng = np.random.default_rng(scenario)
        band = SPEED_RANGE
        if self.edge_p > 0.0 and self.rng.random() < self.edge_p:
            band = EDGE_RANGE
        speed = float(self.rng.uniform(*band))
        self._speed = speed
        world = self.worlds[self._ep % len(self.worlds)]
        self._ep += 1
        spec = get_scenario(world)
        if world == "classic":
            # mostly threatened, some clear — the distribution the tail lives in
            self.scenario = spec.spawn(
                self.env,
                rng,
                speed=speed,
                randomize=self.randomize,
                in_path=bool(self.rng.random() < 0.8),
            )
        else:
            self.scenario = spec.spawn(
                self.env, rng, speed=speed, randomize=self.randomize
            )
        self.pillars = self.scenario.positions()
        meta = getattr(self.scenario, "meta", None) or {}
        self._fences, self._spent = (), set()
        if self.gate_bonus:
            # lazy import (planner <-> skills would cycle at module level);
            # only fence-carrying worlds (the slaloms) ever pay the bonus
            from skills.gap_flight.skill import PILLAR_R

            self._pillar_r = PILLAR_R
            self._fences = tuple(meta.get("fences", ()))
        # station mode is carried by the WORLD, not a constructor knob:
        # ball-carrying worlds flip the episode's objective to survival
        # (the dodgeball campaign); every other world keeps the transit
        # reward bit-for-bit
        self._station = None
        if "balls" in meta:
            from skills.dodgeball.skill import BOX_BACK  # lazy, as above

            (sx, sy), (bx, by) = meta["station"], meta["box"]
            self._station = (sx, sy, bx, by, BOX_BACK)
        self.ob = ObsBuilder(
            self.enc,
            self.pred,
            self.cheads,
            self.meta,
            speed,
            history=self.history,
            x_progress=self.x_progress,
        )
        self.vecs = speed * ACTION_VECS
        self.lat = int(self.rng.integers(0, 3)) if self.randomize else 0
        self.pending = [FORWARD] * max(self.lat, 1)
        self.state = obs[0]
        self.prev_x = float(self.state[0])
        self.prev_y = float(self.state[1])
        self.decisions = 0
        return (
            self.ob.push(
                self._frame(), float(self.state[1]), 0, x=float(self.state[0])
            ),
            {},
        )

    def step(self, action: int):
        a_id = self.ob.ids[int(action)]
        self.pending.append(a_id)
        a_exec = self.pending.pop(0) if self.lat else self.pending.pop()
        d_min = np.inf
        for _ in range(DECIDE_EVERY):  # the PID flies 4 control steps per decision
            v = self.vecs[a_exec]
            if self.randomize:  # actuation wobbles; the intent stays clean
                v = v * (1.0 + self.rng.normal(0.0, 0.08, size=4))
            rpm = self.cmd.rpm(self.state, v)
            obs, _, _, _, _ = self.env.step(rpm.reshape(1, 4))
            self.state = obs[0]
            self.scenario.step()  # static worlds: no-op
            if self._station:
                # balls close at up to ~3.4 m/s relative: a per-decision
                # (12 Hz) check can tunnel through the 0.22 m ring that the
                # 48 Hz exam enforces — train on the exam's collision rule
                d_min = min(
                    d_min, nearest_planar(self.state[0:2], self.scenario.positions())
                )
        self.decisions += 1
        x, y = float(self.state[0]), float(self.state[1])
        d = (
            d_min
            if self._station
            else nearest_planar(self.state[0:2], self.scenario.positions())
        )

        if self._station:
            if self.station_tick > 0.0:
                sx, sy, bx, by, back = self._station
                inside = (sx - back <= x <= sx + bx) and abs(y - sy) <= by
                reward = self.station_tick if inside else -0.02
            else:
                reward = -0.02  # no progress term: the goal is time, not distance
        else:
            # progress, small time cost, crash, goal — and deliberately no
            # danger-shaping term (that is what we learn)
            reward = 25.0 * (x - self.prev_x) - 0.02
            if self._fences:
                hits = gate_bonus_hits(
                    (self.prev_x, self.prev_y),
                    (x, y),
                    self._fences,
                    self._spent,
                    self._pillar_r,
                )
                reward += self.gate_bonus * len(hits)
        self.prev_x = x
        self.prev_y = y
        terminated, truncated = False, False
        if d < COLLISION_R:
            reward -= 30.0
            terminated = True
        elif self._station:
            sx, sy, bx, by, back = self._station
            if x > sx + bx or x < sx - back or abs(y - sy) > by:
                truncated = True  # busted the box: forfeits the survival bonus
            elif self.decisions >= self.max_decisions:
                # survival IS the goal — `terminated`, not `truncated`: SB3
                # bootstraps gamma*V(s) onto truncations, which would
                # double-pay imagined future exactly here. The distal variant
                # pays +50 now; the dense variant already paid its ticks.
                if self.station_tick == 0.0:
                    reward += 50.0
                terminated = True
        elif x >= GOAL_X:
            reward += 50.0
            terminated = True
        elif abs(y) > 2.4 or self.decisions >= self.max_decisions:
            truncated = True

        next_obs = self.ob.push(self._frame(), y, int(action), x=x)
        return next_obs, float(reward), terminated, truncated, {}

    def close(self):
        self.env.close()


class LearnedPolicy:
    """The trained policy behind the same interface as WMPolicy /
    ReactivePolicy, so `run_episode` and every scoreboard can fly it
    unchanged. Vision only: frames -> world model -> memory (stacked history
    or the LSTM's hidden state) -> network -> one of five commands. The
    memory flavour and stack depth are inferred from the loaded model."""

    def __init__(self, model, enc, pred, cheads, meta, speed: float = 1.0):
        self.model = model
        self.recurrent = model.__class__.__name__ == "RecurrentPPO"
        obs_dim = int(model.observation_space.shape[0])
        per = ObsBuilder(enc, pred, cheads, meta, speed, history=1).per_step
        if obs_dim % per == 0:  # legacy layout (no map pin)
            history, xp = obs_dim // per, False
        elif obs_dim % (per + 1) == 0:  # x-progress layout
            history, xp = obs_dim // (per + 1), True
        else:
            raise SystemExit(f"unrecognized policy obs dim {obs_dim}")
        self.ob = ObsBuilder(
            enc, pred, cheads, meta, speed, history=history, x_progress=xp
        )
        self.i_fwd = self.ob.ids.index(FORWARD)
        self.prev = self.i_fwd
        self.lstm_state = None
        self.first = True

    def begin(self, pillars) -> None:
        del pillars  # vision only — same rule as WMPolicy
        self.ob.reset()
        self.prev = self.i_fwd
        self.lstm_state = None
        self.first = True

    def decide(self, frame: np.ndarray, state: np.ndarray) -> int:
        obs = self.ob.push(frame, float(state[1]), self.prev, x=float(state[0]))
        if self.recurrent:
            action, self.lstm_state = self.model.predict(
                obs,
                state=self.lstm_state,
                episode_start=np.array([self.first]),
                deterministic=True,
            )
            self.first = False
        else:
            action, _ = self.model.predict(obs, deterministic=True)
        self.prev = int(action)
        return self.ob.ids[self.prev]


def load_policy(path: str):
    if "_recurrent" in os.path.basename(path):
        from sb3_contrib import RecurrentPPO

        return RecurrentPPO.load(path)
    from stable_baselines3 import PPO

    return PPO.load(path)


def train(
    timesteps: int,
    seed0: int = 0,
    recurrent: bool = False,
    randomize: bool = False,
    edge_bias: bool = False,
    hard: bool = False,
    x_progress: bool = False,
    worlds: tuple | None = None,
    out: str = None,
    n_steps: int = 256,
    lstm_size: int = 64,
    gate_bonus: float = 0.0,
    station_tick: float = 0.0,
):
    from stable_baselines3.common.env_util import make_vec_env

    history = 1 if recurrent else HISTORY
    if worlds is not None:
        assert not hard, "pass either worlds= or hard=, not both"
        worlds = resolve_worlds(worlds)
        assert out is not None or set(worlds) <= {"classic", "dense", "moving"}, (
            "custom worlds need an explicit out= (the research runner path) — "
            "zip_path suffixes only encode the builtin presets"
        )
    else:
        worlds = ("classic", "dense", "moving") if hard else ("classic",)
    env = make_vec_env(
        lambda: WMPolicyEnv(
            seed0=seed0,
            history=history,
            randomize=randomize,
            edge_bias=edge_bias,
            worlds=worlds,
            x_progress=x_progress,
            gate_bonus=gate_bonus,
            station_tick=station_tick,
        ),
        n_envs=1,
    )
    if recurrent:
        from sb3_contrib import RecurrentPPO

        # A right-sized LSTM: the observation is 47 numbers, so the default
        # 256-wide hidden state is mostly empty capacity that slows learning.
        # n_steps=256 gives backprop-through-time a window longer than the
        # stacked variant's 12 decisions.
        model = RecurrentPPO(
            "MlpLstmPolicy",
            env,
            ent_coef=0.01,
            n_steps=n_steps,
            policy_kwargs=dict(lstm_hidden_size=lstm_size),
            seed=seed0,
            verbose=0,
        )
    else:
        from stable_baselines3 import PPO

        model = PPO("MlpPolicy", env, ent_coef=0.01, seed=seed0, verbose=0)
    model.learn(total_timesteps=timesteps)
    out = out or zip_path(recurrent, randomize, edge_bias, hard=hard, xp=x_progress)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    model.save(out)
    env.close()
    return model


def train_curriculum(
    timesteps: int,
    seed0: int = 0,
    out: str = None,
    n_steps: int = 256,
    lstm_size: int = 64,
):
    """The mixed-diet curriculum (recurrent only — the stack never needed it):
    one model, one total budget, three diets in sequence per `CURRICULUM`.
    Everything else matches `train(recurrent=True)`, so against the uniform
    and edge-biased runs the *order of the data* is the only variable.
    Measured verdict: it backfires — see the module docstring."""
    from sb3_contrib import RecurrentPPO
    from stable_baselines3.common.env_util import make_vec_env

    env = make_vec_env(lambda: WMPolicyEnv(seed0=seed0, history=1), n_envs=1)
    model = RecurrentPPO(
        "MlpLstmPolicy",
        env,
        ent_coef=0.01,
        n_steps=n_steps,
        policy_kwargs=dict(lstm_hidden_size=lstm_size),
        seed=seed0,
        verbose=0,
    )
    done = 0
    for i, (edge_p, share) in enumerate(CURRICULUM):
        last = i == len(CURRICULUM) - 1
        chunk = timesteps - done if last else int(round(timesteps * share))
        env.env_method("set_edge_p", edge_p)
        print(f"[INFO] curriculum phase {i + 1}: edge_p={edge_p}, {chunk} steps")
        model.learn(total_timesteps=chunk, reset_num_timesteps=False)
        done += chunk
    out = out or zip_path(recurrent=True, curr=True)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    model.save(out)
    env.close()
    return model


def selftest() -> None:
    env = WMPolicyEnv(seed0=7)
    obs, _ = env.reset()
    n_act = env.action_space.n
    per = env.obs_dim // HISTORY
    assert n_act == 5, f"menu should be 5 commands, got {n_act}"
    assert per == 5 * 8 + 2 + 5, f"per-step obs dim off ({per})"
    assert obs.shape == (env.obs_dim,), "stacked obs shape off"
    obs2, r, term, trunc, _ = env.step(0)
    assert obs2.shape == obs.shape and np.isfinite(r), "step broken"
    env.close()
    env = WMPolicyEnv(seed0=7, history=1, randomize=True)  # the storm
    obs, _ = env.reset()
    assert obs.shape == (env.obs_dim,) and env.obs_dim == per, "randomized env off"
    env.step(0)
    env.close()
    paths = {
        zip_path(),
        zip_path(True),
        zip_path(True, True),
        zip_path(True, False, True),
        zip_path(True, False, False, True),
    }
    assert len(paths) == 5, "zip suffixes clash"
    # smoke-train all three flavours (wiring, not skill) — into _selftest zips,
    # so a real trained policy is never clobbered by a selftest
    st = os.path.join(_ROOT, "output", "ppo_wm_policy_selftest.zip")
    st_r = os.path.join(_ROOT, "output", "ppo_wm_policy_selftest_rnn.zip")
    st_c = os.path.join(_ROOT, "output", "ppo_wm_policy_selftest_curr.zip")
    train(1500, seed0=7, out=st)
    train(1024, seed0=7, recurrent=True, out=st_r)
    train_curriculum(768, seed0=7, out=st_c)  # one 256-step rollout per diet
    assert os.path.exists(st) and os.path.exists(st_r) and os.path.exists(st_c)
    print(
        f"LEARNED-POLICY-MODULE OK: obs={HISTORY}x{per} stacked (or 1x{per} + "
        f"LSTM), 5 actions, smoke-trained stacked/LSTM/curriculum, saved {st}"
    )


if __name__ == "__main__":
    selftest()

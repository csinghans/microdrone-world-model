"""World-model-driven complete-coverage policy — RL on the WM latent.

The owner's directive: "coverage matters, not room count; FIRST use the
world model to completely cover the indoor space by flying." This is the
first time the world model DRIVES a task (transit safety went to cheap
rangefinders; coverage went to the geometric Frontier). Architecture
(owner-chosen): RL on the WM latent.

Division of labour (fixed by the search_wm_v3 verdict — the WM's place in
indoor search is coverage/where-to-go reasoning, NOT collision):
  * collision safety   -> the deployable beams8 rangefinder veto (never
    learned; wraps every executed action).
  * WM (this module)   -> a *where-to-go* signal: per-nav-action collision
    probabilities read from the camera (openness ahead of each move).
  * spatial memory     -> an egocentric covered/occupancy grid (the WM
    latent is local; the dispatch arc proved spatial identity is not in
    the threat channel). Built from odometry + the beam ring — deployable,
    O(cells) SRAM.

Layout mirrors `planner/learned_policy.py` (ObsBuilder shared verbatim by
the training env and the deployed policy): `CoverageMemory`,
`NavObsBuilder`, `CoverageEnv`, `CoveragePolicy`, `train`, `selftest`.

The `wm_off` flag zeroes the 40 WM slots and skips the WM forward pass —
the ablation arm that isolates whether the world model actually buys
coverage over the grid alone (search_roomgraph found the beam-occupancy
signal partly duplicates the WM collision probs; this measures it).
"""

import gymnasium as gym
import numpy as np

from planner.latent_mpc import DECIDE_EVERY, _frame_tensor
from planner.nav_action_set import HOVER, NAV_ACTION_VECS, nav_menu
from sim.scenarios import COLLISION_R
from sim.search_scenario import remove_bodies

GRID_R = 5  # egocentric window half-width in cells -> 11x11
N_MENU = 5  # nav_menu(): forward / reverse / strafe_L / strafe_R / hover
N_PROBS = 8  # 4 horizons x 2 rings (warn/crit) per candidate
WM_DIM = N_MENU * N_PROBS  # 40 collision probs
GRID_DIM = (2 * GRID_R + 1) ** 2 * 2  # 242 (covered + occupancy channels)
OBS_DIM = WM_DIM + GRID_DIM + 4 + N_MENU + 1 + 1  # 293


class CoverageMemory:
    """Egocentric covered+occupancy grid from odometry + the beam ring.

    Two world-cell dicts (keyed by integer (i,j) cell index relative to the
    room's grid origin — the drone knows this from odometry off its start):
      * `covered`: cells the drone has been within `sensor_range` of.
      * `occ`: cells the beam ring has seen through (+1 free) or hit (-1).
    Deployable: no ground truth, just odometry + `beam_ranges`. The
    egocentric read (yaw==0, so the window is a plain index offset, no
    rotation) is the policy's spatial memory."""

    def __init__(self, scenario, n_beams=8):
        self.cell = float(scenario.cell)
        self.x0, _, self.y0, _ = scenario.bounds
        self.sensor = float(scenario.sensor_range)
        self.n_beams = n_beams
        self.covered = set()
        self.occ = {}

    def _cell(self, x, y):
        return (int((x - self.x0) / self.cell), int((y - self.y0) / self.cell))

    def update(self, scenario, pos):
        x, y = float(pos[0]), float(pos[1])
        ci, cj = self._cell(x, y)
        # covered: every grid cell within sensor_range of the drone
        r = int(self.sensor / self.cell) + 1
        for di in range(-r, r + 1):
            for dj in range(-r, r + 1):
                cx = self.x0 + (ci + di + 0.5) * self.cell
                cy = self.y0 + (cj + dj + 0.5) * self.cell
                if (cx - x) ** 2 + (cy - y) ** 2 <= self.sensor**2:
                    self.covered.add((ci + di, cj + dj))
        # occupancy: mark cells along each beam ray free, the hit cell blocked
        for ang, dist in scenario.beam_ranges(pos, n_beams=self.n_beams):
            ux, uy = np.cos(ang), np.sin(ang)
            steps = int(dist / (self.cell * 0.5)) + 1
            for k in range(steps):
                d = min(dist, k * self.cell * 0.5)
                c = self._cell(x + ux * d, y + uy * d)
                if c not in self.occ:
                    self.occ[c] = 1.0  # seen-through -> free
            if dist < 2.99:  # a real hit (not a max-range miss) -> blocked
                self.occ[self._cell(x + ux * dist, y + uy * dist)] = -1.0

    def egocentric(self, pos):
        """(2, 11, 11) covered/occupancy window centred on the drone."""
        ci, cj = self._cell(float(pos[0]), float(pos[1]))
        n = 2 * GRID_R + 1
        cov = np.zeros((n, n), dtype=np.float32)
        occ = np.zeros((n, n), dtype=np.float32)
        for di in range(-GRID_R, GRID_R + 1):
            for dj in range(-GRID_R, GRID_R + 1):
                key = (ci + di, cj + dj)
                cov[di + GRID_R, dj + GRID_R] = 1.0 if key in self.covered else 0.0
                occ[di + GRID_R, dj + GRID_R] = self.occ.get(key, 0.0)
        return np.stack([cov, occ])


class NavObsBuilder:
    """Builds the 293-d coverage observation, shared by the env and the
    deployed policy (the ObsBuilder discipline). WM collision probs over the
    5 nav candidates + egocentric grid + 4 beams + prev-action + covered
    fraction + speed. `wm_off` zeroes the WM block and skips its forward
    pass (the ablation)."""

    def __init__(self, enc, pred, cheads, meta, speed, wm_off=False):
        import torch

        self.torch = torch
        self.enc, self.pred, self.cheads = enc, pred, cheads
        self.wm_off = wm_off
        a_norm = np.array(meta["a_norm"], dtype=np.float32)
        # nav candidates, normalized by the MODEL's a_norm (v3 probe
        # convention — NOT nav_action_set.A_NORM — or train/deploy diverge)
        menu = nav_menu()
        cands = NAV_ACTION_VECS[menu] * float(speed) / a_norm
        self.cands = torch.tensor(cands, dtype=torch.float32)
        self.menu = menu

    def wm_probs(self, frame):
        if self.wm_off or frame is None:
            return np.zeros(WM_DIM, dtype=np.float32)
        torch = self.torch
        with torch.no_grad():
            z = self.enc(_frame_tensor(frame))
            zc = z.expand(len(self.cands), -1)
            z_hat = self.pred(zc, self.cands, base=zc)
            p = torch.sigmoid(self.cheads(z_hat)).numpy()  # (5, H, 2)
        return p.reshape(-1).astype(np.float32)  # 40

    def build(self, frame, mem, pos, ranges, prev_action, covered_fraction, speed):
        wm = self.wm_probs(frame)  # 40
        grid = mem.egocentric(pos).reshape(-1)  # 242
        beams = np.array(
            [min(ranges[k], 3.0) / 3.0 for k in ("+x", "-x", "+y", "-y")],
            dtype=np.float32,
        )  # 4
        prev = np.zeros(N_MENU, dtype=np.float32)
        if prev_action in self.menu:
            prev[self.menu.index(prev_action)] = 1.0
        tail = np.array([covered_fraction, speed], dtype=np.float32)
        return np.concatenate([wm, grid, beams, prev, tail]).astype(np.float32)


def _load_wm(ckpt=None):
    """The shipped champion WM (ckpt=None) or a nav-retrained checkpoint."""
    if ckpt:
        from world_model.training import load_model

        return load_model(ckpt, device="cpu")
    from eval.eval_closed_loop import load_or_train

    return load_or_train(device="cpu")


def _rooms(seed, mix):
    """Rotate rooms for training: `mix` fractions of clean single vs
    cluttered n_room (the coverage win lives in clutter, but clean anchors
    the sweep behaviour)."""
    from sim.indoor.rooms import n_room, single_room

    r = (seed * 2654435761) % 1000 / 1000.0  # cheap deterministic pick
    if r < mix:
        return n_room(seed, n_rooms=3, clutter=2, clutter_lane=0.0)
    return single_room(seed)


class CoverageEnv(gym.Env):
    """Gym env: learn to COVER a rendered room from WM perception + the
    coverage grid, safety on beams8. Reward = dense coverage delta − step
    cost − crash; episode ends when coverage plateaus/threshold (done) or
    crash or budget. The return-home leg is delegated to the deploy runner
    (this env trains only the hard part: covering)."""

    metadata = {"render_modes": []}

    def __init__(
        self,
        seed0=500000,
        clutter_mix=0.5,
        speed=0.6,
        ckpt=None,
        wm_off=False,
        coverage_threshold=0.95,
        plateau=100,
        max_decisions=800,
        w_cov=50.0,
        step_cost=0.02,
        crash_pen=30.0,
    ):
        from sim.envs import make_env

        self.env = make_env()
        self.body_ids = None
        if wm_off:  # grid-only ablation: no camera, no WM load (fast + CI-safe)
            self.enc = self.pred = self.cheads = None
            self.meta = {"a_norm": [1.0, 1.0, 1.0, 1.0]}
        else:
            self.enc, self.pred, self.cheads, _n, self.meta = _load_wm(ckpt)
        self.speed = float(speed)
        self.wm_off = bool(wm_off)
        self.clutter_mix = clutter_mix
        self.coverage_threshold = coverage_threshold
        self.plateau = plateau
        self.max_decisions = max_decisions
        self.w_cov, self.step_cost, self.crash_pen = w_cov, step_cost, crash_pen
        self._seed0, self._ep = seed0, 0
        self.render_room = not wm_off  # grid-only ablation needs no camera
        self.action_space = gym.spaces.Discrete(N_MENU)
        self.observation_space = gym.spaces.Box(-np.inf, np.inf, (OBS_DIM,), np.float32)
        self.menu = nav_menu()

    def _room_xy(self, state):
        sx, sy = self.scenario.start_xy
        from sim.envs import START

        return (float(state[0]) + sx - START[0], float(state[1]) + sy - START[1])

    def reset(self, *, seed=None, options=None):
        from sim.envs import START, VelCommander, grab_frame, make_ctrl

        seed = self._seed0 + self._ep if seed is None else seed
        self._ep += 1
        self.scenario = _rooms(seed, self.clutter_mix)
        if self.body_ids:  # clear the previous episode's visual bodies
            remove_bodies(self.env, self.body_ids)
            self.body_ids = None
        obs, _ = self.env.reset(seed=int(seed))
        self.cmd = VelCommander(make_ctrl(), self.env.CTRL_TIMESTEP)
        self.cmd.reset(obs[0][0:3])
        sx, sy = self.scenario.start_xy
        if self.render_room:
            self.body_ids = self.scenario.spawn_bodies(
                self.env, offset=(sx - START[0], sy - START[1])
            )
        self.state = obs[0]
        self.mem = CoverageMemory(self.scenario)
        self.obb = NavObsBuilder(
            self.enc, self.pred, self.cheads, self.meta, self.speed, self.wm_off
        )
        self.free = np.asarray(self.scenario.free_cells(), dtype=float)
        self.covmask = np.zeros(len(self.free), dtype=bool)
        self.prev_a = HOVER
        self.d, self.no_gain, self.prev_cov = 0, 0, 0.0
        rpos = self._room_xy(self.state)
        self._mark(rpos)
        self.mem.update(self.scenario, rpos)
        frame = grab_frame(self.env) if self.render_room else None
        if self.render_room:
            assert float(np.std(frame)) > 5.0, "blank frame — room not rendered"
        return self._obs(frame, rpos), {}

    def _mark(self, pos):
        if len(self.free):
            self.covmask[
                np.linalg.norm(self.free - np.asarray(pos), axis=1)
                <= self.scenario.sensor_range
            ] = True

    def _cov(self):
        return float(self.covmask.mean()) if len(self.free) else 0.0

    def _obs(self, frame, rpos):
        return self.obb.build(
            frame,
            self.mem,
            rpos,
            self.scenario.range_sensors(rpos),
            self.prev_a,
            self._cov(),
            self.speed,
        )

    def step(self, action):
        from eval.search_episode import _SAFETY
        from sim.envs import grab_frame

        beams8 = _SAFETY["beams8"]
        rpos = self._room_xy(self.state)
        proposed = self.menu[int(action)]
        a = beams8(self.scenario, rpos, proposed)
        vec = self.speed * NAV_ACTION_VECS[a]
        crashed = False
        for _ in range(DECIDE_EVERY):
            o, _, _, _, _ = self.env.step(self.cmd.rpm(self.state, vec).reshape(1, 4))
            self.state = o[0]
            if self.scenario.clearance(self._room_xy(self.state)) < COLLISION_R:
                crashed = True
                break
        self.prev_a = a
        self.d += 1
        rpos = self._room_xy(self.state)
        c0 = self._cov()
        self._mark(rpos)
        self.mem.update(self.scenario, rpos)
        c1 = self._cov()
        reward = self.w_cov * (c1 - c0) - self.step_cost
        if c1 > self.prev_cov + 1e-9:
            self.no_gain, self.prev_cov = 0, c1
        else:
            self.no_gain += 1
        terminated, truncated = False, False
        if crashed:
            reward -= self.crash_pen
            terminated = True
        elif c1 >= self.coverage_threshold or self.no_gain >= self.plateau:
            terminated = True  # covered what it could — the coverage goal
        elif self.d >= self.max_decisions:
            truncated = True
        frame = grab_frame(self.env) if self.render_room else None
        return (
            self._obs(frame, rpos),
            float(reward),
            terminated,
            truncated,
            {"coverage": c1},
        )

    def close(self):
        try:
            self.env.close()
        except Exception:
            pass


class CoveragePolicy:
    """Deploy wrapper for a trained coverage policy — `wants_frame=True` so
    `run_coverage_episode` renders the room and taps the camera. Mirrors
    LearnedPolicy: begin(scenario) resets the egocentric memory; decide(ctx)
    builds the 293-d obs and calls model.predict."""

    wants_frame = True

    def __init__(self, zip_path, ckpt=None, speed=0.6, wm_off=False):
        from stable_baselines3 import PPO

        self.model = PPO.load(zip_path, device="cpu")
        self.enc, self.pred, self.cheads, _n, self.meta = _load_wm(ckpt)
        self.speed, self.wm_off = float(speed), bool(wm_off)

    def begin(self, scenario):
        self._sc = scenario  # kept for the memory's beam-ring occupancy update
        self.mem = CoverageMemory(scenario)
        self.obb = NavObsBuilder(
            self.enc, self.pred, self.cheads, self.meta, self.speed, self.wm_off
        )
        self.menu = nav_menu()
        self.prev_a = HOVER

    def decide(self, ctx):
        pos = ctx["pos"]
        self.mem.update(self._sc, pos)
        obs = self.obb.build(
            ctx.get("frame"),
            self.mem,
            pos,
            ctx["ranges"],
            self.prev_a,
            ctx.get("covered_fraction", 0.0),
            self.speed,
        )
        a, _ = self.model.predict(obs, deterministic=True)
        self.prev_a = self.menu[int(a)]
        return self.prev_a


def train(
    out, timesteps=300_000, wm_off=False, ckpt=None, clutter_mix=0.5, seed0=500000
):
    """PPO on CoverageEnv. `wm_off=True` trains the grid-only ablation."""
    from stable_baselines3 import PPO

    env = CoverageEnv(seed0=seed0, clutter_mix=clutter_mix, wm_off=wm_off, ckpt=ckpt)
    model = PPO("MlpPolicy", env, ent_coef=0.01, verbose=0)
    model.learn(total_timesteps=timesteps)
    model.save(out)
    env.close()
    return out


def selftest() -> None:
    # wm_off (grid-only) path: exercises env/obs/reward/memory/render-skip
    # without loading the champion WM (fast + CI-safe). The WM path (40
    # real probs) is exercised by the G1 smoke-train / Phase-2 gate.
    env = CoverageEnv(max_decisions=8, clutter_mix=0.0, wm_off=True)
    obs, _ = env.reset(seed=500000)
    assert obs.shape == (OBS_DIM,), obs.shape
    assert np.all(np.isfinite(obs)), "obs finite"
    fwd = env.menu.index(nav_menu()[0])  # forward
    tot = 0.0
    c_start = env._cov()
    for _ in range(6):
        obs, r, term, trunc, info = env.step(fwd)
        tot += r
        assert np.isfinite(r) and obs.shape == (OBS_DIM,)
        if term or trunc:
            break
    assert env._cov() >= c_start, "coverage does not decrease"
    env.close()
    print(
        f"COVERAGE-POLICY OK: obs {OBS_DIM}-d finite, reward finite, "
        f"coverage {c_start:.2f}->{env._cov():.2f} over a forward sweep"
    )


if __name__ == "__main__":
    selftest()

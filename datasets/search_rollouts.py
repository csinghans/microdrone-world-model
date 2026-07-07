"""Intervention rollouts for the Indoor Active Search world model (Phase 1b).

The transit dataset (`generate_rollouts`) taught the world model thin
pillars; the transfer probe showed it is BLIND TO WALLS head-on
(forward AUC 0.48 in rooms) while fine on box obstacles. This generator
produces the missing diet: the drone approaches WALLS and boxes under
held TRANSLATIONAL nav commands, so the encoder learns the wall
appearance and the collision heads learn wall proximity for the nav
action set.

Same npz schema as `generate_rollouts` (so `as_pairs` and
`world_model.training` consume it unchanged), with three deliberate
differences:

  * **World = a single search room** (walls + box obstacles), not a
    pillar corridor. `dists` stores `SearchScenario.clearance()` — the
    distance to the nearest wall OR obstacle SURFACE — so the danger
    label (`dist < DANGER_R`) fires on walls, which `nearest_planar`
    to pillar centres never could.
  * **Actions = the nav vocabulary** (forward/reverse/strafe/slow/
    hover), recorded normalized by the SAME a_norm the WM expects.
  * **No safety filter, varied in-room starts.** Each rollout re-homes
    the room around a random safe start (the coordinate-offset trick,
    no teleport) and flies a random held-command schedule straight at
    whatever is there — so "forward INTO a wall -> danger" is actually
    in the data (a safety filter would veto exactly those pairs).

Run:
  python -m datasets.search_rollouts --rollouts 96 --len 150
  python -m datasets.search_rollouts --selftest
Saves output/search_dataset.npz (git-ignored).
"""

import argparse
import os
import sys

import numpy as np

from datasets.intervention_labels import H_MAX, HORIZONS
from planner.action_set import A_NORM
from planner.nav_action_set import NAV_ACTION_NAMES, NAV_ACTION_VECS
from sim.envs import IMG_RES, START, VelCommander, grab_frame, make_ctrl, make_env
from sim.indoor.rooms import single_room
from sim.scenarios import DANGER_R

OUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "output",
    "search_dataset.npz",
)
# collection speed sampled per rollout so the WM sees nav actions across
# speeds; brackets the Phase-1a flight speed (0.36 m/s). Capped at 1.0 so a
# full held segment doesn't fly clear across the room before switching.
SPEED_LO, SPEED_HI = 0.6, 1.0
# segments MUST exceed H_MAX (32): a k=32 training window has to fit inside
# one held command, or `window_valid` yields ZERO samples (measured — an
# earlier 24-step hold produced an empty index and a 1-D-array crash).
SEG_MIN, SEG_MAX = H_MAX + 8, H_MAX + 32


def _nav_schedule(rng, length):
    """Held segments of random nav commands (the counterfactual-contrast
    recipe: keep a command for a stretch, then switch). Each hold exceeds
    H_MAX so k-step windows are valid."""
    act_id = np.zeros(length, dtype=np.int16)
    seg = np.zeros(length, dtype=np.int16)
    t, s = 0, 1
    while t < length:
        a = int(rng.integers(0, len(NAV_ACTION_VECS)))
        n = int(rng.integers(SEG_MIN, SEG_MAX + 1))
        act_id[t : t + n] = a
        seg[t : t + n] = s
        t += n
        s += 1
    return act_id, seg


def _safe_start(sc, rng):
    """A random room point with clearance > 0.6 m (a fair launch spot)."""
    x0, x1, y0, y1 = sc.bounds
    for _ in range(100):
        p = (
            float(rng.uniform(x0 + 0.6, x1 - 0.6)),
            float(rng.uniform(y0 + 0.6, y1 - 0.6)),
        )
        if sc.clearance(p) > 0.6:
            return p
    return sc.start_xy


def gen(n_rollouts, length, seed=0):
    env = make_env()
    cmd = VelCommander(make_ctrl(), env.CTRL_TIMESTEP)
    rng = np.random.default_rng(seed)
    R, L = n_rollouts, length

    frames = np.zeros((R, L, IMG_RES, IMG_RES, 3), dtype=np.uint8)
    actions = np.zeros((R, L, 4), dtype=np.float32)
    act_id = np.zeros((R, L), dtype=np.int16)
    seg = np.zeros((R, L), dtype=np.int16)
    dists = np.zeros((R, L), dtype=np.float32)
    pos = np.zeros((R, L, 3), dtype=np.float32)
    rollout_speed = np.zeros(R, dtype=np.float32)

    for r in range(R):
        sc = single_room(int(rng.integers(2**31 - 1)))
        start = _safe_start(sc, rng)
        # re-home the room around this start (env origin == start), so the
        # drone launches from a varied in-room spot without teleporting
        ox, oy = start[0] - START[0], start[1] - START[1]
        obs, _ = env.reset(seed=int(rng.integers(2**31 - 1)))
        cmd.reset(obs[0][0:3])
        act_id[r], seg[r] = _nav_schedule(rng, L)
        v_speed = float(rng.uniform(SPEED_LO, SPEED_HI))
        rollout_speed[r] = v_speed
        state = obs[0]
        for t in range(L):
            frames[r, t] = grab_frame(env)
            pos[r, t] = state[0:3]
            rpos = (float(state[0]) + ox, float(state[1]) + oy)
            dists[r, t] = sc.clearance(rpos)
            v = v_speed * NAV_ACTION_VECS[act_id[r, t]]
            actions[r, t] = v
            obs, _, _, _, _ = env.step(cmd.rpm(state, v).reshape(1, 4))
            state = obs[0]
        near = float((dists[r] < DANGER_R).mean())
        print(f"  rollout {r + 1}/{R} (room, near-wall frac {near:.2f})", flush=True)

    env.close()
    return {
        "frames": frames,
        "actions": actions,
        "act_id": act_id,
        "seg": seg,
        "dists": dists,
        "pos": pos,
        "speed": rollout_speed,
        "horizons": np.array(HORIZONS, dtype=np.int16),
        "a_norm": A_NORM,
        "danger_r": np.float32(DANGER_R),
        "nav_action_names": np.array(NAV_ACTION_NAMES),
        # compatibility keys so world_model.training consumes this npz
        # unchanged: one "room" world; all-NaN pillars so the (transit-only)
        # veer-ranking probe finds no pillar and is skipped cleanly.
        "world_id": np.zeros(R, dtype=np.int16),
        "world_names": np.array(["room"]),
        "pillars": np.full((R, 8, 2), np.nan, dtype=np.float32),
        "pillar_vel": np.zeros((R, 8, 2), dtype=np.float32),
        "in_path": np.ones(R, dtype=bool),
    }


def selftest() -> None:
    data = gen(3, 90, seed=0)
    assert data["frames"].shape == (3, 90, IMG_RES, IMG_RES, 3)
    assert data["actions"].shape == (3, 90, 4)
    # nav actions include reverse (vx<0) and pure strafe (vx==0, vy!=0)
    seen = {tuple(np.sign(a[:2])) for a in data["actions"].reshape(-1, 4)}
    assert any(sx < 0 for sx, _ in seen), "reverse recorded"
    # dists are surface clearances (can go <=0 if a rollout exits a wall)
    assert data["dists"].min() < DANGER_R, "some frames are near a wall/obstacle"
    # as_pairs consumes it unchanged (schema compatibility)
    from datasets.generate_rollouts import as_pairs

    pairs = as_pairs(data, k=4)
    assert "X" in pairs and "c" in pairs
    print(
        f"SEARCH-ROLLOUTS OK: schema matches generate_rollouts, nav actions "
        f"recorded, as_pairs -> {len(pairs['c'])} k=4 windows"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rollouts", type=int, default=96)
    ap.add_argument("--len", type=int, default=150)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    data = gen(args.rollouts, args.len, args.seed)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    np.savez_compressed(args.out, **data)
    near = float((data["dists"] < DANGER_R).mean())
    print(
        f"SEARCH-DATA OK: {args.rollouts} rollouts x {args.len} steps, "
        f"near-wall frac {near:.2f}, saved {args.out}"
    )


if __name__ == "__main__":
    sys.exit(main())

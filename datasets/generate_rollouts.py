"""Self-produce an *intervention* dataset for the world model.

A frame-to-label mapping can be learned from single images. A world model is
different: it learns how the world *changes* — and, crucially, how it changes
*because of what you do*. So the data is no longer single frames, and it is
no longer passive footage either. Each rollout is a tiny controlled
experiment:

  1. **Fresh trial.** The simulator is reset every rollout (drone back at the
     start, PID integrators cleared), so all rollouts really are independent
     passes through a fresh pillar layout — not one long drifting flight.
  2. **Approach.** The drone cruises forward under a *commanded* velocity
     setpoint (the same "forward" command the controller will use later).
  3. **Interventions.** The rest of the flight is a chain of held *segments*:
     every ~1 s we draw one of six high-level commands and **hold it** for
     the whole segment before drawing the next.

Holding the command is the whole point. A world model that must answer "what
happens if I *keep doing this* for the next k steps?" needs training pairs
where one action really was kept for k steps — and every segment switch is
one more counterfactual contrast ("same view, different command, different
outcome"), which is exactly the action-conditioning a planner needs.

No pixel target anywhere: training predicts in *latent* space. This file only
stores raw frames + held commands + distances (+ the pillar layout, used for
labels and evaluation — never for control).

Run:
  python -m datasets.generate_rollouts --rollouts 64 --len 120
  python -m datasets.generate_rollouts --selftest   # tiny, asserts
Saves output/wm_dataset.npz (git-ignored).
"""

import argparse
import os
import sys

import numpy as np

from datasets.intervention_labels import H_MAX, HORIZONS, window_valid
from planner.action_set import A_NORM, ACTION_NAMES, ACTION_VECS, FORWARD, SPEED_RANGE
from sim.envs import (
    CTRL_HZ,
    IMG_RES,
    START,
    VelCommander,
    grab_frame,
    make_ctrl,
    make_env,
)
from sim.scenarios import DANGER_R, nearest_planar, spawn_pillars

OUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "output",
    "wm_dataset.npz",
)


def _schedule(rng, length: int, passive: bool):
    """Per-step (action-id, segment-id) arrays for one rollout: an all-forward
    approach, then ~1 s held segments each drawing a fresh random command."""
    ids = np.full(length, FORWARD, dtype=np.int16)
    seg = np.zeros(length, dtype=np.int16)
    if passive:
        return ids, seg
    t, s = int(rng.integers(24, 49)), 0
    while t < length:
        s += 1
        n = int(rng.integers(H_MAX + 8, H_MAX + 25))  # hold 40..56 steps (~1 s)
        ids[t : t + n] = int(rng.integers(0, len(ACTION_NAMES)))
        seg[t : t + n] = s
        t += n
    return ids, seg


def gen(n_rollouts: int, length: int, seed: int = 0, randomize: bool = False) -> dict:
    """Fly `n_rollouts` fresh intervention trials and return the raw sequences:
    frames (uint8), held commands, nearest-pillar distances, drone positions,
    plus per-rollout metadata (pillar layout, per-step segment ids, in-path
    flag).

    `randomize=True` randomizes the *plant* as well as the scene: random
    pillar shape/colour, 0-2 control steps of command latency, and ±8 %
    per-step actuation noise on the executed command. The RECORDED action
    stays the clean commanded one — the model conditions on intent, reality
    wobbles, and the labels come from where the drone really went — which is
    precisely the robustness a deployed controller needs."""
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
    pillars_meta = np.full((R, 3, 2), np.nan, dtype=np.float32)
    in_path = np.zeros(R, dtype=bool)
    speed = np.zeros(R, dtype=np.float32)

    for r in range(R):
        obs, _ = env.reset(seed=int(rng.integers(2**31 - 1)))
        cmd.reset(START)
        in_path[r] = r % 2 == 0
        speed[r] = rng.uniform(*SPEED_RANGE)
        pillars = spawn_pillars(env, rng, in_path=bool(in_path[r]), randomize=randomize)
        pillars_meta[r, : len(pillars)] = pillars
        act_id[r], seg[r] = _schedule(rng, L, passive=(r % 3 == 2))
        lat = int(rng.integers(0, 3)) if randomize else 0

        state = obs[0]
        for t in range(L):
            frames[r, t] = grab_frame(env)
            pos[r, t] = state[0:3]
            dists[r, t] = nearest_planar(state[0:2], pillars)
            actions[r, t] = speed[r] * ACTION_VECS[act_id[r, t]]  # the intent
            # ... while the *executed* command may lag and wobble (randomize)
            v_exec = speed[r] * ACTION_VECS[act_id[r, max(t - lat, 0)]]
            if randomize:
                v_exec = v_exec * (1.0 + rng.normal(0.0, 0.08, size=4))
            obs, _, _, _, _ = env.step(cmd.rpm(state, v_exec).reshape(1, 4))
            state = obs[0]
        held = sorted({ACTION_NAMES[i] for i in act_id[r][seg[r] > 0]})
        print(
            f"  rollout {r + 1}/{R} ({'in-path' if in_path[r] else 'clear'}, "
            f"{speed[r]:.2f}x, "
            f"{'passive' if seg[r].max() == 0 else '+'.join(held)})"
        )

    env.close()
    return {
        "frames": frames,
        "actions": actions,
        "act_id": act_id,
        "seg": seg,
        "dists": dists,
        "pos": pos,
        "pillars": pillars_meta,
        "in_path": in_path,
        "speed": speed,
        "randomized": np.uint8(randomize),
        "horizons": np.array(HORIZONS, dtype=np.int16),
        "a_norm": A_NORM,
        "danger_r": np.float32(DANGER_R),
    }


def as_pairs(data: dict, k: int) -> dict:
    """Slice the sequence format into single-horizon (X, Xk, A, c) triples —
    only windows where the command was genuinely held for all k steps."""
    F, A, D = data["frames"], data["actions"], data["dists"]
    R, L = F.shape[:2]
    X, Xk, Aout, c = [], [], [], []
    for r in range(R):
        for t in range(L - k):
            if not window_valid(data["seg"][r], t, k):
                continue
            X.append(F[r, t])
            Xk.append(F[r, t + k])
            Aout.append(A[r, t] / A_NORM)
            c.append(1.0 if float(D[r, t : t + k + 1].min()) < DANGER_R else 0.0)
    return {
        "X": np.array(X, dtype=np.float32) / 255.0,
        "Xk": np.array(Xk, dtype=np.float32) / 255.0,
        "A": np.array(Aout, dtype=np.float32),
        "c": np.array(c, dtype=np.float32),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rollouts", type=int, default=32)
    ap.add_argument("--len", dest="length", type=int, default=120)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--randomize", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    n_roll, length = (10, 100) if args.selftest else (args.rollouts, args.length)

    tag = " (randomized)" if args.randomize else ""
    print(f"[INFO] flying {n_roll} intervention rollouts x {length} steps{tag} ...")
    data = gen(n_roll, length, seed=args.seed, randomize=args.randomize)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    np.savez_compressed(OUT, **data)

    rates = {}
    for k in HORIZONS:
        pairs = as_pairs(data, k)
        rates[k] = (len(pairs["c"]), float(pairs["c"].mean()))
    rate_str = ", ".join(f"k={k}: n={n} pos={p:.2f}" for k, (n, p) in rates.items())
    n_seg = int(sum(data["seg"][r].max() for r in range(n_roll)))
    held = sorted({ACTION_NAMES[i] for r in range(n_roll) for i in data["act_id"][r]})
    print(
        f"WM-DATA OK: {n_roll} rollouts x {length} steps @ {CTRL_HZ} Hz, "
        f"{n_seg} held intervention segments, labels [{rate_str}], saved {OUT}"
    )
    print(f"  commands held: {held}")

    if args.selftest:
        assert data["frames"].dtype == np.uint8, "frames must be uint8"
        assert data["frames"].shape[2:] == (IMG_RES, IMG_RES, 3), "bad frame shape"
        # every rollout must really restart at START
        drift = np.abs(data["pos"][:, 0, :] - START).max()
        assert drift < 0.1, f"rollouts do not reset to START (drift {drift:.2f} m)"
        # commands are commanded, not measured: they must live on the action set
        env_max = np.abs(ACTION_VECS).max() * SPEED_RANGE[1]
        assert np.abs(data["actions"]).max() <= env_max + 1e-6
        # speed diversity is the point: the same command set flown at many paces
        assert data["speed"].max() - data["speed"].min() > 0.3, "speeds too uniform"
        assert n_seg >= n_roll, "too few held segments for counterfactual contrast"
        assert len(held) >= 4, f"too little action diversity ({held})"
        for k, (n, p) in rates.items():
            assert n > 0, f"no valid windows at k={k}"
            assert 0.03 < p < 0.97, f"labels too imbalanced at k={k} ({p:.2f})"


if __name__ == "__main__":
    main()
    sys.exit(0)

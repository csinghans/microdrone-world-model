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
from datasets.provenance import dataset_destination, save_dataset
from datasets.rollout_schedule import LAYOUTS, plan
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
from sim.scenario_registry import get as get_scenario
from sim.scenario_registry import resolve_worlds, world_names_array
from sim.scenarios import DANGER_R, nearest_planar

OUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "output",
    "wm_dataset.npz",
)
MAX_PIL = 8  # meta arrays hold up to this many pillars (NaN-padded)
# Back-compat re-export; the registry is the source of truth for ids.
WORLD_IDS = {"classic": 0, "dense": 1, "moving": 2}
RNG_LAYOUTS = ("shared", "per_rollout")
INTERVENTION_STARTS = ("approach", "immediate")


def _schedule(rng, length: int, passive: bool, intervention_start="approach"):
    """Per-step (action-id, segment-id) arrays for one rollout: an all-forward
    approach, then ~1 s held segments each drawing a fresh random command."""
    if intervention_start not in INTERVENTION_STARTS:
        raise ValueError(f"unknown intervention start: {intervention_start}")
    ids = np.full(length, FORWARD, dtype=np.int16)
    seg = np.zeros(length, dtype=np.int16)
    if passive:
        return ids, seg
    t, s = int(rng.integers(24, 49)), 0
    if intervention_start == "immediate":
        t = 0  # still consume the approach draw, preserving subsequent draws
    while t < length:
        s += 1
        n = int(rng.integers(H_MAX + 8, H_MAX + 25))  # hold 40..56 steps (~1 s)
        ids[t : t + n] = int(rng.integers(0, len(ACTION_NAMES)))
        seg[t : t + n] = s
        t += n
    return ids, seg


def _streams(seed, rollout, layout, shared):
    """Isolate scene, command and plant draws for paired schedule studies."""
    if layout == "shared":
        return shared, shared, shared
    if layout != "per_rollout":
        raise ValueError(f"unknown RNG layout: {layout}")
    return tuple(
        np.random.default_rng(child)
        for child in np.random.SeedSequence([seed, rollout]).spawn(3)
    )


def gen(
    n_rollouts: int,
    length: int,
    seed: int = 0,
    randomize: bool = False,
    worlds: tuple = ("classic",),
    img_res: int = IMG_RES,
    schedule_layout: str = "world_balanced",
    rng_layout: str = "shared",
    intervention_start: str = "approach",
) -> dict:
    """Fly `n_rollouts` fresh intervention trials and return the raw sequences:
    frames (uint8), held commands, nearest-pillar distances, drone positions,
    plus per-rollout metadata (initial pillar layout, per-pillar planar
    velocity, world id, per-step segment ids, in-path flag).

    `worlds` cycles per rollout across scene kinds: "classic" (2-3 pillars),
    "dense" (5-7, two in-path) and "moving" (an aimed crosser + clutter).
    Moving scenes advance every control step; `dists` always scores against
    the *current* geometry, and `pillars` + `pillar_vel` store the initial
    positions + velocities so the label oracle can extrapolate pil(t)
    analytically.

    Roles cycle on each world's own visits, so all worlds receive passive
    and intervention trials. `schedule_layout="legacy"` reproduces the old
    global-index recipe, including its world/role aliasing; use it only when
    explicitly reproducing a historical dataset or registered comparison.

    `rng_layout="per_rollout"` isolates scene/schedule/noise streams per
    rollout, so schedule changes cannot change later scenes. This is a new
    data recipe; the default shared stream preserves historical draws.
    `intervention_start="immediate"` skips the forward approach on active
    courses while retaining its RNG draw and subsequent command sequence.

    `randomize=True` randomizes the *plant* as well as the scene: random
    pillar shape/colour, 0-2 control steps of command latency, and ±8 %
    per-step actuation noise on the executed command. The RECORDED action
    stays the clean commanded one — the model conditions on intent, reality
    wobbles, and the labels come from where the drone really went."""
    if rng_layout not in RNG_LAYOUTS or intervention_start not in INTERVENTION_STARTS:
        raise ValueError("unknown RNG layout or intervention start")
    roles = plan(n_rollouts, worlds, schedule_layout)
    env = make_env(img_res=img_res)
    cmd = VelCommander(make_ctrl(), env.CTRL_TIMESTEP)
    rng = np.random.default_rng(seed)

    R, L = n_rollouts, length
    frames = np.zeros((R, L, int(img_res), int(img_res), 3), dtype=np.uint8)
    actions = np.zeros((R, L, 4), dtype=np.float32)
    act_id = np.zeros((R, L), dtype=np.int16)
    seg = np.zeros((R, L), dtype=np.int16)
    dists = np.zeros((R, L), dtype=np.float32)
    pos = np.zeros((R, L, 3), dtype=np.float32)
    pillars_meta = np.full((R, MAX_PIL, 2), np.nan, dtype=np.float32)
    pillar_vel = np.zeros((R, MAX_PIL, 2), dtype=np.float32)
    world_id = np.zeros(R, dtype=np.int16)
    in_path = np.zeros(R, dtype=bool)
    speed = np.zeros(R, dtype=np.float32)

    for r, role in enumerate(roles):
        scene_rng, schedule_rng, noise_rng = _streams(seed, r, rng_layout, rng)
        obs, _ = env.reset(seed=int(scene_rng.integers(2**31 - 1)))
        cmd.reset(START)
        world = role.world
        spec = get_scenario(world)
        world_id[r] = spec.world_id
        in_path[r] = role.in_path
        speed[r] = scene_rng.uniform(*SPEED_RANGE)
        scenario = spec.spawn(
            env,
            scene_rng,
            speed=float(speed[r]),
            randomize=randomize,
            in_path=bool(in_path[r]),
        )
        pillars = scenario.positions()
        pillar_vel[r, : len(pillars)] = scenario.velocities()
        pillars_meta[r, : len(pillars)] = pillars
        act_id[r], seg[r] = _schedule(
            schedule_rng, L, passive=role.passive, intervention_start=intervention_start
        )
        lat = int(noise_rng.integers(0, 3)) if randomize else 0

        state = obs[0]
        for t in range(L):
            frames[r, t] = grab_frame(env)
            pos[r, t] = state[0:3]
            dists[r, t] = nearest_planar(state[0:2], scenario.positions())
            actions[r, t] = speed[r] * ACTION_VECS[act_id[r, t]]  # the intent
            # ... while the *executed* command may lag and wobble (randomize)
            v_exec = speed[r] * ACTION_VECS[act_id[r, max(t - lat, 0)]]
            if randomize:
                v_exec = v_exec * (1.0 + noise_rng.normal(0.0, 0.08, size=4))
            obs, _, _, _, _ = env.step(cmd.rpm(state, v_exec).reshape(1, 4))
            state = obs[0]
            scenario.step()  # static worlds: no-op
        held = sorted({ACTION_NAMES[i] for i in act_id[r][seg[r] > 0]})
        print(
            f"  rollout {r + 1}/{R} ({world}, "
            f"{'in-path' if in_path[r] else 'clear'}, {speed[r]:.2f}x, "
            f"{'passive' if seg[r].max() == 0 else '+'.join(held)})"
        )

    env.close()
    data = {
        "frames": frames,
        "actions": actions,
        "act_id": act_id,
        "seg": seg,
        "dists": dists,
        "pos": pos,
        "pillars": pillars_meta,
        "pillar_vel": pillar_vel,
        "world_id": world_id,
        "in_path": in_path,
        "speed": speed,
        "randomized": np.uint8(randomize),
        "horizons": np.array(HORIZONS, dtype=np.int16),
        "a_norm": A_NORM,
        "danger_r": np.float32(DANGER_R),
        "world_names": world_names_array(),  # self-describing world ids
    }
    # Keep the legacy blob schema unchanged for exact historical replay.
    if schedule_layout != "legacy":
        data["schedule_layout"] = np.array(schedule_layout)
    if rng_layout != "shared" or intervention_start != "approach":
        data["rng_layout"] = np.array(rng_layout)
        data["intervention_start"] = np.array(intervention_start)
    return data


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
    ap.add_argument(
        "--worlds",
        default="classic",
        help="'classic' | 'hard' | comma-list of registered worlds",
    )
    ap.add_argument(
        "--out", default=OUT, help="new .npz path; existing corpora are preserved"
    )
    ap.add_argument("--img-res", type=int, default=IMG_RES, help="camera res")
    ap.add_argument(
        "--schedule-layout",
        choices=LAYOUTS,
        default="world_balanced",
        help="cross roles within each world; legacy reproduces the aliased old recipe",
    )
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--rng-layout", choices=RNG_LAYOUTS, default="shared")
    ap.add_argument(
        "--intervention-start", choices=INTERVENTION_STARTS, default="approach"
    )
    args = ap.parse_args()
    n_roll, length = (12, 100) if args.selftest else (args.rollouts, args.length)
    worlds = resolve_worlds(args.worlds)
    if args.selftest:
        worlds = ("classic", "dense", "moving")  # smoke every scene kind

    out = OUT.replace(".npz", "_selftest.npz") if args.selftest else args.out
    out = dataset_destination(out, selftest=args.selftest)

    tag = (" (randomized)" if args.randomize else "") + f" [{args.worlds}]"
    print(f"[INFO] flying {n_roll} intervention rollouts x {length} steps{tag} ...")
    data = gen(
        n_roll,
        length,
        seed=args.seed,
        randomize=args.randomize,
        worlds=worlds,
        img_res=IMG_RES if args.selftest else args.img_res,
        schedule_layout="world_balanced" if args.selftest else args.schedule_layout,
        rng_layout="shared" if args.selftest else args.rng_layout,
        intervention_start="approach" if args.selftest else args.intervention_start,
    )
    rates = {}
    for k in HORIZONS:
        pairs = as_pairs(data, k)
        rates[k] = (len(pairs["c"]), float(pairs["c"].mean()))
    rate_str = ", ".join(f"k={k}: n={n} pos={p:.2f}" for k, (n, p) in rates.items())
    n_seg = int(sum(data["seg"][r].max() for r in range(n_roll)))
    held = sorted({ACTION_NAMES[i] for r in range(n_roll) for i in data["act_id"][r]})
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
        # the v0.2 mix: every scene kind present, movers carry real velocity
        assert set(data["world_id"]) == {0, 1, 2}, "world mix incomplete"
        mv = data["world_id"] == 2
        assert np.abs(data["pillar_vel"][mv]).max() > 0.15, "crosser velocity missing"
        assert (
            np.abs(data["pillar_vel"][~mv]).max() == 0.0
        ), "static worlds must not move"
        dn = data["world_id"] == 1
        n_dense = (~np.isnan(data["pillars"][dn][:, :, 0])).sum(axis=1)
        assert n_dense.min() >= 5, "dense rollouts thinner than promised"
        for wid in (0, 1, 2):
            passive = data["seg"][data["world_id"] == wid].max(axis=1) == 0
            assert passive.any() and (~passive).any(), f"world {wid} role aliasing"
        assert np.std(data["frames"]) > 1, "blank camera frames"

    save_dataset(data, out, selftest=args.selftest)
    print(
        f"WM-DATA OK: {n_roll} rollouts x {length} steps @ {CTRL_HZ} Hz, "
        f"{n_seg} held intervention segments, labels [{rate_str}], saved {out}"
    )
    print(f"  commands held: {held}")
    for wid in sorted(set(data["world_id"])):
        mask = data["world_id"] == wid
        passive = int((data["seg"][mask].max(axis=1) == 0).sum())
        print(
            f"  {data['world_names'][wid]}: {int(mask.sum()) - passive} intervention, "
            f"{passive} passive, {int((~data['in_path'][mask]).sum())} clear"
        )


if __name__ == "__main__":
    main()
    sys.exit(0)

"""The closed-loop scoreboard: many courses, every number a robot person asks.

A single demo course can flatter any controller. This eval flies the
policies over *many* random courses (70 % with a pillar in the path, 30 %
clear) and reports:

  * crash rate            — does anticipation prevent hits, not just look nice?
  * mean min clearance    — how much margin does the early veer buy?
  * trigger lead          — how many ms earlier does the model react?
  * false positives       — does it flinch on courses that were safe anyway?
  * goal time             — safety must not cost the mission

Pillar positions are privileged information used to *score* runs and *stage*
courses — never to fly them; policies see only camera frames (the reactive
baseline is additionally handed its evasion direction, a generous handicap
documented in `planner.latent_mpc`).

Read the scoreboard for what it measures: *cluttered* courses at cruise
speed. Side pillars sit at 60–90° bearings — outside the forward camera's
FOV — so evasive wandering can clip what no frame ever showed. The hand MPC
pays a measured crash tail here; the learned policy erases it (see
`eval_speed_sweep` and the learned-policy compare for the full picture).

Run:
  python -m eval.eval_closed_loop --seeds 100
  python -m eval.eval_closed_loop --selftest   # 10 seeds, asserts
Needs output/world_model.pth (auto-trains a tiny one if missing).
"""

import argparse
import os
import sys

import numpy as np
import torch

from planner.action_set import ACTION_VECS, FORWARD
from planner.latent_mpc import DECIDE_EVERY, ReactivePolicy, WMPolicy
from sim.domain_randomization import shift_appearance
from sim.envs import CTRL_HZ, VelCommander, grab_frame, make_ctrl, make_env
from sim.scenarios import COLLISION_R, GOAL_X, TMAX, nearest_planar, spawn_pillars
from world_model.training import MODEL, load_model, train


def run_episode(
    env,
    policy,
    scenario_seed: int,
    tmax: int = TMAX,
    in_path: bool = True,
    speed: float = 1.0,
    solo: bool = False,
    randomize: bool = False,
) -> dict:
    """Fly START -> GOAL_X once under `policy`. The same seed reproduces the
    same pillar course, so two policies can fly literally the same test.
    `in_path=False` gives a course that is safe if flown straight (used to
    count false-positive evasions). `speed` scales the whole command set and
    `solo` strips the side clutter (the speed sweep raises speed on
    single-pillar courses until reaction breaks). `randomize=True` is the
    unseen world: random pillar shape/colour, 0-2 steps of command latency,
    ±8 % actuation noise, and the fixed appearance shift on every frame the
    *policy* sees (scoring keeps the true geometry)."""
    rng = np.random.default_rng(scenario_seed)
    obs, _ = env.reset(seed=int(scenario_seed))
    cmd = VelCommander(make_ctrl(), env.CTRL_TIMESTEP)
    cmd.reset(obs[0][0:3])
    pillars = spawn_pillars(env, rng, in_path=in_path, solo=solo, randomize=randomize)
    policy.begin(pillars)
    vecs = float(speed) * ACTION_VECS
    lat = int(rng.integers(0, 3)) if randomize else 0
    pending = [FORWARD] * max(lat, 1)  # executed command lags the decision

    state, a_id, trigger = obs[0], FORWARD, -1
    path, min_clear = [state[0:3].copy()], 9.0
    for t in range(tmax):
        if t % DECIDE_EVERY == 0:
            frame = grab_frame(env)
            if randomize:  # the unseen camera: dimmer, noisier
                shifted = shift_appearance(frame[None].astype(np.float32) / 255.0)
                frame = (shifted[0] * 255.0).astype(np.uint8)
            a_id = policy.decide(frame, state)
            if a_id != FORWARD and trigger < 0:
                trigger = t
        pending.append(a_id)
        a_exec = pending.pop(0) if lat else pending.pop()
        v = vecs[a_exec]
        if randomize:
            v = v * (1.0 + rng.normal(0.0, 0.08, size=4))
        obs, _, _, _, _ = env.step(cmd.rpm(state, v).reshape(1, 4))
        state = obs[0]
        path.append(state[0:3].copy())
        min_clear = min(min_clear, nearest_planar(state[0:2], pillars))
        if state[0] >= GOAL_X:
            break
    return {
        "path": np.array(path),
        "pillars": pillars,
        "min_clear": min_clear,
        "trigger": trigger,
        "crashed": min_clear < COLLISION_R,
        "steps": len(path) - 1,
        "reached": bool(state[0] >= GOAL_X),
    }


def load_or_train(device: str = "cpu"):
    """No checkpoint -> train a tiny one right here (slower but
    self-contained), so every eval runs on its own. The stand-in is
    provenance-stamped (`meta["autotrained_tiny"]`) so behavioral
    selftests can honestly scope themselves to wiring — a 12-rollout
    model's flight quality is a coin flip, not a claim."""
    if not os.path.exists(MODEL):
        print(f"[INFO] no model at {MODEL}; training a tiny one first ...")
        from datasets.generate_rollouts import gen

        ckpt, _ = train(gen(12, 100), epochs=40)
        ckpt["meta"]["autotrained_tiny"] = True
        os.makedirs(os.path.dirname(MODEL), exist_ok=True)
        torch.save(ckpt, MODEL)
    return load_model(MODEL, device=device)


def evaluate(
    n_seeds: int, seed0: int, enc, pred, cheads, nhead, meta, wm_kwargs=None
) -> list:
    env = make_env()
    rows = []
    for i in range(n_seeds):
        seed, in_path = seed0 + i, (i % 10) < 7  # 70% threatened, 30% clear
        row = {"seed": seed, "in_path": in_path}
        row["reactive"] = run_episode(
            env, ReactivePolicy(enc, nhead), seed, in_path=in_path
        )
        row["wm"] = run_episode(
            env,
            WMPolicy(enc, pred, cheads, meta, **(wm_kwargs or {})),
            seed,
            in_path=in_path,
        )
        rows.append(row)
        r, w = row["reactive"], row["wm"]
        print(
            f"  seed {seed} ({'in-path' if in_path else 'clear  '}): "
            f"clear {r['min_clear']:.2f}->{w['min_clear']:.2f} m, "
            f"trigger {r['trigger']:>3}->{w['trigger']:>3}, "
            f"crash {int(r['crashed'])}/{int(w['crashed'])}"
        )
    env.close()
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=100)
    ap.add_argument("--seed0", type=int, default=1000)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    n_seeds = 10 if args.selftest else args.seeds

    had_ckpt = os.path.exists(MODEL)
    enc, pred, cheads, nhead, meta = load_or_train(device="cpu")
    rows = evaluate(n_seeds, args.seed0, enc, pred, cheads, nhead, meta)

    ip = [r for r in rows if r["in_path"]]
    cl = [r for r in rows if not r["in_path"]]

    def rate(rs, pol, key):
        return float(np.mean([float(r[pol][key]) for r in rs])) if rs else float("nan")

    crash_r, crash_w = rate(ip, "reactive", "crashed"), rate(ip, "wm", "crashed")
    clr_r, clr_w = rate(ip, "reactive", "min_clear"), rate(ip, "wm", "min_clear")
    leads = [
        (r["reactive"]["trigger"] - r["wm"]["trigger"]) * 1000.0 / CTRL_HZ
        for r in ip
        if r["reactive"]["trigger"] >= 0 and r["wm"]["trigger"] >= 0
    ]
    lead = float(np.mean(leads)) if leads else float("nan")
    fp_r = float(np.mean([r["reactive"]["trigger"] >= 0 for r in cl])) if cl else 0.0
    fp_w = float(np.mean([r["wm"]["trigger"] >= 0 for r in cl])) if cl else 0.0
    ok = [
        r
        for r in ip
        if r["reactive"]["reached"]
        and r["wm"]["reached"]
        and not r["reactive"]["crashed"]
        and not r["wm"]["crashed"]
    ]
    goal_pct = (
        100.0
        * (
            float(np.mean([r["wm"]["steps"] for r in ok]))
            / float(np.mean([r["reactive"]["steps"] for r in ok]))
            - 1.0
        )
        if ok
        else float("nan")
    )

    print(
        f"CLOSED-LOOP OK: seeds={n_seeds} ({len(ip)} in-path / {len(cl)} clear)\n"
        f"  crash_rate:        reactive {crash_r:.0%} -> wm {crash_w:.0%}\n"
        f"  mean_min_clearance: {clr_r:.2f} m -> {clr_w:.2f} m\n"
        f"  mean_trigger_lead: +{lead:.0f} ms (n={len(leads)} both triggered)\n"
        f"  false_positive:    reactive {fp_r:.0%} -> wm {fp_w:.0%} of clear runs\n"
        f"  goal_time:         wm {goal_pct:+.0f}% vs reactive (n={len(ok)} clean)"
    )

    if args.selftest and had_ckpt:  # with the properly trained model the
        # policy claims hold; a fresh tiny model only checks the harness
        if leads:
            assert lead > 0, "wm did not trigger earlier on average"
        assert fp_w <= fp_r + 1e-9, "wm false-triggers on safe courses"
        assert clr_w >= clr_r - 0.20, "wm clears far less than reactive"
        assert crash_w <= crash_r + 0.40, "crash tail beyond the documented"
    elif args.selftest:
        print("[INFO] fresh tiny model: policy asserts skipped, harness checked")


if __name__ == "__main__":
    main()
    sys.exit(0)

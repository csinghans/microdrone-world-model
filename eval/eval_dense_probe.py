"""dense-speedrun stage-0 probe: the arena ceiling and the failure map.

Two arms over the frozen cells (dense x speed {1.0, 1.5, 2.0}, n=30,
seed0=7000 — experiments/dense_speedrun/journal.md):

  * **OracleField** — privileged scripted pilot (reads the pillar
    layout, tracks the best gap in a rolling window ahead, same
    action set and decision cadence). Its success is the arena ceiling — honestly a
    LOWER bound: scripted quality is a confound, but dense is a
    spatial task, where the Weave/Dodge scripted ceilings held.
  * **--zip contender** — measured-only baseline through the exact
    same runner, so the failure taxonomy is comparable.

Every non-success is classified mechanically from path + layout:
timeout | in_path_1 | in_path_2 | side, crashes flagged blind-side
when they land within BLIND_DECISIONS of the last veer direction
flip (the world's design thesis: evasion steers into unseen space).

Run:
  python -m eval.eval_dense_probe --n 30 --zip output/ppo_wm_policy_edge_hard_xp.zip
  python -m eval.eval_dense_probe --selftest
"""

import argparse
import json
import os
import sys

import numpy as np

from planner.action_set import ACTION_NAMES, FORWARD
from planner.latent_mpc import DECIDE_EVERY
from sim.scenarios import COLLISION_R

VEER_L = ACTION_NAMES.index("veer_left")  # +y
VEER_R = ACTION_NAMES.index("veer_right")  # -y

SPEED_GRID = (1.0, 1.5, 2.0)
SEED0 = 7000
OUT_DIR = "experiments/dense_speedrun"

# OracleField geometry (instrument constants, frozen with the tool)
LOOK2 = 1.6  # rolling gap-ladder window ahead (m)
EDGE = 1.7  # virtual corridor edges for gap construction
DEADBAND = 0.12  # |target - y| that counts as centred
PROX_W = 0.55  # distance-to-reach penalty weight
STICKY = 0.25  # bonus for keeping the current target (commitment)
CAP = 1.1  # gap-width contribution cap (edge gaps must not dominate)
RECENTER = 0.9  # drift-home threshold past the field
BLIND_DECISIONS = 3  # crash within this many decisions of a flip = blind-side


class OracleField:
    """Privileged gap-tracker for scattered-pillar fields (the Weave
    recipe, adapted): each decision, sort the pillars in a rolling
    window ahead into a virtual y-ladder (corridor edges included),
    score every gap by width (capped) minus distance-to-reach, with a
    stickiness bonus for the currently held target — then error-steer
    to the winning gap centre with a deadband. Commitment via
    stickiness kills the relative-lane dither the first bring-up smoke
    caught; scoring gaps against ALL window pillars (ignoring their x
    spread) is deliberately conservative — this ceiling is a lower
    bound."""

    def begin(self, pillars) -> None:
        self.p = [(float(q[0]), float(q[1])) for q in pillars]
        self.target = None

    def decide(self, frame, state) -> int:
        del frame  # privileged pilot: honestly not a vision contender
        x, y = float(state[0]), float(state[1])
        win = [py for px, py in self.p if x < px <= x + LOOK2]
        if not win:
            self.target = None
            if y > RECENTER:
                return VEER_R
            if y < -RECENTER:
                return VEER_L
            return FORWARD
        ys = [-EDGE] + sorted(win) + [EDGE]
        best, tgt = None, 0.0
        for lo, hi in zip(ys, ys[1:]):
            width, mid = hi - lo, (hi + lo) / 2.0
            score = min(width, CAP) - PROX_W * abs(mid - y)
            if self.target is not None and abs(mid - self.target) < 0.2:
                score += STICKY
            if best is None or score > best:
                best, tgt = score, mid
        self.target = tgt
        err = tgt - y
        if abs(err) < DEADBAND:
            return FORWARD
        return VEER_L if err > 0 else VEER_R


class DecisionRecorder:
    """Thin wrapper: pass decisions through, remember (index, action)."""

    def __init__(self, inner):
        self.inner, self.log = inner, []

    def begin(self, pillars) -> None:
        self.log = []
        self.inner.begin(pillars)

    def decide(self, frame, state) -> int:
        a = self.inner.decide(frame, state)
        self.log.append(int(a))
        return a


def classify(ep, decisions) -> dict:
    """Mechanical failure taxonomy from path + layout (journal-frozen)."""
    if ep["reached"] and not ep["crashed"]:
        return {"outcome": "success"}
    if not ep["crashed"]:
        return {"outcome": "timeout"}
    path = np.asarray(ep["path"])[:, 0:2]
    pil = np.asarray([(float(q[0]), float(q[1])) for q in ep["pillars"]])
    d = np.linalg.norm(path[:, None, :] - pil[None, :, :], axis=2)
    hits = np.argwhere(d < COLLISION_R)
    step, pidx = (
        (int(hits[0][0]), int(hits[0][1]))
        if len(hits)
        else (
            int(np.argmin(d.min(axis=1))),
            int(d[np.argmin(d.min(axis=1))].argmin()),
        )
    )
    px, py = pil[pidx]
    if abs(py) >= 0.4:
        zone = "side"
    else:
        zone = "in_path_1" if px < 1.75 else "in_path_2"
    # blind-side: crash close after the last veer direction flip
    k = step // DECIDE_EVERY  # decision index at the crash step
    flips = [
        i
        for i in range(1, min(k + 1, len(decisions)))
        if decisions[i] != decisions[i - 1]
        and decisions[i] in (VEER_L, VEER_R)
        and decisions[i - 1] in (VEER_L, VEER_R)
    ]
    blind = bool(flips and (k - flips[-1]) <= BLIND_DECISIONS)
    return {"outcome": zone, "blind_side": blind, "crash_x": float(px)}


def fly_cell(env, make_policy, speed: float, n: int) -> dict:
    from eval.episode import run_scenario_episode

    counts = {"success": 0, "timeout": 0, "in_path_1": 0, "in_path_2": 0, "side": 0}
    blind = 0
    for i in range(n):
        pol = DecisionRecorder(make_policy(speed))
        ep = run_scenario_episode(env, pol, SEED0 + i, "dense", speed)
        tax = classify(ep, pol.log)
        counts[tax["outcome"]] += 1
        blind += int(tax.get("blind_side", False))
    crashes = counts["in_path_1"] + counts["in_path_2"] + counts["side"]
    return {
        "speed": speed,
        "n": n,
        "success": counts["success"] / n,
        "crash": crashes / n,
        "timeout": counts["timeout"] / n,
        "taxonomy": {k: counts[k] for k in ("in_path_1", "in_path_2", "side")},
        "blind_side": blind,
    }


def probe(n: int, zip_path=None) -> dict:
    from scripts.research import _policy_factory
    from sim.envs import make_env

    env, arms = make_env(), {}
    arms["oracle"] = lambda speed: OracleField()
    if zip_path:
        arms["contender"] = _policy_factory(zip_path)
    out = {"n": n, "seed0": SEED0, "zip": zip_path, "cells": []}
    for arm, factory in arms.items():
        for speed in SPEED_GRID:
            cell = fly_cell(env, factory, speed, n)
            cell["arm"] = arm
            out["cells"].append(cell)
            print(
                f"  {arm} @x{speed:.1f}: success {cell['success']:.3f} "
                f"crash {cell['crash']:.3f} timeout {cell['timeout']:.3f} "
                f"taxonomy {cell['taxonomy']} blind {cell['blind_side']}",
                flush=True,
            )
    env.close()
    return out


def selftest() -> None:
    # steering signs, env-free
    pilot = OracleField()
    pilot.begin([(1.2, 0.05), (1.5, 0.9)])
    s = np.array([0.4, 0.0, 1.0])
    assert pilot.decide(None, s) == VEER_R, "widest gap is below the pair -> -y"
    s2 = np.array([0.4, -0.85, 1.0])
    assert pilot.decide(None, s2) == FORWARD, "centred in the target gap -> cruise"
    assert pilot.target is not None and pilot.target < 0
    pilot.begin([(1.2, -0.3)])
    s4 = np.array([0.5, -0.2, 1.0])
    assert pilot.decide(None, s4) == VEER_R, "nearer gap (below the pillar) wins"
    pilot.begin([(1.2, 0.0)])
    s5 = np.array([3.0, 0.5, 1.0])
    assert pilot.decide(None, s5) == FORWARD, "past the field, inside band -> cruise"
    assert pilot.target is None
    s6 = np.array([3.0, 1.4, 1.0])
    assert pilot.decide(None, s6) == VEER_R, "past the field, far off-axis -> home"

    # taxonomy: fabricated side-pillar crash, blind-side flagged
    path = np.zeros((41, 3))
    path[:, 0] = np.linspace(0.0, 2.0, 41)
    path[:, 1] = np.linspace(0.0, 0.62, 41)
    ep = {
        "reached": False,
        "crashed": True,
        "path": path,
        "pillars": [(1.95, 0.62), (1.2, 0.0)],
    }
    hit_step = int(
        np.argwhere(
            np.linalg.norm(path[:, 0:2] - np.array([1.95, 0.62]), axis=1) < COLLISION_R
        )[0][0]
    )
    k = hit_step // DECIDE_EVERY
    decisions = [VEER_L] * max(1, k - 1) + [VEER_R] * 8
    tax = classify(ep, decisions)
    assert tax["outcome"] == "side" and tax["blind_side"], tax
    ep2 = {"reached": False, "crashed": False, "path": path, "pillars": []}
    assert classify(ep2, [FORWARD])["outcome"] == "timeout"
    ep3 = {"reached": True, "crashed": False, "path": path, "pillars": []}
    assert classify(ep3, [FORWARD])["outcome"] == "success"
    print("eval_dense_probe selftest OK")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--zip", dest="zip_path", default=None)
    ap.add_argument("--out", default=os.path.join(OUT_DIR, "probe.json"))
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    res = probe(args.n, args.zip_path)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(res, f, indent=1)
    print(f"[dense-probe] wrote {args.out}")


if __name__ == "__main__":
    sys.exit(main())

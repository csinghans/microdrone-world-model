"""clutter_governor_v1 G0 — the oracle-governor ceiling probe.

The dense frontier's autopsies (oracle_memory_v1: the failure is
kinematic, not informational; dense_recal_v1: heads under-warn where
clutter peaks) compose into one untried knob: reduce the demand for
time. This probe prices its ceiling with privileged clutter — the
champion flies dense cells untouched vs wrapped in a governor that
interleaves SLOW on alternating decisions wherever the dense_recal
8-ray clutter count reads >= 2. Bars in
experiments/clutter_governor_v1/journal.md, frozen before any number.

Run:
  python -m eval.eval_clutter_governor --n 200
  python -m eval.eval_clutter_governor --selftest
"""

import argparse
import json
import os

import numpy as np

from eval.eval_dense_recal import clutter_count
from planner.action_set import ACTION_NAMES

SLOW = ACTION_NAMES.index("slow")
CLUTTER_FIRE = 2  # rays < 1.0 m (the dense_recal signal, same NEAR)
SPEED_GRID = (1.5, 2.0)
SEED0 = 162000
OUT_JSON = "experiments/clutter_governor_v1/g0_results.json"
# frozen bars (journal G0)
CEILING_BAR = -0.07
REACHED_GUARD = 0.05
HIST = {1.5: 0.267, 2.0: 0.467}


class OracleGovernor:
    """Privileged speed governor: where local clutter is thick
    (>= CLUTTER_FIRE of the 8 rays return under 1 m), substitute the
    menu's SLOW action on alternating decisions; elsewhere pass the
    inner policy through untouched. Never hover (the stop-observe OOD
    lesson); a ceiling instrument, never deployed."""

    def __init__(self, inner, pillar_r: float):
        self.inner, self.pillar_r = inner, float(pillar_r)
        self.fires = 0
        self._tick = 0

    def begin(self, pillars) -> None:
        self.p = np.array([(float(q[0]), float(q[1])) for q in pillars])
        self.fires, self._tick = 0, 0
        self.inner.begin(pillars)

    def decide(self, frame, state) -> int:
        a = int(self.inner.decide(frame, state))
        self._tick += 1
        c = clutter_count(np.asarray(state[0:2], dtype=float), self.p, self.pillar_r)
        if c >= CLUTTER_FIRE and self._tick % 2 == 0:
            self.fires += 1
            return SLOW
        return a


def fly(env, factory, speed: float, n: int, seed0: int, governed: bool) -> dict:
    from eval.episode import run_scenario_episode
    from skills.gap_flight.skill import PILLAR_R

    crash, reached, fires, steps = 0, 0, 0, []
    for i in range(n):
        pol = factory(speed)
        if governed:
            pol = OracleGovernor(pol, PILLAR_R)
        ep = run_scenario_episode(env, pol, seed0 + i, "dense", speed)
        crash += int(ep["crashed"])
        reached += int(ep["reached"] and not ep["crashed"])
        fires += getattr(pol, "fires", 0)
        steps.append(ep["steps"])
    return {
        "speed": speed,
        "n": n,
        "crash": crash / n,
        "reached": reached / n,
        "fires_per_flight": fires / n,
        "mean_steps": float(np.mean(steps)),
    }


def run(n: int, seed0: int = SEED0, out: str = OUT_JSON) -> dict:
    from scripts.research import _policy_factory
    from sim.envs import make_env

    factory = _policy_factory("output/ppo_wm_policy_edge_hard_xp.zip")
    env = make_env()
    cells = []
    for governed in (False, True):
        arm = "gov" if governed else "base"
        for speed in SPEED_GRID:
            c = fly(env, factory, speed, n, seed0, governed)
            c["arm"] = arm
            cells.append(c)
            print(
                f"  {arm} dense@x{speed:.1f}: crash {c['crash']:.3f} reached "
                f"{c['reached']:.3f} fires/flight {c['fires_per_flight']:.1f} "
                f"steps {c['mean_steps']:.0f}",
                flush=True,
            )
    env.close()

    def pooled(arm):
        cs = [c for c in cells if c["arm"] == arm]
        return sum(c["crash"] * c["n"] for c in cs) / sum(c["n"] for c in cs)

    d_crash = pooled("gov") - pooled("base")
    fire_rate = np.mean([c["fires_per_flight"] for c in cells if c["arm"] == "gov"])
    guards = all(
        g["reached"] >= b["reached"] - REACHED_GUARD
        for g in cells
        for b in cells
        if g["arm"] == "gov" and b["arm"] == "base" and g["speed"] == b["speed"]
    )
    if fire_rate < 0.5:
        verdict = "VACUOUS"
    elif d_crash <= CEILING_BAR and guards:
        verdict = "CEILING-EXISTS"
    else:
        verdict = "REFUTED" if guards else "REFUTED-GUARD-TRIPPED"
    res = {
        "n": n,
        "seed0": seed0,
        "cells": cells,
        "pooled_crash": {"base": pooled("base"), "gov": pooled("gov")},
        "delta_crash": d_crash,
        "fires_per_flight": float(fire_rate),
        "reached_guard_ok": bool(guards),
        "verdict": verdict,
    }
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(res, f, indent=1)
    print(
        f"[g0] pooled crash base {res['pooled_crash']['base']:.3f} -> gov "
        f"{res['pooled_crash']['gov']:.3f} | dcrash {d_crash:+.3f} (bar <= "
        f"{CEILING_BAR}) | fires/flight {fire_rate:.1f} | guards "
        f"{'OK' if guards else 'TRIPPED'} -> {verdict}"
    )
    print(f"[g0] wrote {out}")
    return res


class _Straight:
    def begin(self, pillars) -> None:
        pass

    def decide(self, frame, state) -> int:
        return 0


def selftest() -> None:
    # thick clutter -> SLOW interleave on alternating decisions
    ring = [
        (0.6 * np.cos(t), 0.6 * np.sin(t))
        for t in np.linspace(0, 2 * np.pi, 8, endpoint=False)
    ]
    g = OracleGovernor(_Straight(), 0.15)
    g.begin(ring)
    s = np.zeros(20)
    seq = [g.decide(None, s) for _ in range(4)]
    assert seq == [0, SLOW, 0, SLOW], f"thick -> interleave, got {seq}"
    assert g.fires == 2
    # open space -> pure passthrough, zero fires
    g2 = OracleGovernor(_Straight(), 0.15)
    g2.begin([(2.8, 0.0)])
    assert [g2.decide(None, s) for _ in range(4)] == [0, 0, 0, 0]
    assert g2.fires == 0
    # SLOW is a real menu action and is not hover
    assert ACTION_NAMES[SLOW] == "slow" and "hover" not in ACTION_NAMES[SLOW]
    # frozen constants
    assert (CLUTTER_FIRE, CEILING_BAR, REACHED_GUARD) == (2, -0.07, 0.05)
    assert SEED0 == 162000 and SPEED_GRID == (1.5, 2.0)
    print("CLUTTER-GOVERNOR OK: interleave semantics, passthrough, frozen constants")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--seed0", type=int, default=SEED0)
    ap.add_argument("--out", default=OUT_JSON)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    run(args.n, args.seed0, args.out)


if __name__ == "__main__":
    main()

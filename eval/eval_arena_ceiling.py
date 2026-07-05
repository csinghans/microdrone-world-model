"""Price an arena's physical ceiling BEFORE freezing bars on it.

The corridor-slalom v1 campaign closed on an across-the-board honest
negative whose post-mortem could not separate "the policies can't
chain" from "the arena can't be chained at this spacing" — because no
feasibility probe was pre-registered. This tool is that probe, made
reusable: a **scripted oracle pilot** (privileged geometry, bang-bang
veer toward the next gate centre — honestly labelled, never a
contender) flies a (dx × speed) grid of slalom arenas, and its success
rate per config IS the arena's ceiling *under the same action set the
learned policies use*. Bars for a v2 campaign get frozen strictly under
a proven ceiling, or the question is closed as infeasible.

Each grid point registers a throwaway scenario (dynamic registry ids
exist for exactly this), so the standard `run_scenario_episode` loop is
reused verbatim — no probe-only flight code to drift.

Run:
  python -m eval.eval_arena_ceiling --n 30 --out <json>
  python -m eval.eval_arena_ceiling --selftest
"""

import argparse
import json
import sys
from functools import partial

import numpy as np

from planner.action_set import ACTION_NAMES, FORWARD

VEER_L = ACTION_NAMES.index("veer_left")  # +y
VEER_R = ACTION_NAMES.index("veer_right")  # -y
DEADBAND = 0.06  # |y error| below this: stop correcting, cruise
PLANE_LEAD = 0.05  # switch target this far before the fence plane

DX_GRID = (0.70, 0.85, 1.00, 1.15)
SPEED_GRID = (1.0, 1.25, 1.5)
SEED0 = 30000


class OracleWeave:
    """The scripted pilot: reads the privileged pillar layout once at
    begin(), infers the gate ladder (per x-plane, the widest y-spacing
    is the gap), then bang-bang veers toward the next gate centre. It
    can only lose to dynamics — which is exactly what a ceiling probe
    should measure."""

    def begin(self, pillars) -> None:
        planes: dict = {}
        for x, y in [(float(p[0]), float(p[1])) for p in pillars]:
            planes.setdefault(round(x, 3), []).append(y)
        self.gates = []
        for x in sorted(planes):
            ys = sorted(planes[x])
            gaps = [(b - a, (a + b) / 2.0) for a, b in zip(ys, ys[1:])]
            width, yc = max(gaps)
            self.gates.append((x, yc, width))

    def decide(self, frame, state) -> int:
        del frame  # privileged pilot: honestly not a vision contender
        x, y = float(state[0]), float(state[1])
        target = next((g for g in self.gates if g[0] > x - PLANE_LEAD), None)
        if target is None:
            return FORWARD
        err = target[1] - y
        if abs(err) < DEADBAND:
            return FORWARD
        return VEER_L if err > 0 else VEER_R


def probe(n_seeds: int) -> dict:
    """Fly the oracle over the (dx x speed) grid on slalom3 arenas via
    throwaway registered worlds; return the ceiling table."""
    from eval.episode import run_scenario_episode
    from sim.envs import make_env
    from sim.scenario_registry import register
    from skills.corridor_slalom.skill import slalom_success, spawn_slalom

    env, table = make_env(), []
    for dx in DX_GRID:
        x0 = min(0.9, round(2.5 - 2 * dx, 3))
        name = f"_probe_slalom_dx{int(dx * 100)}"
        register(name, partial(spawn_slalom, n_fences=3, dx=dx, x0=x0))
        for speed in SPEED_GRID:
            ok = 0
            for i in range(n_seeds):
                ep = run_scenario_episode(env, OracleWeave(), SEED0 + i, name, speed)
                ok += int(slalom_success(ep))
            table.append({"dx": dx, "x0": x0, "speed": speed, "ceiling": ok / n_seeds})
            print(f"  dx={dx:.2f} x0={x0:.2f} speed={speed:.2f}: {ok}/{n_seeds}")
    env.close()
    return {"n": n_seeds, "seed0": SEED0, "grid": table}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--out", default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        # gate inference + steering signs, env-free
        pilot = OracleWeave()
        pillars = [
            (1.0, -1.5),
            (1.0, -0.9),
            (1.0, -0.3),
            (1.0, 0.5),
            (1.0, 1.1),
            (1.8, -1.2),
            (1.8, -0.3),
            (1.8, 0.4),
            (1.8, 1.0),
            (1.8, 1.6),
        ]
        pilot.begin(pillars)
        assert len(pilot.gates) == 2
        (x1, yc1, w1), (x2, yc2, w2) = pilot.gates
        assert x1 == 1.0 and abs(yc1 - 0.1) < 1e-9 and abs(w1 - 0.8) < 1e-9
        assert x2 == 1.8 and abs(yc2 - (-0.75)) < 1e-9, "widest spacing is the gap"
        state_low = np.array([0.2, -0.4, 1.0])
        state_high = np.array([0.2, 0.6, 1.0])
        state_ok = np.array([0.2, 0.12, 1.0])
        assert pilot.decide(None, state_low) == VEER_L, "below target -> +y veer"
        assert pilot.decide(None, state_high) == VEER_R, "above target -> -y veer"
        assert pilot.decide(None, state_ok) == FORWARD, "deadband cruises"
        past = np.array([2.5, 0.0, 1.0])
        assert pilot.decide(None, past) == FORWARD, "past the ladder: cruise"
        mid = np.array([1.4, -0.75, 1.0])  # between planes, on gate-2 centre
        assert pilot.decide(None, mid) == FORWARD, "target switches after a plane"
        print(
            "ARENA-CEILING OK: gate inference (widest spacing wins), steering "
            "signs, deadband, plane handoff — the oracle is wired straight"
        )
        return

    print(
        f"[INFO] oracle ceiling probe: {len(DX_GRID)}x{len(SPEED_GRID)} grid, "
        f"n={args.n} seeds each"
    )
    result = probe(args.n)
    if args.out:
        with open(args.out, "w") as f:
            json.dump(result, f, indent=1)
        print(f"[INFO] saved {args.out}")


if __name__ == "__main__":
    main()
    sys.exit(0)

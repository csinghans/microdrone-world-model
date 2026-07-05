"""Price the dodgeball arena's ceiling BEFORE freezing bars on it.

The slalom arc's exported lesson, applied to the catalog's first
DEFENSE arena: a **scripted oracle dodger** (privileged live ball
positions, velocity from finite differences — honestly labelled, never
a contender) holds the station and dodges with the SAME action set the
learned policies use. Its survival rate per ball-speed cell IS the
arena ceiling under this body: veers are (0.5, ±0.5), so every dodge
costs ~0.45 m of unrecoverable forward drift against the 1.9 m box
budget — the probe measures whether hover-veer-hover station defense
is physically affordable at all, per ball speed.

What the probe does NOT price (pre-registered in the feasibility
journal): the perception wall. The oracle reads geometry; the learned
policies read a single-frame model's collision probabilities, and
head-on radial closure is outside that model's training envelope. A
high ceiling here only removes the ARENA excuse.

Each cell registers a throwaway scenario (dynamic registry ids exist
for exactly this) and reuses `run_scenario_episode` verbatim.

Run:
  python -m eval.eval_dodge_ceiling --n 30 --out <json>
  python -m eval.eval_dodge_ceiling --selftest
"""

import argparse
import json
import sys
from functools import partial

import numpy as np

from planner.action_set import ACTION_NAMES
from planner.latent_mpc import DECIDE_EVERY
from sim.envs import CTRL_HZ

VEER_L = ACTION_NAMES.index("veer_left")  # +y
VEER_R = ACTION_NAMES.index("veer_right")  # -y
HOVER = ACTION_NAMES.index("hover")
DT = DECIDE_EVERY / CTRL_HZ  # exactly 1/12 s between decisions
NEED = 0.45  # ball r 0.18 + COLLISION_R 0.22 + margin
HORIZON = 2.5  # s: threats further out than this are left alone
CLIP = 1.5  # apparent speed > CLIP x nominal => teleport alias, reset track

BALL_GRID = (0.6, 1.0, 1.4, 1.8)  # m/s, head-on
SEED0 = 31000


class OracleDodge:
    """The scripted defender: hovers at the station; differentiates
    consecutive privileged snapshots (the runner live-refreshes
    `.pillars` every decision) into per-ball velocities, guards against
    teleport aliasing with a plausibility clip, and veers away from the
    projected pass side ONLY while the projected miss is under NEED —
    every needless veer burns unrecoverable box budget. It can only
    lose to dynamics and arithmetic, which is what a ceiling probe
    should measure."""

    def __init__(self, ball_speed: float):
        self.pillars: list = []  # live-refreshed by the runner per decision
        self.vmax = CLIP * float(ball_speed)
        self.prev = None

    def begin(self, pillars) -> None:
        self.pillars = [np.array(q, dtype=float) for q in pillars]
        self.prev = None

    def decide(self, frame, state) -> int:
        del frame  # privileged pilot: honestly not a vision contender
        me = np.array([float(state[0]), float(state[1])])
        cur = np.array([p[:2] for p in self.pillars], dtype=float)
        vel = np.zeros_like(cur)
        if self.prev is not None and self.prev.shape == cur.shape:
            vel = (cur - self.prev) / DT
            fresh = np.linalg.norm(vel, axis=1) > self.vmax  # teleport alias
            vel[fresh] = 0.0
        self.prev = cur
        threat = None  # (t*, miss_vec) of the soonest under-NEED pass
        for r, v in zip(cur - me, vel):
            sp2 = float(v @ v)
            if sp2 < 0.01:  # parked / freshly-clipped: no track yet
                continue
            t_star = -float(r @ v) / sp2
            if not (0.0 <= t_star <= HORIZON):
                continue  # receding or too far out
            miss_vec = r + v * t_star
            if float(np.linalg.norm(miss_vec)) >= NEED:
                continue
            if threat is None or t_star < threat[0]:
                threat = (t_star, miss_vec)
        if threat is None:
            return HOVER
        my = float(threat[1][1])
        if abs(my) < 1e-6:  # dead-on: dodge toward the station centreline
            return VEER_R if me[1] >= 0.0 else VEER_L
        return VEER_R if my > 0.0 else VEER_L  # away from the pass side


def probe(n_seeds: int) -> dict:
    """Fly the oracle over the ball-speed grid at drone factor 1.0 via
    throwaway registered worlds; return the ceiling table (with the
    crash / box-bust split — the failure mode is the diagnosis)."""
    from eval.episode import run_scenario_episode
    from sim.envs import make_env
    from sim.scenario_registry import register
    from skills.dodgeball.skill import dodge_metrics, dodge_success, spawn_dodgeball

    env, table = make_env(), []
    for v in BALL_GRID:
        name = f"_probe_dodge_v{int(v * 10):02d}"
        register(name, partial(spawn_dodgeball, ball_speed=v))
        ok = crashes = 0
        disp = []
        for i in range(n_seeds):
            ep = run_scenario_episode(env, OracleDodge(v), SEED0 + i, name, 1.0)
            m = dodge_metrics(ep)
            ok += int(dodge_success(ep))
            crashes += int(ep["crashed"])
            disp.append(m["disp_x"])
        table.append(
            {
                "ball_speed": v,
                "ceiling": ok / n_seeds,
                "crash": crashes / n_seeds,
                "disp_x_mean": float(np.mean(disp)),
            }
        )
        print(
            f"  ball_speed={v:.1f}: ceiling {ok}/{n_seeds}  "
            f"crash {crashes}/{n_seeds}  disp_x {np.mean(disp):.2f} m"
        )
    env.close()
    return {"n": n_seeds, "seed0": SEED0, "grid": table}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--out", default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        pilot = OracleDodge(1.0)
        pilot.begin([(3.0, 6.0)])
        idle = np.array([0.0, 0.0, 1.0])
        assert pilot.decide(None, idle) == HOVER, "first tick: no track yet"
        assert pilot.decide(None, idle) == HOVER, "parked ball never threatens"
        # dead-on approach: two snapshots build the track, then dodge —
        # drone at y=0 breaks the tie toward -y by convention
        pilot.begin([(2.2, 0.0)])
        assert pilot.decide(None, idle) == HOVER
        pilot.pillars = [np.array([2.2 - 1.0 * DT, 0.0])]
        assert pilot.decide(None, idle) == VEER_R, "dead-on: dodge -y from y>=0"
        # pass-side geometry: ball sliding to cross at +0.2 -> dodge -y;
        # crossing at -0.2 -> dodge +y
        pilot.begin([(2.2, 0.2)])
        pilot.decide(None, idle)
        pilot.pillars = [np.array([2.2 - 1.0 * DT, 0.2])]
        assert pilot.decide(None, idle) == VEER_R, "passes +y side: go -y"
        pilot.begin([(2.2, -0.2)])
        pilot.decide(None, idle)
        pilot.pillars = [np.array([2.2 - 1.0 * DT, -0.2])]
        assert pilot.decide(None, idle) == VEER_L, "passes -y side: go +y"
        # a clean miss (0.9 m off) is left alone — veers cost box budget
        pilot.begin([(2.2, 0.9)])
        pilot.decide(None, idle)
        pilot.pillars = [np.array([2.2 - 1.0 * DT, 0.9])]
        assert pilot.decide(None, idle) == HOVER, "under-NEED only"
        # teleport alias: park -> launch jump reads ~70 m/s and must be
        # clipped to a fresh (stationary) track, not a panic veer
        pilot.begin([(2.0, 6.0)])
        pilot.decide(None, idle)
        pilot.pillars = [np.array([2.2, 0.0])]
        assert pilot.decide(None, idle) == HOVER, "alias clipped, one blind tick"
        # receding ball (t* < 0) never threatens
        pilot.begin([(-0.5, 0.0)])
        pilot.decide(None, idle)
        pilot.pillars = [np.array([-0.5 - 1.0 * DT, 0.0])]
        assert pilot.decide(None, idle) == HOVER, "receding: hover"
        print(
            "DODGE-CEILING OK: track building, teleport-alias clip, pass-side "
            "steering, dead-on tie rule, thrift (miss >= NEED hovers)"
        )
        return

    print(f"[INFO] oracle dodge probe: {len(BALL_GRID)} ball speeds, n={args.n} each")
    result = probe(args.n)
    if args.out:
        with open(args.out, "w") as f:
            json.dump(result, f, indent=1)
        print(f"[INFO] saved {args.out}")


if __name__ == "__main__":
    main()
    sys.exit(0)

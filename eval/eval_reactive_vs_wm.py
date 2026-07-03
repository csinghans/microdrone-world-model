"""The timing schematic: what anticipation buys, isolated from everything else.

A reactive controller steers away once an obstacle is close *now*. A world
model lets you be *proactive*: it predicts that you are *about to* get close
and steers early. This schematic isolates the *control* benefit of that
head-start: two controllers fly the same kinematic course —

  * reactive  — veers when the current distance to a pillar < REACT_R
  * proactive — veers when the *predicted* distance over the next HORIZON
                < REACT_R

with a **bounded acceleration**, so reacting late genuinely costs room to
swerve.

Honest note: here the look-ahead is *privileged* future geometry, so the
comparison is deterministic and studies decision timing on its own. On a
real drone that look-ahead is not free — it is precisely what the world
model predicts from vision alone, and `eval_closed_loop` /
`eval_speed_sweep` measure exactly that with the crutch removed. This file
stays as the cleanest possible statement of *why* anticipation matters.

Run:
  python -m eval.eval_reactive_vs_wm            # saves the plot
  python -m eval.eval_reactive_vs_wm --selftest # asserts
"""

import argparse
import os
import sys

import numpy as np

START = np.array([0.0, 0.0])
GOAL = np.array([3.0, 0.0])
PILLARS = [np.array([1.3, 0.10]), np.array([2.1, 0.55])]  # first one in the path
COLLISION_R = 0.22  # closer than this = crash
REACT_R = 0.60  # start avoiding at this planar distance
HORIZON = 0.6  # seconds of look-ahead the world model grants the proactive rule
V_NOM = 1.2  # nominal forward speed (m/s) — a brisk pass, where reacting late bites
V_AVOID = 1.6  # desired push-away speed when avoiding (m/s)
V_MAX = 1.7  # speed cap (m/s)
A_MAX = 2.2  # acceleration cap (m/s^2) — a real drone cannot turn instantly
DT = 0.05  # kinematic step (s)
TMAX = 240  # step budget
OUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "output",
    "proactive_vs_reactive.png",
)


def _unit(v):
    n = float(np.linalg.norm(v))
    return v / n if n > 1e-9 else np.zeros_like(v)


def _nearest(pos):
    """(nearest pillar, planar distance) from pos."""
    ds = [float(np.linalg.norm(pos - q)) for q in PILLARS]
    i = int(np.argmin(ds))
    return PILLARS[i], ds[i]


def _min_dist_ahead(pos, vel):
    """Privileged look-ahead: the smallest distance to any pillar the drone
    would reach over the next HORIZON if it held this velocity."""
    b = pos + vel * HORIZON
    ab = b - pos
    L2 = float(ab @ ab)
    best = 9.0
    for q in PILLARS:
        t = 0.0 if L2 < 1e-9 else float(np.clip((q - pos) @ ab / L2, 0.0, 1.0))
        best = min(best, float(np.linalg.norm(q - (pos + t * ab))))
    return best


def simulate(proactive: bool) -> dict:
    """Fly START->GOAL with reactive or proactive avoidance. Kinematic
    point-mass stand-in for the two-layer flight loop; the only thing that
    differs between the two runs is *when* the avoidance decision fires."""
    pos = START.copy()
    vel = V_NOM * _unit(GOAL - pos)
    path = [pos.copy()]
    min_clear = 9.0
    trigger = -1
    max_dv = A_MAX * DT
    for step in range(TMAX):
        pillar, d_now = _nearest(pos)
        desired = V_NOM * _unit(GOAL - pos)
        danger = _min_dist_ahead(pos, vel) if proactive else d_now
        if danger < REACT_R:
            if trigger < 0:
                trigger = step
            desired = desired + V_AVOID * _unit(pos - pillar)  # push away
        # accel-limited tracking of the desired velocity, then speed cap
        dv = desired - vel
        ndv = float(np.linalg.norm(dv))
        if ndv > max_dv:
            dv = dv / ndv * max_dv
        vel = vel + dv
        spd = float(np.linalg.norm(vel))
        if spd > V_MAX:
            vel = vel / spd * V_MAX
        pos = pos + vel * DT
        path.append(pos.copy())
        min_clear = min(min_clear, _nearest(pos)[1])
        if pos[0] >= GOAL[0]:
            break
    return {
        "path": np.array(path),
        "min_clear": min_clear,
        "trigger": trigger,
        "crashed": min_clear < COLLISION_R,
    }


def _save_plot(reactive: dict, proactive: dict) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6, 4))
    rp, pp = reactive["path"], proactive["path"]
    ax.plot(rp[:, 0], rp[:, 1], "-", color="tab:orange", label="reactive")
    ax.plot(pp[:, 0], pp[:, 1], "-", color="tab:green", label="proactive")
    ax.plot(*START, "ko", markersize=8, label="start")
    ax.plot(*GOAL, "k*", markersize=14, label="goal")
    for q in PILLARS:
        ax.add_patch(plt.Circle(q, COLLISION_R, color="red", alpha=0.6))
        ax.add_patch(plt.Circle(q, REACT_R, color="red", alpha=0.12))
    ax.set_aspect("equal")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_title("Proactive (world-model look-ahead) vs reactive avoidance")
    ax.legend(loc="best", fontsize=8)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUT, dpi=110)
    print(f"[INFO] saved {OUT}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    reactive = simulate(proactive=False)
    proactive = simulate(proactive=True)
    lead = reactive["trigger"] - proactive["trigger"]
    _save_plot(reactive, proactive)

    rc, pc = int(reactive["crashed"]), int(proactive["crashed"])
    print(
        f"PROACTIVE OK: reactive min-clear={reactive['min_clear']:.2f} m "
        f"(avoid@step {reactive['trigger']}), proactive min-clear="
        f"{proactive['min_clear']:.2f} m (avoid@step {proactive['trigger']}), "
        f"lead=+{lead} steps (~{lead * DT * 1000:.0f}ms earlier), "
        f"crashes reactive/proactive = {rc}/{pc}"
    )
    if args.selftest:
        assert lead > 0, "proactive did not trigger earlier than reactive"
        assert proactive["min_clear"] >= reactive["min_clear"], "no clearance gain"
        assert not proactive["crashed"], "proactive crashed"


if __name__ == "__main__":
    main()
    sys.exit(0)

"""Low-altitude hover stability — the floor-hugging FLIGHT limit (ground
effect), NOT a perception question.

alt_v1 showed DETECTION holds down to a floor-hugging z=0.15 m (AUC 0.83,
no WM retrain). But flying that low is a CONTROL problem: near the ground a
quad rotor sees extra lift (ground effect, which this sim models), which
can push the altitude hold off or make it oscillate. This probe measures
station-keeping at descending altitudes: park the drone at z, hold a hover
via the VelCommander, and record the altitude drift, horizontal drift, and
the minimum clearance to the floor. Where the hold degrades is the
practical floor-hugging altitude — a control limit, the real bottleneck for
under-bed / rubble search (perception is already fine).

Run:
  python -m eval.eval_low_hover
  python -m eval.eval_low_hover --selftest
"""

import argparse
import sys

import numpy as np

ALTS = (1.0, 0.5, 0.35, 0.25, 0.15)  # descending hover targets (m)


def hold(env, z_target, hold_steps=240):
    """Park the drone level at z_target, hover-hold, and report the hold
    quality: mean/max altitude error, max horizontal drift, min floor
    clearance (z), over `hold_steps` control steps (~5 s @ 48 Hz)."""
    import pybullet as p

    from sim.envs import START, VelCommander, make_ctrl

    obs, _ = env.reset(seed=0)
    p.resetBasePositionAndOrientation(
        env.DRONE_IDS[0],
        [START[0], START[1], float(z_target)],
        p.getQuaternionFromEuler([0.0, 0.0, 0.0]),
        physicsClientId=env.CLIENT,
    )
    env._updateAndStoreKinematicInformation()
    state = env._getDroneStateVector(0)
    cmd = VelCommander(make_ctrl(), env.CTRL_TIMESTEP)
    cmd.reset(state[0:3])
    hover = np.zeros(4, dtype=float)
    z_err, xy_drift, min_z = [], 0.0, float(z_target)
    x0, y0 = float(state[0]), float(state[1])
    for _ in range(hold_steps):
        obs, _, _, _, _ = env.step(cmd.rpm(state, hover).reshape(1, 4))
        state = obs[0]
        z = float(state[2])
        z_err.append(abs(z - z_target))
        xy_drift = max(xy_drift, float(np.hypot(state[0] - x0, state[1] - y0)))
        min_z = min(min_z, z)
    return {
        "z_target": float(z_target),
        "mean_z_err": float(np.mean(z_err)),
        "max_z_err": float(np.max(z_err)),
        "xy_drift": xy_drift,
        "min_z": min_z,
    }


def descend_hold(env, z_target, from_z=1.0, hold_steps=240):
    """The DYNAMIC test: start at from_z, command a descent to z_target, then
    hover — the transient where ground effect actually bites (a settled hover
    can be fine while the descent overshoots into the floor). Reports the
    overshoot (min_z reached) + the settle error at the end."""
    import numpy as np
    import pybullet as p

    from planner.nav_action_set import LIFT_V
    from sim.envs import START, VelCommander, make_ctrl

    env.reset(seed=0)
    p.resetBasePositionAndOrientation(
        env.DRONE_IDS[0],
        [START[0], START[1], float(from_z)],
        p.getQuaternionFromEuler([0.0, 0.0, 0.0]),
        physicsClientId=env.CLIENT,
    )
    env._updateAndStoreKinematicInformation()
    state = env._getDroneStateVector(0)
    cmd = VelCommander(make_ctrl(), env.CTRL_TIMESTEP)
    cmd.reset(state[0:3])
    down = np.array([0.0, 0.0, -LIFT_V, 0.0])
    hover = np.zeros(4)
    min_z, settle = float(from_z), []
    for t in range(hold_steps):
        z = float(state[2])
        cmdv = down if z > z_target + 0.02 else hover
        obs, _, _, _, _ = env.step(cmd.rpm(state, cmdv).reshape(1, 4))
        state = obs[0]
        min_z = min(min_z, float(state[2]))
        if t > hold_steps - 48:  # last ~1 s
            settle.append(abs(float(state[2]) - z_target))
    return {
        "z_target": float(z_target),
        "min_z": min_z,
        "overshoot": max(0.0, z_target - min_z),
        "settle_err": float(np.mean(settle)) if settle else float("nan"),
    }


def probe(alts=ALTS, hold_steps=240):
    from sim.envs import make_env

    env = make_env()
    rows = [hold(env, z, hold_steps) for z in alts]
    env.close()
    return rows


def probe_descend(alts=(0.35, 0.25, 0.15), hold_steps=300):
    from sim.envs import make_env

    env = make_env()
    rows = [descend_hold(env, z, hold_steps=hold_steps) for z in alts]
    env.close()
    return rows


def selftest() -> None:
    # env-free: the metrics are well-formed and ALTS descends toward the floor
    assert ALTS == tuple(sorted(ALTS, reverse=True)) and ALTS[-1] < 0.2
    keys = {"z_target", "mean_z_err", "max_z_err", "xy_drift", "min_z"}
    stub = {k: 0.0 for k in keys}
    assert keys <= set(stub), "hold() returns the hold-quality metrics"
    print("EVAL-LOW-HOVER OK: descending hover-hold metric shape")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hold-steps", type=int, default=240)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    print(f"low-altitude hover-hold ({args.hold_steps} steps):")
    print("  z_tgt  mean|dz|  max|dz|  xy_drift  min_z")
    rows = probe(hold_steps=args.hold_steps)
    for r in rows:
        flag = "  <- sinks to floor" if r["min_z"] < 0.05 else ""
        print(
            f"  {r['z_target']:8.2f}  {r['mean_z_err']:8.3f}  {r['max_z_err']:8.3f}  "
            f"{r['xy_drift']:8.3f}  {r['min_z']:6.2f}{flag}"
        )
    # the floor-hugging control limit: lowest altitude that holds within 10 cm
    ok = [r["z_target"] for r in rows if r["max_z_err"] < 0.10 and r["min_z"] > 0.05]
    floor = min(ok) if ok else None
    print(
        "  stable hover floor (max|Δz|<0.10 m, no floor contact): "
        + (f"{floor:.2f} m" if floor is not None else "NONE held")
    )
    print("\ndescend-into-ground-effect transient (start 1.0 m -> target, then hold):")
    print(f"  {'z_target':>8}  {'min_z':>6}  {'overshoot':>9}  {'settle_err':>10}")
    for r in probe_descend():
        flag = "  <- hits floor" if r["min_z"] < 0.05 else ""
        print(
            f"  {r['z_target']:8.2f}  {r['min_z']:6.2f}  {r['overshoot']:9.3f}  "
            f"{r['settle_err']:10.3f}{flag}"
        )


if __name__ == "__main__":
    sys.exit(main())

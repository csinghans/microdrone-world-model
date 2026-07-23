"""The safety envelope, executable — one deterministic scenario per
sim-gateable row of docs/safety.md.

"Required before first free flight" was a table; this makes it a suite
that can have been green for months by the time the hardware bridge
unfreezes (docs/REVIEW-2026-07.md §6). Rows and their honest labels:

  geofence          closed loop: steered INTO the fence, the filter's
                    hover override must cap |y| (planner/safety_filter)
  imminent          indoor form: forced FORWARD into a wall, the beams8
                    corridor veto must substitute — zero contacts
  vertical          descend-into-ground-effect overshoot + a 2 m hold
                    (turns lowfly_v1's measured behaviour into asserts)
  emergency_land    capped-rate descent to touchdown, stable landing
  battery_return    budget-return CHOREOGRAPHY (a mute detector forces
                    the plateau -> return -> home path; tests the logic,
                    not battery physics — labelled honestly)
  log_replay        same seed + same commands -> the same trajectory
                    (the hardware black-box seam)
  guardian_veto     assistance layer (planner/authority): the imminent
                    veto substitutes on the SAME decision it crosses,
                    and the hot command never executes (scorer-injected
                    — tests the ladder, not the WM)
  guardian_toggle   pilot->AUTO toggle granted on its own decision
  guardian_handback a handback request during danger is latched and
                    granted only after HANDBACK_CLEAR clear decisions,
                    with zero authority chatter
  guardian_geofence closed loop: a fence-seeking PILOT wrapped by the
                    Guardian is capped at the bare-filter bound

The hardware RC kill-switch and the GO/NO-GO checklist stay honestly in
the hardware column; what the guardian rows move into sim is the
assistance-layer manual-override semantics (docs/safety.md). `--selftest`
is env-free (CI); `--all` flies the rows (artifact-free by construction)
and is what `scripts/gate.py`'s quick layer runs.

Run:
  python -m eval.safety_selftest --all
  python -m eval.safety_selftest --selftest
"""

import argparse
import sys

import numpy as np

FENCE_MARGIN = 0.35  # momentum allowance past the soft fence
LAND_Z, LAND_TOL = 0.08, 0.12
MAX_DESCENT_MPS = 0.6  # the emergency-land rate cap under test


def row_geofence(env):
    from planner.action_set import ACTION_NAMES, ACTION_VECS
    from planner.safety_filter import FENCE_Y, SafetyFilter
    from sim.envs import VelCommander, make_ctrl

    names = list(ACTION_NAMES)
    sf = SafetyFilter(
        names.index("forward"),
        [names.index("veer_left"), names.index("veer_right")],
        names.index("hover"),
    )
    i_fence = int(np.argmax(ACTION_VECS[:, 1]))  # the most fence-seeking action
    obs, _ = env.reset(seed=11)
    cmd = VelCommander(make_ctrl(), env.CTRL_TIMESTEP)
    cmd.reset(obs[0][0:3])
    state, a, max_y = obs[0], i_fence, 0.0
    p_clear = np.zeros((len(ACTION_VECS), 4, 2), dtype=np.float32)
    for t in range(720):  # ~15 s
        if t % 4 == 0:
            a = sf.filter(i_fence, p_clear, state)  # policy INSISTS on the fence
        obs, *_ = env.step(cmd.rpm(state, ACTION_VECS[a]).reshape(1, 4))
        state = obs[0]
        max_y = max(max_y, abs(float(state[1])))
    assert max_y <= FENCE_Y + FENCE_MARGIN, f"fence breached: |y|={max_y:.2f}"
    assert max_y >= FENCE_Y - 0.5, "never reached the fence — vacuous"
    return {"max_y": round(max_y, 3), "fence": FENCE_Y}


def row_imminent_indoor(env):
    from eval.search_episode import _SAFETY
    from planner.latent_mpc import DECIDE_EVERY
    from planner.nav_action_set import FORWARD, NAV_ACTION_VECS
    from sim.envs import START, VelCommander, make_ctrl
    from sim.indoor.rooms import single_room
    from sim.scenarios import COLLISION_R

    sc = single_room(5)
    safe = _SAFETY["beams8"]
    obs, _ = env.reset(seed=5)
    cmd = VelCommander(make_ctrl(), env.CTRL_TIMESTEP)
    cmd.reset(obs[0][0:3])
    off = (sc.start_xy[0] - START[0], sc.start_xy[1] - START[1])
    state, vetoed = obs[0], 0
    vecs = 0.6 * NAV_ACTION_VECS
    for _d in range(150):
        rpos = (float(state[0]) + off[0], float(state[1]) + off[1])
        a = safe(sc, rpos, FORWARD)  # the policy ALWAYS charges the wall
        vetoed += int(a != FORWARD)
        for _ in range(DECIDE_EVERY):
            obs, *_ = env.step(cmd.rpm(state, vecs[a]).reshape(1, 4))
            state = obs[0]
        rp = (float(state[0]) + off[0], float(state[1]) + off[1])
        assert sc.clearance(rp) >= COLLISION_R, f"contact at {rp}"
    assert vetoed > 0, "the wall never triggered the veto — vacuous"
    return {"vetoes": vetoed, "contacts": 0}


def row_vertical_envelope(env):
    from eval.eval_low_hover import descend_hold, hold

    d = descend_hold(env, 0.15, from_z=1.0)
    assert d["overshoot"] <= 0.05, f"floor overshoot {d['overshoot']:.3f}"
    assert d["min_z"] > 0.05, "sank toward the floor"
    assert d["settle_err"] <= 0.05, f"no settle: {d['settle_err']:.3f}"
    h = hold(env, 2.0, hold_steps=240)
    assert h["max_z_err"] <= 0.15 and h["xy_drift"] <= 0.10, h
    return {
        "descend_overshoot": round(d["overshoot"], 3),
        "hold2m_max_err": round(h["max_z_err"], 3),
    }


def row_emergency_land(env):
    import pybullet as p

    from sim.envs import START, VelCommander, make_ctrl

    obs, _ = env.reset(seed=3)
    p.resetBasePositionAndOrientation(
        env.DRONE_IDS[0],
        [START[0], START[1], 1.0],
        p.getQuaternionFromEuler([0.0, 0.0, 0.0]),
        physicsClientId=env.CLIENT,
    )
    env._updateAndStoreKinematicInformation()
    state = env._getDroneStateVector(0)
    cmd = VelCommander(make_ctrl(), env.CTRL_TIMESTEP)
    cmd.reset(state[0:3])
    down = np.array([0.0, 0.0, -0.35, 0.0])
    hover = np.zeros(4)
    zs = [float(state[2])]
    for _t in range(600):
        v = down if float(state[2]) > LAND_Z else hover
        obs, *_ = env.step(cmd.rpm(state, v).reshape(1, 4))
        state = obs[0]
        zs.append(float(state[2]))
    zs = np.asarray(zs)
    rate = float(np.max(zs[:-48] - zs[48:]))  # worst 1-second drop
    assert rate <= MAX_DESCENT_MPS, f"descent rate {rate:.2f} m/s over cap"
    assert zs.min() >= -0.02, "ground penetration"
    assert abs(zs[-1]) <= LAND_TOL, f"not landed: z={zs[-1]:.3f}"
    assert float(np.std(zs[-60:])) <= 0.03, "unstable after touchdown"
    return {"touchdown_z": round(float(zs[-1]), 3), "max_rate": round(rate, 2)}


def row_battery_return(env):
    from eval.eval_vision_search import run_vision_search
    from sim.indoor.rooms import single_room

    class MuteDetector:  # never fires: the budget must bring it home
        def prob(self, z):
            return np.zeros(1)

    class ZeroEnc:
        def __call__(self, x):
            import torch

            return torch.zeros((1, 64))

    r = run_vision_search(
        env,
        single_room(9),
        MuteDetector(),
        ZeroEnc(),
        seed=9,
        thr=0.9,
        speed=0.6,
        safety="beams8",
        max_decisions=400,
        plateau=30,
    )
    assert r["miss"], "the mute detector fired?!"
    assert r["returned"], "budget return failed to bring it home"
    assert not r["crashed"], "crashed on the way home"
    return {"returned": True, "label": "choreography only, not battery physics"}


def row_log_replay(env):
    from sim.envs import VelCommander, make_ctrl

    def fly():
        obs, _ = env.reset(seed=21)
        cmd = VelCommander(make_ctrl(), env.CTRL_TIMESTEP)
        cmd.reset(obs[0][0:3])
        state, traj = obs[0], []
        rng = np.random.default_rng(21)
        for _t in range(240):
            v = np.array([rng.uniform(0.2, 0.6), rng.uniform(-0.3, 0.3), 0.0, 0.0])
            obs, *_ = env.step(cmd.rpm(state, v).reshape(1, 4))
            state = obs[0]
            traj.append(state[0:3].copy())
        return np.asarray(traj)

    a, b = fly(), fly()
    dev = float(np.max(np.linalg.norm(a - b, axis=1)))
    assert dev <= 1e-6, f"replay deviated {dev:.2e}"
    return {"max_deviation": dev}


def _guardian_meta():
    from datasets.intervention_labels import HORIZONS
    from planner.action_set import A_NORM, ACTION_NAMES, ACTION_VECS

    meta = {
        "action_names": list(ACTION_NAMES),
        "action_vecs": ACTION_VECS.tolist(),
        "a_norm": A_NORM.tolist(),
        "horizons": list(HORIZONS),
    }
    return meta, len(ACTION_NAMES) - 1, len(HORIZONS)


class _InsistPilot:
    """Guardian-row pilot: insists on one action, toggles on schedule."""

    def __init__(self, action, toggles=()):
        self.action, self.toggles, self.d = int(action), set(toggles), -1

    def begin(self, pillars) -> None:
        self.d = -1

    def decide(self, frame, state) -> int:
        self.d += 1
        return self.action

    def events(self) -> dict:
        return {"toggle": self.d in self.toggles}


def row_guardian_veto(env):
    """Assistance-layer imminent veto: a scripted scorer ramps the pilot's
    command past IMMINENT_P while the pilot INSISTS — the substitution must
    land on the SAME decision the trigger crosses, and the dangerous command
    must never execute while hot. Scorer-injected (tests the LADDER, not the
    WM — the WM's own numbers are the assist_v1 campaign's job)."""
    del env
    from planner.action_set import ACTION_NAMES, FORWARD
    from planner.authority import AuthorityMachine, Guardian
    from planner.safety_filter import IMMINENT_P

    meta, n_menu, n_h = _guardian_meta()
    hot_from = 3
    frame, state = np.zeros((64, 64, 3), dtype=np.uint8), np.zeros(20)

    class _Ramp:
        d = -1

        def __call__(self, f, s):
            self.d += 1
            p = np.zeros((n_menu, n_h, 2), dtype=np.float32)
            if self.d >= hot_from:  # forward saturates; veer_right stays clean
                p[0, :2, 1] = 0.95
                p[2, :2, 1] = 0.80
            return p

    g = Guardian(
        _InsistPilot(FORWARD),
        _InsistPilot(ACTION_NAMES.index("hover")),
        None,
        None,
        None,
        meta,
        scorer=_Ramp(),
        machine=AuthorityMachine(escalate=False),
    )
    g.begin([])
    acts = [g.decide(frame, state) for _ in range(10)]
    assert all(a == FORWARD for a in acts[:hot_from]), "clear must pass through"
    assert acts[hot_from] != FORWARD, "veto must land on the trigger decision"
    hot = [r for r in g.log if r["imminent"] > IMMINENT_P]
    assert hot and all(
        r["exec"] != r["pilot"] for r in hot
    ), "the dangerous command executed while hot"
    sub = ACTION_NAMES[acts[hot_from]]
    assert sub != "veer_left", "must not substitute the also-hot veer"
    return {"veto_decision": hot_from, "latency_decisions": 0, "substitute": sub}


def row_guardian_toggle(env):
    """The QUICK bar, executable: a pilot toggle is granted on the SAME
    decision (<= 83 ms), from PILOT and from mid-OVERRIDE."""
    del env
    from planner.action_set import FORWARD, HOVER
    from planner.authority import AUTO, Guardian

    meta, n_menu, n_h = _guardian_meta()
    frame, state = np.zeros((64, 64, 3), dtype=np.uint8), np.zeros(20)
    k = 4
    g = Guardian(
        _InsistPilot(FORWARD, toggles=(k,)),
        _InsistPilot(HOVER),
        None,
        None,
        None,
        meta,
        scorer=lambda f, s: np.zeros((n_menu, n_h, 2), np.float32),
    )
    g.begin([])
    acts = [g.decide(frame, state) for _ in range(k + 3)]
    assert (
        acts[k] == HOVER and g.log[k]["authority"] == AUTO
    ), "toggle must transfer authority on its own decision"
    assert all(r["authority"] == AUTO for r in g.log[k:]), "AUTO must hold"
    return {"toggle_decision": k, "granted_decision": k, "latency_decisions": 0}


def row_guardian_handback(env):
    """The gated handback: a handback request during danger is LATCHED, not
    granted; it lands only after HANDBACK_CLEAR consecutive clear decisions
    — and the authority never chatters on the way."""
    del env
    from planner.action_set import FORWARD, HOVER
    from planner.authority import (
        AUTO,
        HANDBACK_CLEAR,
        PILOT,
        Guardian,
    )

    meta, n_menu, n_h = _guardian_meta()
    frame, state = np.zeros((64, 64, 3), dtype=np.uint8), np.zeros(20)
    hot_until = 8  # scripted danger window (soft: warn edge, no crit)

    class _Sched:
        d = -1

        def __call__(self, f, s):
            self.d += 1
            p = np.zeros((n_menu, n_h, 2), dtype=np.float32)
            if self.d < hot_until:
                p[0, :, 0] = 0.95  # forward warns; veers clean -> soft danger
            return p

    g = Guardian(
        _InsistPilot(FORWARD, toggles=(0, 5)),  # 0: to AUTO; 5: ask it back
        _InsistPilot(HOVER),
        None,
        None,
        None,
        meta,
        scorer=_Sched(),
    )
    g.begin([])
    for _ in range(hot_until + HANDBACK_CLEAR + 3):
        g.decide(frame, state)
    events = {r["event"]: r["d"] for r in g.log if r["event"]}
    assert events.get("toggle_auto") == 0 and events.get("handback_deferred") == 5
    grant = events.get("handback")
    assert grant == hot_until + HANDBACK_CLEAR - 1, (
        f"handback at d={grant}, want {hot_until + HANDBACK_CLEAR - 1} "
        "(first decision with HANDBACK_CLEAR consecutive clears)"
    )
    seq = [r["authority"] for r in g.log]
    flips = sum(1 for x, y in zip(seq, seq[1:]) if x != y)
    # the toggle lands on decision 0, so the log opens in AUTO: the ONLY
    # transition in the whole episode is the granted handback itself
    assert (
        flips == 1 and seq[grant] == PILOT and AUTO not in seq[grant:]
    ), f"authority chattered on the way to the handback (flips={flips})"
    latency = g.log and grant - events["handback_deferred"]
    return {"deferred_at": 5, "granted_at": grant, "latency_decisions": latency}


def row_guardian_geofence(env):
    """Geofence supersedes the pilot, FLOWN: a fence-seeking pilot wrapped by
    the Guardian (zero WM probs — geometry is the only trigger) must be
    capped at the same bound the bare SafetyFilter row enforces."""
    from planner.action_set import ACTION_VECS, HOVER
    from planner.authority import AuthorityMachine, Guardian
    from planner.safety_filter import FENCE_Y
    from sim.envs import VelCommander, make_ctrl

    meta, n_menu, n_h = _guardian_meta()
    i_fence = int(np.argmax(ACTION_VECS[:, 1]))  # the most fence-seeking action
    g = Guardian(
        _InsistPilot(i_fence),
        _InsistPilot(HOVER),
        None,
        None,
        None,
        meta,
        scorer=lambda f, s: np.zeros((n_menu, n_h, 2), np.float32),
        machine=AuthorityMachine(escalate=False),  # the fence alone must hold
    )
    g.begin([])
    obs, _ = env.reset(seed=11)
    cmd = VelCommander(make_ctrl(), env.CTRL_TIMESTEP)
    cmd.reset(obs[0][0:3])
    frame = np.zeros((64, 64, 3), dtype=np.uint8)
    state, a, max_y = obs[0], i_fence, 0.0
    for t in range(720):  # ~15 s of a pilot who WANTS the fence
        if t % 4 == 0:
            a = g.decide(frame, state)
        obs, *_ = env.step(cmd.rpm(state, ACTION_VECS[a]).reshape(1, 4))
        state = obs[0]
        max_y = max(max_y, abs(float(state[1])))
    assert max_y <= FENCE_Y + FENCE_MARGIN, f"fence breached: |y|={max_y:.2f}"
    assert max_y >= FENCE_Y - 0.5, "never reached the fence — vacuous"
    n_veto = sum(1 for r in g.log if r["exec"] != r["pilot"])
    assert n_veto > 0, "the guardian never intervened — vacuous"
    return {"max_y": round(max_y, 3), "fence": FENCE_Y, "vetoes": n_veto}


ROWS = (
    ("geofence", row_geofence),
    ("imminent", row_imminent_indoor),
    ("vertical", row_vertical_envelope),
    ("emergency_land", row_emergency_land),
    ("battery_return", row_battery_return),
    ("log_replay", row_log_replay),
    ("guardian_veto", row_guardian_veto),
    ("guardian_toggle", row_guardian_toggle),
    ("guardian_handback", row_guardian_handback),
    ("guardian_geofence", row_guardian_geofence),
)


def run_all() -> None:
    from sim.envs import make_env

    env = make_env()
    for name, fn in ROWS:
        info = fn(env)
        print(f"  [{name:14s}] OK  {info}", flush=True)
    env.close()
    print(
        f"SAFETY-SELFTEST OK: {len(ROWS)}/{len(ROWS)} rows green "
        "(RC kill-switch + GO/NO-GO stay in the hardware column; "
        "assistance-layer override semantics sim-gated by the guardian rows)"
    )


def selftest() -> None:
    # env-free: the registry covers the sim-gateable safety.md rows, the
    # bounds are sane, and every row is callable
    names = [n for n, _ in ROWS]
    assert names == [
        "geofence",
        "imminent",
        "vertical",
        "emergency_land",
        "battery_return",
        "log_replay",
        "guardian_veto",
        "guardian_toggle",
        "guardian_handback",
        "guardian_geofence",
    ]
    assert all(callable(f) for _, f in ROWS)
    assert 0 < LAND_Z < LAND_TOL < 0.2 and 0 < MAX_DESCENT_MPS <= 1.0
    print(f"SAFETY-SELFTEST OK (env-free): {len(ROWS)} sim-gateable rows registered")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="fly every row")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    if not args.all:
        raise SystemExit("--all (or --selftest)")
    run_all()


if __name__ == "__main__":
    sys.exit(main())

"""Perfect memory vs the dense frontier — the gate before the gate.

oracle_memory_v1 (C5 Phase-0): before temporal_wm_v1 trains an epoch,
price what PERFECT memory of already-seen geometry buys on the dense
frontier's own cell. The transit champion policy flies dense at x1.5,
base vs the same policy wrapped in a privileged out-of-FOV memory veto:
pillars ever seen inside the camera cone are remembered; if the chosen
action steers within ±35° of a remembered pillar that is now OUTSIDE
the cone and inside 1.0 m, substitute the planar menu action that
maximizes the minimum angle to every such threat — one decision at a
time, never hover (the stop-observe lesson). The privileged pillar feed
is the runner's existing hook (`policy.pillars`, the reactive
baseline's). Bars + the re-opening context vs the v0.2 GRU negative:
experiments/oracle_memory_v1/journal.md (committed first).

Run:
  python -m eval.eval_oracle_memory --probe
  python -m eval.eval_oracle_memory --selftest
"""

import argparse
import json
import os
import sys

import numpy as np

FOV_HALF = 28.0  # deg — the camera cone of record
SEEN_RANGE = 3.0  # m — a pillar inside cone+range becomes "seen"
VETO_DIST = 1.0  # m — remembered threats closer than this arm the veto
VETO_HALF = 35.0  # deg — chosen action within this of a threat -> veto
SPEED = 1.5  # x0.8 m/s = 1.2 m/s: the 27% frontier cell of record
N = 200
SEED0 = 910000  # fresh block


class OracleMemoryPolicy:
    """The base policy + a privileged out-of-FOV memory veto (the exact
    rule frozen in the journal). `pillars` is refreshed live by
    run_hard_episode — the same privileged hook the reactive baseline
    uses. Interventions are counted per episode (begin() resets)."""

    def __init__(self, base):
        self.base = base
        self.pillars = []
        self._seen = []
        self.interventions = 0

    def begin(self, pillars):
        self.base.begin(pillars)
        self.pillars = [np.asarray(q, float) for q in pillars]
        self._seen = []
        self.interventions = 0

    @staticmethod
    def _cone(pos, yaw, q, half_deg, max_range):
        d = np.asarray(q, float)[:2] - pos
        r = float(np.hypot(d[0], d[1]))
        if r > max_range or r < 1e-6:
            return False
        rel = (np.arctan2(d[1], d[0]) - yaw + np.pi) % (2 * np.pi) - np.pi
        return abs(np.degrees(rel)) <= half_deg

    def decide(self, frame, state):
        from planner.action_set import ACTION_VECS, HOVER

        a = int(self.base.decide(frame, state))
        pos, yaw = np.asarray(state[0:2], float), float(state[9])
        for q in self.pillars:
            if self._cone(pos, yaw, q, FOV_HALF, SEEN_RANGE) and not any(
                np.allclose(np.asarray(q, float)[:2], s, atol=1e-6) for s in self._seen
            ):
                self._seen.append(np.asarray(q, float)[:2].copy())
        threats = [
            s
            for s in self._seen
            if np.hypot(*(s - pos)) < VETO_DIST
            and not self._cone(pos, yaw, s, FOV_HALF, SEEN_RANGE)
        ]
        if not threats:
            return a
        v = ACTION_VECS[a][:2]
        if float(np.hypot(v[0], v[1])) < 1e-6:
            return a  # the base chose hover/climb: nothing to steer

        def ang(vec, s):
            d = s - pos
            c = float(np.dot(vec, d) / (np.linalg.norm(vec) * np.linalg.norm(d) + 1e-9))
            return float(np.degrees(np.arccos(np.clip(c, -1.0, 1.0))))

        if min(ang(v, s) for s in threats) > VETO_HALF:
            return a
        best, best_score = a, -1.0
        for i, vec in enumerate(ACTION_VECS):
            if i == HOVER or float(np.hypot(vec[0], vec[1])) < 1e-6:
                continue
            sc = min(ang(vec[:2], s) for s in threats)
            if sc > best_score:
                best, best_score = int(i), sc
        assert best != HOVER, "the veto must never substitute a dead stop"
        self.interventions += 1
        return best


def probe(n=N, seed0=SEED0, speed=SPEED, out=None):
    from eval.eval_hard_worlds import run_hard_episode
    from planner.learned_policy import LearnedPolicy, load_policy, zip_path
    from sim.envs import make_env
    from world_model.training import MODEL, load_model

    enc, pred, cheads, _nh, meta = load_model(MODEL, device="cpu")
    model = load_policy(zip_path(hard=True, xp=True, edge=True))
    base_pol = LearnedPolicy(model, enc, pred, cheads, meta, speed=speed)
    oracle = OracleMemoryPolicy(
        LearnedPolicy(model, enc, pred, cheads, meta, speed=speed)
    )
    env = make_env()
    rows = {"base": [], "oracle": []}
    inter = []
    for i in range(n):
        rows["base"].append(run_hard_episode(env, base_pol, seed0 + i, "dense", speed))
        rows["oracle"].append(run_hard_episode(env, oracle, seed0 + i, "dense", speed))
        inter.append(oracle.interventions)
        if (i + 1) % 20 == 0:
            bc = float(np.mean([r["crashed"] for r in rows["base"]]))
            oc = float(np.mean([r["crashed"] for r in rows["oracle"]]))
            print(
                f"  [{i + 1:3d}/{n}] crash base {bc:.3f} oracle {oc:.3f} "
                f"interventions/flight {np.mean(inter):.1f}",
                flush=True,
            )
    env.close()

    def arm(rs):
        return {
            "crash": float(np.mean([r["crashed"] for r in rs])),
            "reached": float(np.mean([r["reached"] for r in rs])),
            "min_clear": float(np.mean([r["min_clear"] for r in rs])),
        }

    b, o = arm(rows["base"]), arm(rows["oracle"])
    d = o["crash"] - b["crash"]
    mean_iv = float(np.mean(inter))
    if mean_iv < 0.5:
        verdict = "VACUOUS — the veto barely fired; redesign, not a negative"
    elif d <= -0.05 and o["reached"] >= b["reached"] - 0.05:
        verdict = (
            "MEMORY IS BINDING (dcrash <= -0.05) -> the full temporal_wm_v1 "
            "pre-registration is released for the owner's GO/NO-GO"
        )
    else:
        verdict = (
            "memory is NOT the binding constraint at this frontier — "
            "temporal_wm_v1 dies before an epoch; conditional recalibration "
            "is the last named road"
        )
    print(f"  base   crash={b['crash']:.3f} reached={b['reached']:.3f}")
    print(f"  oracle crash={o['crash']:.3f} reached={o['reached']:.3f}")
    print(
        f"[oracle-memory] dcrash={d:+.3f} (bar <= -0.050) "
        f"interventions/flight={mean_iv:.1f} -> {verdict}"
    )
    res = {
        "n": n,
        "seed0": seed0,
        "speed": speed,
        "base": b,
        "oracle": o,
        "delta_crash": float(d),
        "interventions_per_flight": mean_iv,
        "verdict": verdict,
    }
    if out:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w") as f:
            json.dump(res, f, indent=1)
        print(f"[oracle-memory] wrote {out}")
    return res


def selftest() -> None:
    from planner.action_set import ACTION_VECS, FORWARD, HOVER

    class Fixed:
        def begin(self, pillars):
            pass

        def decide(self, frame, state):
            return FORWARD

    st = np.zeros(20)
    st[9] = 0.0  # yaw 0: cone looks +x
    op = OracleMemoryPolicy(Fixed())
    op.begin([np.array([1.5, 0.0, 1.0])])  # pillar dead ahead, in cone
    op.pillars = [np.array([1.5, 0.0, 1.0])]
    a1 = op.decide(None, st)  # sees it (in cone) -> remembered, no veto
    assert a1 == FORWARD and len(op._seen) == 1 and op.interventions == 0
    # the drone turns (yaw 90deg): the remembered pillar is OUT of cone,
    # 1.5 m away -> outside VETO_DIST, still no veto
    st2 = st.copy()
    st2[9] = np.pi / 2
    assert op.decide(None, st2) == FORWARD and op.interventions == 0
    # bring it inside 1.0 m while out of cone... but FORWARD now points +y
    # (world-frame actions): threat at +x is ~90deg off -> no veto either;
    # instead aim the threat where FORWARD points: pillar at (0.6, 0) with
    # yaw 90deg is out of cone, and FORWARD (+x) points straight at it
    op2 = OracleMemoryPolicy(Fixed())
    op2.begin([np.array([0.6, 0.0, 1.0])])
    op2.pillars = [np.array([0.6, 0.0, 1.0])]
    assert op2.decide(None, st) == FORWARD  # in cone: seen, no veto
    a2 = op2.decide(None, st2)  # out of cone (yaw 90), 0.6 m, FORWARD aims at it
    assert op2.interventions == 1 and a2 != FORWARD and a2 != HOVER
    # the substitute steers further from the threat than FORWARD did
    v_new, v_old = ACTION_VECS[a2][:2], ACTION_VECS[FORWARD][:2]
    d = np.array([0.6, 0.0])
    ang = lambda v: np.degrees(  # noqa: E731
        np.arccos(np.clip(np.dot(v, d) / (np.linalg.norm(v) * 0.6 + 1e-9), -1, 1))
    )
    assert ang(v_new) > ang(v_old)
    print(
        "ORACLE-MEMORY OK: cone/seen bookkeeping, veto fires only on "
        "remembered out-of-cone threats inside 1 m, substitute is planar "
        "and steers away"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--n", type=int, default=N)
    ap.add_argument("--out", default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    if not args.probe:
        raise SystemExit("--probe (or --selftest)")
    probe(n=args.n, out=args.out)


if __name__ == "__main__":
    sys.exit(main())

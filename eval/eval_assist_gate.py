"""assist_v1 — the assisted-flight (Level 3) feasibility probe and gate.

The chapter's question, in the repo's own currency: how much of a HUMAN
pilot's crash mass can the world model's 0.67 s of anticipation buy back,
and at what cost in freedom? Protocol (pre-registration:
experiments/assist_v1/journal.md — committed BEFORE any number):

  Stage A  the pilot map: unassisted persona x world x speed cells validate
           the instrument (usable band: crash_u in [0.15, 0.85]).
  Stage B  guardian arms on the same seeds, PAIRED (eval/assist_episode):
             wm_unified   the contender — vision-only WM guardian
             wm_champion  control (unified's 6% false-evasion prior)
             oracle       privileged ceiling — perfect eyes, same ladder,
                          never a contender; prices the kinematic floor
           plus the full-auto champion reference column (persona-free).
  Bars     frozen FROM the probe in a follow-up commit (the indoor-gate
           pattern); the gate flies fresh seeds (probe + GATE_OFF) at the
           DEPLOYED trigger constants — no threshold fishing.

Run:
  python -m eval.eval_assist_gate --probe 20
  python -m eval.eval_assist_gate --gate 30      # refuses until bars freeze
  python -m eval.eval_assist_gate --budget
  python -m eval.eval_assist_gate --selftest
"""

import argparse
import json
import os
import sys

import numpy as np

from eval.assist_episode import (
    ASSIST_SPEEDS,
    ASSIST_WORLDS,
    GATE_OFF,
    SEED0,
    aggregate,
    pair_record,
    run_assist_episode,
)
from sim.envs import CTRL_HZ
from sim.scenarios import RADII

PERSONA_GRID = ("novice", "average", "expert")
CELLS = tuple(
    (w, s, per) for w in ASSIST_WORLDS for s in ASSIST_SPEEDS for per in PERSONA_GRID
)  # 12 barred-candidate cells; +1 labelled diagnostic:
DIAG_CELLS = (("moving", 1.0, "average"),)  # movers: WM v2 sees no velocity
ARMS = ("wm_unified", "wm_champion", "oracle")
OUT_DIR = os.path.join("experiments", "assist_v1")

# Frozen AFTER the probe, in their own commit (never edited once the gate
# flies). None = the gate refuses to run — probe first.
BARS = None

# every seed block this repo has ever spent (kept in sync by the selftest's
# disjointness assert; the assist block is 800000..800000+15*1000+GATE_OFF+60)
_SEED_LEDGER = (
    1000,
    3000,
    7000,
    9000,
    30000,
    31000,
    40000,
    60000,
    90000,
    91000,
    92000,
    100000,
    110000,
    120000,
    130000,
    140000,
    158000,
    162000,
    210000,
    600000,
    740000,
    750000,
    910000,
)
_BLOCK_SPAN = (len(CELLS) + len(DIAG_CELLS) + 1) * 1000 + GATE_OFF + 1000


def _meta_from_constants() -> dict:
    """A checkpoint-free meta for privileged arms (latent_mpc.selftest idiom)."""
    from datasets.intervention_labels import HORIZONS
    from planner.action_set import A_NORM, ACTION_NAMES, ACTION_VECS

    return {
        "action_names": list(ACTION_NAMES),
        "action_vecs": ACTION_VECS.tolist(),
        "a_norm": A_NORM.tolist(),
        "horizons": list(HORIZONS),
    }


def _seg_dist(a: np.ndarray, b: np.ndarray, pillars) -> float:
    """Min planar distance from any pillar to the segment a->b."""
    ab = b - a
    den = float(ab @ ab)
    best = 9.0
    for q in pillars:
        q = np.asarray(q, dtype=float)[:2]
        t = 0.0 if den <= 1e-12 else float(np.clip((q - a) @ ab / den, 0.0, 1.0))
        best = min(best, float(np.linalg.norm(a + t * ab - q)))
    return best


class OracleScorer:
    """PRIVILEGED ceiling eyes — never a contender. Each menu command is
    forward-simulated at constant velocity over the WM's own horizons
    against the true pillar layout, and emitted in the collision heads'
    exact vocabulary (per-horizon warn/crit ring hits). Same ladder, same
    triggers, perfect eyes: crashes even THIS arm cannot prevent are
    kinematically committed — the honest floor under every WM claim.
    Static geometry only (the moving column stays a labelled diagnostic)."""

    def __init__(self, meta: dict, speed: float = 1.0):
        names = list(meta["action_names"])
        vecs = float(speed) * np.array(meta["action_vecs"], dtype=np.float32)
        ids = [i for i, n in enumerate(names) if n != "climb"]
        self.vec = vecs[ids][:, :2]
        self.horizons = tuple(int(h) for h in meta["horizons"])
        self.pillars: list = []  # guardian-forwarded privileged refresh

    def __call__(self, frame, state) -> np.ndarray:
        del frame
        xy = np.asarray([float(state[0]), float(state[1])])
        p = np.zeros((len(self.vec), len(self.horizons), 2), dtype=np.float32)
        for k, v in enumerate(self.vec):
            for hi, h in enumerate(self.horizons):
                d = _seg_dist(xy, xy + v * (h / CTRL_HZ), self.pillars)
                p[k, hi, 0] = 1.0 if d < RADII[0] else 0.0
                p[k, hi, 1] = 1.0 if d < RADII[1] else 0.0
        return p


# --- arm factories ------------------------------------------------------------
def make_pilot_factory(persona: str, seed: int):
    from assist.pilot import SyntheticPilot

    return lambda: SyntheticPilot(persona, seed)


def guardian_factory(arm: str, speed: float, margin: float = None):
    """-> make_guardian(pilot) for one arm. WM arms ride the real artifacts;
    the oracle arm is artifact-free (privileged scorer + near-perfect
    scripted takeover pilot). `margin` overrides the escalation edge for the
    LABELLED characterization sweep only — the gate always flies None (the
    deployed constant)."""
    from planner.authority import Guardian

    if arm == "oracle":
        from assist.pilot import PERFECT, SyntheticPilot

        meta = _meta_from_constants()

        def make(pilot):
            return Guardian(
                pilot,
                SyntheticPilot(PERFECT, 0),
                None,
                None,
                None,
                meta,
                speed=speed,
                scorer=OracleScorer(meta, speed=speed),
                margin=margin,
            )

        return make

    from planner.flight_mode import UNIFIED_WM, load_wm_cached
    from planner.latent_mpc import WMPolicy
    from world_model.training import MODEL

    wm_path = {"wm_unified": UNIFIED_WM, "wm_champion": MODEL}[arm]
    enc, pred, cheads, _n, meta = load_wm_cached(wm_path)

    def make(pilot):
        auto = WMPolicy(enc, pred, cheads, meta, speed=speed)
        return Guardian(
            pilot, auto, enc, pred, cheads, meta, speed=speed, margin=margin
        )

    return make


def champion_reference(speed: float):
    """The Level-4 datum: the deployed transit champion on the same seeds."""
    from planner.flight_mode import load_wm_cached
    from planner.learned_policy import LearnedPolicy, load_policy, zip_path
    from world_model.training import MODEL

    enc, pred, cheads, _n, meta = load_wm_cached(MODEL)
    model = load_policy(zip_path(hard=True, xp=True, edge=True))
    return LearnedPolicy(model, enc, pred, cheads, meta, speed=speed)


# --- the probe ----------------------------------------------------------------
def probe(n: int = 20, arms=ARMS, out_json: str = None, margin: float = None) -> dict:
    """Stage A + Stage B in one sweep: per cell, fly the unassisted arm once
    per seed, then pair every guardian arm against it; the champion
    reference flies per (world, speed) — it is persona-free. Cells dump to
    `out_json` incrementally, so a killed run keeps its finished cells."""
    from sim.envs import make_env

    print(
        f"[assist-probe] config: n={n}/cell seed0={SEED0} "
        f"cells={len(CELLS)}+{len(DIAG_CELLS)}diag arms={arms} "
        f"speeds={ASSIST_SPEEDS} worlds={ASSIST_WORLDS}+moving "
        f"margin={'deployed' if margin is None else margin} "
        f"(escalation ladder ON)"
    )
    env = make_env()
    cells_out, ref_out = [], {}

    def _dump():
        if not out_json:
            return
        os.makedirs(os.path.dirname(out_json), exist_ok=True)
        with open(out_json, "w") as f:
            json.dump(
                {
                    "config": {
                        "n": n,
                        "seed0": SEED0,
                        "arms": list(arms),
                        "margin": margin,
                        "worlds": list(ASSIST_WORLDS),
                        "speeds": list(ASSIST_SPEEDS),
                        "personas": list(PERSONA_GRID),
                    },
                    "cells": cells_out,
                    "full_auto_ref": {f"{w}@{s}": v for (w, s), v in ref_out.items()},
                },
                f,
                indent=1,
            )

    try:
        for idx, (world, speed, persona) in enumerate(CELLS + DIAG_CELLS):
            s0 = SEED0 + idx * 1000
            makers = {a: guardian_factory(a, speed, margin=margin) for a in arms}
            eps_u, recs = [], {a: [] for a in arms}
            for i in range(n):
                seed = s0 + i
                mk = make_pilot_factory(persona, seed)
                ep_u = run_assist_episode(env, mk(), seed, world, speed)
                eps_u.append(ep_u)
                for a in arms:
                    ep_a = run_assist_episode(env, makers[a](mk()), seed, world, speed)
                    recs[a].append(pair_record(ep_u, ep_a))
            row = {
                "cell": f"{world}@{speed}/{persona}",
                "world": world,
                "speed": speed,
                "persona": persona,
                "seed0": s0,
                "diagnostic": (world, speed, persona) in DIAG_CELLS,
                "crash_u": round(float(np.mean([e["crashed"] for e in eps_u])), 4),
                "reach_u": round(float(np.mean([e["reached"] for e in eps_u])), 4),
                "arms": {a: aggregate(recs[a]) for a in arms},
            }
            cells_out.append(row)
            arms_txt = "  ".join(
                f"{a}: dcrash={row['arms'][a]['dcrash']:+.3f} "
                f"ov={row['arms'][a]['override_rate']}"
                for a in arms
            )
            print(f"  [{row['cell']:24s}] crash_u={row['crash_u']:.2f}  {arms_txt}")
            if (world, speed) not in ref_out:
                ref = champion_reference(speed)
                eps = [
                    run_assist_episode(env, ref, s0 + i, world, speed) for i in range(n)
                ]
                ref_out[(world, speed)] = {
                    "crash": round(float(np.mean([e["crashed"] for e in eps])), 4),
                    "reach": round(float(np.mean([e["reached"] for e in eps])), 4),
                }
                print(
                    f"  [{world}@{speed} full-auto ref ] "
                    f"crash={ref_out[(world, speed)]['crash']:.2f}"
                )
            _dump()  # finished cells survive a killed run
    finally:
        env.close()
    _dump()
    if out_json:
        print(f"[assist-probe] wrote {out_json}")
    return {
        "cells": cells_out,
        "full_auto_ref": {f"{w}@{s}": v for (w, s), v in ref_out.items()},
    }


def gate(n: int = 30) -> None:
    if BARS is None:
        raise SystemExit(
            "assist_v1 gate: bars are not frozen yet — run the probe, freeze "
            "the bars from it in their own commit (experiments/assist_v1/"
            "journal.md), then fly the gate on fresh seeds (+GATE_OFF)."
        )
    raise SystemExit("assist_v1 gate: bar-freeze commit must implement this")


def budget() -> None:
    """The embedded bill for the guardian: weights +0 KB, and the deployed
    decision path is EXACTLY the MPC's (encoder once + one menu MLP sweep —
    the pilot's command is a menu row, the authority machine is scalar
    bookkeeping). The Python prototype composes guardian + warm autopilot as
    two policies (~2 encoder passes/tick, correctness-by-composition); a
    deployment shares the single pass — both numbers printed, dispatch-note
    style."""
    from assist.pilot import SyntheticPilot
    from eval.eval_closed_loop import load_or_train
    from eval.eval_latency_budget import GAP8_GMACS, measure_latency, onboard_budget
    from planner.authority import Guardian
    from planner.latent_mpc import WMPolicy
    from world_model.training import GAP8_BUDGET_KB

    enc, pred, cheads, nhead, meta = load_or_train(device="cpu")
    b = onboard_budget(enc, pred, cheads, nhead)
    gap8_ms = b["macs_decision"] / (GAP8_GMACS * 1e9) * 1000
    g = Guardian(
        SyntheticPilot("average", 0),
        WMPolicy(enc, pred, cheads, meta),
        enc,
        pred,
        cheads,
        meta,
    )
    proto_ms = measure_latency(g)
    print(
        f"ASSIST-BUDGET OK: guardian weights +0.0 KB (total stays "
        f"{b['total_kb']:.1f} KB < {GAP8_BUDGET_KB} KB); deployed decision = "
        f"the MPC's own {b['macs_decision'] / 1e6:.1f} M MACs "
        f"(~{gap8_ms:.0f} ms est @ GAP8, shared encoder) | prototype "
        f"{proto_ms:.1f} ms/decision on this CPU (guardian sweep + warm "
        f"autopilot as two policies; a deployment shares the single pass)"
    )
    assert b["total_kb"] < GAP8_BUDGET_KB
    assert gap8_ms < 1000.0 / 12, "guardian must fit the 12 Hz decision loop"


def selftest() -> None:
    # the grid is what the prereg says it is
    assert len(CELLS) == 12 and len(DIAG_CELLS) == 1
    assert all(w in ASSIST_WORLDS for w, _s, _p in CELLS)
    assert DIAG_CELLS[0][0] == "moving"
    assert set(ARMS) == {"wm_unified", "wm_champion", "oracle"}
    # the assist seed block is virgin and self-contained
    lo, hi = SEED0, SEED0 + _BLOCK_SPAN
    assert not any(lo <= s < hi for s in _SEED_LEDGER), "seed block collision"
    assert hi < 910000 - 0 or lo > 910000, "stay clear of the 910k block"
    assert BARS is None or isinstance(BARS, dict)
    # oracle geometry: a pillar dead ahead fires forward's far-horizon crit,
    # never hover's; the veer away stays clean
    from planner.action_set import ACTION_NAMES, FORWARD, HOVER

    meta = _meta_from_constants()
    sc = OracleScorer(meta, speed=1.0)
    sc.pillars = [(0.60, 0.0)]
    state = np.zeros(20)
    p = sc(None, state)
    ids = [i for i, n in enumerate(ACTION_NAMES) if n != "climb"]
    j_fwd, j_hov = ids.index(FORWARD), ids.index(HOVER)
    j_vl = ids.index(ACTION_NAMES.index("veer_left"))
    assert p[j_fwd, -1, 1] == 1.0, "0.60 m ahead at 0.8 m/s hits crit in 0.67 s"
    assert p[j_hov, :, 1].max() == 0.0, "hover never reaches the pillar"
    assert p[j_vl, -1, 1] == 0.0, "the veer clears the crit ring (0.42 m)"
    assert p[j_vl, -1, 0] == 1.0, "...but does cross the warn ring — honest"
    assert p[j_fwd, 0, 1] == 0.0, "83 ms is too short to close 0.60 m"
    # a guardian on the oracle scorer vetoes the charge, artifact-free
    from assist.pilot import PERFECT, SyntheticPilot
    from planner.authority import Guardian

    class _Charge:
        pillars: list = []

        def begin(self, pillars):
            pass

        def decide(self, frame, state):
            return FORWARD

    g = Guardian(
        _Charge(),
        SyntheticPilot(PERFECT, 0),
        None,
        None,
        None,
        meta,
        scorer=OracleScorer(meta, speed=1.0),
    )
    g.begin([(0.30, 0.0)])
    g.pillars = [(0.30, 0.0)]
    a = g.decide(np.zeros((64, 64, 3), np.uint8), state)
    assert a != FORWARD and g.log[0]["event"] == "override_fire"
    print(
        f"ASSIST-GATE OK (env-free): {len(CELLS)}+1 cells, seed block "
        f"[{lo}, {hi}) disjoint from the ledger, oracle geometry sane, "
        "privileged guardian vetoes the charge, bars unfrozen (probe first)"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", type=int, default=0, metavar="N")
    ap.add_argument("--gate", type=int, default=0, metavar="N")
    ap.add_argument("--budget", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--out", default=os.path.join(OUT_DIR, "probe_results.json"))
    ap.add_argument(
        "--arms", default=",".join(ARMS), help="comma list, e.g. wm_unified"
    )
    ap.add_argument(
        "--margin",
        type=float,
        default=None,
        help="LABELLED characterization sweep only — the gate flies deployed",
    )
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    if args.budget:
        budget()
        return
    if args.probe:
        arms = tuple(a for a in args.arms.split(",") if a)
        assert all(a in ARMS for a in arms), f"unknown arm in {arms}"
        probe(n=args.probe, arms=arms, out_json=args.out, margin=args.margin)
        return
    if args.gate:
        gate(n=args.gate)
        return
    raise SystemExit("--probe N | --gate N | --budget | --selftest")


if __name__ == "__main__":
    sys.exit(main())

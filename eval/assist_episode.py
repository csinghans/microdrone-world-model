"""The assisted-flight episode runner + the paired-seed protocol.

Sibling of `eval/episode.py`, which stays bit-for-bit frozen: the Guardian
(`planner.authority`) already speaks the standard policy contract, so one
assisted flight IS `run_scenario_episode`. This module adds what the ADAS
question needs on top:

  * the authority log merged into the episode dict (+ `t_impact`, the first
    48 Hz step inside COLLISION_R, derived env-free from the recorded path
    against the STATIC layout — the moving world stays a labelled
    diagnostic, its impact step is not derivable from the frozen record);
  * the counterfactual PAIRING — the same (persona, seed) flown without and
    with the guardian, so "prevented", "added" and "false intervention" are
    attributable per seed (arms share course + pilot rng and are identical
    up to the first intervention; after divergence the comparison is
    between closed-loop systems, not per-decision counterfactuals);
  * the aggregate cell scorecard (paired deltas, never levels).

Track constants below are the ONLY defaults an assist eval may silently
inherit (the ROBUST_SPEED lesson, applied from birth); the gate imports
them from here and its selftest asserts the parity.

Run:
  python -m eval.assist_episode           # env-free selftest
  python -m eval.assist_episode --sim     # + one paired smoke episode
"""

import sys

import numpy as np

from eval.episode import run_scenario_episode
from planner.authority import summarize_log
from planner.latent_mpc import DECIDE_EVERY
from sim.envs import CTRL_HZ
from sim.scenarios import COLLISION_R, TMAX

# --- track constants: the assist track's frozen config -----------------------
ASSIST_WORLDS = ("classic", "dense")  # the WM-validated collision domain
ASSIST_SPEEDS = (1.0, 1.5)  # x base -> 0.8 / 1.2 m/s cruise
SEED0 = 800000  # virgin block (ledger: 7k/30k/31k/40k/100k/110k/120k/130k/
#                140k/158k/162k/210k/600k/60-92k/740k/750k/910k all used)
GATE_OFF = 500  # gate seeds = probe seeds + GATE_OFF, never reused
STATIC_WORLDS = ("classic", "dense")  # impact-step derivation is valid here


def impact_step(path: np.ndarray, pillars) -> int:
    """First 48 Hz step index with a pillar inside COLLISION_R, else -1.
    Env-free and exact for STATIC layouts (the recorded `pillars` are the
    spawn positions, which static worlds never move)."""
    if len(pillars) == 0:
        return -1
    q = np.asarray([[float(p[0]), float(p[1])] for p in pillars])
    d = np.linalg.norm(path[:, None, :2] - q[None, :, :], axis=2).min(axis=1)
    hits = np.nonzero(d < COLLISION_R)[0]
    return int(hits[0]) if len(hits) else -1


def run_assist_episode(
    env,
    policy,
    seed: int,
    world: str,
    speed: float = 1.0,
    tmax: int = TMAX,
) -> dict:
    """One flight through the frozen runner, plus the assist-track fields.
    `policy` is either a bare pilot (the unassisted arm) or a Guardian."""
    ep = run_scenario_episode(env, policy, seed, world, speed=speed, tmax=tmax)
    ep["t_impact"] = (
        impact_step(ep["path"], ep["pillars"]) if world in STATIC_WORLDS else -1
    )
    log = list(getattr(policy, "log", []) or [])
    ep["authority"] = summarize_log(log) if log else None
    ep["authority_log"] = log
    return ep


def pair_record(ep_u: dict, ep_a: dict) -> dict:
    """The paired verdict for one seed: unassisted arm `ep_u`, assisted arm
    `ep_a`. `prevented`/`added` are per-seed crash attributions; a false
    intervention is any override on a seed whose unassisted arm was clean;
    `lead_ms` is how much earlier the guardian moved than the counterfactual
    impact it prevented (only defined on prevented seeds with an override)."""
    au = ep_a.get("authority") or {}
    n_over = int(au.get("n_overridden", 0))
    first_d = int(au.get("first_override_d", -1))
    clean_u = bool((not ep_u["crashed"]) and ep_u["reached"])
    lead_ms = None
    if (
        ep_u["crashed"]
        and not ep_a["crashed"]
        and first_d >= 0
        and ep_u["t_impact"] >= 0
    ):
        lead_ms = (ep_u["t_impact"] - first_d * DECIDE_EVERY) * 1000.0 / CTRL_HZ
    return {
        "prevented": bool(ep_u["crashed"] and not ep_a["crashed"]),
        "added": bool((not ep_u["crashed"]) and ep_a["crashed"]),
        "clean_u": clean_u,
        "false_intervened": bool(clean_u and n_over > 0),
        "crashed_u": bool(ep_u["crashed"]),
        "crashed_a": bool(ep_a["crashed"]),
        "reached_u": bool(ep_u["reached"]),
        "reached_a": bool(ep_a["reached"]),
        "steps_u": int(ep_u["steps"]),
        "steps_a": int(ep_a["steps"]),
        "n_overridden": n_over,
        "n_decisions_a": int(au.get("n_decisions", 0)),
        "n_escalations": int(au.get("n_escalations", 0)),
        "frac_auto": float(au.get("frac_auto", 0.0)),
        "lead_ms": lead_ms,
    }


def run_paired(env, make_pilot, make_guardian, seed, world, speed, tmax=TMAX):
    """THE unit of measurement: the same (pilot, seed, world, speed) flown
    twice — bare, then guardian-wrapped. `make_pilot()` must build a FRESH
    pilot per arm (same seed => same imperfection stream)."""
    ep_u = run_assist_episode(env, make_pilot(), seed, world, speed, tmax)
    ep_a = run_assist_episode(
        env, make_guardian(make_pilot()), seed, world, speed, tmax
    )
    return ep_u, ep_a, pair_record(ep_u, ep_a)


def aggregate(recs: list) -> dict:
    """The cell scorecard. Paired deltas are the read, never levels;
    denominator-starved rates return None, never NaN."""
    n = len(recs)
    if n == 0:
        return {"n": 0}
    crash_u = float(np.mean([r["crashed_u"] for r in recs]))
    crash_a = float(np.mean([r["crashed_a"] for r in recs]))
    crashes_u = int(sum(r["crashed_u"] for r in recs))
    clean = [r for r in recs if r["clean_u"]]
    dec = sum(r["n_decisions_a"] for r in recs)
    over = sum(r["n_overridden"] for r in recs)
    dec_c = sum(r["n_decisions_a"] for r in clean)
    over_c = sum(r["n_overridden"] for r in clean)
    leads = [r["lead_ms"] for r in recs if r["lead_ms"] is not None]
    both = [r for r in recs if r["reached_u"] and r["reached_a"]]
    return {
        "n": n,
        "crash_u": round(crash_u, 4),
        "crash_a": round(crash_a, 4),
        "dcrash": round(crash_a - crash_u, 4),
        "prevented": int(sum(r["prevented"] for r in recs)),
        "added": int(sum(r["added"] for r in recs)),
        "rel_cut": (
            round((crash_u - crash_a) / crash_u, 4) if crashes_u >= 3 else None
        ),
        "n_clean_u": len(clean),
        "fi": (
            round(float(np.mean([r["false_intervened"] for r in clean])), 4)
            if clean
            else None
        ),
        "override_rate": round(over / dec, 4) if dec else None,
        "override_rate_clean": round(over_c / dec_c, 4) if dec_c else None,
        "escalations": int(sum(r["n_escalations"] for r in recs)),
        "frac_auto": round(float(np.mean([r["frac_auto"] for r in recs])), 4),
        "lead_ms": round(float(np.mean(leads)), 1) if leads else None,
        "lead_n": len(leads),
        "goal_pct": (
            round(
                float(np.mean([r["steps_a"] / r["steps_u"] for r in both])) - 1.0,
                4,
            )
            if both
            else None
        ),
    }


# --- selftest -----------------------------------------------------------------
def _fake_ep(crashed, reached, steps=200, t_impact=-1, authority=None):
    return {
        "crashed": crashed,
        "reached": reached,
        "steps": steps,
        "t_impact": t_impact,
        "authority": authority,
    }


def selftest() -> None:
    import inspect

    # frozen track constants + runner-default parity (the stale-default trap)
    assert ASSIST_WORLDS == ("classic", "dense") and ASSIST_SPEEDS == (1.0, 1.5)
    assert SEED0 == 800000 and GATE_OFF == 500
    sig = inspect.signature(run_assist_episode)
    assert sig.parameters["speed"].default == 1.0
    assert sig.parameters["tmax"].default == TMAX

    # impact_step: straight run at a pillar crosses COLLISION_R exactly once
    path = np.stack([np.linspace(0, 2, 97), np.zeros(97), np.ones(97)], axis=1)
    t = impact_step(path, [(1.0, 0.0)])
    assert t > 0 and np.linalg.norm(path[t, :2] - (1.0, 0.0)) < COLLISION_R
    assert np.linalg.norm(path[t - 1, :2] - (1.0, 0.0)) >= COLLISION_R
    assert impact_step(path, [(1.0, 5.0)]) == -1 and impact_step(path, []) == -1

    # pair_record truth table over the (crash_u, crash_a, overridden) cube
    for cu in (False, True):
        for ca in (False, True):
            for over in (0, 3):
                au = {
                    "n_overridden": over,
                    "first_override_d": 5 if over else -1,
                    "n_decisions": 60,
                    "n_escalations": 0,
                    "frac_auto": 0.0,
                }
                r = pair_record(
                    _fake_ep(cu, not cu, t_impact=48 if cu else -1),
                    {**_fake_ep(ca, not ca), "authority": au},
                )
                assert r["prevented"] == (cu and not ca)
                assert r["added"] == (not cu and ca)
                assert r["clean_u"] == (not cu)
                assert r["false_intervened"] == ((not cu) and over > 0)
                want_lead = (cu and not ca) and over > 0
                assert (r["lead_ms"] is not None) == want_lead
                if want_lead:  # impact 48, first override d=5 -> step 20
                    assert abs(r["lead_ms"] - (48 - 20) * 1000.0 / 48) < 1e-6

    # aggregate: hand-checked on three synthetic pairs
    recs = [
        {  # prevented, override fired early
            "prevented": True,
            "added": False,
            "clean_u": False,
            "false_intervened": False,
            "crashed_u": True,
            "crashed_a": False,
            "reached_u": False,
            "reached_a": True,
            "steps_u": 120,
            "steps_a": 150,
            "n_overridden": 4,
            "n_decisions_a": 40,
            "n_escalations": 1,
            "frac_auto": 0.3,
            "lead_ms": 250.0,
        },
        {  # clean pass-through
            "prevented": False,
            "added": False,
            "clean_u": True,
            "false_intervened": False,
            "crashed_u": False,
            "crashed_a": False,
            "reached_u": True,
            "reached_a": True,
            "steps_u": 100,
            "steps_a": 100,
            "n_overridden": 0,
            "n_decisions_a": 25,
            "n_escalations": 0,
            "frac_auto": 0.0,
            "lead_ms": None,
        },
        {  # false intervention on a clean seed
            "prevented": False,
            "added": False,
            "clean_u": True,
            "false_intervened": True,
            "crashed_u": False,
            "crashed_a": False,
            "reached_u": True,
            "reached_a": True,
            "steps_u": 100,
            "steps_a": 110,
            "n_overridden": 2,
            "n_decisions_a": 27,
            "n_escalations": 0,
            "frac_auto": 0.0,
            "lead_ms": None,
        },
    ]
    agg = aggregate(recs)
    assert agg["n"] == 3 and agg["prevented"] == 1 and agg["added"] == 0
    assert abs(agg["dcrash"] - (-1 / 3)) < 1e-3
    assert agg["rel_cut"] is None, "rel_cut needs >=3 unassisted crashes"
    assert agg["fi"] == 0.5 and agg["n_clean_u"] == 2
    assert agg["override_rate"] == round(6 / 92, 4)
    assert agg["override_rate_clean"] == round(2 / 52, 4)
    assert agg["lead_ms"] == 250.0 and agg["lead_n"] == 1
    # goal_pct averages only seeds BOTH arms landed (recs 2+3: 1.0, 1.1)
    assert abs(agg["goal_pct"] - 0.05) < 1e-6
    assert aggregate([]) == {"n": 0}
    print(
        "ASSIST-EPISODE OK (env-free): paired truth table, impact-step "
        "geometry, aggregate hand-checks, frozen track constants"
    )


def sim_smoke() -> None:
    """One paired flight on classic: the silent-wrapper invariant (a guardian
    that never triggers must leave the trajectory bit-identical) and the
    intervention path (a scorer that always screams must override + escalate).
    Artifact-free: raw untrained modules would be garbage eyes, so both
    guardian arms use scripted scorers — this smokes the WIRING, the WM arm
    is the campaign's job."""
    import torch  # noqa: F401  (torch presence gates the guardian import)

    from assist.pilot import SyntheticPilot
    from datasets.intervention_labels import HORIZONS
    from planner.action_set import A_NORM, ACTION_NAMES, ACTION_VECS
    from planner.authority import Guardian
    from sim.envs import grab_frame, make_env

    meta = {
        "action_names": ACTION_NAMES,
        "action_vecs": ACTION_VECS.tolist(),
        "a_norm": A_NORM.tolist(),
        "horizons": list(HORIZONS),
    }
    n_menu, n_h = len(ACTION_NAMES) - 1, len(HORIZONS)

    class _Hover:
        def begin(self, pillars):
            pass

        def decide(self, frame, state):
            return ACTION_NAMES.index("hover")

    env = make_env()
    world, seed, tmax = "classic", SEED0, 144

    def mk_pilot():
        return SyntheticPilot("average", seed)

    ep_u = run_assist_episode(env, mk_pilot(), seed, world, tmax=tmax)
    frame = grab_frame(env)
    assert float(frame.std()) > 0, "blank frame — the geometry did not render"

    silent = Guardian(
        mk_pilot(),
        _Hover(),
        None,
        None,
        None,
        meta,
        scorer=lambda f, s: np.zeros((n_menu, n_h, 2), np.float32),
    )
    ep_s = run_assist_episode(env, silent, seed, world, tmax=tmax)
    assert ep_s["authority"]["n_overridden"] == 0
    assert ep_u["path"].shape == ep_s["path"].shape
    dev = float(np.max(np.linalg.norm(ep_u["path"] - ep_s["path"], axis=1)))
    assert dev <= 1e-6, f"silent guardian changed the flight: {dev:.2e}"

    hot = np.zeros((n_menu, n_h, 2), np.float32)
    hot[:, :, :] = 0.9  # every command about to hit: override then escalate
    loud = Guardian(
        mk_pilot(), _Hover(), None, None, None, meta, scorer=lambda f, s: hot
    )
    ep_l = run_assist_episode(env, loud, seed, world, tmax=tmax)
    au = ep_l["authority"]
    assert au["n_overridden"] > 0 and au["n_escalations"] >= 1
    assert not ep_l["reached"], "a screaming scorer must ground the flight"
    _u, _a, rec = run_paired(
        env,
        mk_pilot,
        lambda p: Guardian(
            p,
            _Hover(),
            None,
            None,
            None,
            meta,
            scorer=lambda f, s: np.zeros((n_menu, n_h, 2), np.float32),
        ),
        seed,
        world,
        1.0,
        tmax,
    )
    assert rec["n_overridden"] == 0 and not rec["added"]
    env.close()
    print(
        "ASSIST-EPISODE OK (--sim): frame non-blank, silent guardian "
        "bit-identical, screaming scorer overrides+escalates, pairing wired"
    )


if __name__ == "__main__":
    selftest()
    if "--sim" in sys.argv:
        sim_smoke()

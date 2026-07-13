"""Flight-mode selector — pick the mission mode at flight start.

The unified WM ships ALONGSIDE the pinned champion (never overwriting it —
the full-zoo pass showed a swap breaks the distilled skill zoo, e.g. slalom
80%->0%; see experiments/unified_wm_v1). A "flight mode" is the seam that
makes alongside real: each mode binds its OWN (WM checkpoint, action set,
controller, safety filter, runner), set once when the flight starts.

  * `transit`       — pillar-corridor avoidance on the PINNED CHAMPION
                      (`world_model.pth`) + the general transit champion
                      policy. This is the mature deployed transit stack; its
                      distilled policies must keep the champion latent.
  * `indoor_search` — room coverage + beacon find/return on the UNIFIED WM
                      (`world_model_unified.pth`): frontier strategy + the
                      beams8 geometric safety veto; the unified WM rides this
                      mode as the detection brain (its indoor home).

Both WMs stay resident (~163 KB int8 total, 32% of the 512 KB budget), but
only one runs per mode, so latency does not double. New modes register with
`register(FlightMode(...))` — the registry mirrors the `_SAFETY` /
`get_strategy` idiom already used elsewhere. This module sits ABOVE
`planner/dispatch.py` (which is a WITHIN-transit auto-router).

Run:
  python -m planner.flight_mode --selftest
  python -m planner.flight_mode --verify   # lock-consistency + on-disk shas
"""

import argparse
import os
import sys
from dataclasses import dataclass, field
from typing import Callable

from world_model.training import MODEL

# the unified WM lives beside the pinned champion (both under output/)
UNIFIED_WM = os.path.join(os.path.dirname(MODEL), "world_model_unified.pth")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_WM_CACHE: dict = {}


def load_wm_cached(path: str):
    """Load a WM checkpoint once and reuse it. Both WMs can be resident at
    once; the pinned champion is loaded by path, never swapped in place."""
    if path not in _WM_CACHE:
        from world_model.training import load_model

        _WM_CACHE[path] = load_model(path, device="cpu")
    return _WM_CACHE[path]


@dataclass
class FlightMode:
    """A bound mission stack. `build(env, seed, speed)` flies ONE episode in
    this mode and returns the runner's scorecard dict. `heads` maps a role
    (e.g. "yaw", "low", "person") to the repo-relative dest of the
    detection head that rides this mode's WM — every head must be pinned
    in artifacts.lock.json with a `wm` field naming this mode's WM entry
    (a head is only valid with the latent it was trained on; `verify()`
    cross-checks the whole binding)."""

    name: str
    wm_path: str
    description: str
    build: Callable
    heads: dict = field(default_factory=dict)


MODES: dict = {}


def register(mode: FlightMode) -> None:
    MODES[mode.name] = mode


def get_mode(name: str) -> FlightMode:
    if name not in MODES:
        raise SystemExit(f"unknown flight mode {name!r}; have {list_modes()}")
    return MODES[name]


def list_modes() -> list:
    return sorted(MODES)


def verify(mode: FlightMode) -> list:
    """Cross-check a mode's bindings against `artifacts.lock.json`.

    Two layers. CONSISTENCY (needs only the committed lock — CI-safe, CI
    runners have no output/): the mode's WM and every head are lock
    entries, each head carries a `wm` field, and that field names THIS
    mode's WM entry. INTEGRITY (only for files present on disk): sha256
    must match the lock, mirroring `fetch_champions --check`. Returns
    report lines; raises AssertionError on any inconsistency."""
    import json

    with open(os.path.join(ROOT, "artifacts.lock.json")) as f:
        lock = json.load(f)
    by_dest = {a["dest"]: a for a in lock["artifacts"]}
    by_name = {a["name"]: a for a in lock["artifacts"]}

    wm_dest = os.path.relpath(mode.wm_path, ROOT)
    wm_entry = by_dest.get(wm_dest)
    assert wm_entry, f"{mode.name}: WM {wm_dest} is not pinned in the lock"
    checks = [(wm_dest, wm_entry)]
    for role, dest in sorted(mode.heads.items()):
        h = by_dest.get(dest)
        assert h, f"{mode.name}: head {dest} ({role}) is not pinned in the lock"
        assert h.get("wm") in by_name, f"{h['name']}: 'wm' must name a lock entry"
        assert by_name[h["wm"]]["dest"] == wm_dest, (
            f"{h['name']} was trained on {h['wm']}, but mode {mode.name!r} "
            f"flies {wm_entry['name']} — head/WM binding mismatch"
        )
        checks.append((dest, h))

    lines = []
    for dest, entry in checks:
        path = os.path.join(ROOT, dest)
        if os.path.exists(path):
            from scripts.fetch_champions import _sha256

            assert _sha256(path) == entry["sha256"], f"{dest}: sha256 != lock"
            lines.append(f"  [ok  ] {dest} (sha verified)")
        else:
            lines.append(f"  [skip] {dest} (not on disk — consistency only)")
    return lines


def verify_quantized() -> list:
    """Cross-check the lock's `quantized` deployment configs (adopted
    2026-07-13): every config's `wm` names a pinned lock artifact, the
    derivation recipe fields are present, the transit trigger carries
    numeric thresholds, and each evidence ledger exists in the tree.
    CI-safe (committed files only). Raises AssertionError on any hole."""
    import json

    with open(os.path.join(ROOT, "artifacts.lock.json")) as f:
        lock = json.load(f)
    q = lock.get("quantized")
    assert q, "lock has no 'quantized' section"
    by_name = {a["name"] for a in lock["artifacts"]}
    lines = []
    for mode in ("transit", "indoor_search"):
        c = q[mode]
        assert c["wm"] in by_name, f"quantized.{mode}: wm not a lock entry"
        assert c["arm"] and c["weights"] and c["activations"]
        cal = c["calibration"]
        assert cal["corpus"] and int(cal["n"]) > 0 and int(cal["seed"])
        led = c["evidence"]["ledger"]
        assert os.path.exists(os.path.join(ROOT, led)), f"missing ledger {led}"
        if mode == "transit":
            trg = c["trigger"]
            assert 0.0 < float(trg["margin"]) < 1.0
            assert 0.0 < float(trg["imm_thr"]) < 1.0
        lines.append(f"  [ok  ] quantized.{mode} ({c['arm']}, wm={c['wm']})")
    return lines


# --- transit: pinned champion WM + general transit champion policy ----------
def _fly_transit(env, seed: int = 7, speed: float = 1.0, world: str = "dense"):
    from eval.episode import run_scenario_episode
    from planner.learned_policy import LearnedPolicy, load_policy, zip_path

    enc, pred, cheads, _n, meta = load_wm_cached(MODEL)
    model = load_policy(zip_path(hard=True, xp=True, edge=True))
    pol = LearnedPolicy(model, enc, pred, cheads, meta, speed=speed)
    return run_scenario_episode(env, pol, seed, world, speed=speed)


register(
    FlightMode(
        name="transit",
        wm_path=MODEL,
        description="pillar-corridor avoidance — pinned champion WM + general "
        "transit champion policy (ppo_wm_policy_edge_hard_xp)",
        build=_fly_transit,
    )
)


# --- indoor_search: unified WM + frontier + beams8 --------------------------
def _fly_indoor(
    env,
    seed: int = 130000,
    speed: float = 0.6,
    safety: str = "beams8",
    max_decisions: int = 1500,
):
    from eval.search_episode import run_search_episode
    from search.strategies import get_strategy
    from sim.indoor.rooms import single_room

    # the unified WM rides this mode (resident as the detection brain — its
    # indoor home); the DEPLOYABLE search itself is frontier + beams8 on the
    # abstract beacon (Phase-1a/v3: find ~0.92, collision ~0.03 at speed 0.6,
    # the robust indoor speed — never the stale 1.0 default).
    load_wm_cached(UNIFIED_WM)
    sc = single_room(seed)
    return run_search_episode(
        env,
        sc,
        get_strategy("frontier"),
        seed=seed,
        max_decisions=max_decisions,
        speed=speed,
        safety=safety,
    )


register(
    FlightMode(
        name="indoor_search",
        wm_path=UNIFIED_WM,
        description="room coverage + beacon find/return — unified WM "
        "(detection) + frontier strategy + beams8 geometric safety",
        build=_fly_indoor,
        # the deployed detection heads, all trained on the frozen unified
        # latent (lock-pinned with a wm binding; alt/alt_os stay
        # journal-side — superseded by `low` on the deployed path)
        heads={
            "yaw": "output/target_head_yaw.pt",
            "low": "output/target_head_low.pt",
            "person": "output/target_head_person.pt",
        },
    )
)


def selftest() -> None:
    assert set(list_modes()) == {"transit", "indoor_search"}, list_modes()
    t, i = get_mode("transit"), get_mode("indoor_search")
    assert t.wm_path == MODEL, "transit rides the pinned champion"
    assert i.wm_path == UNIFIED_WM, "indoor rides the unified WM"
    assert t.wm_path != i.wm_path, "each mode binds a DISTINCT WM (alongside)"
    assert callable(t.build) and callable(i.build)
    assert t.heads == {}, "transit has no detection heads"
    assert set(i.heads) == {"yaw", "low", "person"}, i.heads
    # lock consistency for both modes (CI-safe: sha layer skips missing files)
    for m in (t, i):
        verify(m)
    # the adopted quantized deployment configs parse and reference the lock
    assert len(verify_quantized()) == 2
    # negative: a head bound to the WRONG WM must fail the binding check
    bad = FlightMode(
        name="bad",
        wm_path=MODEL,  # champion...
        description="head/WM mismatch fixture",
        build=t.build,
        heads={"yaw": "output/target_head_yaw.pt"},  # ...but a unified head
    )
    try:
        verify(bad)
        raise AssertionError("head/WM mismatch must raise")
    except AssertionError as e:
        assert "binding mismatch" in str(e), e
    try:
        get_mode("nope")
        raise AssertionError("unknown mode must raise")
    except SystemExit:
        pass
    print(
        f"FLIGHT-MODE OK: modes {list_modes()}, transit->champion, "
        f"indoor->unified (distinct WMs, alongside); lock bindings verified "
        f"({len(i.heads)} indoor heads), wrong-WM head refused"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument(
        "--verify",
        action="store_true",
        help="cross-check every mode's WM+head bindings against the lock "
        "(sha256 for files on disk)",
    )
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    if args.verify:
        for name in list_modes():
            m = get_mode(name)
            print(f"[{name}]")
            for line in verify(m):
                print(line)
        print("[quantized]")
        for line in verify_quantized():
            print(line)
        print(
            "FLIGHT-MODE VERIFY OK: every mode's WM+head bindings match the "
            "lock, quantized configs consistent"
        )
        return
    for name in list_modes():
        m = get_mode(name)
        print(f"{name:14s} wm={os.path.basename(m.wm_path):24s} {m.description}")


if __name__ == "__main__":
    sys.exit(main())

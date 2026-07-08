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
"""

import argparse
import os
import sys
from dataclasses import dataclass
from typing import Callable

from world_model.training import MODEL

# the unified WM lives beside the pinned champion (both under output/)
UNIFIED_WM = os.path.join(os.path.dirname(MODEL), "world_model_unified.pth")

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
    this mode and returns the runner's scorecard dict."""

    name: str
    wm_path: str
    description: str
    build: Callable


MODES: dict = {}


def register(mode: FlightMode) -> None:
    MODES[mode.name] = mode


def get_mode(name: str) -> FlightMode:
    if name not in MODES:
        raise SystemExit(f"unknown flight mode {name!r}; have {list_modes()}")
    return MODES[name]


def list_modes() -> list:
    return sorted(MODES)


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
    )
)


def selftest() -> None:
    assert set(list_modes()) == {"transit", "indoor_search"}, list_modes()
    t, i = get_mode("transit"), get_mode("indoor_search")
    assert t.wm_path == MODEL, "transit rides the pinned champion"
    assert i.wm_path == UNIFIED_WM, "indoor rides the unified WM"
    assert t.wm_path != i.wm_path, "each mode binds a DISTINCT WM (alongside)"
    assert callable(t.build) and callable(i.build)
    try:
        get_mode("nope")
        raise AssertionError("unknown mode must raise")
    except SystemExit:
        pass
    print(
        f"FLIGHT-MODE OK: modes {list_modes()}, transit->champion, "
        f"indoor->unified (distinct WMs, alongside)"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    for name in list_modes():
        m = get_mode(name)
        print(f"{name:14s} wm={os.path.basename(m.wm_path):24s} {m.description}")


if __name__ == "__main__":
    sys.exit(main())

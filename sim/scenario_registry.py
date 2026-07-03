"""The scenario registry: one source of truth for what worlds exist.

Before this module, world names were hardcoded in five places (dataset
generation, the training env, per-world AUC reporting, two CLIs) and adding
a scenario meant editing every one of them. Now a scenario registers once —
builtins here, flight skills via `skills.load_skill` — and every consumer
dispatches through the registry.

The protocol is MovingCrosser's de-facto duck type, formalized: a scenario
object answers `positions()` (current planar pillar centres — used for
scoring and for privileged baselines), `step()` (advance one control step;
no-op for static worlds) and `velocities()` (planar velocity per pillar,
zeros for static — what the motion-aware label oracle reads). `meta` carries
skill-defined facts (e.g. the gap's centre and width) that success
predicates need.

World ids: builtins keep the historical 0/1/2 forever (old datasets stay
readable); dynamic registrations get ids >= 3. New datasets embed a
`world_names` array so they are self-describing regardless of registration
order.
"""

from dataclasses import dataclass, field
from typing import Callable, Protocol, runtime_checkable

import numpy as np


@runtime_checkable
class Scenario(Protocol):
    def positions(self) -> list: ...

    def step(self) -> None: ...

    def velocities(self) -> list: ...


@dataclass
class StaticScenario:
    """Wraps a plain pillar list in the Scenario protocol."""

    pillars: list
    meta: dict = field(default_factory=dict)

    def positions(self) -> list:
        return list(self.pillars)

    def step(self) -> None:
        pass

    def velocities(self) -> list:
        return [(0.0, 0.0)] * len(self.pillars)


@dataclass(frozen=True)
class ScenarioSpec:
    name: str
    world_id: int
    spawn: (
        Callable  # (env, rng, *, speed=1.0, randomize=False, in_path=True) -> Scenario
    )


_REGISTRY: dict = {}
_BUILTIN_IDS = {"classic": 0, "dense": 1, "moving": 2}


def register(name: str, spawn: Callable, world_id: int | None = None) -> ScenarioSpec:
    """Register a scenario factory. Re-registering the same name replaces it
    (skills re-import freely); ids are stable per name within a process."""
    if world_id is None:
        if name in _BUILTIN_IDS:
            world_id = _BUILTIN_IDS[name]
        elif name in _REGISTRY:
            world_id = _REGISTRY[name].world_id
        else:
            world_id = max([2] + [s.world_id for s in _REGISTRY.values()]) + 1
    spec = ScenarioSpec(name=name, world_id=int(world_id), spawn=spawn)
    _REGISTRY[name] = spec
    return spec


def get(name: str) -> ScenarioSpec:
    if name not in _REGISTRY:
        raise KeyError(
            f"unknown world '{name}' — builtins: {sorted(_BUILTIN_IDS)}; "
            f"skill worlds register via skills.load_skill(...)"
        )
    return _REGISTRY[name]


def names() -> tuple:
    return tuple(sorted(_REGISTRY, key=lambda n: _REGISTRY[n].world_id))


def world_names_array() -> np.ndarray:
    """id -> name lookup table for npz embedding (self-describing datasets)."""
    by_id = {s.world_id: s.name for s in _REGISTRY.values()}
    return np.array([by_id.get(i, str(i)) for i in range(max(by_id) + 1)])


def resolve_worlds(arg) -> tuple:
    """CLI surface: 'classic' | 'hard' | 'a,b,c' | tuple -> validated tuple."""
    if isinstance(arg, (tuple, list)):
        parts = list(arg)
    elif arg == "classic":
        parts = ["classic"]
    elif arg == "hard":
        parts = ["classic", "dense", "moving"]
    else:
        parts = [p.strip() for p in str(arg).split(",") if p.strip()]
    for p in parts:
        get(p)  # raises with a helpful message on unknown names
    return tuple(parts)


# --- builtins: thin adapters over the untouched spawn functions -------------


def _spawn_classic(env, rng, *, speed=1.0, randomize=False, in_path=True):
    from sim.scenarios import spawn_pillars

    del speed
    return StaticScenario(spawn_pillars(env, rng, in_path=in_path, randomize=randomize))


def _spawn_dense(env, rng, *, speed=1.0, randomize=False, in_path=True):
    from sim.scenarios import spawn_dense_pillars

    del speed, randomize, in_path
    return StaticScenario(spawn_dense_pillars(env, rng))


def _spawn_moving(env, rng, *, speed=1.0, randomize=False, in_path=True):
    from sim.scenarios import MovingCrosser

    del randomize, in_path
    return MovingCrosser(env, rng, cruise=0.8 * float(speed))


register("classic", _spawn_classic)
register("dense", _spawn_dense)
register("moving", _spawn_moving)


def selftest() -> None:
    assert names()[:3] == ("classic", "dense", "moving")
    assert [get(n).world_id for n in ("classic", "dense", "moving")] == [0, 1, 2]
    spec = register("_probe", lambda env, rng, **kw: StaticScenario([(1.0, 0.0)]))
    assert spec.world_id >= 3, "dynamic ids must start above the builtins"
    assert register("_probe", spec.spawn).world_id == spec.world_id, "id must be stable"
    assert resolve_worlds("hard") == ("classic", "dense", "moving")
    assert resolve_worlds("classic,_probe") == ("classic", "_probe")
    try:
        resolve_worlds("no_such_world")
        raise AssertionError("unknown world must raise")
    except KeyError:
        pass
    wn = world_names_array()
    assert wn[0] == "classic" and wn[spec.world_id] == "_probe"
    sc = spec.spawn(None, None)
    assert isinstance(sc, Scenario) and sc.velocities() == [(0.0, 0.0)]
    sc.step()  # no-op must exist
    del _REGISTRY["_probe"]
    print(
        f"SCENARIO-REGISTRY OK: builtins 0/1/2 fixed, dynamic ids >=3 stable, "
        f"resolve_worlds classic|hard|csv, {len(names())} registered"
    )


if __name__ == "__main__":
    selftest()

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
Registration rejects ambiguous names, conflicting/reassigned IDs and
non-integer IDs before mutating the catalog. Numeric names are reserved for
unregistered slots in sparse catalogs; `all` is reserved for pooled metrics.
"""

import operator
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
    (skills re-import freely); ids are stable per name within a process.

    Explicit IDs must be unused or the existing ID of this same name.
    Builtin 0/1/2 are reserved even if a caller is restoring an empty registry.
    """
    if (
        not isinstance(name, str)
        or not name
        or name != name.strip()
        or name.isdecimal()
        or name == "all"
    ):
        raise ValueError(
            "world name must be nonempty, trimmed, nonnumeric and not 'all'"
        )
    if not callable(spawn):
        raise ValueError("scenario spawn must be callable")
    if world_id is None:
        if name in _BUILTIN_IDS:
            world_id = _BUILTIN_IDS[name]
        elif name in _REGISTRY:
            world_id = _REGISTRY[name].world_id
        else:
            world_id = max([2] + [s.world_id for s in _REGISTRY.values()]) + 1
    try:
        if isinstance(world_id, (bool, np.bool_)):
            raise TypeError
        world_id = operator.index(world_id)
    except TypeError as exc:
        raise ValueError("world_id must be a nonnegative integer") from exc
    if world_id < 0:
        raise ValueError("world_id must be a nonnegative integer")
    if name in _BUILTIN_IDS and world_id != _BUILTIN_IDS[name]:
        raise ValueError(f"builtin {name} must keep world_id {_BUILTIN_IDS[name]}")
    if name not in _BUILTIN_IDS and world_id in _BUILTIN_IDS.values():
        raise ValueError("world_id 0/1/2 are reserved for classic/dense/moving")
    previous = _REGISTRY.get(name)
    if previous is not None and previous.world_id != world_id:
        raise ValueError(
            f"registered world {name} must keep world_id {previous.world_id}"
        )
    if any(s.name != name and s.world_id == world_id for s in _REGISTRY.values()):
        raise ValueError(f"world_id {world_id} already belongs to another world")
    spec = ScenarioSpec(name=name, world_id=world_id, spawn=spawn)
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
    initial = dict(_REGISTRY)
    try:
        assert names()[:3] == ("classic", "dense", "moving")
        assert [get(n).world_id for n in ("classic", "dense", "moving")] == [0, 1, 2]

        def factory(env, rng, **kw):
            return StaticScenario([(1.0, 0.0)])

        spec = register("_probe", factory)
        assert spec.world_id >= 3, "dynamic ids must start above the builtins"
        assert register("_probe", factory).world_id == spec.world_id

        def replacement(env, rng, **kw):
            return StaticScenario([(2.0, 0.0)])

        updated = register("_probe", replacement, world_id=np.int64(spec.world_id))
        assert updated.world_id == spec.world_id and updated.spawn is replacement
        sparse_id = max(s.world_id for s in _REGISTRY.values()) + 3
        sparse = register("_sparse", factory, world_id=np.int64(sparse_id))
        auto = register("_after_sparse", factory)
        assert auto.world_id == sparse.world_id + 1
        assert resolve_worlds("hard") == ("classic", "dense", "moving")
        assert resolve_worlds("_probe,classic,_probe") == (
            "_probe",
            "classic",
            "_probe",
        )
        try:
            resolve_worlds("no_such_world")
        except KeyError:
            pass
        else:
            raise AssertionError("unknown world must raise")

        invalid = [
            ("_collision", factory, 0),
            ("_collision", factory, spec.world_id),
            ("moving", factory, 8),
            ("_probe", factory, sparse.world_id + 9),
            ("_invalid", factory, -1),
            ("_invalid", factory, 3.9),
            ("_invalid", factory, 3.0),
            ("_invalid", factory, "6"),
            ("_invalid", factory, True),
            ("_invalid", factory, np.bool_(False)),
            ("", factory, None),
            (" bad", factory, None),
            ("bad ", factory, None),
            (None, factory, None),
            ("all", factory, None),
            (str(sparse_id - 1), factory, None),
            ("_invalid", None, None),
        ]
        before = dict(_REGISTRY)
        for name, spawn, world_id in invalid:
            try:
                register(name, spawn, world_id)
            except ValueError:
                pass
            else:
                raise AssertionError(
                    f"invalid registration accepted: {name}, {world_id}"
                )
            assert _REGISTRY == before, "failed registration changed existing entries"
        catalog = world_names_array()
        assert len(set(catalog)) == len(catalog), "catalog names must be unambiguous"
        for name, entry in _REGISTRY.items():
            assert catalog[entry.world_id] == name
        assert catalog[sparse_id - 1] == str(sparse_id - 1)
        sc = get("_probe").spawn(None, None)
        assert isinstance(sc, Scenario) and sc.positions() == [(2.0, 0.0)]
        assert sc.velocities() == [(0.0, 0.0)]
        sc.step()
        # Even temporarily absent builtin slots cannot be claimed by a plugin.
        del _REGISTRY["classic"]
        try:
            register("_collision", factory, 0)
        except ValueError:
            pass
        else:
            raise AssertionError("absent builtin slot was not reserved")
    finally:
        _REGISTRY.clear()
        _REGISTRY.update(initial)
    print(
        f"SCENARIO-REGISTRY OK: immutable unique IDs, sparse/name roundtrip, "
        f"factory replacement, 18 rejected registrations; {len(names())} restored"
    )


if __name__ == "__main__":
    selftest()

"""The flight-skill schema: what a plugged-in capability must declare.

A skill is a package under skills/ whose `skill.py` exports `SKILL`, a
frozen declaration of:

  * **scenarios** it needs (registered into the scenario registry on load),
  * **cells** to fly (targets on the new capability + guards on everything
    the champion already does),
  * **criteria** — the pre-registered bars. Frozen at skill version; the
    research loop may add knobs, never move bars,
  * **knobs** — the ordered experiment schedule (zero-shot first, then
    single-variable training runs),
  * a **success predicate** and optional per-episode metrics over the flown
    path (capabilities are statements about trajectories, not endpoints).

`load_skill` is the only importer of skill modules; the registry never
imports skills (no cycles).
"""

import importlib
from dataclasses import dataclass, field
from typing import Callable

from sim import scenario_registry

VALID_KNOB_KINDS = ("zero_shot", "policy", "world_model")
VALID_ROLES = ("target", "guard")
VALID_OPS = (">=", "<=")


@dataclass(frozen=True)
class EvalCell:
    id: str
    world: str | None  # registry name; None => classic run_episode cell
    speed: float = 1.0
    n_seeds: int = 30
    seed0: int = 9000
    kwargs: dict = field(default_factory=dict)  # in_path/solo for classic cells
    role: str = "target"


@dataclass(frozen=True)
class Criterion:
    cell: str
    metric: str  # "success" | "crash" | any aggregated key
    op: str
    bar: float
    kind: str  # "target" | "guard"

    def check(self, measured: float) -> bool:
        return measured >= self.bar if self.op == ">=" else measured <= self.bar


@dataclass(frozen=True)
class Knob:
    id: str
    kind: str  # zero_shot | policy | world_model
    desc: str
    hypothesis: str
    train_kwargs: dict = field(default_factory=dict)
    policy_path: str | None = None  # zero_shot only


@dataclass(frozen=True)
class Skill:
    name: str
    version: str
    scenarios: dict  # name -> spawn factory
    cells: tuple
    criteria: tuple
    knobs: tuple
    max_knobs: int
    success: Callable  # episode dict -> bool
    episode_metrics: Callable | None = None  # episode dict -> dict
    recheck_margin: float = 0.08
    recheck_n: int = 60


def _validate(skill: Skill) -> None:
    cell_ids = {c.id for c in skill.cells}
    assert len(cell_ids) == len(skill.cells), "duplicate cell ids"
    for c in skill.cells:
        assert c.role in VALID_ROLES, f"bad role {c.role}"
        if c.world is not None:
            scenario_registry.get(c.world)  # must be registered by now
    for cr in skill.criteria:
        assert cr.cell in cell_ids, f"criterion for unknown cell {cr.cell}"
        assert cr.op in VALID_OPS and cr.kind in VALID_ROLES
    assert skill.knobs, "a skill needs at least one knob"
    for k in skill.knobs:
        assert k.kind in VALID_KNOB_KINDS, f"bad knob kind {k.kind}"
        if k.kind == "zero_shot":
            assert k.policy_path, "zero_shot knob needs policy_path"
    assert skill.max_knobs >= 1 and callable(skill.success)


def load_skill(arg: str) -> Skill:
    """Accepts 'skills/gap_flight', 'gap-flight' or 'gap_flight'; imports the
    skill module, registers its scenarios, validates the schema. Errors are
    wrapped for newcomers — the raw traceback is chained underneath."""
    mod_name = arg.strip().strip("/").split("/")[-1].replace("-", "_")
    try:
        module = importlib.import_module(f"skills.{mod_name}.skill")
    except ModuleNotFoundError as e:
        import os

        skills_dir = os.path.dirname(os.path.abspath(__file__))
        have = sorted(
            d
            for d in os.listdir(skills_dir)
            if os.path.isdir(os.path.join(skills_dir, d)) and not d.startswith("_")
        )
        raise SystemExit(
            f"[skill not found] '{arg}' -> no module skills.{mod_name}.skill\n"
            f"  available skills: {', '.join(have)}\n"
            f"  scaffold a new one: python -m scripts.new_skill {mod_name}\n"
            f"  docs: docs/ONBOARDING.md  (import error: {e})"
        ) from e
    try:
        skill: Skill = module.SKILL
    except AttributeError as e:
        raise SystemExit(
            f"[skill malformed] skills/{mod_name}/skill.py has no SKILL export — "
            f"every skill module must define `SKILL = Skill(...)`. "
            f"See docs/ONBOARDING.md and skills/gap_flight/skill.py. ({e})"
        ) from e
    for name, spawn in skill.scenarios.items():
        scenario_registry.register(name, spawn)
    try:
        _validate(skill)
    except AssertionError as e:
        raise SystemExit(
            f"[skill invalid] {mod_name}: {e}\n"
            f"  schema reference: skills/base.py docstring; worked example: "
            f"skills/gap_flight/skill.py; glossary: docs/GLOSSARY.md"
        ) from e
    return skill


def selftest() -> None:
    dummy = Skill(
        name="dummy",
        version="0",
        scenarios={},
        cells=(EvalCell("a@1.0", None), EvalCell("g", None, role="guard")),
        criteria=(
            Criterion("a@1.0", "success", ">=", 0.8, "target"),
            Criterion("g", "crash", "<=", 0.05, "guard"),
        ),
        knobs=(Knob("K0", "zero_shot", "d", "h", policy_path="x.zip"),),
        max_knobs=1,
        success=lambda ep: True,
    )
    _validate(dummy)
    assert Criterion("a", "success", ">=", 0.8, "target").check(0.85)
    assert not Criterion("a", "crash", "<=", 0.05, "guard").check(0.10)
    try:
        _validate(
            Skill(
                "bad",
                "0",
                {},
                (EvalCell("a", None),),
                (Criterion("missing", "x", ">=", 1, "target"),),
                (Knob("K0", "zero_shot", "d", "h", policy_path="x"),),
                1,
                lambda ep: True,
            )
        )
        raise AssertionError("criterion for unknown cell must fail validation")
    except AssertionError as e:
        assert "unknown cell" in str(e)
    print("SKILLS-BASE OK: schema dataclasses + validation asserts")


if __name__ == "__main__":
    selftest()

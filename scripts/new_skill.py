"""Scaffold a new flight skill — the conventions, pre-filled.

    python -m scripts.new_skill my-skill                 # static scenario
    python -m scripts.new_skill my-skill --kind moving   # moving scenario

Writes `skills/my_skill/{__init__.py,skill.py}` with every house
convention a newcomer would otherwise reverse-engineer from 200-340
lines of existing skills: the spawn signature (env-free selftest
guard, `del` unused args), the metrics/success dispatch pattern, the
standard guard block (cluttered @ seed0=1000 n=60; the sweep triple @
seed0=3000 with the noisy 2.0 cell pinned to n=60 — a paid-for lesson),
the K0 zero-shot + K1-K3 knob ladder, and a selftest skeleton with a
soul-assert placeholder. Every decision left to the researcher is a
`TODO(researcher)` marker.

Next steps are printed on success; the full path is docs/ONBOARDING.md.
"""

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SPAWN_STATIC = '''\
def spawn_{mod}(env, rng, *, speed=1.0, randomize=False, in_path=True):
    """TODO(researcher): build your scenario. Return a StaticScenario
    (or a class with positions()/step()/velocities()/meta for motion).
    The `if env is not None` guard keeps geometry selftests env-free."""
    del speed, randomize, in_path  # keep the registry signature; use what you need
    # TODO(researcher): compute pillar (x, y) centres with rng
    pillars = [(float(rng.uniform(1.3, 2.0)), float(rng.uniform(-0.2, 0.2)))]
    if env is not None:
        from sim.scenarios import _pillar_body

        for px, py in pillars:
            _pillar_body(env, px, py)
    return StaticScenario(pillars, meta={{}})  # TODO(researcher): meta facts
'''

SPAWN_MOVING = '''\
class {cls}Scenario:
    """TODO(researcher): a moving scenario. Protocol: positions() ->
    current centres, step() -> advance one control step (move pybullet
    bodies too — vision is the policy's input!), velocities() -> per-
    pillar (vx, vy) for the label oracle, meta -> facts your success
    predicate needs. See MovingGapFence (skills/moving_gap/skill.py)
    and remember the AIMED-encounter convention: an unaimed mover
    misses on most seeds and measures nothing."""

    def __init__(self, env, rng, *, speed=1.0):
        import pybullet as p

        self._p, self.env, self.t = p, env, 0.0
        # TODO(researcher): geometry + aim the encounter at arrival time
        self.x = float(rng.uniform(1.4, 2.2))
        self.y0, self.vy = float(rng.uniform(-1.5, 1.5)), 0.3
        self.meta = {{"x": self.x, "y0": self.y0, "vy": self.vy}}
        self.bodies = []
        if env is not None:
            from sim.scenarios import _pillar_body

            self.dt = env.CTRL_TIMESTEP
            self.bodies = [_pillar_body(env, self.x, self.y0)]
        else:
            self.dt = 1.0 / CTRL_HZ

    def positions(self) -> list:
        return [(self.x, self.y0 + self.vy * self.t)]

    def velocities(self) -> list:
        return [(0.0, self.vy)]

    def step(self) -> None:
        self.t += self.dt
        for body, (x, y) in zip(self.bodies, self.positions()):
            self._p.resetBasePositionAndOrientation(
                body, [x, y, 0.7], [0, 0, 0, 1], physicsClientId=self.env.CLIENT
            )


def spawn_{mod}(env, rng, *, speed=1.0, randomize=False, in_path=True):
    del randomize, in_path
    return {cls}Scenario(env, rng, speed=speed)
'''

TEMPLATE = '''\
"""{name}: TODO(researcher) — one line on the capability this skill probes.

TODO(researcher): the pre-registration lives HERE, in this docstring,
written BEFORE any number exists: what the scenario is, why it should
separate policies, what you expect each knob to do (hypotheses are
falsifiable — record them so being wrong is a finding, not an
embarrassment), and what the bars mean. See skills/gap_flight/skill.py
for the canonical worked example and docs/GLOSSARY.md for the words.
"""

import numpy as np

from sim.envs import CTRL_HZ
from sim.scenario_registry import StaticScenario
from skills.base import Criterion, EvalCell, Knob, Skill

{spawn}

def {mod}_metrics(ep: dict) -> dict:
    """Per-episode metrics over the flown path. Runs for EVERY cell of
    this skill — dispatch on ep["scenario_meta"] keys if your guard
    cells come from other skills (the single-predicate-per-skill trap;
    see skills/moving_gap/skill.py's dispatch for the pattern)."""
    meta = ep.get("scenario_meta", {{}})
    del meta  # TODO(researcher): trajectory-level metrics, e.g. transit checks
    return {{}}


def {mod}_success(ep: dict) -> bool:
    """TODO(researcher): what counts as success — a statement about the
    TRAJECTORY, not just the endpoint, wherever possible."""
    return bool(ep["reached"] and not ep["crashed"])


_CHAMPION = "output/ppo_wm_policy_edge_hard_xp.zip"  # or a skill champion zip
_DIET = ("classic", "dense", "moving")  # TODO(researcher): your training worlds

SKILL = Skill(
    name="{name}",
    version="1",
    scenarios={{
        "{mod}": spawn_{mod},
        # TODO(researcher): re-register any other skill's worlds that your
        # guard cells OR your knobs' training diets reference — schema
        # validation checks both (re-registering a name is safe)
    }},
    cells=(
        # targets: fresh seed0 series for a new family (gap=9000, moving=9500)
        EvalCell("{mod}@1.0", "{mod}", 1.0, 30, 9900),  # TODO(researcher): seed0
        EvalCell("{mod}@1.5", "{mod}", 1.5, 30, 9900),
        # the standard guard block — regression bars on what already works
        EvalCell("guard:cluttered", None, 1.0, 60, 1000, {{"in_path": True}}, "guard"),
        EvalCell(
            "guard:sweep@1.0",
            None,
            1.0,
            30,
            3000,
            {{"in_path": True, "solo": True}},
            "guard",
        ),
        EvalCell(
            "guard:sweep@1.5",
            None,
            1.5,
            30,
            3000,
            {{"in_path": True, "solo": True}},
            "guard",
        ),
        # the noisy cell starts at n=60 — its n=30 reads bounced 27/22/8/17
        # across one campaign (docs/GLOSSARY.md: "instrument discipline")
        EvalCell(
            "guard:sweep@2.0",
            None,
            2.0,
            60,
            3000,
            {{"in_path": True, "solo": True}},
            "guard",
        ),
    ),
    criteria=(
        # bars freeze at skill version — campaigns may add knobs, never move bars
        Criterion("{mod}@1.0", "success", ">=", 0.70, "target"),  # TODO(researcher)
        Criterion("{mod}@1.5", "success", ">=", 0.55, "target"),  # TODO(researcher)
        Criterion("guard:cluttered", "crash", "<=", 0.05, "guard"),
        Criterion("guard:sweep@1.0", "crash", "<=", 0.05, "guard"),
        Criterion("guard:sweep@1.5", "crash", "<=", 0.10, "guard"),
        Criterion("guard:sweep@2.0", "crash", "<=", 0.10, "guard"),
    ),
    knobs=(
        Knob(
            "K0",
            "zero_shot",
            "the current champion, zero-shot",
            "TODO(researcher): what do you EXPECT it to do here, and why? "
            "An honest predicted failure is the best possible K0",
            policy_path=_CHAMPION,
        ),
        Knob(
            "K1",
            "policy",
            "the new world joins the diet",
            "TODO(researcher): single-variable hypothesis",
            train_kwargs=dict(
                worlds=_DIET + ("{mod}",),
                x_progress=True,
                edge_bias=True,
                timesteps=450_000,
            ),
        ),
        # TODO(researcher): K2/K3 — one variable each (share? budget? mixture
        # shape?). Cite the lesson that motivates each (see docs/GLOSSARY.md).
    ),
    max_knobs=4,
    success={mod}_success,
    episode_metrics={mod}_metrics,
)


def selftest() -> None:
    rng = np.random.default_rng(7)
    sc = spawn_{mod}(None, rng)  # env-free geometry checks
    assert len(sc.positions()) >= 1, "scenario must place pillars"
    # TODO(researcher): the SOUL assert — the one synthetic-path check that
    # encodes what this skill is really about (gap: through=success vs
    # around=fail; moving-gap: now=success vs was=fail; door: on-time vs
    # late). If you cannot write it, the success predicate is not done.
    from skills.base import load_skill

    s = load_skill("{name}")
    assert s.name == "{name}"
    from sim.scenario_registry import get

    sc2 = get("{mod}").spawn(None, np.random.default_rng(3))
    sc3 = get("{mod}").spawn(None, np.random.default_rng(3))
    assert str(sc2.meta) == str(sc3.meta), "spawn must reproduce per seed"
    print("{shout}-SKILL OK: TODO(researcher) — say what was proven")


if __name__ == "__main__":
    selftest()
'''

NEXT_STEPS = """\
scaffolded skills/{mod}/skill.py — next steps (docs/ONBOARDING.md has the tour):
  1. fill every TODO(researcher); write the docstring pre-registration FIRST
  2. python -m skills.{mod}.skill                       # selftest green
  3. python -m scripts.research doctor skills/{mod}     # preflight green
  4. python -m scripts.research step skills/{mod} --knob 0 --dry --no-commit
  5. add `python -m skills.{mod}.skill` to .github/workflows/ci.yml
  6. launch: python -m scripts.research run skills/{mod}
"""


def render(name: str, kind: str) -> str:
    mod = name.replace("-", "_")
    cls = "".join(w.capitalize() for w in mod.split("_"))
    spawn = (SPAWN_STATIC if kind == "static" else SPAWN_MOVING).format(
        mod=mod, cls=cls
    )
    return TEMPLATE.format(name=name, mod=mod, spawn=spawn, shout=mod.upper())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("name", nargs="?", help="skill name, e.g. opening-door")
    ap.add_argument("--kind", choices=("static", "moving"), default="static")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        for kind in ("static", "moving"):
            src = render("probe-skill", kind)
            compile(src, f"<{kind}>", "exec")  # syntax-valid as generated
            assert src.count("TODO(researcher)") >= 8, "markers went missing"
            # the noisy fast-solo cell must ship pinned to n=60 (the lesson)
            i = src.index('"guard:sweep@2.0"')
            assert "60," in src[i : i + 120], "sweep@2.0 must default to n=60"
            assert "1000" in src and "3000" in src, "guard seed0 conventions"
        print(
            "NEW-SKILL OK: both templates compile, TODO markers + guard "
            "conventions (cluttered@1000 n=60, sweep@3000, 2.0 pinned n=60) intact"
        )
        return

    if not args.name:
        raise SystemExit("usage: python -m scripts.new_skill <name> [--kind moving]")
    mod = args.name.replace("-", "_")
    pkg = os.path.join(ROOT, "skills", mod)
    if os.path.exists(pkg):
        raise SystemExit(f"skills/{mod}/ already exists — pick another name")
    os.makedirs(pkg)
    open(os.path.join(pkg, "__init__.py"), "w").close()
    with open(os.path.join(pkg, "skill.py"), "w") as f:
        f.write(render(args.name, args.kind))
    print(NEXT_STEPS.format(mod=mod))


if __name__ == "__main__":
    main()
    sys.exit(0)

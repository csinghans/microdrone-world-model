"""Score one policy zip on a declared cell list — the generic policy-gate probe.

Model-axis gates got `eval_wm_checkpoint`; this is the policy-axis twin.
The frozen scoreboards keep their hardcoded line-ups (history must stay
comparable), and the research runner only flies skill-declared cells — so
manual campaigns (the G/H/M series) had no rerunnable way to fly *one*
candidate zip over an explicit cell list. Now they do:

  python -m eval.eval_policy_cells --zip <policy.zip> \
      --cells experiments/<campaign>/m2_cells.json --out <results.json>

The cells file is a JSON list of EvalCell fields
(`{"id", "world", "speed", "n", "seed0", "kwargs"}`) committed *before*
the numbers exist — the cell spec is part of the pre-registration. The
flying path is `scripts.research.run_cell` itself (the same machinery the
skill campaigns use — no drift), with a minimal success shim
(reached and not crashed). `--only/--n/--seed0` support the borderline
recheck rule (n=60, fresh seeds) without editing the spec.

--wm selects a world-model file directly (default: output/world_model.pth).
The file must exist and must not be an auto-trained tiny stand-in. No model
is swapped or trained. Results retain the zip/cells fields and also record
input SHA-256 identities, effective cell settings, judge and runtime.
Outputs must be new and are published atomically after input rechecks.
"""

import argparse
import json
import math
import platform
import sys
from contextlib import closing
from datetime import datetime, timezone
from importlib.metadata import version
from types import SimpleNamespace

from datasets.provenance import file_identity
from skills.base import VALID_ROLES, EvalCell
from world_model.checkpoint_io import check_destination, publish_checkpoint

SHIM = SimpleNamespace(
    episode_metrics=None,
    success=lambda ep: bool(ep["reached"]) and not bool(ep["crashed"]),
)


def load_cells(path: str) -> list:
    with open(path) as f:
        spec = json.load(f)
    if not isinstance(spec, list) or not spec:
        raise ValueError("cells must be a nonempty JSON list")
    cells, ids = [], set()
    for c in spec:
        if not isinstance(c, dict) or not {"id", "speed", "n", "seed0"} <= c.keys():
            raise ValueError("every cell needs id, speed, n and seed0")
        if not isinstance(c["id"], str) or not c["id"].strip() or c["id"] in ids:
            raise ValueError("cell ids must be nonempty and unique")
        ids.add(c["id"])
        if type(c["n"]) is not int or c["n"] <= 0:
            raise ValueError("cell n must be a positive integer")
        if type(c["seed0"]) is not int or c["seed0"] < 0:
            raise ValueError("cell seed0 must be a nonnegative integer")
        speed = c["speed"]
        if type(speed) not in (int, float) or not math.isfinite(speed) or speed <= 0:
            raise ValueError("cell speed must be finite and positive")
        role = c.get("role", "target")
        if role not in VALID_ROLES:
            raise ValueError(f"invalid cell role: {role}")
        world, kwargs = c.get("world"), c.get("kwargs", {})
        if not isinstance(kwargs, dict):
            raise ValueError("cell kwargs must be an object")
        if world is not None and (not isinstance(world, str) or not world.strip()):
            raise ValueError("cell world must be a registered name or null")
        if world is not None and kwargs:
            raise ValueError("registered-world cells do not support kwargs in run_cell")
        if set(kwargs) - {"tmax", "in_path", "solo", "randomize"}:
            raise ValueError("unsupported classic-cell kwargs")
        for flag in ("in_path", "solo", "randomize"):
            if flag in kwargs and type(kwargs[flag]) is not bool:
                raise ValueError(f"cell {flag} must be a boolean")
        if "tmax" in kwargs and (
            type(kwargs["tmax"]) is not int or kwargs["tmax"] <= 0
        ):
            raise ValueError("cell tmax must be a positive integer")
        cells.append(
            EvalCell(c["id"], world, float(speed), c["n"], c["seed0"], kwargs, role)
        )
    return cells


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", dest="zip_path")
    ap.add_argument("--cells")
    ap.add_argument("--wm", default=None, help="explicit world-model checkpoint")
    ap.add_argument("--out", default=None)
    ap.add_argument("--only", default=None, help="run a single cell id")
    ap.add_argument("--n", type=int, default=None, help="override n (rechecks)")
    ap.add_argument("--seed0", type=int, default=None, help="override seed0")
    ap.add_argument(
        "--skill",
        default=None,
        help="judge with this skill's success/metrics instead of the "
        "reached-and-clean shim (registers its worlds too) — promotion "
        "gates need the skill's own trajectory-level verdicts",
    )
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        from scripts.policy_eval_selftest import selftest

        selftest()
        return

    if not (args.zip_path and args.cells):
        raise SystemExit("--zip and --cells required (or --selftest)")

    from scripts.research import _policy_factory, run_cell
    from sim.envs import make_env
    from sim.scenario_registry import get as get_world
    from world_model.training import MODEL

    if args.n is not None and args.n <= 0:
        raise ValueError("--n must be positive")
    if args.seed0 is not None and args.seed0 < 0:
        raise ValueError("--seed0 must be nonnegative")
    destination = check_destination(args.out) if args.out else None
    wm_path = args.wm or MODEL
    sources = {"world_model": wm_path, "cell_spec": args.cells}
    if args.zip_path.startswith("builtin:"):
        if args.zip_path not in ("builtin:reactive", "builtin:wm_mpc"):
            raise ValueError(f"unknown builtin policy: {args.zip_path}")
    else:
        sources["policy"] = args.zip_path
    provenance = {name: file_identity(path) for name, path in sources.items()}

    def verify_inputs():
        if provenance != {name: file_identity(path) for name, path in sources.items()}:
            raise ValueError("evaluation inputs changed; no result published")

    judge = SHIM
    judge_identity = {"kind": "reached_and_clean_shim"}
    if args.skill:
        from skills.base import load_skill

        judge = load_skill(args.skill)  # registers its worlds as a side effect
        judge_identity = {"kind": "skill", "name": judge.name, "version": judge.version}
    cells = load_cells(args.cells)
    if args.only:
        cells = [c for c in cells if c.id == args.only]
        if not cells:
            raise SystemExit(f"no cell id {args.only!r} in {args.cells}")
    for cell in cells:
        if cell.world is not None:
            get_world(cell.world)
    verify_inputs()
    factory = _policy_factory(args.zip_path, wm_path=wm_path)
    verify_inputs()
    results = {}
    with closing(make_env()) as env:
        for cell in cells:
            r = run_cell(factory, cell, judge, env, n=args.n, seed0=args.seed0)
            results[cell.id] = r
            print(
                f"  {cell.id}: crash {r['crash']:.3f}  success {r['success']:.3f}  "
                f"clearance {r['clearance_mean']:.2f} m  "
                f"(n={r['n']}, seed0 {r['seed0']})"
            )
    verify_inputs()
    record = {
        "schema_version": 2,
        "zip": args.zip_path,
        "cells": results,
        "provenance": provenance,
        "judge": judge_identity,
        "evaluation": {
            "only": args.only,
            "n_override": args.n,
            "seed0_override": args.seed0,
            "cells": [
                dict(
                    id=c.id,
                    world=c.world,
                    speed=c.speed,
                    role=c.role,
                    kwargs=c.kwargs,
                    n=args.n if args.n is not None else c.n_seeds,
                    seed0=args.seed0 if args.seed0 is not None else c.seed0,
                )
                for c in cells
            ],
        },
        "runtime": {
            "python": platform.python_version(),
            **{
                name: version(name)
                for name in (
                    "numpy",
                    "torch",
                    "stable-baselines3",
                    "sb3-contrib",
                    "pybullet",
                )
            },
        },
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    serialized = (json.dumps(record, indent=2, allow_nan=False) + "\n").encode()
    if destination:
        publish_checkpoint(destination, lambda stream: stream.write(serialized))
    print(f"PCELLS OK: {len(cells)} cells flown with {args.zip_path}")


if __name__ == "__main__":
    main()
    sys.exit(0)

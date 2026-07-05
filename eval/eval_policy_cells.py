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

The world model is whatever sits at output/world_model.pth — model swaps
are the campaign's responsibility, and the results file records nothing
about it, so journal the active checkpoint alongside the numbers.
"""

import argparse
import json
import sys
from types import SimpleNamespace

from skills.base import EvalCell

SHIM = SimpleNamespace(
    episode_metrics=None,
    success=lambda ep: bool(ep["reached"]) and not bool(ep["crashed"]),
)


def load_cells(path: str) -> list:
    with open(path) as f:
        spec = json.load(f)
    return [
        EvalCell(
            c["id"],
            c.get("world"),
            float(c["speed"]),
            int(c["n"]),
            int(c["seed0"]),
            c.get("kwargs") or {},
            c.get("role", "target"),
        )
        for c in spec
    ]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", dest="zip_path")
    ap.add_argument("--cells")
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
        import tempfile

        spec = [
            {"id": "a@1.0", "world": "dense", "speed": 1.0, "n": 30, "seed0": 7000},
            {
                "id": "guard:x",
                "world": None,
                "speed": 2.0,
                "n": 30,
                "seed0": 3000,
                "kwargs": {"in_path": True, "solo": True},
                "role": "guard",
            },
        ]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(spec, f)
            path = f.name
        cells = load_cells(path)
        assert cells[0].world == "dense" and cells[0].n_seeds == 30
        assert cells[1].world is None and cells[1].kwargs["solo"] is True
        assert cells[1].role == "guard"
        ok = {"reached": True, "crashed": False}
        bad = {"reached": True, "crashed": True}
        assert SHIM.success(ok) and not SHIM.success(bad)
        print("PCELLS OK: spec -> EvalCell parsing + success shim (flying path is")
        print("  scripts.research.run_cell, exercised by its own selftest)")
        return

    if not (args.zip_path and args.cells):
        raise SystemExit("--zip and --cells required (or --selftest)")

    from scripts.research import _policy_factory, run_cell
    from sim.envs import make_env

    judge = SHIM
    if args.skill:
        from skills.base import load_skill

        judge = load_skill(args.skill)  # registers its worlds as a side effect
    cells = load_cells(args.cells)
    if args.only:
        cells = [c for c in cells if c.id == args.only]
        if not cells:
            raise SystemExit(f"no cell id {args.only!r} in {args.cells}")
    factory = _policy_factory(args.zip_path)
    env = make_env()
    results = {}
    for cell in cells:
        r = run_cell(factory, cell, judge, env, n=args.n, seed0=args.seed0)
        results[cell.id] = r
        print(
            f"  {cell.id}: crash {r['crash']:.3f}  success {r['success']:.3f}  "
            f"clearance {r['clearance_mean']:.2f} m  (n={r['n']}, seed0 {r['seed0']})"
        )
    env.close()
    if args.out:
        with open(args.out, "w") as f:
            json.dump({"zip": args.zip_path, "cells": results}, f, indent=1)
    print(f"PCELLS OK: {len(cells)} cells flown with {args.zip_path}")


if __name__ == "__main__":
    main()
    sys.exit(0)

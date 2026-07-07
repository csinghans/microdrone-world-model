"""search-beams v1 — the rangefinder beam-count ablation.

Run the SAME rooms through the deployable body-aware safety filter at
4 / 8 / 16 beams, alongside the v3 single-beam rangefinder filter and
the privileged geometric ceiling, and tabulate collision / find /
return. All filters see identical seeds, so the collision deltas are
per-room paired, not sampling noise.

Pre-registered decision rule (experiments/search_beams_v1/journal.md):
PASS if collision(beams8) < collision(beams4) with find_rate and
return_rate holding (>= 0.85 find, not frozen); honest negative if more
beams don't move the residual or freeze the drone. Geometric = 0.000 is
the ceiling N beams approach, never beat.

Run:
  python -m eval.eval_beam_ablation --n 60 --seed0 140000
  python -m eval.eval_beam_ablation --selftest
"""

import argparse
import sys

FILTERS = ["geometric", "rangefinder", "beams4", "beams8", "beams16"]


def ablation(n, seed0, max_decisions=600, speed=0.6, filters=FILTERS):
    from eval.eval_search import suite

    rows = {}
    for f in filters:
        agg, _ = suite(
            "frontier",
            n,
            seed0=seed0,
            max_decisions=max_decisions,
            n_obstacles=2,
            speed=speed,
            safety=f,
        )
        rows[f] = agg
        print(
            f"  [{f}] collision {agg['collision_rate']:.3f}  "
            f"find {agg['find_rate']:.3f}  return {agg['return_rate']:.3f}",
            flush=True,
        )
    return rows


def selftest() -> None:
    # smoke: the beams8 filter runs a room end to end, aggregate schema ok
    rows = ablation(1, 90000, max_decisions=8, filters=["beams8"])
    assert 0.0 <= rows["beams8"]["collision_rate"] <= 1.0
    print("EVAL-BEAM-ABLATION OK: beams8 suite runs end to end, aggregate schema")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--seed0", type=int, default=140000)
    ap.add_argument("--max-decisions", type=int, default=600)
    ap.add_argument("--speed", type=float, default=0.6)
    ap.add_argument("--filters", nargs="+", default=FILTERS)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return

    rows = ablation(args.n, args.seed0, args.max_decisions, args.speed, args.filters)
    print(f"\n[beam-ablation] n={args.n} seed0={args.seed0} (same rooms, all filters)")
    print(f"  {'filter':<12}{'collision':>11}{'find':>8}{'return':>9}")
    for f in args.filters:
        a = rows[f]
        print(
            f"  {f:<12}{a['collision_rate']:>11.3f}"
            f"{a['find_rate']:>8.3f}{a['return_rate']:>9.3f}"
        )
    if "beams4" in rows and "beams8" in rows:
        c4, c8 = rows["beams4"]["collision_rate"], rows["beams8"]["collision_rate"]
        verdict = "beams HELP" if c8 < c4 else "NO improvement (honest negative)"
        print(
            f"\n  PRE-REG READ: collision beams4={c4:.3f} -> beams8={c8:.3f}  "
            f"[{verdict}]"
        )


if __name__ == "__main__":
    sys.exit(main())

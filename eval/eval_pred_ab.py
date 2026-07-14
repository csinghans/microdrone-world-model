"""The paired-geometry predecessor A/B (slalom_depth_v1 P3).

P1/P2 measured a real odoor->slalom death multiplier (z ~ 3.0) that no
recorded coordinate carries. This is the settling intervention: fly
2-stage courses [PRED, slalom3_fixed] at the SAME course seed with only
the predecessor name swapped — each stage consumes exactly one
course-rng draw, so the slalom stage's geometry is bit-identical across
arms (asserted at runtime). If the multiplier survives geometry pairing
it lives in the hand-off dynamics; if it vanishes it was a composition/
position confound wearing a predecessor costume.

Run:
  python -m eval.eval_pred_ab --pairs 160
  python -m eval.eval_pred_ab --selftest
"""

import argparse
import json
import os

import numpy as np

ARM_A = "opening_door"  # the hostile hand-off (P1: 0.333)
ARM_B = "door"  # the gentle hand-off (P1: 0.097)
SEED0 = 158000
PAIRS = 160
OUT_JSON = "experiments/slalom_depth_v1/p3_pred_ab.json"
# frozen verdict lines (journal P3, before any number)
RATIO_CONFIRM = 2.0  # odoor/door slalom death ratio, both-reached pairs
Z_CONFIRM = 2.0  # McNemar z on discordant pairs
RATIO_REFUTE = 1.5


def _fences(env, seed: int, names) -> list:
    """Spawn the course logically and return the slalom stage's fence
    meta (geometry fingerprint for the pairing assert)."""
    from sim.composite import CompositeCourse

    rng = np.random.default_rng(seed)
    sc = CompositeCourse(env, rng, stages=names)
    meta = getattr(sc, "meta", {}) or {}
    stages = meta.get("stages", names)
    del stages
    return [tuple(f) for f in meta.get("fences", ())]


def run(pairs: int = PAIRS, seed0: int = SEED0, out: str = OUT_JSON) -> dict:
    import torch  # noqa: F401

    from eval.eval_integration import (
        HYBRID,
        PerStageExperts,
        _load_all_skills,
        run_composite_episode,
    )
    from sim.composite import integration_metrics, register_course
    from sim.envs import make_env

    _load_all_skills()
    env = make_env()
    rows = []
    for i in range(pairs):
        seed = seed0 + i
        rec = {"seed": seed}
        for arm in (ARM_A, ARM_B):
            names = (arm, "slalom3_fixed")
            world = register_course(seed, k=2, names=names, tag=f"_{arm}")
            pol = PerStageExperts(names, 1.0, experts=dict(HYBRID))
            ep = run_composite_episode(env, pol, seed, world, k=2)
            m = integration_metrics(ep)
            brk = int(m.get("stage_break_at", -1))
            rec[arm] = {
                "reached_slalom": brk >= 1,
                "slalom_death": brk == 1,
                "fences": _fences(None, seed, names),
            }
        # the pairing assert: the slalom draw must be bit-identical
        assert (
            rec[ARM_A]["fences"] == rec[ARM_B]["fences"]
        ), f"geometry pairing broke at seed {seed}"
        rows.append(rec)
        print(
            f"  [{i + 1}/{pairs}] seed={seed} "
            f"{ARM_A}: {'DEAD' if rec[ARM_A]['slalom_death'] else 'ok'} | "
            f"{ARM_B}: {'DEAD' if rec[ARM_B]['slalom_death'] else 'ok'}",
            flush=True,
        )
    env.close()

    both = [
        r for r in rows if r[ARM_A]["reached_slalom"] and r[ARM_B]["reached_slalom"]
    ]
    a = sum(r[ARM_A]["slalom_death"] for r in both)
    b = sum(r[ARM_B]["slalom_death"] for r in both)
    disc_a = sum(
        r[ARM_A]["slalom_death"] and not r[ARM_B]["slalom_death"] for r in both
    )
    disc_b = sum(
        r[ARM_B]["slalom_death"] and not r[ARM_A]["slalom_death"] for r in both
    )
    n = len(both)
    ra, rb = a / max(n, 1), b / max(n, 1)
    ratio = ra / max(rb, 1e-9)
    z = (disc_a - disc_b) / max(np.sqrt(disc_a + disc_b), 1e-9)
    verdict = (
        "CONFIRMED"
        if (ratio >= RATIO_CONFIRM and z >= Z_CONFIRM)
        else ("REFUTED" if ratio < RATIO_REFUTE else "GRAY")
    )
    res = {
        "pairs": pairs,
        "seed0": seed0,
        "both_reached": n,
        "deaths": {ARM_A: a, ARM_B: b},
        "rates": {ARM_A: ra, ARM_B: rb},
        "ratio": ratio,
        "mcnemar": {"a_only": disc_a, "b_only": disc_b, "z": float(z)},
        "verdict": verdict,
        "rows": rows,
    }
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(res, f, indent=1)
    print(
        f"[pred-ab] both-reached {n}/{pairs} | slalom death "
        f"{ARM_A} {a}/{n} = {ra:.3f} vs {ARM_B} {b}/{n} = {rb:.3f} "
        f"ratio {ratio:.2f} (confirm >= {RATIO_CONFIRM}) | "
        f"McNemar {disc_a}/{disc_b} z {z:.2f} -> {verdict}"
    )
    print(f"[pred-ab] wrote {out}")
    return res


def selftest() -> None:
    from skills.base import load_skill

    for s in ("corridor-slalom-v2", "closing-door", "opening-door"):
        load_skill(s)
    from sim.composite import register_course
    from sim.scenario_registry import get

    # custom names + tag register distinct worlds at the same seed
    wa = register_course(7, k=2, names=(ARM_A, "slalom3_fixed"), tag="_a")
    wb = register_course(7, k=2, names=(ARM_B, "slalom3_fixed"), tag="_b")
    assert wa != wb and get(wa) is not None and get(wb) is not None
    # the pairing mechanism: one rng draw per stage -> identical slalom
    fa = _fences(None, 7, (ARM_A, "slalom3_fixed"))
    fb = _fences(None, 7, (ARM_B, "slalom3_fixed"))
    assert fa == fb and len(fa) == 3, (fa, fb)
    # a different seed draws different geometry (the assert has teeth)
    fc = _fences(None, 8, (ARM_A, "slalom3_fixed"))
    assert fc != fa
    # frozen constants
    assert (RATIO_CONFIRM, Z_CONFIRM, RATIO_REFUTE) == (2.0, 2.0, 1.5)
    assert (SEED0, PAIRS) == (158000, 160)
    print(
        "PRED-AB OK: paired registration, bit-identical slalom draw, "
        "teeth, frozen constants"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", type=int, default=PAIRS)
    ap.add_argument("--seed0", type=int, default=SEED0)
    ap.add_argument("--out", default=OUT_JSON)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    run(args.pairs, args.seed0, args.out)


if __name__ == "__main__":
    main()

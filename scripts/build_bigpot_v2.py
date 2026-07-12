"""Rebuild the slalom big pot with a DEPLOYMENT-MATCHED hot component.

transit_gate_v2 K1 (the pre-registration owns the bars): the record's
big pot mixed native chain-shape demos with hot seam-entry segments
whose upstream was the ORACLE relay — but at gate time the specialist
inherits the FT GENERALIST's exit states. This builder regenerates the
recipe and ADDS deployment-matched segments: a relay whose non-slalom
stages are flown by the deployed v3 generalist (creating the real exit
states) while the oracle Weave flies and labels the slalom stages;
courses restricted to slalom at position >= 1 (seam entries
guaranteed), the door->slalom mix reported.

Implementation note (a harness fact, not a bar change): the record
pot's raw arrays were never persisted, so "top up" = regenerate
(native + oracle-hot) by the same recipe + add the deployed-hot
component. The knob remains the added component; regeneration variance
is covered by the val >= 0.96 floor and the graduation gate.

Run:
  python -m scripts.build_bigpot_v2 --out experiments/transit_gate_v2/artifacts/ppo_slalom_bigpot_v2.zip
  python -m scripts.build_bigpot_v2 --selftest
"""

import argparse
import os
import sys

import numpy as np

NATIVE_EPS = 600  # weave chain demos on the standalone slalom world
HOT_ORACLE = 240  # courses, the recorded recipe's relay
HOT_DEPLOYED = 240  # courses, deployed upstream, slalom @ idx>=1 only
VAL_FLOOR = 0.96  # the big pot's own fidelity floor (frozen in the journal)
DEPLOYED_MIN = 4000  # minimum deployed-hot slalom decisions (frozen)
FT_V3 = "experiments/integration_ft/artifacts_local/ppo_integration_ft_v3.zip"
OUT = "experiments/transit_gate_v2/artifacts/ppo_slalom_bigpot_v2.zip"

# the deployed upstream: the v3 course-FT generalist flies every
# non-slalom stage (the exit states the specialist actually inherits);
# the oracle Weave flies AND LABELS the slalom stages
DEPLOYED_TEACHERS = {
    "gap": ("zip", FT_V3),
    "moving_gap": ("zip", FT_V3),
    "door": ("zip", FT_V3),
    "opening_door": ("zip", FT_V3),
    "slalom3_fixed": ("oracle", "weave"),
}


def _seam_slalom(names) -> bool:
    return "slalom3_fixed" in names[1:]


def build(out=OUT, native_eps=NATIVE_EPS, hot_oracle=HOT_ORACLE, hot_dep=HOT_DEPLOYED):
    from scripts.distill import bc_train, collect, collect_hot
    from sim.composite import course_for_seed
    from skills.base import load_skill

    for sk in (
        "gap-flight",
        "corridor-slalom-v2",
        "moving-gap",
        "closing-door",
        "opening-door",
    ):
        load_skill(sk)

    print(f"[pot-v2] native: {native_eps} weave chain episodes", flush=True)
    Xa, Ya = collect(native_eps, "slalom3_fixed", 1.0, teacher="weave")

    print(f"[pot-v2] hot-oracle: {hot_oracle} courses (the recorded recipe)")
    Xb, Yb, Tb, r_o = collect_hot(hot_oracle, seed0=120000)
    mb = Tb == "slalom3_fixed"

    print(f"[pot-v2] hot-deployed: {hot_dep} seam courses (v3 upstream)")
    Xc, Yc, Tc, r_d = collect_hot(
        hot_dep, seed0=125000, teachers=DEPLOYED_TEACHERS, course_filter=_seam_slalom
    )
    mc = Tc == "slalom3_fixed"
    # the transition mix of the deployed component, reported (door->slalom
    # carried 6 of the record's 13 slalom breaks)
    mix, cursor, found = {}, 0, 0
    while found < hot_dep:
        names = course_for_seed(125000 + cursor)
        cursor += 1
        if not _seam_slalom(names):
            continue
        found += 1
        for j in range(1, len(names)):
            if names[j] == "slalom3_fixed":
                mix[names[j - 1]] = mix.get(names[j - 1], 0) + 1
    print(f"[pot-v2] deployed X->slalom transition mix: {mix}")

    n_dep = int(mc.sum())
    assert n_dep >= DEPLOYED_MIN, f"deployed-hot floor: {n_dep} < {DEPLOYED_MIN}"
    X = np.concatenate([Xa, Xb[mb], Xc[mc]])
    Y = np.concatenate([Ya, Yb[mb], Yc[mc]])
    W = np.asarray(
        ["native"] * len(Xa) + ["hot_oracle"] * int(mb.sum()) + ["hot_deployed"] * n_dep
    )
    print(
        f"[pot-v2] pot: native {len(Xa)} + hot_oracle {int(mb.sum())} + "
        f"hot_deployed {n_dep} = {len(X)} decisions "
        f"(relay rates oracle {r_o:.3f} / deployed {r_d:.3f})"
    )
    os.makedirs(os.path.dirname(out), exist_ok=True)
    acc, _ = bc_train(X, Y, out, epochs=40, W=W)
    ok = acc >= VAL_FLOOR
    print(
        f"[pot-v2] pooled val {acc:.4f} (floor {VAL_FLOOR}) -> "
        f"{'FLOOR OK' if ok else 'FLOOR MISSED'} | saved {out}"
    )
    return 0 if ok else 3


def selftest() -> None:
    # env-free: the deployed table covers every stage type, slalom stays
    # oracle-taught, the seam filter and floors are sane
    from eval.eval_integration import STAGE_EXPERT

    assert set(DEPLOYED_TEACHERS) == set(STAGE_EXPERT)
    assert DEPLOYED_TEACHERS["slalom3_fixed"] == ("oracle", "weave")
    assert all(
        kind == "zip" and path == FT_V3
        for name, (kind, path) in DEPLOYED_TEACHERS.items()
        if name != "slalom3_fixed"
    )
    assert _seam_slalom(["gap", "slalom3_fixed", "door"])
    assert not _seam_slalom(["slalom3_fixed", "gap", "door"])  # cold start
    assert not _seam_slalom(["gap", "door", "moving_gap"])
    assert VAL_FLOOR == 0.96 and DEPLOYED_MIN == 4000
    print(
        "BUILD-BIGPOT-V2 OK: deployed table complete (slalom stays "
        "oracle-labelled), seam filter, frozen floors"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--native", type=int, default=NATIVE_EPS)
    ap.add_argument("--hot-oracle", type=int, default=HOT_ORACLE)
    ap.add_argument("--hot-deployed", type=int, default=HOT_DEPLOYED)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    sys.exit(build(args.out, args.native, args.hot_oracle, args.hot_deployed))


if __name__ == "__main__":
    sys.exit(main())

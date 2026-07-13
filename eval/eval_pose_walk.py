"""The entry-state random walk, measured (integration_k6_v1 K1).

The k=6 read found seam failure rates rising with position (3.2 % at
seam 1 → 20.6 % at seam 5). Hypothesis: StageLocal resets the policy's
memory at every stage but nothing resets the AIRCRAFT — exit-pose
variance accumulates like a random walk, so deeper seams sample wider,
more-OOD entry distributions. This probe re-flies the SAME k=6 block
with a read-only pose recorder at every stage entry and judges the
frozen branches in experiments/integration_k6_v1/journal.md.

Run:
  python -m eval.eval_pose_walk --probe
  python -m eval.eval_pose_walk --selftest
"""

import argparse
import json
import os

import numpy as np

STAGE_LEN = 3.0
SEED0 = 140000
N = 100
K = 6
K6_RECORD = "experiments/integration_k6_v1/k6_n100.json"
OUT_JSON = "experiments/integration_k6_v1/k1_pose_walk.json"

# frozen in the journal before any number
R_CONFIRM = 1.5  # deep/early spread ratio, |y| or |vy|
R_REFUTE = 1.2  # both below -> the walk is dead
LINK_RATIO = 2.0  # wide-entry vs narrow-entry seam failure rate


class PoseWalkProbe:
    """Read-only: records the aircraft pose at the first decision tick
    of every stage entry. Never touches the flight."""

    def __init__(self):
        self.rows: list = []

    def begin_course(self, seed: int, names) -> None:
        self.seed, self.names, self._stage = int(seed), tuple(names), -1

    def __call__(self, t, frame, state, a, scenario) -> None:
        del frame, a, scenario
        k = int(np.clip(float(state[0]) // STAGE_LEN, 0, len(self.names) - 1))
        if k != self._stage:
            self._stage = k
            self.rows.append(
                {
                    "seed": self.seed,
                    "pos": k,
                    "type": self.names[k],
                    "y": float(state[1]),
                    "z": float(state[2]),
                    "vx": float(state[10]),
                    "vy": float(state[11]),
                    "t": int(t),
                }
            )


def _spread(rows, metric, positions):
    vals = [abs(r[metric]) for r in rows if r["pos"] in positions]
    return float(np.mean(vals)) if vals else 0.0


def _verdict(rows, outcomes):
    by_seed = {o["seed"]: o for o in outcomes}
    for r in rows:
        o = by_seed[r["seed"]]
        stop = int(o.get("stage_break_at", K))
        r["broke_here"] = (not o["success"]) and stop == r["pos"]

    seam = [r for r in rows if r["pos"] >= 1]
    early, deep = (1, 2), (4, 5)
    ratios = {}
    table = {}
    for m in ("y", "vy"):
        e, d = _spread(seam, m, early), _spread(seam, m, deep)
        ratios[m] = float(d / max(e, 1e-9))
        table[m] = {
            "early_mean_abs": e,
            "deep_mean_abs": d,
            "by_pos": {
                p: {
                    "mean_abs": _spread(seam, m, (p,)),
                    "p90_abs": float(
                        np.percentile([abs(r[m]) for r in seam if r["pos"] == p], 90)
                    ),
                }
                for p in range(1, K)
            },
        }
    walk = (
        "CONFIRMED"
        if max(ratios.values()) >= R_CONFIRM
        else ("REFUTED" if max(ratios.values()) < R_REFUTE else "GRAY")
    )

    # death link: seam failure rate above vs below the median |y| entry
    ys = sorted(abs(r["y"]) for r in seam)
    med = ys[len(ys) // 2]
    wide = [r for r in seam if abs(r["y"]) >= med]
    narrow = [r for r in seam if abs(r["y"]) < med]
    f_wide = float(np.mean([r["broke_here"] for r in wide]))
    f_narrow = float(np.mean([r["broke_here"] for r in narrow]))
    link = float(f_wide / max(f_narrow, 1e-9))
    linked = bool(link >= LINK_RATIO)

    return {
        "ratios": ratios,
        "walk": walk,
        "table": table,
        "death_link": {
            "median_abs_y": med,
            "fail_wide": f_wide,
            "fail_narrow": f_narrow,
            "ratio": link,
            "linked": linked,
        },
    }


def probe_run(n=N, seed0=SEED0, out=OUT_JSON):
    import torch  # noqa: F401

    from eval.eval_integration import (
        HYBRID,
        PerStageExperts,
        _load_all_skills,
        run_composite_episode,
    )
    from sim.composite import (
        course_for_seed,
        integration_metrics,
        integration_success,
        register_course,
    )
    from sim.envs import make_env

    _load_all_skills()
    pw = PoseWalkProbe()
    env = make_env()
    outcomes = []
    for i in range(n):
        seed = seed0 + i
        names = course_for_seed(seed, k=K)
        world = register_course(seed, k=K)
        pw.begin_course(seed, names)
        ep = run_composite_episode(
            env,
            PerStageExperts(names, 1.0, experts=dict(HYBRID)),
            seed,
            world,
            k=K,
            probe=pw,
        )
        m = integration_metrics(ep)
        outcomes.append(
            {
                "seed": seed,
                "success": bool(integration_success(ep)),
                "stage_break_at": int(m.get("stage_break_at", -1)),
            }
        )
        print(f"  [{i + 1}/{n}] seed={seed} entries={len(pw.rows)}", flush=True)
    env.close()

    # instrument: the probe only reads — outcomes must match the record
    with open(K6_RECORD) as f:
        rec = {r["seed"]: r["success"] for r in json.load(f)["records"]}
    match = float(np.mean([o["success"] == rec[o["seed"]] for o in outcomes]))

    res = _verdict(pw.rows, outcomes)
    res["instrument"] = {"outcome_match": match, "n_entries": len(pw.rows)}
    print(
        f"[pose-walk] instrument match {match:.3f} | spread ratios "
        f"y {res['ratios']['y']:.2f} / vy {res['ratios']['vy']:.2f} "
        f"(confirm >= {R_CONFIRM}) -> WALK {res['walk']}"
    )
    dl = res["death_link"]
    print(
        f"[pose-walk] death link: fail(wide |y|) {dl['fail_wide']:.3f} vs "
        f"fail(narrow) {dl['fail_narrow']:.3f} = x{dl['ratio']:.1f} "
        f"(bar {LINK_RATIO}) -> {'LINKED' if dl['linked'] else 'not linked'}"
    )
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(res, f, indent=1)
    print(f"[pose-walk] wrote {out}")
    return res


def selftest() -> None:
    # entry detection: one row per stage change, pose captured
    pw = PoseWalkProbe()
    pw.begin_course(7, ("gap", "door", "gap"))
    s = np.zeros(20)

    def st(x, y, vy):
        s2 = s.copy()
        s2[0], s2[1], s2[11] = x, y, vy
        return s2

    for x, y, vy in (
        (0.1, 0.0, 0.0),
        (1.5, 0.1, 0.0),
        (3.2, 0.4, -0.2),
        (4.0, 0.2, 0.0),
        (6.3, -0.5, 0.3),
    ):
        pw(0, None, st(x, y, vy), 0, None)
    assert [r["pos"] for r in pw.rows] == [0, 1, 2]
    assert abs(pw.rows[1]["y"] - 0.4) < 1e-9 and abs(pw.rows[2]["vy"] - 0.3) < 1e-9

    # verdict arithmetic on a synthetic walk (spread doubles, deaths wide)
    rows = []
    for p in range(1, 6):
        for i in range(40):
            y = (0.1 + 0.05 * p) * (1 if i % 2 else -1) * (1 + (i % 5) / 5)
            rows.append(
                {
                    "seed": 1000 + i,
                    "pos": p,
                    "type": "gap",
                    "y": y,
                    "z": 0.5,
                    "vx": 1.0,
                    "vy": y / 2,
                    "t": 0,
                }
            )
    outs = [{"seed": 1000 + i, "success": True, "stage_break_at": 6} for i in range(40)]
    v = _verdict(rows, outs)
    assert v["ratios"]["y"] > 1.5 and v["walk"] == "CONFIRMED"

    # flat spread -> refuted
    flat = [dict(r, y=0.2 * (1 if r["seed"] % 2 else -1), vy=0.1) for r in rows]
    v2 = _verdict(flat, outs)
    assert v2["walk"] == "REFUTED", v2["ratios"]

    assert (R_CONFIRM, R_REFUTE, LINK_RATIO) == (1.5, 1.2, 2.0)
    assert (SEED0, N, K) == (140000, 100, 6)
    print(
        "POSE-WALK OK: entry detection, synthetic walk CONFIRMED, flat "
        "REFUTED, frozen thresholds"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--n", type=int, default=N)
    ap.add_argument("--out", default=OUT_JSON)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    if args.probe:
        probe_run(args.n, out=args.out)
        return
    ap.print_help()


if __name__ == "__main__":
    main()

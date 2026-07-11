"""The first noisy beam — pricing the ring (beam_noise_v1 / P1).

Every beam the indoor safety case rides (91/100, zero collision
missions) has been noiseless. This pricing run perturbs EXACTLY what
the beams8 safety filter reads — a delegating scenario proxy whose
`beam_ranges` alone carries range noise or ToF-style dropout-to-max —
while the judge (`clearance`), the planner context (`range_sensors`)
and the beacon stay clean. Six arms on identical fresh seeds; the
deliverable is the noise footnote on the deployable claim (where does
collision cross the 0.05 SEARCH-ROOM bar?). Pre-registration:
experiments/beam_noise_v1/journal.md (committed first).

Run:
  python -m eval.eval_beam_noise --price
  python -m eval.eval_beam_noise --selftest
"""

import argparse
import json
import os
import sys

import numpy as np

SEED0 = 740000  # fresh block
N = 30  # the v3 gate's n
ARMS = (
    ("clean", 0.00, 0.00),
    ("sigma05", 0.05, 0.00),
    ("sigma10", 0.10, 0.00),
    ("sigma20", 0.20, 0.00),
    ("drop05", 0.00, 0.05),
    ("drop10", 0.00, 0.10),
)
COLLISION_BAR = 0.05  # the SEARCH-ROOM bar the footnote is priced against


class NoisyBeams:
    """A delegating scenario proxy: `beam_ranges` — and ONLY
    `beam_ranges` — is perturbed (seeded rng per mission). Everything
    else (clearance judging, range_sensors, sense_beacon, spawn_*)
    delegates untouched."""

    def __init__(self, sc, sigma=0.0, drop=0.0, seed=0):
        self._sc = sc
        self._sigma, self._drop = float(sigma), float(drop)
        self._rng = np.random.default_rng(seed)

    def __getattr__(self, name):
        return getattr(self._sc, name)

    def beam_ranges(self, pos_xy, n_beams: int = 8, max_range: float = 3.0):
        out = []
        for b, r in self._sc.beam_ranges(pos_xy, n_beams=n_beams, max_range=max_range):
            if self._drop > 0.0 and self._rng.random() < self._drop:
                r = float(max_range)  # a missed ToF return reads "far"
            elif self._sigma > 0.0:
                r = max(0.0, float(r) + float(self._rng.normal(0.0, self._sigma)))
            out.append((b, float(r)))
        return out


def price(n=N, seed0=SEED0, out=None):
    from eval.search_episode import run_search_episode
    from search.strategies import get_strategy
    from sim.envs import make_env
    from sim.indoor.rooms import single_room

    env = make_env()
    res = {}
    for name, sigma, drop in ARMS:
        rows = []
        for i in range(n):
            sc = NoisyBeams(single_room(seed0 + i), sigma, drop, seed=seed0 + i)
            m = run_search_episode(
                env,
                sc,
                get_strategy("frontier"),
                seed=seed0 + i,
                max_decisions=600,
                speed=0.6,  # hardcoded robust config (never inherited)
                safety="beams8",
            )
            rows.append(m)
        res[name] = {
            "sigma": sigma,
            "drop": drop,
            "find": float(np.mean([r["target_found"] for r in rows])),
            "return": float(np.mean([r["returned"] for r in rows])),
            "collision": float(np.mean([r["crashed"] for r in rows])),
        }
        s = res[name]
        print(
            f"  [{name:8s}] find={s['find']:.3f} return={s['return']:.3f} "
            f"collision={s['collision']:.3f}"
            + ("  <-- over the 0.05 bar" if s["collision"] > COLLISION_BAR else ""),
            flush=True,
        )
    env.close()
    clean_ok = (
        res["clean"]["find"] >= 0.80 and res["clean"]["collision"] <= COLLISION_BAR
    )
    if not clean_ok:
        print(
            "[beam-noise] CLEAN ARM OUT OF ITS HISTORICAL BAND — harness "
            "suspect, no pricing read (instrument-first)."
        )
    else:
        sig_knee = next(
            (
                f"sigma={s}"
                for nm, s, _d in ARMS[1:4]
                if res[nm]["collision"] > COLLISION_BAR
            ),
            "beyond sigma=0.20",
        )
        drop_knee = next(
            (
                f"p={d}"
                for nm, _s, d in ARMS[4:]
                if res[nm]["collision"] > COLLISION_BAR
            ),
            "beyond p=0.10",
        )
        print(
            f"[beam-noise] the footnote: collision crosses {COLLISION_BAR} at "
            f"{sig_knee} (noise) / {drop_knee} (dropout)"
        )
    if out:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w") as f:
            json.dump(res, f, indent=1)
        print(f"[beam-noise] wrote {out}")
    return res


def selftest() -> None:
    from sim.indoor.rooms import single_room

    sc = single_room(3)
    raw = sc.beam_ranges((0.0, 0.0), n_beams=8)
    # sigma=0, drop=0: byte-identical passthrough
    p0 = NoisyBeams(sc, 0.0, 0.0, seed=1).beam_ranges((0.0, 0.0), n_beams=8)
    assert all(abs(a[1] - b[1]) < 1e-12 and a[0] == b[0] for a, b in zip(raw, p0))
    # noise: bearings identical, ranges differ, never negative
    pn = NoisyBeams(sc, 0.10, 0.0, seed=1).beam_ranges((0.0, 0.0), n_beams=8)
    assert all(a[0] == b[0] for a, b in zip(raw, pn))
    assert any(abs(a[1] - b[1]) > 1e-6 for a, b in zip(raw, pn))
    assert all(b[1] >= 0.0 for b in pn)
    # full dropout: every reading is the max range
    pd = NoisyBeams(sc, 0.0, 1.0, seed=1).beam_ranges((0.0, 0.0), n_beams=8)
    assert all(abs(b[1] - 3.0) < 1e-12 for b in pd)
    # seeded reproducibility
    pa = NoisyBeams(sc, 0.10, 0.0, seed=7).beam_ranges((0.0, 0.0), n_beams=8)
    pb = NoisyBeams(sc, 0.10, 0.0, seed=7).beam_ranges((0.0, 0.0), n_beams=8)
    assert all(abs(a[1] - b[1]) < 1e-12 for a, b in zip(pa, pb))
    # everything else delegates untouched (the judge stays clean)
    prox = NoisyBeams(sc, 0.20, 0.5, seed=1)
    assert prox.clearance((0.0, 0.0)) == sc.clearance((0.0, 0.0))
    assert prox.range_sensors((0.0, 0.0)) == sc.range_sensors((0.0, 0.0))
    print(
        "BEAM-NOISE OK: passthrough at zero, seeded noise/dropout on beams "
        "only, judge and planner context delegate clean"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--price", action="store_true")
    ap.add_argument("--n", type=int, default=N)
    ap.add_argument("--out", default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    if not args.price:
        raise SystemExit("--price (or --selftest)")
    price(n=args.n, out=args.out)


if __name__ == "__main__":
    sys.exit(main())

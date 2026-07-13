"""The late beam — pricing ring latency (beam_latency_v1).

P1 priced noise and dropout; this prices the last sensor axis: a ToF
ring that reports LATE. `DelayedBeams` is a delegating scenario proxy
in the P1 mould — `beam_ranges`, and ONLY `beam_ranges`, returns the
reading captured k calls ago (readings keep their old positions: the
report lags the aircraft) — while the judge (`clearance`), the planner
context (`range_sensors`) and the beacon stay clean. Five arms on
identical fresh seeds; the deliverable completes the sensor BOM spec
line: how much ring latency does beams8 safety absorb at 0.6 m/s?
Pre-registration: experiments/beam_latency_v1/journal.md (committed
first).

Run:
  python -m eval.eval_beam_latency --price
  python -m eval.eval_beam_latency --selftest
"""

import argparse
import json
import os
import sys

import numpy as np

SEED0 = 750000  # fresh block (P1 used 740000)
N = 30
ARMS = (("d0", 0), ("d1", 1), ("d2", 2), ("d4", 4), ("d8", 8))
COLLISION_BAR = 0.05  # the SEARCH-ROOM bar the footnote is priced against
MS_PER_DECISION = 1000.0 / 12.0  # the 12 Hz decide rate


class DelayedBeams:
    """A delegating scenario proxy: `beam_ranges` — and ONLY
    `beam_ranges` — returns the reading captured k calls ago (FIFO;
    the first k calls replay the initial reading — sensor warm-up,
    stated honestly). Everything else delegates untouched."""

    def __init__(self, sc, delay=0):
        self._sc = sc
        self._k = int(delay)
        self._buf = []
        self.reads = 0  # instrument: reads-per-decision is reported

    def __getattr__(self, name):
        return getattr(self._sc, name)

    def beam_ranges(self, pos_xy, n_beams: int = 8, max_range: float = 3.0):
        self.reads += 1
        cur = self._sc.beam_ranges(pos_xy, n_beams=n_beams, max_range=max_range)
        if self._k == 0:
            return cur
        self._buf.append(cur)
        if len(self._buf) > self._k + 1:
            self._buf.pop(0)
        return self._buf[0]


def price(n=N, seed0=SEED0, out=None):
    from eval.search_episode import run_search_episode
    from search.strategies import get_strategy
    from sim.envs import make_env
    from sim.indoor.rooms import single_room

    env = make_env()
    res = {}
    for name, k in ARMS:
        rows, reads, decs = [], 0, 0
        for i in range(n):
            sc = DelayedBeams(single_room(seed0 + i), delay=k)
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
            reads += sc.reads
            decs += int(m.get("decisions", 0)) or 600
        rpd = reads / max(decs, 1)
        res[name] = {
            "delay_reads": k,
            "reads_per_decision": float(rpd),
            "delay_ms_est": float(k * MS_PER_DECISION / max(rpd, 1e-9)),
            "find": float(np.mean([r["target_found"] for r in rows])),
            "return": float(np.mean([r["returned"] for r in rows])),
            "collision": float(np.mean([r["crashed"] for r in rows])),
        }
        s = res[name]
        print(
            f"  [{name:3s}] find={s['find']:.3f} return={s['return']:.3f} "
            f"collision={s['collision']:.3f} "
            f"(~{s['delay_ms_est']:.0f} ms at {s['reads_per_decision']:.2f} "
            f"reads/decision)"
            + ("  <-- over the 0.05 bar" if s["collision"] > COLLISION_BAR else ""),
            flush=True,
        )
    env.close()
    clean_ok = res["d0"]["find"] >= 0.80 and res["d0"]["collision"] <= COLLISION_BAR
    if not clean_ok:
        print(
            "[beam-latency] CONTROL ARM OUT OF ITS HISTORICAL BAND — harness "
            "suspect, no pricing read (instrument-first)."
        )
    else:
        knee = next(
            (nm for nm, _k in ARMS[1:] if res[nm]["collision"] > COLLISION_BAR),
            None,
        )
        pocket = None
        for nm, _k in ARMS[1:]:
            if res[nm]["collision"] > COLLISION_BAR:
                break
            pocket = nm
        p_ms = res[pocket]["delay_ms_est"] if pocket else 0.0
        print(
            f"[beam-latency] the footnote: pocket = {pocket or 'none'} "
            f"(~{p_ms:.0f} ms absorbed); collision crosses {COLLISION_BAR} at "
            f"{knee or 'beyond d8'}"
        )
    if out:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w") as f:
            json.dump(res, f, indent=1)
        print(f"[beam-latency] wrote {out}")
    return res


def selftest() -> None:
    class FakeSC:
        """Scripted scenario: beam_ranges returns its call index."""

        def __init__(self):
            self.calls = 0
            self.beacon = "untouched"

        def beam_ranges(self, pos_xy, n_beams=8, max_range=3.0):
            self.calls += 1
            return [(0, float(self.calls))]

        def clearance(self, xy):
            return 9.0

    # d0 is a pure passthrough
    p0 = DelayedBeams(FakeSC(), delay=0)
    assert [p0.beam_ranges((0, 0))[0][1] for _ in range(3)] == [1.0, 2.0, 3.0]

    # d2 returns the reading from two calls ago after warm-up, and the
    # first calls replay the initial reading
    p2 = DelayedBeams(FakeSC(), delay=2)
    got = [p2.beam_ranges((0, 0))[0][1] for _ in range(5)]
    assert got == [1.0, 1.0, 1.0, 2.0, 3.0], got

    # delegation untouched; read counter counts
    assert p2.beacon == "untouched" and p2.clearance((0, 0)) == 9.0
    assert p2.reads == 5

    # frozen constants
    assert [k for _n, k in ARMS] == [0, 1, 2, 4, 8]
    assert COLLISION_BAR == 0.05 and SEED0 == 750000
    print(
        "BEAM-LATENCY OK: d0 passthrough, FIFO delay + warm-up replay, "
        "delegation untouched, read counter, frozen arms"
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
    if args.price:
        price(args.n, out=args.out)
        return
    ap.print_help()


if __name__ == "__main__":
    sys.exit(main())

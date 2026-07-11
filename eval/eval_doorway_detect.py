"""Feasibility probe — can a cheap beam ring detect doorway-adjacency?

The topological room graph needs the drone to know it is at a doorway,
from deployable sensing alone. This measures how well `doorway_score`
(a beam-ring scalar, no ground truth) separates doorway-adjacent
positions from room interiors, as a rank AUC over sampled positions in
N-room layouts — the same instrument-probe shape as the WM transfer
probe.

Pre-registered rule (experiments/search_doorway_v1/journal.md, frozen
before the number): AUC >= 0.80 -> a cheap ring detects doorways well
enough to build a room graph on; AUC < 0.65 -> single-position ring
detection is too weak (honest negative — the topological map would need
trajectory integration or a richer signal). The matrix reports the
pre-registered static probe (`doorway_score` vs a loose "near" label)
and the trajectory-integration hypothesis (`passage_score` vs an
in-the-gap "crossing" label), 16 beams.

Run:
  python -m eval.eval_doorway_detect --n 12 --n-rooms 4
  python -m eval.eval_doorway_detect --selftest
"""

import argparse
import sys

import numpy as np

from search.doorway import doorway_score, max_wall_run, passage_score
from sim.scenarios import COLLISION_R

FIRE_THR = 1.0  # passage_score above this = the naive counter fires a crossing

R_DOOR = 1.3  # "doorway-adjacent" (loose): within this of a doorway centre
GAP_DX = 0.5  # "in the gap" (tight): |x - divider| < this ...
GAP_DY = 0.9  # ... and |y| < this (inside the clear opening)
MIN_CLEAR = 0.35  # only score positions the drone would actually occupy
GRID = 0.25  # sampling resolution (m)


def _auc(scores, labels) -> float:
    s, y = np.asarray(scores, float), np.asarray(labels, int)
    pos, neg = s[y == 1], s[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty(len(s), float)
    ranks[order] = np.arange(1, len(s) + 1)
    return float(
        (ranks[y == 1].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))
    )


def _doorway_centres(scenario):
    """Each divider gap centre (x0 + k*ROOM_W, y=0) — from the layout
    geometry, NOT the obstacle list (box clutter adds obstacle x's that are
    not doorways)."""
    from sim.indoor.rooms import ROOM_W

    x0 = scenario.bounds[0]
    n = int(scenario.meta.get("n_rooms", 1))
    return [(x0 + k * ROOM_W, 0.0) for k in range(1, n)]


def _label(x, y, centres, mode):
    if mode == "gap":  # standing IN a doorway opening
        return (
            1
            if any(abs(x - cx) < GAP_DX and abs(y) < GAP_DY for cx, _ in centres)
            else 0
        )
    near = min(np.hypot(x - cx, y - cy) for cx, cy in centres)  # "near": loose
    return 1 if near < R_DOOR else 0


def probe(score_fn, label_mode, n=12, n_rooms=4, seed0=210000, n_beams=16, clutter=0):
    from sim.indoor.rooms import n_room

    scores, labels = [], []
    for i in range(n):
        sc = n_room(seed0 + i, n_rooms=n_rooms, clutter=clutter)
        centres = _doorway_centres(sc)
        x0, x1, y0, y1 = sc.bounds
        for x in np.arange(x0 + GRID, x1, GRID):
            for y in np.arange(y0 + GRID, y1, GRID):
                if sc.clearance((x, y)) <= MIN_CLEAR:
                    continue  # not a spot the drone occupies
                scores.append(score_fn(sc, (x, y), n_beams=n_beams))
                labels.append(_label(x, y, centres, label_mode))
    return _auc(scores, labels), len(scores), float(np.mean(labels))


def discriminate_window(
    n=12, n_rooms=4, seed0=210000, clutter=2, n_beams=16, half_len=0.5, samples=9
):
    """roomgraph_v2 P0: on the SAME firing set as discriminate(), score the
    traversal-window features. The window is synthesized: `samples` points
    at +-half_len along the crossing direction (the squeeze axis's
    perpendicular) — the line a real 0.36 m/s traversal would sweep in
    ~+-1.4 s. Samples inside geometry count as NOT bilateral (a real
    crossing could not produce them; the HARNESS uses clearance() for that
    and for labels — the FEATURE reads only the ring). Primary =
    traversal persistence (fraction of samples with both flanks);
    secondaries = window-mean -max_wall_run, window-min passage_score."""
    from search.doorway import _squeeze_axis, bilateral_flanks
    from sim.indoor.rooms import n_room

    prim, sec_run, sec_pass, labels = [], [], [], []
    for i in range(n):
        sc = n_room(seed0 + i, n_rooms=n_rooms, clutter=clutter)
        centres = _doorway_centres(sc)
        x0, x1, y0, y1 = sc.bounds
        for x in np.arange(x0 + GRID, x1, GRID):
            for y in np.arange(y0 + GRID, y1, GRID):
                if sc.clearance((x, y)) <= MIN_CLEAR:
                    continue
                if passage_score(sc, (x, y), n_beams=n_beams) <= FIRE_THR:
                    continue
                theta = _squeeze_axis(sc, (x, y), n_beams=n_beams)
                dx, dy = np.cos(theta + np.pi / 2), np.sin(theta + np.pi / 2)
                hits, runs, passes = 0, [], []
                for t in np.linspace(-half_len, half_len, samples):
                    p = (x + t * dx, y + t * dy)
                    if sc.clearance(p) <= COLLISION_R:  # blocked: not bilateral
                        runs.append(-float(n_beams))
                        passes.append(-10.0)
                        continue
                    if bilateral_flanks(sc, p, theta, n_beams=n_beams):
                        hits += 1
                    runs.append(-float(max_wall_run(sc, p, n_beams=n_beams)))
                    passes.append(passage_score(sc, p, n_beams=n_beams))
                prim.append(hits / samples)
                sec_run.append(float(np.mean(runs)))
                sec_pass.append(float(np.min(passes)))
                labels.append(_label(x, y, centres, "gap"))
    fp = 1.0 - (sum(labels) / len(labels)) if labels else float("nan")
    return {
        "n_firings": int(len(labels)),
        "fp_rate": float(fp),
        "primary_auc": _auc(prim, labels),
        "sec_wallrun_auc": _auc(sec_run, labels),
        "sec_minpass_auc": _auc(sec_pass, labels),
    }


def discriminate(n=12, n_rooms=4, seed0=210000, clutter=2, n_beams=16):
    """Among positions where passage_score FIRES (> FIRE_THR), can
    max_wall_run tell a TRUE doorway (thin dividers -> small run) from a
    box-wall pinch false-positive (extended wall -> large run)? Report the
    false-positive rate the naive counter suffers and the AUC of
    -max_wall_run separating true doorways from those false-positives."""
    from sim.indoor.rooms import n_room

    feats, labels = [], []
    for i in range(n):
        sc = n_room(seed0 + i, n_rooms=n_rooms, clutter=clutter)
        centres = _doorway_centres(sc)
        x0, x1, y0, y1 = sc.bounds
        for x in np.arange(x0 + GRID, x1, GRID):
            for y in np.arange(y0 + GRID, y1, GRID):
                if sc.clearance((x, y)) <= MIN_CLEAR:
                    continue
                if passage_score(sc, (x, y), n_beams=n_beams) <= FIRE_THR:
                    continue  # only positions the naive counter would fire on
                true_door = _label(x, y, centres, "gap")
                feats.append(-max_wall_run(sc, (x, y), n_beams=n_beams))
                labels.append(true_door)
    fp_rate = 1.0 - (sum(labels) / len(labels)) if labels else float("nan")
    return _auc(feats, labels), len(labels), fp_rate


def selftest() -> None:
    assert abs(_auc([0.1, 0.2, 0.8, 0.9], [0, 0, 1, 1]) - 1.0) < 1e-9
    assert abs(_auc([0.9, 0.8, 0.2, 0.1], [0, 0, 1, 1]) - 0.0) < 1e-9
    assert COLLISION_R < MIN_CLEAR < R_DOOR
    print("EVAL-DOORWAY OK: AUC math + probe constants sane")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--n-rooms", type=int, default=4)
    ap.add_argument("--seed0", type=int, default=210000)
    ap.add_argument("--clutter", type=int, default=0, help="box obstacles per room")
    ap.add_argument(
        "--discriminate",
        action="store_true",
        help="can max_wall_run separate true doorways from box-pinch false-fires?",
    )
    ap.add_argument(
        "--window",
        action="store_true",
        help="roomgraph_v2 P0: the traversal-window features on the firing set",
    )
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    if args.window:
        r = discriminate_window(
            args.n, args.n_rooms, args.seed0, clutter=max(args.clutter, 2)
        )
        a = r["primary_auc"]
        verdict = (
            "FLIGHT REGATE RELEASED (>= 0.85)"
            if a >= 0.85
            else (
                "learned-window-head knob released (0.75-0.85)"
                if a >= 0.75
                else "honest bound (< 0.75) — the room graph stays clean-room-only"
            )
        )
        print(
            f"[window] {r['n_firings']} firings, {r['fp_rate']:.0%} box-pinch | "
            f"traversal_persistence AUC {a:.3f} "
            f"(single-frame ref 0.631)  [{verdict}]"
        )
        print(
            f"  secondaries: window-mean -max_wall_run {r['sec_wallrun_auc']:.3f}  "
            f"window-min passage_score {r['sec_minpass_auc']:.3f}"
        )
        return
    if args.discriminate:
        auc, npos, fp = discriminate(
            args.n, args.n_rooms, args.seed0, clutter=max(args.clutter, 2)
        )
        verdict = (
            "usable (>=0.80)"
            if auc >= 0.80
            else ("weak (<0.65)" if auc < 0.65 else "borderline")
        )
        print(
            f"[discriminate] {npos} passage-firing positions, "
            f"{fp:.0%} are box-pinch false-fires | -max_wall_run AUC {auc:.3f}  "
            f"[{verdict}]"
        )
        return

    def tag(auc):
        return (
            "FEASIBLE (>=0.80)"
            if auc >= 0.80
            else ("weak (<0.65)" if auc < 0.65 else "borderline")
        )

    # (score, label): the pre-registered static probe, then the
    # trajectory-integration hypothesis (detect the passage while IN it)
    combos = [
        ("doorway_score", doorway_score, "near"),
        ("passage_score", passage_score, "near"),
        ("passage_score", passage_score, "gap"),
    ]
    for nb in (16,):
        for name, fn, mode in combos:
            auc, npos, rate = probe(
                fn,
                mode,
                args.n,
                args.n_rooms,
                args.seed0,
                n_beams=nb,
                clutter=args.clutter,
            )
            print(
                f"[doorway] {nb}b {name} vs '{mode}' clutter={args.clutter} "
                f"({npos} pos, pos-rate {rate:.2f}): AUC {auc:.3f}  [{tag(auc)}]"
            )


if __name__ == "__main__":
    sys.exit(main())

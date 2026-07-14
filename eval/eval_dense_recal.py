"""dense_recal_v1 K0 — the clutter-context instrument probe.

head_calibration C0 closed with "conditional recalibration needs a
world label the flying drone doesn't have". This probe asks whether a
DEPLOYABLE signal — a beams8-style local-clutter count, the priced
multiranger's twin — can stand in for that label: (K0a) does it
separate the dense regime, (K0b) does the conditional warn inflation
rise monotonically along it, (K0c) does a per-bin temperature move
C0's own metric the way C0's global scalar could not. No flights;
everything is computed offline from stored rollouts (pos + pillars).

Run:
  python -m eval.eval_dense_recal --rollouts 48 --len 120
  python -m eval.eval_dense_recal --selftest
"""

import argparse
import json
import os

import numpy as np
import torch

from eval.eval_head_calibration import _ece, _surface
from world_model.training import _split_rollouts

MAX_RANGE = 3.0
NEAR = 1.0  # a ray returning under this counts as clutter
N_RAYS = 8
T_GRID = np.arange(0.25, 4.0001, 0.05)
OUT_JSON = "experiments/dense_recal_v1/k0_results.json"
# frozen bars (journal K0, before any number)
K0A_AUC = 0.80
K0B_GAP = 0.05
K0C_DENSE_WARN_ECE = 0.09  # C0's own target, verbatim
K0C_SLICE_WORSEN = 0.01
K0C_AUC_DROP = 0.005


def clutter_count(xy, pillars, pillar_r) -> int:
    """Count of the 8 compass rays from `xy` that hit a pillar circle
    (radius pillar_r) within NEAR metres. Pure geometry — the offline
    twin of the multiranger ring."""
    hits = 0
    px = pillars[~np.isnan(pillars[:, 0])]
    if len(px) == 0:
        return 0
    for i in range(N_RAYS):
        th = 2.0 * np.pi * i / N_RAYS
        d = np.array([np.cos(th), np.sin(th)])
        best = MAX_RANGE
        for cx, cy in px[:, :2]:
            rel = np.array([cx, cy]) - xy
            proj = float(rel @ d)
            if proj <= 0:
                continue
            perp2 = float(rel @ rel) - proj * proj
            r2 = pillar_r * pillar_r
            if perp2 > r2:
                continue
            t = proj - np.sqrt(r2 - perp2)
            if 0.0 < t < best:
                best = t
        if best < NEAR:
            hits += 1
    return hits


def _auc(score: np.ndarray, y: np.ndarray) -> float:
    pos, neg = score[y == 1], score[y == 0]
    if not len(pos) or not len(neg):
        return float("nan")
    return float(np.mean([(np.mean(p > neg) + 0.5 * np.mean(p == neg)) for p in pos]))


def _fit_T(logit: np.ndarray, y: np.ndarray) -> float:
    """1-D deterministic grid fit of temperature by BCE (C0's fit,
    restricted to one bin)."""
    best_t, best_l = 1.0, np.inf
    for t in T_GRID:
        p = 1.0 / (1.0 + np.exp(-logit / t))
        p = np.clip(p, 1e-6, 1 - 1e-6)
        loss = float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean())
        if loss < best_l:
            best_l, best_t = loss, float(t)
    return best_t


def run(n_rollouts: int, length: int, out: str = OUT_JSON) -> dict:
    from datasets.generate_rollouts import gen
    from datasets.intervention_labels import counterfactual_labels
    from skills.gap_flight.skill import PILLAR_R

    data = gen(n_rollouts, length, seed=160, worlds=("classic", "dense", "moving"))
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    rng = np.random.default_rng(0)
    tr_rolls, va_rolls = _split_rollouts(data, rng)
    cf, vis = counterfactual_labels(data)

    def flat(rolls):
        P = _surface("output/world_model.pth", data, rolls, device)
        L = data["frames"].shape[1]
        lbl = np.concatenate([cf[r, :, :, -1, :] for r in rolls])
        msk = np.concatenate([vis[r] for r in rolls]).astype(bool)
        world = np.concatenate([np.full(L, int(data["world_id"][r])) for r in rolls])
        clut = np.concatenate(
            [
                np.array(
                    [
                        clutter_count(
                            data["pos"][r, t, :2], data["pillars"][r], PILLAR_R
                        )
                        for t in range(L)
                    ]
                )
                for r in rolls
            ]
        )
        return P, lbl, msk, world, clut

    Ptr, ltr, mtr, wtr, ctr = flat(tr_rolls)
    Pva, lva, mva, wva, cva = flat(va_rolls)
    wn = ["classic", "dense", "moving"]

    # bins — INSTRUMENT REPAIR (documented in the journal): the frozen
    # tercile spec degenerates on this corpus (the clutter count is
    # mostly low, so tercile edges collapse and bin 0 empties to NaN).
    # Fixed integer bins replace it: {0}, {1-2}, {>=3}. Deterministic,
    # no fitting; the K0a/K0c verdict semantics are unchanged.
    edges = (0.5, 2.5)

    def binof(c):
        return np.digitize(c, edges)  # 0 / 1-2 / >=3

    # K0a — separation on val frames
    k0a = _auc(cva.astype(float), (wva == wn.index("dense")).astype(float))

    # K0b — signed warn gap by clutter bin (val, masked, warn ring)
    gaps = []
    for b in range(3):
        fm = binof(cva) == b
        p = Pva[fm][:, :, 0][mva[fm]]
        y = lva[fm][:, :, 0][mva[fm]]
        gaps.append(float(p.mean() - y.mean()))
    monotone = gaps[0] <= gaps[1] <= gaps[2]
    k0b_gap = gaps[2] - gaps[0]

    # K0c — per-(ring, bin) temperature fitted on TRAIN, applied to VAL
    temps = {}
    for ring in (0, 1):
        for b in range(3):
            fm = binof(ctr) == b
            p = np.clip(Ptr[fm][:, :, ring][mtr[fm]], 1e-6, 1 - 1e-6)
            logit = np.log(p / (1 - p))
            y = ltr[fm][:, :, ring][mtr[fm]].astype(float)
            temps[(ring, b)] = _fit_T(logit, y)

    def apply_T(P, clut):
        Q = P.copy()
        bb = binof(clut)
        for ring in (0, 1):
            for b in range(3):
                fm = bb == b
                p = np.clip(P[fm][:, :, ring], 1e-6, 1 - 1e-6)
                Q[fm, :, ring] = 1.0 / (
                    1.0 + np.exp(-np.log(p / (1 - p)) / temps[(ring, b)])
                )
        return Q

    Qva = apply_T(Pva, cva)
    slices = {}
    for w in range(3):
        fm = wva == w
        row = {}
        for ring, q in (("warn", 0), ("crit", 1)):
            pv0 = Pva[fm][:, :, q][mva[fm]]
            pv1 = Qva[fm][:, :, q][mva[fm]]
            yv = lva[fm][:, :, q][mva[fm]]
            row[ring] = {
                "ece_before": _ece(pv0, yv),
                "ece_after": _ece(pv1, yv),
                "auc_before": _auc(pv0, yv),
                "auc_after": _auc(pv1, yv),
            }
        slices[wn[w]] = row

    dense_warn_after = slices["dense"]["warn"]["ece_after"]
    worsened = max(
        s[r]["ece_after"] - s[r]["ece_before"]
        for s in slices.values()
        for r in ("warn", "crit")
    )
    auc_drop = max(
        s[r]["auc_before"] - s[r]["auc_after"]
        for s in slices.values()
        for r in ("warn", "crit")
    )
    verdict = {
        "k0a": bool(k0a >= K0A_AUC),
        "k0b": bool(monotone and k0b_gap >= K0B_GAP),
        "k0c": bool(
            dense_warn_after <= K0C_DENSE_WARN_ECE
            and worsened <= K0C_SLICE_WORSEN
            and auc_drop <= K0C_AUC_DROP
        ),
    }
    res = {
        "n_rollouts": n_rollouts,
        "len": length,
        "bin_edges": list(edges),
        "k0a_auc": k0a,
        "k0b_gaps_by_bin": gaps,
        "k0b_monotone": bool(monotone),
        "k0b_span": float(k0b_gap),
        "temps": {f"ring{r}_bin{b}": t for (r, b), t in temps.items()},
        "slices": slices,
        "k0c_dense_warn_after": dense_warn_after,
        "k0c_worst_worsening": float(worsened),
        "k0c_worst_auc_drop": float(auc_drop),
        "verdict": verdict,
    }
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(res, f, indent=1)
    # per-frame arrays: future recuts are free (no corpus regeneration)
    np.savez_compressed(
        out.replace(".json", "_frames.npz"),
        clut_tr=ctr,
        world_tr=wtr,
        clut_va=cva,
        world_va=wva,
        p_va=Pva,
        y_va=lva,
        m_va=mva,
        p_tr=Ptr,
        y_tr=ltr,
        m_tr=mtr,
    )
    print(
        f"[k0a] clutter->dense AUC {k0a:.3f} (bar >= {K0A_AUC}) -> "
        f"{'PASS' if verdict['k0a'] else 'FAIL'}"
    )
    print(
        f"[k0b] warn gap by bin {['%.4f' % g for g in gaps]} monotone={monotone} "
        f"span {k0b_gap:+.4f} (bar >= +{K0B_GAP}) -> "
        f"{'PASS' if verdict['k0b'] else 'FAIL'}"
    )
    print(
        f"[k0c] dense warn ECE {slices['dense']['warn']['ece_before']:.4f} -> "
        f"{dense_warn_after:.4f} (bar <= {K0C_DENSE_WARN_ECE}) | worst slice "
        f"worsening {worsened:+.4f} (<= {K0C_SLICE_WORSEN}) | worst AUC drop "
        f"{auc_drop:+.4f} (<= {K0C_AUC_DROP}) -> "
        f"{'PASS' if verdict['k0c'] else 'FAIL'}"
    )
    print(f"[k0] wrote {out}")
    return res


def selftest() -> None:
    # ray geometry: pillar dead east at 0.5 m -> exactly one near ray
    pil = np.array([[0.5, 0.0]])
    assert clutter_count(np.zeros(2), pil, 0.15) == 1
    # empty world -> zero; far pillar -> zero
    assert clutter_count(np.zeros(2), np.full((1, 2), np.nan), 0.15) == 0
    assert clutter_count(np.zeros(2), np.array([[2.5, 0.0]]), 0.15) == 0
    # surrounded -> many rays fire
    ring = np.array(
        [
            [0.6 * np.cos(t), 0.6 * np.sin(t)]
            for t in np.linspace(0, 2 * np.pi, 8, endpoint=False)
        ]
    )
    assert clutter_count(np.zeros(2), ring, 0.15) >= 6
    # temperature fit recovers the injected scale on synthetic logits
    rng = np.random.default_rng(0)
    logit = rng.normal(0, 2.0, 20000)
    y = (rng.random(20000) < 1.0 / (1.0 + np.exp(-logit / 1.6))).astype(float)
    t = _fit_T(logit, y)
    assert 1.4 <= t <= 1.8, t
    # AUC sanity + frozen constants
    assert _auc(np.array([0.9, 0.8, 0.1]), np.array([1, 1, 0])) == 1.0
    assert (K0A_AUC, K0B_GAP, K0C_DENSE_WARN_ECE) == (0.80, 0.05, 0.09)
    assert (K0C_SLICE_WORSEN, K0C_AUC_DROP) == (0.01, 0.005)
    assert (MAX_RANGE, NEAR, N_RAYS) == (3.0, 1.0, 8)
    print("DENSE-RECAL OK: ray geometry, T-fit recovery, AUC, frozen constants")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rollouts", type=int, default=48)
    ap.add_argument("--len", type=int, default=120, dest="length")
    ap.add_argument("--out", default=OUT_JSON)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    run(args.rollouts, args.length, args.out)


if __name__ == "__main__":
    main()

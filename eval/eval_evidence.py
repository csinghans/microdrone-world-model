"""Detection as sequential evidence — the offline duel (evidence_v1).

C1 measured the failure shape of fixed thresholds on moving frames:
scores shift down, ranking survives (AUC 0.889, recall@0.65
0.758→0.182). This duel replays C1's recorded 40-flight / 10,542-frame
corpus through two per-flight firing rules on IDENTICAL data:

  confirm-k (incumbent)   fire on the k-th consecutive frame >= thr
  CUSUM-SPRT (challenger) accumulate quantile-binned, Laplace-smoothed
                          log-likelihood ratios with reset-at-zero
                          (S <- max(0, S + LLR)); fire at S >= A

Config selection happens on the TRAIN block only (max correct-find
subject to per-flight FA <= 0.10, the deployed gate's bar), scored
frozen on the EVAL block, cross-fit both directions. Replay caveat
(stated in the pre-registration): post-fire frames are return-leg
imagery — the comparison is fair, the absolutes belong to the flight
regate. Bars: experiments/evidence_v1/journal.md (committed first).

Run:
  python -m eval.eval_evidence --duel
  python -m eval.eval_evidence --selftest
"""

import argparse
import json
import os
import sys

import numpy as np

B1 = os.path.join("experiments", "detect_inflight_v1", "artifacts", "streams.npz")
B2 = os.path.join("experiments", "detect_inflight_v1", "artifacts", "streams_b2.npz")
FA_BUDGET = 0.10  # the deployed flight gate's false-alarm bar
CONFIRM_GRID = tuple((k, t) for k in (1, 2, 3, 5) for t in (0.3, 0.4, 0.5, 0.65, 0.8))
A_GRID = (1.0, 2.0, 3.0, 4.0, 6.0, 8.0)
BINS = 10


def load_flights(path):
    d = np.load(path)
    out = []
    for f in np.unique(d["flight"]):
        m = d["flight"] == f
        order = np.argsort(d["step"][m])
        out.append((d["prob"][m][order], d["label"][m][order].astype(int)))
    return out


def fit_llr(flights, bins=BINS):
    """Quantile-bin LLR calibration from (prob, label) pairs — counting
    plus Laplace smoothing, nothing learned beyond that."""
    p = np.concatenate([pr for pr, _ in flights])
    y = np.concatenate([lb for _, lb in flights])
    edges = np.quantile(p, np.linspace(0, 1, bins + 1)[1:-1])
    idx = np.digitize(p, edges)
    n_pos, n_neg = float((y == 1).sum()), float((y == 0).sum())
    llr = np.zeros(bins)
    for b in range(bins):
        pb = (float(((idx == b) & (y == 1)).sum()) + 1.0) / (n_pos + bins)
        nb = (float(((idx == b) & (y == 0)).sum()) + 1.0) / (n_neg + bins)
        llr[b] = float(np.log(pb / nb))
    return edges, llr


def fire_confirm(probs, k, thr):
    run = 0
    for i, p in enumerate(probs):
        run = run + 1 if p >= thr else 0
        if run >= k:
            return i
    return None


def fire_cusum(probs, edges, llr, a):
    s = 0.0
    for i, p in enumerate(probs):
        s = max(0.0, s + llr[int(np.digitize(p, edges))])
        if s >= a:
            return i
    return None


def score(flights, fire):
    """Mission semantics: first fire correct/false by that frame's label;
    no fire = miss. Median steps-to-fire among correct fires."""
    correct = fa = miss = 0
    steps = []
    for probs, labels in flights:
        i = fire(probs)
        if i is None:
            miss += 1
        elif labels[i] == 1:
            correct += 1
            steps.append(i)
        else:
            fa += 1
    n = len(flights)
    return {
        "correct": correct / n,
        "fa": fa / n,
        "miss": miss / n,
        "median_steps": float(np.median(steps)) if steps else float("nan"),
    }


def select(flights, configs, mk_fire):
    """TRAIN-block selection: max correct subject to fa <= FA_BUDGET
    (tie-break: fewer median steps); if nothing fits the budget, the
    min-fa config. Returns (config, train_stats)."""
    best = None
    for cfg in configs:
        st = score(flights, mk_fire(cfg))
        if st["fa"] > FA_BUDGET + 1e-9:
            continue
        med = st["median_steps"] if np.isfinite(st["median_steps"]) else 1e9
        key = (st["correct"], -med)
        if best is None or key > best[0]:
            best = (key, cfg, st)
    if best is None:
        for cfg in configs:
            st = score(flights, mk_fire(cfg))
            key = (-st["fa"], st["correct"])
            if best is None or key > best[0]:
                best = (key, cfg, st)
    return best[1], best[2]


def duel(train, evalb, tag):
    edges, llr = fit_llr(train)
    ck, _ = select(train, CONFIRM_GRID, lambda c: (lambda p: fire_confirm(p, *c)))
    aa, _ = select(train, A_GRID, lambda a: (lambda p: fire_cusum(p, edges, llr, a)))
    ck_ev = score(evalb, lambda p: fire_confirm(p, *ck))
    aa_ev = score(evalb, lambda p: fire_cusum(p, edges, llr, aa))
    print(
        f"  [{tag}] confirm-k k={ck[0]} thr={ck[1]}: "
        + "  ".join(f"{m}={ck_ev[m]:.3f}" for m in ("correct", "fa", "miss"))
        + f"  med_steps={ck_ev['median_steps']:.0f}"
    )
    print(
        f"  [{tag}] CUSUM-SPRT A={aa}:      "
        + "  ".join(f"{m}={aa_ev[m]:.3f}" for m in ("correct", "fa", "miss"))
        + f"  med_steps={aa_ev['median_steps']:.0f}"
    )
    return {
        "confirm": {"cfg": list(ck), "eval": ck_ev},
        "sprt": {"cfg": float(aa), "eval": aa_ev},
    }


def _wins(sp, ck):
    """The pre-registered win test for one direction."""
    fast = (
        np.isfinite(sp["median_steps"])
        and np.isfinite(ck["median_steps"])
        and sp["median_steps"] <= 0.8 * ck["median_steps"]
    )
    a = sp["correct"] >= ck["correct"] and fast
    b = sp["correct"] >= ck["correct"] + 0.10 and (
        not np.isfinite(ck["median_steps"]) or sp["median_steps"] <= ck["median_steps"]
    )
    return bool(a or b)


def run_duel(out=None):
    b1, b2 = load_flights(B1), load_flights(B2)
    print(f"[evidence] corpus: {len(b1)}+{len(b2)} flights")
    r12 = duel(b1, b2, "fit b1 -> eval b2")
    r21 = duel(b2, b1, "fit b2 -> eval b1")
    w12 = _wins(r12["sprt"]["eval"], r12["confirm"]["eval"])
    w21 = _wins(r21["sprt"]["eval"], r21["confirm"]["eval"])
    verdict = (
        "SPRT WINS both directions -> flight regate released"
        if (w12 and w21)
        else "honest negative — the incumbent holds at this operating point"
    )
    print(f"[evidence] direction wins: b1->b2 {w12}, b2->b1 {w21} -> {verdict}")
    res = {"b1_to_b2": r12, "b2_to_b1": r21, "wins": [w12, w21], "verdict": verdict}
    if out:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w") as f:
            json.dump(res, f, indent=1)
        print(f"[evidence] wrote {out}")
    return res


def selftest() -> None:
    rng = np.random.default_rng(0)

    # synthetic flights: noise floor, then the target enters at step 60
    def flight(enter=60, n=120):
        p = rng.uniform(0.05, 0.35, n)
        p[enter:] = rng.uniform(0.55, 0.95, n - enter)
        y = np.zeros(n, int)
        y[enter:] = 1
        return p, y

    fls = [flight() for _ in range(12)]
    # confirm-k fires inside the target segment, never before
    i = fire_confirm(fls[0][0], 2, 0.5)
    assert i is not None and fls[0][1][i] == 1
    # the calibrated CUSUM also fires inside the target segment
    edges, llr = fit_llr(fls[:6])
    assert llr[-1] > 0 > llr[0], "LLR must rise with the score"
    j = fire_cusum(fls[7][0], edges, llr, 3.0)
    assert j is not None and fls[7][1][j] == 1
    # score() semantics: an all-noise flight is a miss at a high bar
    quiet = (rng.uniform(0.05, 0.2, 100), np.zeros(100, int))
    st = score([quiet], lambda p: fire_confirm(p, 3, 0.8))
    assert st["miss"] == 1.0 and st["fa"] == 0.0
    # select() respects the FA budget on a mixed set
    cfg, tr = select(
        fls + [quiet], CONFIRM_GRID, lambda c: (lambda p: fire_confirm(p, *c))
    )
    assert tr["fa"] <= FA_BUDGET + 1e-9
    print(
        "EVIDENCE OK: confirm/CUSUM fire in-target on synthetic streams, "
        "LLR monotone, miss semantics, FA-budgeted selection"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--duel", action="store_true")
    ap.add_argument("--out", default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    if not args.duel:
        raise SystemExit("--duel (or --selftest)")
    run_duel(args.out)


if __name__ == "__main__":
    sys.exit(main())

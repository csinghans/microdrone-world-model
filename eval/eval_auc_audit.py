"""Quantify the legacy AUC tie error on frozen, exported checkpoint scores.

    python -m eval.eval_auc_audit --scores model_scores.npz --out audit.json
    python -m eval.eval_auc_audit --selftest

No training, tuning, promotion or historical record replacement. The legacy
formula is reproduced here solely to diagnose old measurement behavior.
"""

import argparse
import json
from pathlib import Path

import numpy as np

from eval.compare_wm_scores import _load, _validate
from world_model.metrics import AUC_METHOD, roc_auc


def _row(scores, labels):
    pos, neg = scores[labels == 1], scores[labels == 0]
    out = {"positive": int(len(pos)), "negative": int(len(neg))}
    if not len(pos) or not len(neg):
        return dict(
            out,
            legacy_auc=None,
            corrected_auc=None,
            delta=None,
            tied_pair_fraction=None,
            reason="single label class",
        )
    values = np.concatenate([pos, neg])
    order = values.argsort()  # exact previous implementation
    ranks = np.empty(len(order), dtype=np.float64)
    ranks[order] = np.arange(1, len(order) + 1)
    pairs = len(pos) * len(neg)
    legacy = float((ranks[: len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / pairs)
    _, inverse = np.unique(values, return_inverse=True)
    n_groups = int(inverse.max()) + 1
    pcount = np.bincount(inverse[: len(pos)], minlength=n_groups)
    ncount = np.bincount(inverse[len(pos) :], minlength=n_groups)
    tied = int(np.dot(pcount, ncount))
    corrected = roc_auc(scores, labels)
    return dict(
        out,
        legacy_auc=legacy,
        corrected_auc=corrected,
        delta=corrected - legacy,
        tied_cross_class_pairs=tied,
        total_cross_class_pairs=pairs,
        tied_pair_fraction=tied / pairs,
        max_absolute_tie_bias=tied / (2 * pairs),
    )


def audit(blob):
    _validate(blob, blob)
    s, y, wid = blob["scores"][:, -1], blob["labels"][:, -1], blob["world_id"]
    worlds = {"all": _row(s, y)}
    for w in np.unique(wid):
        names = blob["world_names"]
        name = str(names[int(w)]) if 0 <= w < len(names) else str(w)
        mask = wid == w
        worlds[name] = _row(s[mask], y[mask])
    return {
        "auc_method": AUC_METHOD,
        "legacy_method": "positive_then_negative_argsort_distinct_ranks",
        "legacy_numpy_version": np.__version__,
        "scope": "deterministic metric audit on these fixed scores; "
        "legacy tie ordering can vary with NumPy implementation",
        "source": blob["metadata"],
        "worlds": worlds,
    }


def selftest():
    labels = np.array([1, 1, 0, 0])
    tied = _row(np.full(4, 0.5), labels)
    assert tied["corrected_auc"] == 0.5 and tied["tied_pair_fraction"] == 1
    assert abs(tied["delta"]) <= tied["max_absolute_tie_bias"]
    mixed = _row(np.array([0.9, 0.5, 0.5, 0.1]), labels)
    assert mixed["corrected_auc"] == 0.875
    assert mixed["tied_cross_class_pairs"] == 1
    unique = _row(np.array([0.9, 0.8, 0.2, 0.1]), labels)
    assert unique["delta"] == 0 and unique["tied_pair_fraction"] == 0
    assert _row(np.ones(4), np.zeros(4))["corrected_auc"] is None
    print("AUC-AUDIT OK: ties counted, bias bound, no-tie identity, missing classes")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scores")
    ap.add_argument("--out")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    if not args.scores or not args.out:
        ap.error("--scores and --out are required")
    out = Path(args.out)
    if out.exists():
        ap.error("--out must be new; preserve existing diagnostics")
    report = audit(_load(args.scores))
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(f"AUC-AUDIT OK: {out}")


if __name__ == "__main__":
    main()

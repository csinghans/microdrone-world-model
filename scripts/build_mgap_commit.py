"""terminal_commit_v1 pot builder — clone the oracle-wrapped behavior.

Takes a SeamProbe collection npz (target=moving_gap, thread_commit
teacher), applies the cleared-stage kept mask, tags every row
terminal/approach by distance to the fence plane, asserts the frozen
floors, and BC-trains the vision-only mgap slot specialist. The
per-region val (terminal vs approach) is the mechanism meter: the
clone must fit the commit, not just the cruise.

Run:
  python -m scripts.build_mgap_commit --npz <collection.npz> --out <zip>
  python -m scripts.build_mgap_commit --selftest
"""

import argparse
import os
import sys

import numpy as np

FLOOR_ROWS = 10000  # kept mgap decisions (frozen in the journal)
FLOOR_TERM = 2000  # of which inside the terminal metre
VAL_FLOOR = 0.94  # frozen BELOW the slalom pots' 0.96 — reason in journal
TERM_X = 1.0  # the oracle's terminal window
OUT = "experiments/terminal_commit_v1/artifacts/ppo_mgap_commit.zip"


def _slice(z):
    """Kept rows -> (X, Y=executed, region tags, n_terminal)."""
    m = np.asarray(z["kept"]).astype(bool)
    X = np.asarray(z["vecs"])[m]
    Y = np.asarray(z["exec_menu"])[m]
    dist = np.asarray(z["plane_x"])[m] - np.asarray(z["x"])[m]
    term = (dist > 0.0) & (dist <= TERM_X)
    W = np.where(term, "terminal", "approach")
    return X, Y, W, int(term.sum())


def build(npz_path, out=OUT):
    from scripts.distill import bc_train

    with np.load(npz_path) as z:
        X, Y, W, n_term = _slice(z)
    print(f"[mgap-pot] kept {len(X)} decisions ({n_term} terminal)")
    assert len(X) >= FLOOR_ROWS, f"pot floor: {len(X)} < {FLOOR_ROWS}"
    assert n_term >= FLOOR_TERM, f"terminal floor: {n_term} < {FLOOR_TERM}"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    rep: dict = {}
    acc, _ = bc_train(X, Y, out, epochs=40, W=W, report=rep)
    ok = acc >= VAL_FLOOR
    print(
        f"[mgap-pot] pooled val {acc:.4f} (floor {VAL_FLOOR}) "
        f"per_region={rep.get('per_world')} -> "
        f"{'FLOOR OK' if ok else 'FLOOR MISSED'} | saved {out}"
    )
    return 0 if ok else 3


def selftest() -> None:
    z = {
        "kept": np.array([True, True, False, True]),
        "vecs": np.arange(8.0).reshape(4, 2),
        "exec_menu": np.array([0, 1, 2, 3]),
        "x": np.array([0.5, 4.2, 0.0, 4.9]),
        "plane_x": np.array([4.8, 4.8, 4.8, 4.8]),
    }
    X, Y, W, n_term = _slice(z)
    assert X.shape == (3, 2) and list(Y) == [0, 1, 3]
    # row0: dist 4.3 -> approach; row1: dist 0.6 -> terminal;
    # row3: dist -0.1 (past the plane) -> approach
    assert list(W) == ["approach", "terminal", "approach"] and n_term == 1
    assert (FLOOR_ROWS, FLOOR_TERM, VAL_FLOOR, TERM_X) == (10000, 2000, 0.94, 1.0)
    print("MGAP-COMMIT OK: kept mask, terminal tagging, frozen floors")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--npz", default=None)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    if not args.npz:
        raise SystemExit("--npz required (SeamProbe collection)")
    sys.exit(build(args.npz, args.out))


if __name__ == "__main__":
    sys.exit(main())

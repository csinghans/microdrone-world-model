"""Build the UNIFIED world-model training set: transit (pillar) + indoor
(room) rollouts concatenated into one npz.

The question: can ONE WM hold both the transit benchmark and indoor search?
This materializes the union `train()` consumes (scripts/train.py loads a
single npz, no built-in concat). Both generators already share the schema
(frames (R,L,64,64,3) uint8, actions (R,L,4), the transit `a_norm`, the
4-D yaw=0 action space), so they stack — with two reconciliations:

  * **world_id remap**: `search_rollouts` tags rooms `world_id=0`, which
    aliases transit `classic=0`; remap rooms -> 3 and set
    `world_names=["classic","dense","moving","room"]` so the stratified
    split + per-world AUC bucket rooms correctly.
  * **common length**: both generators must run at the SAME `--len` before
    `frames` can stack.

The counterfactual-loss hazard (room frames getting a spurious "all safe"
label) is fixed separately in `datasets/intervention_labels.py` (NaN-pillar
rollouts are marked unanswerable, vis=0).

Run:
  python -m datasets.combine_rollouts --n-transit 96 --n-indoor 96 --len 120
  python -m datasets.combine_rollouts --selftest
"""

import argparse
import os
import sys

import numpy as np

ROOM_ID = 3  # transit uses 0/1/2 (classic/dense/moving); rooms get 3
# per-rollout / per-frame keys present in BOTH npz's (concatenate along axis 0)
_STACK = (
    "frames",
    "actions",
    "act_id",
    "seg",
    "dists",
    "pos",
    "pillars",
    "pillar_vel",
    "world_id",
    "in_path",
    "speed",
)
OUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "output",
    "combined.npz",
)


def combine(transit: dict, indoor: dict) -> dict:
    """Pure concat logic (no sim): stack the shared per-rollout keys, remap
    room world_id -> 3, reconcile world_names + shared normalizers."""
    assert np.allclose(transit["a_norm"], indoor["a_norm"]), "a_norm mismatch"
    assert list(transit["horizons"]) == list(indoor["horizons"]), "horizons mismatch"
    ind = dict(indoor)
    ind["world_id"] = np.full(len(indoor["world_id"]), ROOM_ID, dtype=np.int16)
    out = {k: np.concatenate([transit[k], ind[k]], axis=0) for k in _STACK}
    out["horizons"] = np.asarray(transit["horizons"])
    out["a_norm"] = np.asarray(transit["a_norm"])
    out["danger_r"] = np.asarray(transit["danger_r"])
    out["world_names"] = np.array(["classic", "dense", "moving", "room"])
    return out


def build(n_transit, n_indoor, length, seed=0, worlds=("classic", "dense", "moving")):
    """`worlds` cycles per transit rollout; REPEATS are weights (the
    representation composition knob: ("dense","dense","classic","moving")
    gives a 2:1:1 mix). Default = the frozen uniform mix."""
    from datasets.generate_rollouts import gen as gen_transit
    from datasets.search_rollouts import gen as gen_indoor

    transit = gen_transit(n_transit, length, seed=seed, worlds=tuple(worlds))
    indoor = gen_indoor(n_indoor, length, seed=seed + 100000)
    return combine(transit, indoor)


def _synth(world_ids, length=8, nan_pillars=False):
    """A tiny schema-correct rollout dict for the env-free selftest."""
    r = len(world_ids)
    pil = np.full((r, 8, 2), np.nan if nan_pillars else 0.5, dtype=np.float32)
    return {
        "frames": np.zeros((r, length, 4, 4, 3), dtype=np.uint8),
        "actions": np.zeros((r, length, 4), dtype=np.float32),
        "act_id": np.zeros((r, length), dtype=np.int16),
        "seg": np.ones((r, length), dtype=np.int16),
        "dists": np.ones((r, length), dtype=np.float32),
        "pos": np.zeros((r, length, 3), dtype=np.float32),
        "pillars": pil,
        "pillar_vel": np.zeros((r, 8, 2), dtype=np.float32),
        "world_id": np.array(world_ids, dtype=np.int16),
        "in_path": np.ones(r, dtype=bool),
        "speed": np.ones(r, dtype=np.float32),
        "horizons": np.array([4, 8, 16, 32], dtype=np.int16),
        "a_norm": np.array([1.6, 1.0, 0.8, 1e-6], dtype=np.float32),
        "danger_r": np.float32(0.7),
        "world_names": np.array(["classic", "dense", "moving"]),
    }


def selftest() -> None:
    transit = _synth([0, 1, 2])  # classic/dense/moving
    indoor = _synth([0, 0], nan_pillars=True)  # rooms (tagged 0 by the generator)
    c = combine(transit, indoor)
    assert c["frames"].shape[0] == 5, "5 rollouts stacked"
    assert set(c["world_id"].tolist()) == {0, 1, 2, 3}, "rooms remapped to 3"
    assert (c["world_id"][3:] == ROOM_ID).all(), "the room rollouts carry id 3"
    assert list(c["world_names"]) == ["classic", "dense", "moving", "room"]
    assert np.isnan(c["pillars"][3:, 0, 0]).all(), "room pillars stay NaN"
    assert c["frames"].shape[1:] == transit["frames"].shape[1:], "per-frame shape kept"
    print(
        "COMBINE-ROLLOUTS OK: transit+indoor stack, room world_id->3, "
        "world_names reconciled, room pillars NaN preserved"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-transit", type=int, default=96)
    ap.add_argument("--n-indoor", type=int, default=96)
    ap.add_argument("--len", type=int, default=120)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=OUT)
    ap.add_argument(
        "--worlds",
        default="classic,dense,moving",
        help="transit world cycle; repeats are weights (composition knob)",
    )
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    worlds = tuple(w for w in args.worlds.split(",") if w)
    data = build(args.n_transit, args.n_indoor, args.len, args.seed, worlds=worlds)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    np.savez_compressed(args.out, **data)
    wid = data["world_id"]
    print(
        f"COMBINED OK: {len(wid)} rollouts x {args.len} steps "
        f"(transit {(wid < 3).sum()}, room {(wid == 3).sum()}), saved {args.out}"
    )


if __name__ == "__main__":
    sys.exit(main())

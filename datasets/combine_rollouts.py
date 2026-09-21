"""Build the UNIFIED world-model training set: transit (pillar) + indoor
(room) rollouts concatenated into one npz.

The question: can ONE WM hold both the transit benchmark and indoor search?
This materializes the union `train()` consumes (scripts/train.py loads a
single npz, no built-in concat). Both generators already share the schema
(frames (R,L,64,64,3) uint8, actions (R,L,4), the transit `a_norm`, the
4-D yaw=0 action space), so they stack — with two reconciliations:

  * **world_id remap**: decode each input's own `world_names`, then remap
    to one catalog. Classic/dense/moving keep 0/1/2; custom transit names
    follow, then room. The standard recipe still puts room at 3. Dynamic
    transit world 3 must not silently become room in the combined corpus.
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

from datasets.provenance import dataset_destination, save_dataset
from datasets.rollout_schedule import LAYOUTS

ROOM_ID = 3  # canonical three-world recipe only; custom transit worlds shift room
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


def _catalog(data, source):
    """Validate source-local identities before using them as array indices."""
    names = np.asarray(data["world_names"])
    ids = np.asarray(data["world_id"])
    if (
        names.ndim != 1
        or not names.size
        or names.dtype.kind != "U"
        or any(not name or name != name.strip() for name in names)
        or len(set(names)) != len(names)
    ):
        raise ValueError(f"{source}: world_names must be unique nonempty strings")
    if (
        ids.ndim != 1
        or not np.issubdtype(ids.dtype, np.integer)
        or (ids < 0).any()
        or (ids >= len(names)).any()
    ):
        raise ValueError(f"{source}: world_id must index its source world_names")
    for key in _STACK:
        array = np.asarray(data[key])
        if array.ndim < 1 or len(array) != len(ids):
            raise ValueError(f"{source}: {key} rollout count differs from world_id")
    return names.tolist(), ids


def combine(transit: dict, indoor: dict) -> dict:
    """Stack raw transit/room data without changing any rollout's world name.

    Source catalogs are authoritative, independent of registration order.
    Builtin output ids remain 0/1/2, followed by custom transit names and room.
    """
    transit_names, transit_ids = _catalog(transit, "transit")
    indoor_names, indoor_ids = _catalog(indoor, "indoor")
    if any(transit_names[i] == "room" for i in transit_ids):
        raise ValueError("transit input contains room rollouts; use raw transit data")
    if any(indoor_names[i] != "room" for i in indoor_ids):
        raise ValueError("indoor input must contain only room rollouts")
    assert np.allclose(transit["a_norm"], indoor["a_norm"]), "a_norm mismatch"
    assert list(transit["horizons"]) == list(indoor["horizons"]), "horizons mismatch"
    names = ["classic", "dense", "moving"]
    names += [name for name in transit_names if name not in names and name != "room"]
    names.append("room")
    dtype = np.int16 if len(names) <= np.iinfo(np.int16).max + 1 else np.int64
    lookup = np.array([names.index(name) for name in transit_names], dtype=dtype)
    out = {k: np.concatenate([transit[k], indoor[k]], axis=0) for k in _STACK}
    out["world_id"] = np.concatenate(
        [lookup[transit_ids], np.full(len(indoor_ids), len(names) - 1, dtype=dtype)]
    )
    out["horizons"] = np.asarray(transit["horizons"])
    out["a_norm"] = np.asarray(transit["a_norm"])
    out["danger_r"] = np.asarray(transit["danger_r"])
    out["world_names"] = np.array(names)
    if "schedule_layout" in transit:
        out["transit_schedule_layout"] = np.asarray(transit["schedule_layout"])
    return out


def build(
    n_transit,
    n_indoor,
    length,
    seed=0,
    worlds=("classic", "dense", "moving"),
    img_res=None,
    schedule_layout="world_balanced",
):
    """`worlds` cycles per transit rollout; REPEATS are weights (the
    representation composition knob: ("dense","dense","classic","moving")
    gives a 2:1:1 mix). Default = the frozen uniform mix. `img_res` is the
    perception tier's camera knob (None = the deployed 64)."""
    from datasets.generate_rollouts import gen as gen_transit
    from datasets.search_rollouts import gen as gen_indoor
    from sim.envs import IMG_RES

    res = int(img_res) if img_res else IMG_RES
    transit = gen_transit(
        n_transit,
        length,
        seed=seed,
        worlds=tuple(worlds),
        img_res=res,
        schedule_layout=schedule_layout,
    )
    indoor = gen_indoor(n_indoor, length, seed=seed + 100000, img_res=res)
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
    indoor["world_names"] = np.array(["room"])
    c = combine(transit, indoor)
    assert c["frames"].shape[0] == 5, "5 rollouts stacked"
    assert set(c["world_id"].tolist()) == {0, 1, 2, 3}, "rooms remapped to 3"
    assert (c["world_id"][3:] == ROOM_ID).all(), "the room rollouts carry id 3"
    assert list(c["world_names"]) == ["classic", "dense", "moving", "room"]
    assert np.isnan(c["pillars"][3:, 0, 0]).all(), "room pillars stay NaN"
    assert c["frames"].shape[1:] == transit["frames"].shape[1:], "per-frame shape kept"
    transit["schedule_layout"] = np.array("world_balanced")
    assert str(combine(transit, indoor)["transit_schedule_layout"]) == "world_balanced"

    # Dynamic ids, reordered catalogs and repeated worlds must retain names.
    custom = _synth([3, 0, 4, 3])
    custom["world_names"] = np.array(["dense", "moving", "classic", "gap", "slalom"])
    original = {k: v.copy() for k, v in custom.items()}
    merged = combine(custom, indoor)
    assert merged["world_names"].tolist() == [
        "classic",
        "dense",
        "moving",
        "gap",
        "slalom",
        "room",
    ]
    assert merged["world_id"].tolist() == [3, 1, 4, 3, 5, 5]
    assert merged["world_names"][merged["world_id"]].tolist() == [
        "gap",
        "dense",
        "slalom",
        "gap",
        "room",
        "room",
    ]
    for key, value in custom.items():
        np.testing.assert_array_equal(value, original[key])
    for key in _STACK:
        if key != "world_id":
            np.testing.assert_array_equal(
                merged[key], np.concatenate([custom[key], indoor[key]], axis=0)
            )

    invalid = [
        ("world_names", np.array(["classic", "classic", "moving"])),
        ("world_names", np.array(["classic", "", "moving"])),
        ("world_names", np.array(["classic", " dense", "moving"])),
        ("world_names", np.array([["classic", "dense", "moving"]])),
        ("world_names", np.array([0, 1, 2])),
        ("world_names", np.array(["room", "dense", "moving"])),
        ("world_id", np.array([0, -1, 2])),
        ("world_id", np.array([0, 1, 3])),
        ("world_id", np.array([0.0, 1.0, 2.0])),
        ("world_id", np.array([True, False, True])),
        ("world_id", np.array([[0, 1, 2]])),
        ("world_id", np.array([0, 1])),
        ("actions", np.zeros((2, 8, 4))),
    ]
    for key, value in invalid:
        bad = dict(transit, **{key: value})
        try:
            combine(bad, indoor)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid source identity accepted: {key}={value}")
    for key, value in (
        ("world_names", np.array(["dense"])),
        ("world_id", np.array([0, 1])),
    ):
        try:
            combine(transit, dict(indoor, **{key: value}))
        except ValueError:
            pass
        else:
            raise AssertionError("non-room or invalid indoor identity accepted")
    print(
        "COMBINE-ROLLOUTS OK: canonical/dynamic world identities, reordered catalogs, "
        "strict source validation, room pillars NaN preserved"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-transit", type=int, default=96)
    ap.add_argument("--n-indoor", type=int, default=96)
    ap.add_argument("--len", type=int, default=120)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument(
        "--out", default=OUT, help="new .npz path; existing corpora are preserved"
    )
    ap.add_argument(
        "--worlds",
        default="classic,dense,moving",
        help="transit world cycle; repeats are weights (composition knob)",
    )
    ap.add_argument(
        "--img-res", type=int, default=None, help="camera res (perception knob)"
    )
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--schedule-layout", choices=LAYOUTS, default="world_balanced")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    out = dataset_destination(args.out)
    worlds = tuple(w for w in args.worlds.split(",") if w)
    data = build(
        args.n_transit,
        args.n_indoor,
        args.len,
        args.seed,
        worlds=worlds,
        img_res=args.img_res,
        schedule_layout=args.schedule_layout,
    )
    wid = data["world_id"]
    room = data["world_names"][wid] == "room"
    save_dataset(data, out)
    print(
        f"COMBINED OK: {len(wid)} rollouts x {args.len} steps "
        f"(transit {(~room).sum()}, room {room.sum()}), saved {out}"
    )


if __name__ == "__main__":
    sys.exit(main())

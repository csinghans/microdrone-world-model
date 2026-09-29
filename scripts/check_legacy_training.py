"""Compare legacy generation and two CPU training epochs across two checkouts.

python -m scripts.check_legacy_training --baseline /path/to/main --out output/parity
python -m scripts.check_legacy_training --selftest
"""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import torch

CHILD = """
import inspect, json, sys, torch, numpy as np
from pathlib import Path
from datasets.generate_rollouts import gen
from world_model.training import train
out = Path(sys.argv[1])
torch.backends.mps.is_available = lambda: False
torch.set_num_threads(1)
extra = {}
if 'schedule_layout' in inspect.signature(gen).parameters:
    extra['schedule_layout'] = 'legacy'
data = gen(9, 80, seed=29, worlds=('classic', 'dense', 'moving'), **extra)
assert data['frames'].std() > 1.0
np.savez_compressed(out / 'data_selftest.npz', **data)
checkpoint, _ = train(data, epochs=2, batch=64, seed=7)
torch.save(checkpoint, out / 'model_selftest.pth')
runtime = {'python': sys.version, 'torch': torch.__version__,
           'numpy': np.__version__, 'device': 'cpu', 'threads': 1}
(out / 'runtime.json').write_text(json.dumps(runtime, indent=2))
print('LEGACY-TRAINING-CHILD-DONE', flush=True)
"""


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def compare_states(a, b):
    groups = ("encoder", "predictor", "collision_heads", "now_head")
    count = 0
    for group in groups:
        assert a[group].keys() == b[group].keys(), group
        for name in a[group]:
            x, y = a[group][name], b[group][name]
            assert x.dtype == y.dtype and x.shape == y.shape
            assert torch.equal(x, y), f"state mismatch: {group}.{name}"
            count += 1
    return count


def selftest():
    a = {
        k: {"w": torch.tensor([1.0, 2.0])}
        for k in ("encoder", "predictor", "collision_heads", "now_head")
    }
    assert compare_states(a, a) == 4
    b = {k: {"w": v["w"].clone()} for k, v in a.items()}
    b["encoder"]["w"][0] += 1e-5
    try:
        compare_states(a, b)
    except AssertionError:
        pass
    else:
        raise AssertionError("changed weights accepted")
    print("LEGACY PARITY OK: exact state identity and mismatch detection")


def run(baseline, candidate, out):
    out.mkdir(parents=True, exist_ok=False)
    paths = subprocess.check_output(
        ["git", "ls-files", "*.py", "environment.yml"], cwd=candidate, text=True
    ).splitlines()
    sources = {
        str(root / p): digest(root / p)
        for root in (baseline, candidate)
        for p in paths
        if (root / p).is_file()
    }
    sources[str(Path(__file__).resolve())] = digest(__file__)
    lock = json.loads((candidate / "artifacts.lock.json").read_text())
    protected = {
        str(candidate / a["dest"]): digest(candidate / a["dest"])
        for a in lock["artifacts"]
        if (candidate / a["dest"]).exists()
    }
    for a in lock["artifacts"]:
        path = str(candidate / a["dest"])
        if path in protected:
            assert protected[path] == a["sha256"], path
    (out / "manifest.json").write_text(
        json.dumps(
            {
                "sources": sources,
                "protected": protected,
                "recipe": {
                    "rollouts": 9,
                    "length": 80,
                    "generation_seed": 29,
                    "worlds": ["classic", "dense", "moving"],
                    "layout": "legacy",
                    "training_seed": 7,
                    "epochs": 2,
                    "batch": 64,
                    "device": "cpu",
                    "threads": 1,
                },
            },
            indent=2,
        )
        + "\n"
    )
    for name, root in (("main", baseline), ("candidate", candidate)):
        dest = out / name
        dest.mkdir()
        with (out / f"{name}.log").open("x") as log:
            proc = subprocess.run(
                [sys.executable, "-u", "-c", CHILD, str(dest)],
                cwd=root,
                stdout=log,
                stderr=subprocess.STDOUT,
            )
            log.write(f"\nEXIT={proc.returncode}\n")
        assert proc.returncode == 0, f"{name} failed; preserve full log"
    with (
        np.load(out / "main/data_selftest.npz", allow_pickle=False) as a,
        np.load(out / "candidate/data_selftest.npz", allow_pickle=False) as b,
    ):
        for key in a.files:
            x, y = a[key], b[key]
            assert x.dtype == y.dtype and x.shape == y.shape, key
            assert np.array_equal(x, y, equal_nan=x.dtype.kind in "fc"), key
        arrays = len(a.files)
        added = sorted(set(b.files) - set(a.files))
    checkpoints = [
        torch.load(out / name / "model_selftest.pth", weights_only=True)
        for name in ("main", "candidate")
    ]
    tensors = compare_states(*checkpoints)
    for path, expected in {**sources, **protected}.items():
        assert digest(path) == expected, f"source/protected file changed: {path}"
    result = {
        "status": "bitwise_equal",
        "legacy_arrays": arrays,
        "additional_metadata": added,
        "state_tensors": tensors,
        "protected_unchanged": len(protected),
        "artifacts": {
            str(p.relative_to(out)): digest(p) for p in out.rglob("*") if p.is_file()
        },
    }
    (out / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    print("LEGACY-TRAINING-PARITY-DONE")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--baseline", type=Path)
    parser.add_argument(
        "--candidate", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.selftest:
        selftest()
    else:
        if args.baseline is None or args.out is None:
            parser.error("--baseline and a fresh --out are required")
        run(args.baseline.resolve(), args.candidate.resolve(), args.out.resolve())


if __name__ == "__main__":
    main()

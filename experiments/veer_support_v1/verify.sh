#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python - <<'PY'
import ast
import hashlib
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from datasets.intervention_labels import HORIZONS
from datasets.provenance import file_identity
from eval.eval_veer_support import analyze, check_export, load_metadata, main
from planner.action_set import ACTION_NAMES, ACTION_VECS, FORWARD
from sim.envs import CTRL_HZ
from sim.scenarios import DANGER_R, FOV_HALF_DEG
from world_model.veer_probe import select

root = Path.cwd()
audit = root / "experiments/veer_support_v1"
read = lambda path: json.loads(path.read_text())
reference = "016dc94:world_model/training.py"
source = subprocess.check_output(["git", "show", reference], text=True)
function = next(n for n in ast.parse(source).body
                if isinstance(n, ast.FunctionDef) and n.name == "veer_ranking")

class StopBeforeTensor(Exception):
    pass

def no_tensor(*args, **kwargs):
    raise StopBeforeTensor

class ShapeOnlyFrames:
    def __init__(self, shape):
        self.shape = shape

    def __len__(self):
        return self.shape[0]

    def __getitem__(self, key):
        return 0  # no pixel data read; interception occurs before tensor use

namespace = dict(globals(), torch=SimpleNamespace(tensor=no_tensor, float32=None))
exec(compile(ast.Module(body=[function], type_ignores=[]), reference, "exec"),
     namespace)
old_probe = namespace["veer_ranking"]
verified = {
    "scope": "Geometry/selection compatibility only; no pixels, model scoring, "
             "fitting, resampling, changed bars or overwritten evidence.",
    "reference": reference,
    "reference_source_sha256": hashlib.sha256(source.encode()).hexdigest(),
    "cases": {},
}
campaigns = ("cf_hard_pool_v1", "executed_weight_v1")
datasets = {c: root / "output" / c / "holdout/data.npz" for c in campaigns}
config = read(root / "experiments/executed_weight_v1/registration.json")
datasets["shared_training"] = root / config["training_source"]["path"]
for name, path in datasets.items():
    identity = file_identity(path)
    data = load_metadata(path)
    if name == "shared_training":
        assert identity["sha256"] == config["training_source"]["sha256"]
    else:
        receipt = read(root / "experiments" / name / "records/holdout.json")
        assert identity["sha256"] in receipt["files"].values()
    expected = select(data)
    original = {}
    facade = dict(data, frames=ShapeOnlyFrames(data["act_id"].shape))
    try:
        old_probe(facade, range(len(data["act_id"])), None, None, None, "cpu",
                  sample_output=original)
    except StopBeforeTensor:
        pass
    for key in ("veer_pairs", "veer_gt_left", "veer_world_id"):
        assert np.array_equal(original[key], expected[key]), (name, key)
    result, _ = analyze(data)
    assert file_identity(path) == identity, "dataset changed during audit"
    row = {"dataset": identity, "n_frames": result["n_frames"],
           "n_rollouts": result["n_rollouts"],
           "selection_sha256": result["selection_sha256"], "exports": {}}
    if name in campaigns:
        support_path = audit / f"{name}.json"
        saved = read(root / "experiments" / name / "probe_support.json")
        args = ["--data", str(path), "--out", str(support_path)]
        for relative, digest in saved["source_exports"].items():
            export = root / relative
            receipt = read(root / "experiments" / name /
                           f"records/{export.parent.name}.json")
            actual = check_export(export, expected, data["world_names"],
                                  identity["sha256"])
            assert actual["sha256"] == digest
            assert digest in receipt["files"].values()
            row["exports"][relative] = digest
            args += ["--check-export", str(export)]
        if not support_path.exists():
            main(args)
        else:
            prior = read(support_path)
            assert all(prior[k] == value for k, value in result.items())
            assert prior["provenance"]["dataset"] == identity
        assert saved["n_frames"] == result["n_frames"]
        assert saved["n_rollouts"] == result["n_rollouts"]
    verified["cases"][name] = row
    print(f"{name}: old/new geometry identical, {row['n_frames']} frames / "
          f"{row['n_rollouts']} courses, {len(row['exports'])} matched exports")
verified["status"] = "PASS"
path = audit / "verification.json"
if path.exists():
    assert read(path) == verified, "saved evidence differs; investigate"
else:
    with path.open("x") as stream:
        json.dump(verified, stream, indent=2, allow_nan=False)
        stream.write("\n")
print("VEER-SUPPORT-PARITY OK: original geometry and all twelve exports")
PY

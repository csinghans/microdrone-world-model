#!/bin/bash
# Verify original source/runtime, logs/exit codes, artifacts and numeric receipts.
# Recompute metadata support and metrics from saved scores; never fit or infer.
set -euo pipefail
cd "$(dirname "$0")/../.."
"${PYTHON:-python}" -u -m scripts.intervention_timing_study --verify
"${PYTHON:-python}" -u - <<'PY'
import tempfile
from pathlib import Path

from scripts import intervention_timing_study as study
from scripts.schedule_layout_study import read, sha

config = read(study.REGISTRATION)
folder = study.CAMPAIGN
study.check_manifest(config)
with tempfile.TemporaryDirectory(prefix="timing_receipt_verify_") as temp:
    root = Path(temp)
    for stage, operation in (("preflight", study.preflight), ("report", study.report)):
        directory = root / stage
        directory.mkdir()
        actual = operation(config, directory)
        archived = read(folder / f"{stage}.json")
        assert actual == archived, stage
        original = read(folder / "records" / f"{stage}.json")["result"]
        assert actual == original, stage
        for generated in directory.glob("*.json"):
            if stage == "preflight" and generated.name != "report.json":
                assert read(generated) == read(folder / "support" / generated.name)
        print(f"RECOMPUTED {stage}: exact numeric parity", flush=True)
for stage in study.stages(config):
    outcome = read(study.OUT / f"{stage}_exit.json")
    assert outcome == read(folder / "process_exits" / f"{stage}.json")
    assert outcome["exit_code"] == 0
    assert outcome["log_sha256"] == sha(study.OUT / f"{stage}.log")
assert (study.OUT / "EXIT").read_text().strip() == "0"
assert (study.OUT / "DONE").is_file()
study.check_manifest(config)
print("INTERVENTION TIMING EVIDENCE OK: 23 stages, support, scores, guards, hashes")
PY

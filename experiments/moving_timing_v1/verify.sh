#!/bin/bash
# Read-only reproduction of the frozen study and verification of its archive.
set -euo pipefail
cd "$(dirname "$0")/../.."
"${PYTHON:-python}" -u -m scripts.moving_timing_study --verify
"${PYTHON:-python}" -u - <<'PY'
from scripts.moving_timing_study import CAMPAIGN, OUT, REGISTRATION, stages
from scripts.schedule_layout_study import read, verify_files

verify_files(read(CAMPAIGN / "verification.json")["files"])
assert read(CAMPAIGN / "report.json") == read(OUT / "report/report.json")
assert read(CAMPAIGN / "preflight.json") == read(OUT / "preflight/report.json")
for path in (CAMPAIGN / "support").glob("*.json"):
    assert read(path) == read(OUT / "preflight" / path.name)
for stage in stages(read(REGISTRATION)):
    assert read(CAMPAIGN / "process_exits" / f"{stage}.json") == read(
        OUT / f"{stage}_exit.json"
    )
print("MOVING TIMING ARCHIVE OK: saved report, support, process exits and file hashes")
PY

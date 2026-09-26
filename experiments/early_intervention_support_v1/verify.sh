#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/../.."
"${PYTHON:-python}" -m scripts.early_intervention_study --verify
"${PYTHON:-python}" - <<'PY'
import json
from pathlib import Path
from scripts.schedule_layout_study import sha, verify_files

folder = Path('experiments/early_intervention_support_v1')
receipt = json.loads((folder / 'verification.json').read_text())
verify_files(receipt['frozen_files'])
verify_files(receipt['logs'])
verify_files(receipt['locked_artifacts'])
for path in Path('output/early_intervention_support_v1/support').iterdir():
    assert sha(path) == sha(folder / path.name), path
report = json.loads((folder / 'report.json').read_text())
assert report['statuses'] == {'approach': 'insufficient', 'immediate': 'satisfied'}
rows = {(r['world'], r['action']): r for r in report['rows']}
assert len(rows) == 18
right = rows['dense', 'veer_right']
assert right['approach']['negative_rollouts'] == 1
assert right['immediate']['negative_rollouts'] == 7
assert right['approach']['negative'] == 12
assert right['immediate']['negative'] == 148
for world in ('classic', 'dense', 'moving'):
    forward = rows[world, 'forward']
    assert forward['immediate']['negative_rollouts'] < forward['approach']['negative_rollouts']
print('EARLY-INTERVENTION ARCHIVE OK: frozen records, support result and forward tradeoff')
PY

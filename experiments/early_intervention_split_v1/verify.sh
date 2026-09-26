#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/../.."
"${PYTHON:-python}" -m experiments.early_intervention_split_v1.audit --verify
"${PYTHON:-python}" - <<'PY'
import hashlib
import json
import subprocess
from pathlib import Path
from scripts.schedule_layout_study import verify_files

folder = Path('experiments/early_intervention_split_v1')
receipt = json.loads((folder / 'verification.json').read_text())
for key in ('frozen_files', 'logs', 'locked_artifacts'):
    verify_files(receipt[key])
manifest = json.loads((folder / 'manifest.json').read_text())
for path, digest in manifest['sources'].items():
    original = subprocess.check_output(['git', 'show', f"{receipt['instrument_commit']}:{path}"])
    assert hashlib.sha256(original).hexdigest() == digest, path
report = json.loads((folder / 'report.json').read_text())
for arm, expected in (('approach', (7, 0)), ('immediate', (12, 2))):
    data = report['arms'][arm]
    assert data['requirements']['status'] == 'insufficient'
    for part, count in zip(('train', 'val'), expected):
        rows = [r for r in data['requirements']['checks'] if r['partition'].endswith('/'+part)]
        assert len(rows) == 12 and sum(r['satisfied'] for r in rows) == count
    assert [data['veer_probe'][f'splits/{s}/val']['moving']['rollouts'] for s in (0, 1, 2)] == [1, 0, 0]
assert report['paired_split_membership']
print('TIMING-SPLIT ARCHIVE OK: original sources, frozen files, split limits and absent probe strata')
PY

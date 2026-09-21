#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python -m eval.eval_held_command_support --verify
python - <<'PY'
import hashlib
import json
import subprocess
from pathlib import Path

from datasets.provenance import file_identity

folder = Path('experiments/held_command_support_v1')
report = json.loads((folder / 'report.json').read_text())
for data in report['inputs'].values():
    for group in (data, *data['worlds'].values()):
        assert group['union']['windows'] == group['original']['windows'] + group['recovered']['windows']
        for kind in ('original', 'recovered', 'union'):
            count = group[kind]
            assert count['windows'] == count['positive'] + count['negative']
            if 'actions' in group:
                assert count['windows'] == sum(a[kind]['windows'] for a in group['actions'].values())
    for kind in ('original', 'recovered', 'union'):
        assert data[kind]['windows'] == sum(w[kind]['windows'] for w in data['worlds'].values())
training = report['inputs']['training']
changed = sum(
    action['original'][key] != action['union'][key]
    for world in training['worlds'].values() for action in world['actions'].values()
    for key in ('positive_rollouts', 'negative_rollouts'))
assert changed == 0  # Preserve the reported observation, not a new gate.
assert training['recovered']['windows'] == 1681
assert training['worlds']['moving']['recovered']['windows'] == 83
for action in ('veer_left', 'veer_right'):
    assert training['worlds']['moving']['actions'][action]['recovered']['windows'] == 0
print('HELD-COMMAND ACCOUNTING VERIFIED: training +1681 windows, +0 action/class course coverage')
receipt = json.loads((folder / 'verification.json').read_text())
for path, digest in receipt['frozen_files'].items():
    assert file_identity(path)['sha256'] == digest, path
for path, digest in receipt['instrument_sources'].items():
    original = subprocess.check_output(['git', 'show', f"{receipt['instrument_commit']}:{path}"])
    assert hashlib.sha256(original).hexdigest() == digest, path
print('HELD-COMMAND FROZEN FILES AND ORIGINAL INSTRUMENT SOURCES VERIFIED')
PY

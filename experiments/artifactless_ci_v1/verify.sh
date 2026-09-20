#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python - "$@" <<'PY'
import hashlib
import json
import shlex
import subprocess
import sys
from pathlib import Path

root = Path.cwd()
folder = root / 'experiments/artifactless_ci_v1'
config = json.loads((folder / 'baseline.json').read_text())
result = json.loads((folder / 'baseline_result.json').read_text())
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
assert result['config_sha256'] == sha(folder / 'baseline.json')
assert result['worker_sha256'] == sha(folder / 'run.sh')
assert result['status'] == 'passed' and result['exit_code'] == 0
assert result['active'] is None and result['primary_artifacts_intact']
assert not result['locked_artifacts_present_at_start'] and not result['tracked_changes']
assert result['source_commit'] == config['source_commit']
assert len(result['completed']) == result['total'] == len(config['commands']) == 116
for i, row in enumerate(result['completed']):
    assert row['index'] == i and row['command'] == config['commands'][i]
    assert row['exit_code'] == 0 and row['source_commit'] == result['source_commit']
    assert row['elapsed_seconds'] >= 0 and len(row['log_sha256']) == 64
    if '--local' in sys.argv:
        assert sha(row['log']) == row['log_sha256']
for paths in result['package_origins'].values():
    assert paths and all(Path(p).is_relative_to(config['worktree']) for p in paths)
workflow = subprocess.check_output(
    ['git', 'show', f"{config['source_commit']}:.github/workflows/ci.yml"], text=True)
assert hashlib.sha256(workflow.encode()).hexdigest() == config['workflow_sha256']
groups = {'Pure-math selftests', 'Sim-in-the-loop selftests (headless)'}
commands, active = [], None
for line in workflow.splitlines():
    if line.startswith('      - name: '):
        name = line.removeprefix('      - name: ')
        active = name if name in groups else None
    elif active and line.startswith('          '):
        text = line.strip()
        if text and not text.startswith('#'):
            commands.append({'group': active, 'argv': shlex.split(text)})
    elif active and line.strip() and not line.startswith('        '):
        active = None
assert commands == config['commands']
if '--local' in sys.argv:
    for row in config['primary_artifacts']:
        assert sha(root / row['path']) == row['sha256']
print('ARTIFACTLESS-CI VERIFIED: 116 command receipts, frozen workflow, isolated imports'
      + ('; full logs and primary hashes verified' if '--local' in sys.argv else ''))
PY

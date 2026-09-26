#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/../.."
"${PYTHON:-python}" - <<'PY'
import ast
import json
import subprocess
from pathlib import Path

from eval import eval_dataset_support as dataset
from eval import eval_veer_support as veer
from experiments.early_intervention_split_v1.audit import complete_actions
from scripts.schedule_layout_study import read, sha, verify_files, write_new

root = Path.cwd()
record = {'reference_commit': 'cbd4549', 'unchanged_core_definitions': {}, 'reports': {}}
for module in (dataset, veer):
    path = Path(module.__file__).relative_to(root)
    before = subprocess.check_output(['git', 'show', f'cbd4549:{path}'], text=True)
    def core(source):
        return {node.name: ast.dump(node, include_attributes=False)
                for node in ast.parse(source).body
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name != 'main'}
    old, current = core(before), core(path.read_text())
    assert old == current, path
    record['unchanged_core_definitions'][str(path)] = list(old)

archive_path = Path('experiments/early_intervention_split_v1/report.json')
archive = read(archive_path)
inputs = {}
for arm, saved in archive['arms'].items():
    expected = saved['support']
    identity = expected['provenance']['dataset']
    path = Path(identity['path'])
    assert sha(path) == identity['sha256']
    current = complete_actions(dataset.analyze(dataset.load_metadata(path), seeds=(0, 1, 2), epochs=1))
    assert current == {k: v for k, v in expected.items() if k != 'provenance'}
    inputs[str(path)] = identity['sha256']
    record['reports'][arm + '_all_and_splits'] = {
        'archive': str(archive_path), 'archive_sha256': sha(archive_path),
        'dataset_sha256': identity['sha256'], 'exact_values_equal': True,
        'valid_windows': current['all']['valid_windows'],
    }

for name in ('cf_hard_pool_v1', 'executed_weight_v1'):
    archive_path = Path('experiments/veer_support_v1') / (name + '.json')
    expected = read(archive_path)
    identity = expected['provenance']['dataset']
    path = Path(identity['path'])
    assert sha(path) == identity['sha256']
    current, _ = veer.analyze(veer.load_metadata(path))
    assert current == {k: v for k, v in expected.items() if k != 'provenance'}
    inputs[str(path)] = identity['sha256']
    record['reports'][name + '_veer'] = {
        'archive': str(archive_path), 'archive_sha256': sha(archive_path),
        'dataset_sha256': identity['sha256'], 'exact_values_equal': True,
        'frames': current['n_frames'], 'rollouts': current['n_rollouts'],
    }
verify_files(inputs)
locked = {str(root / row['dest']): row['sha256'] for row in read('artifacts.lock.json')['artifacts']}
verify_files(locked)
record['locked_artifacts'] = locked
destination = Path('experiments/support_publication_v1/compatibility.json')
if destination.exists():
    assert read(destination) == record
else:
    write_new(destination, record)
print('SUPPORT COMPATIBILITY OK: all non-CLI functions unchanged; four archived support reports match exactly; nine protected artifacts intact')
PY

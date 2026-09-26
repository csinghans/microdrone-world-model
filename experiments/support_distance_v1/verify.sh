#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/../.."
bash experiments/support_distance_v1/verify_before.sh
"${PYTHON:-python}" - <<'PY'
from pathlib import Path
from eval.eval_dataset_support import analyze, load_metadata
from experiments.early_intervention_split_v1.audit import complete_actions
from scripts.schedule_layout_study import read, sha, verify_files, write_new

folder = Path('experiments/support_distance_v1')
cases = []
timing = read('experiments/early_intervention_split_v1/report.json')
for arm, value in timing['arms'].items():
    cases.append((arm + '_timing', value['support'], 1, True))
for arm in ('legacy', 'world_balanced'):
    cases.append((arm + '_schedule', read(f'experiments/schedule_support_v1/{arm}.json'), 80, False))
rows = {}
for name, saved, epochs, fill in cases:
    source = saved['provenance']['dataset']
    assert sha(source['path']) == source['sha256']
    actual = analyze(load_metadata(source['path']), seeds=(0, 1, 2), epochs=epochs)
    if fill:
        actual = complete_actions(actual)
    for partition in ('all', 'splits'):
        assert actual[partition] == saved[partition], (name, partition)
    assert sha(source['path']) == source['sha256']
    rows[name] = {'dataset': source, 'valid_windows': actual['all']['valid_windows'],
                  'all_and_three_seed_splits_exactly_equal': True}
locked = {row['dest']: row['sha256'] for row in read('artifacts.lock.json')['artifacts']}
verify_files(locked)
result = {'reports': rows, 'locked_artifacts': locked}
if (folder / 'compatibility.json').exists():
    assert read(folder / 'compatibility.json') == result
else:
    write_new(folder / 'compatibility.json', result)
receipt = folder / 'verification.json'
if receipt.exists():
    for key in ('frozen_files', 'logs', 'locked_artifacts'):
        verify_files(read(receipt)[key])
print('SUPPORT-DISTANCE VERIFIED: four valid corpora retain all counts/splits; nine locked artifacts intact')
PY

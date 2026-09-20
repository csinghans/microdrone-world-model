#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python - "$@" <<'PY'
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from eval.compare_wm_scores import _load, _validate, compare

folder = Path('experiments/score_schema_v1')
def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

config = json.loads((folder / 'registration.json').read_text())
old_source = subprocess.check_output(
    ['git', 'show', f"{config['reference_commit']}:eval/compare_wm_scores.py"], text=True)
assert hashlib.sha256(old_source.encode()).hexdigest() == config['comparator_sha256']
old = {'__name__': 'frozen_comparator'}
exec(compile(old_source, 'frozen_comparator', 'exec'), old)

# This is the only comparison/resampling in this audit: synthetic fixtures.
base = dict(pairs=np.array([(r, t) for r in range(4) for t in range(2)]),
            labels=np.tile([0, 1], 4).reshape(-1, 1),
            scores=np.tile([0, 1], 4).reshape(-1, 1),
            world_id=np.repeat([0, 0, 1, 1], 2),
            world_names=np.array(['classic', 'dense']), horizons=np.array([32]),
            metadata={'split': 'independent_holdout_all', 'auc_method': old['AUC_METHOD'],
                      'provenance': {'dataset': {'sha256': 'synthetic-only'}}})
parity = []
for case in ('no_probe', 'probe', 'empty_probe', 'singleton_probe', 'single_class'):
    a, b = copy.deepcopy(base), copy.deepcopy(base)
    selected = b['pairs'][:, 0] % 2 == 0
    b['scores'][selected] = 1 - b['labels'][selected]
    if case in ('probe', 'empty_probe', 'singleton_probe'):
        for arm in (a, b):
            arm.update(veer_pairs=arm['pairs'].copy(), veer_world_id=arm['world_id'].copy(),
                       veer_gt_left=np.zeros(8, dtype=bool), veer_correct=np.zeros(8, dtype=bool))
        b['veer_correct'][selected] = True
        if case in ('empty_probe', 'singleton_probe'):
            end = 0 if case == 'empty_probe' else 2
            for arm in (a, b):
                for key in ('veer_pairs', 'veer_world_id', 'veer_gt_left', 'veer_correct'):
                    arm[key] = arm[key][:end]
    if case == 'single_class':
        a['labels'][:] = b['labels'][:] = 0
    before = old['compare'](a, b, n_boot=47, seed=13)
    after = compare(a, b, n_boot=47, seed=13)
    assert before == after, case
    parity.append(case)

accepted, groups = [], {}
for entry in config['exports']:
    record_path, export_path = Path(entry['receipt']['path']), Path(entry['scores']['path'])
    for key in ('receipt', 'scores'):
        assert sha(entry[key]['path']) == entry[key]['sha256'], entry[key]['path']
    receipt = json.loads(record_path.read_text())
    original_hashes = [h for p, h in receipt['files'].items() if p.endswith('.npz')]
    assert original_hashes == [entry['scores']['sha256']]
    arm = _load(export_path)
    assert arm['metadata'] == receipt['result']['scores']
    _validate(arm, arm)  # No score calculation or bootstrap for archived files.
    seed = arm['metadata']['training_seed']
    groups.setdefault((entry['study'], seed), []).append(arm)
    accepted.append(dict(study=entry['study'], seed=seed, scores=entry['scores'],
                         receipt=entry['receipt'], status='accepted'))
    for key in ('receipt', 'scores'):
        assert sha(entry[key]['path']) == entry[key]['sha256']
assert len(accepted) == 18 and len(groups) == 9
for arms in groups.values():
    assert len(arms) == 2
    _validate(*arms)

result = dict(
    scope='Archived schema/identity checks only; no archived metric calculation or resampling.',
    registration_sha256=sha(folder / 'registration.json'),
    synthetic_parity_cases=parity,
    synthetic_bootstrap=dict(n_boot=47, seed=13),
    n_archived_exports=len(accepted), n_archived_pairs=len(groups), exports=accepted,
)
output = folder / 'compatibility.json'
if '--record' in sys.argv:
    with output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
else:
    assert json.loads(output.read_text()) == result
print('SCORE-SCHEMA VERIFIED: 18 unchanged archived exports / 9 pairs; '
      '5 synthetic comparisons exactly match the old implementation')
PY

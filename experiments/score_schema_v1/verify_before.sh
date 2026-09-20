#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python - <<'PY'
import copy
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np

config = json.loads(Path('experiments/score_schema_v1/registration.json').read_text())
source = subprocess.check_output(
    ['git', 'show', f"{config['reference_commit']}:eval/compare_wm_scores.py"], text=True)
assert hashlib.sha256(source.encode()).hexdigest() == config['comparator_sha256']
old = {'__name__': 'frozen_comparator'}
exec(compile(source, 'frozen_comparator', 'exec'), old)
base = dict(
    pairs=np.array([(r, t) for r in range(4) for t in range(2)]),
    labels=np.tile([0, 1], 4).reshape(-1, 1),
    scores=np.tile([0, 1], 4).reshape(-1, 1),
    world_id=np.repeat([0, 0, 1, 1], 2),
    world_names=np.array(['classic', 'dense']), horizons=np.array([32]),
    metadata={'split': 'independent_holdout_all', 'auc_method': old['AUC_METHOD'],
              'provenance': {'dataset': {'sha256': 'synthetic-only'}}})
for case in config['before_cases']:
    arm = copy.deepcopy(base)
    if case == 'fractional_pairs': arm['pairs'] = arm['pairs'].astype(float) + 0.5
    elif case == 'negative_pairs': arm['pairs'][:, 1] = -arm['pairs'][:, 1] - 1
    elif case == 'fractional_worlds': arm['world_id'] = arm['world_id'].astype(float) + 0.5
    elif case == 'duplicate_names': arm['world_names'] = np.array(['same', 'same'])
    elif case == 'pooled_name_collision': arm['world_names'] = np.array(['all', 'dense'])
    elif case == 'fractional_horizon': arm['horizons'] = np.array([32.5])
    else:
        arm.update(veer_pairs=arm['pairs'].copy(), veer_gt_left=np.ones(8, dtype=bool),
                   veer_correct=np.ones(8, dtype=bool), veer_world_id=arm['world_id'].copy())
        if case == 'nonbinary_veer_truth': arm['veer_gt_left'] = np.full(8, 2)
        elif case == 'inconsistent_veer_world': arm['veer_world_id'] = 1 - arm['world_id']
        else: raise AssertionError(case)
    result = old['compare'](arm, arm, n_boot=2, seed=0)
    if case == 'pooled_name_collision':
        assert result['worlds']['all']['n_samples'] == 4  # pooled exam has 8
    print(f'{case}: old comparator accepted')
print(f"SCORE-SCHEMA BEFORE VERIFIED: {len(config['before_cases'])} malformed synthetic cases accepted")
PY

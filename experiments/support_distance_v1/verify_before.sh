#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/../.."
"${PYTHON:-python}" - <<'PY'
import json
import subprocess
import types
from pathlib import Path
import numpy as np
from datasets.combine_rollouts import _synth
from planner.action_set import ACTION_VECS

path = Path('eval/eval_dataset_support.py').resolve()
source = subprocess.check_output(['git', 'show', 'c7b6b89:eval/eval_dataset_support.py'], text=True)
module = types.ModuleType('_distance_before')
module.__file__ = str(path)
exec(compile(source, str(path), 'exec'), module.__dict__)
data = _synth([0] * 6, length=40)
data['actions'][:] = ACTION_VECS[0]
data['dists'][:] = 0.1
def counts(blob):
    row = module.analyze(blob, holdout=True)['all']['worlds']['classic']
    return {key: {label: row[key][label] for label in ('positive', 'negative')}
            for key in ('labels_at_32', 'now_labels')}
observed = {'baseline': counts(data)}
nan_distances = data['dists'].copy()
nan_distances[:, 16] = np.nan
observed['nan_in_each_held_window'] = counts(dict(data, dists=nan_distances))
observed['nan_danger_radius'] = counts(dict(data, danger_r=np.float32(np.nan)))
assert observed['baseline']['labels_at_32'] == {'positive': 48, 'negative': 0}
assert observed['nan_in_each_held_window']['labels_at_32'] == {'positive': 0, 'negative': 48}
assert observed['nan_danger_radius']['now_labels'] == {'positive': 0, 'negative': 240}
target = Path('experiments/support_distance_v1/before.json')
if target.exists():
    assert json.loads(target.read_text()) == observed
else:
    with target.open('x') as stream:
        json.dump(observed, stream, indent=2)
        stream.write('\n')
print('SUPPORT-DISTANCE BEFORE VERIFIED: missing distances/radius silently become negative labels')
PY

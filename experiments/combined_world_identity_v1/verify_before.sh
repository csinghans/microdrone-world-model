#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python - "$@" <<'PY'
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

revision = '47668fc'
source = subprocess.check_output(
    ['git', 'show', f'{revision}:datasets/combine_rollouts.py'], text=True)
namespace = {'__name__': 'frozen_combiner',
             '__file__': str(Path('datasets/combine_rollouts.py').resolve())}
exec(compile(source, 'frozen_combiner', 'exec'), namespace)
synth, combine = namespace['_synth'], namespace['combine']

def observe(names, ids, indoor_name='room'):
    transit = synth(ids)
    transit['world_names'] = np.array(names)
    indoor = synth([0], nan_pillars=True)
    indoor['world_names'] = np.array([indoor_name])
    combined = combine(transit, indoor)
    expected = [names[i] for i in ids] + [indoor_name]
    actual = combined['world_names'][combined['world_id']].tolist()
    assert actual != expected
    return {'input_worlds': expected, 'combined_worlds': actual}

result = {
    'reference_commit': revision,
    'source': 'datasets/combine_rollouts.py',
    'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
    'scope': 'Synthetic corpus identity only; no generation, scoring or fitting.',
    'cases': {
        'dynamic_world_3': observe(['classic', 'dense', 'moving', 'gap'], [0, 3]),
        'reordered_catalog': observe(['dense', 'classic', 'moving'], [0, 1]),
        'wrong_indoor_source': observe(['classic', 'dense', 'moving'], [0], 'dense'),
    },
}
path = Path('experiments/combined_world_identity_v1/before.json')
if '--record' in sys.argv:
    with path.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
else:
    assert json.loads(path.read_text()) == result
print('COMBINED-WORLD BEFORE VERIFIED: three silent world-identity changes')
PY

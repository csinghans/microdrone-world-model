#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python - <<'PY'
import ast
import hashlib
import io
import json
import subprocess
from pathlib import Path

import numpy as np

from datasets.combine_rollouts import _synth, combine

before = json.loads(Path('experiments/combined_world_identity_v1/before.json').read_text())
source = subprocess.check_output(
    ['git', 'show', f"{before['reference_commit']}:{before['source']}"], text=True)
assert hashlib.sha256(source.encode()).hexdigest() == before['source_sha256']
old = {'__name__': 'frozen_combiner', '__file__': str(Path(before['source']).resolve())}
exec(compile(source, 'frozen_combiner', 'exec'), old)
cases = 0
for ids in ([0, 1, 2], [2, 1, 2, 0], [1, 1, 1]):
    for layout in ('legacy', 'world_balanced'):
        transit = _synth(ids)
        indoor = _synth([0, 0], nan_pillars=True)
        indoor['world_names'] = np.array(['room'])
        # Distinct rows expose changed ordering or accidental data replacement.
        transit['frames'][:, 0, 0, 0, 0] = np.arange(len(ids)) + 1
        indoor['frames'][:, 0, 0, 0, 0] = [31, 32]
        if layout != 'legacy':
            transit['schedule_layout'] = np.array(layout)
        previous, current = old['combine'](transit, indoor), combine(transit, indoor)
        assert list(previous) == list(current)
        for key in previous:
            assert previous[key].dtype == current[key].dtype, key
            assert previous[key].shape == current[key].shape, key
            assert previous[key].tobytes() == current[key].tobytes(), key
        previous_npz, current_npz = io.BytesIO(), io.BytesIO()
        np.savez_compressed(previous_npz, **previous)
        np.savez_compressed(current_npz, **current)
        assert previous_npz.getvalue() == current_npz.getvalue()
        cases += 1

def definition(text, name):
    return ast.dump(next(node for node in ast.parse(text).body
                         if isinstance(node, ast.FunctionDef) and node.name == name))

current_source = Path(before['source']).read_text()
assert definition(source, 'build') == definition(current_source, 'build')
for filename in ('datasets/generate_rollouts.py', 'datasets/search_rollouts.py'):
    frozen = subprocess.check_output(['git', 'show', f"{before['reference_commit']}:{filename}"])
    assert frozen == Path(filename).read_bytes(), filename
print(f'COMBINED-WORLD PARITY OK: {cases} canonical fixtures and NPZs byte-identical; '
      'build recipe and both generators unchanged')
PY

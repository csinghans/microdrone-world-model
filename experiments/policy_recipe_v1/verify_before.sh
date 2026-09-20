#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python - <<'PY'
import ast
import contextlib
import hashlib
import io
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from planner import learned_policy as policy

receipt = json.loads(Path('experiments/policy_recipe_v1/before.json').read_text())
source = subprocess.check_output(
    ['git', 'show', f"{receipt['reference_commit']}:scripts/train.py"], text=True)
assert hashlib.sha256(source.encode()).hexdigest() == receipt['source_sha256']
node = next(n for n in ast.parse(source).body
            if isinstance(n, ast.FunctionDef) and n.name == 'train_policy')
namespace = {}
exec(compile(ast.Module(body=[node], type_ignores=[]), 'before', 'exec'), namespace)
observed = []
for worlds, curriculum in [('moving,dense,moving', False),
                           ('unknown_world', False), ('hard', True)]:
    args = SimpleNamespace(selftest=False, curriculum=curriculum, timesteps=1,
        seed=17, recurrent=False, randomize=curriculum, edge_bias=curriculum,
        worlds=worlds, x_progress=curriculum, n_steps=256, lstm_size=64,
        out='synthetic_recurrent.zip' if curriculum else 'synthetic.zip')
    with patch.object(policy, 'training_path', return_value=args.out), \
         patch.object(policy, 'train') as ordinary, \
         patch.object(policy, 'train_curriculum') as staged, \
         contextlib.redirect_stdout(io.StringIO()):
        namespace['train_policy'](args)
    kw = (staged if curriculum else ordinary).call_args.kwargs
    observed.append({'requested_worlds': worlds, 'requested_seed': 17,
        'curriculum': curriculum, 'effective_seed': kw.get('seed0', 0),
        'forwarded_worlds': kw.get('worlds'),
        'forwarded_hard': kw.get('hard', False), 'accepted': True})
assert observed == receipt['observed']
print('POLICY-RECIPE-BEFORE VERIFIED: ignored seed/worlds and curriculum flags; no fit')
PY

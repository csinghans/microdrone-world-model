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
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from planner import learned_policy as policy

receipt = json.loads(Path('experiments/policy_checkpoint_v1/before.json').read_text())
sources = {}
for key, path in [('policy_source', 'planner/learned_policy.py'),
                  ('cli_source', 'scripts/train.py')]:
    source = subprocess.check_output(['git', 'show', f'2e6c22d:{path}'], text=True)
    assert hashlib.sha256(source.encode()).hexdigest() == receipt[key]['sha256']
    sources[key] = source

def function(source, name, namespace):
    node = next(n for n in ast.parse(source).body
                if isinstance(n, ast.FunctionDef) and n.name == name)
    exec(compile(ast.Module(body=[node], type_ignores=[]), name, 'exec'), namespace)
    return namespace[name]

with tempfile.TemporaryDirectory(prefix='policy_before_selftest_') as tmp:
    target = Path(tmp) / 'ppo_wm_policy_edge_hard_xp.zip'
    target.write_bytes(b'synthetic champion')
    class FakePPO:
        def __init__(self, *a, **kw): pass
        def learn(self, **kw): pass
        def save(self, path): Path(path).write_bytes(b'synthetic replacement')
    namespace = dict(vars(policy), zip_path=lambda *a, **kw: str(target))
    original_train = function(sources['policy_source'], 'train', namespace)
    with patch('stable_baselines3.common.env_util.make_vec_env',
               return_value=SimpleNamespace(close=lambda:None)), \
         patch('stable_baselines3.PPO', FakePPO):
        original_train(1, hard=True, x_progress=True, edge_bias=True)
    assert target.read_bytes() == b'synthetic replacement'
    cli = function(sources['cli_source'], 'train_policy', {})
    args = SimpleNamespace(curriculum=False, timesteps=1, recurrent=False,
        randomize=False, edge_bias=True, worlds='hard', x_progress=True,
        n_steps=256, lstm_size=64, out=str(Path(tmp)/'requested.zip'))
    with patch.object(policy, 'train') as fake, contextlib.redirect_stdout(io.StringIO()):
        cli(args)
    assert 'out' not in fake.call_args.kwargs
print('POLICY-BEFORE VERIFIED: temporary overwrite and ignored --out; no learning')
PY

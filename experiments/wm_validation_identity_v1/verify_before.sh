#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python - <<'PY'
import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

receipt = json.loads(Path('experiments/wm_validation_identity_v1/before.json').read_text())
source = subprocess.check_output(
    ['git', 'show', f"{receipt['reference_commit']}:eval/eval_wm_checkpoint.py"], text=True)
assert hashlib.sha256(source.encode()).hexdigest() == receipt['source_sha256']
nodes = [node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)
         and node.name in {'evaluate', '_evaluation_seed'}]
meta = {'seed': 7, 'training_dataset_sha256': 'a' * 64}
score = Mock(return_value={'split': 'training_val'})
namespace = {
    'sys': sys,
    'torch': SimpleNamespace(__version__='synthetic'),
    'np': SimpleNamespace(__version__='synthetic'),
    'load_model': Mock(return_value=(None, None, None, None, meta)),
    'evaluate_components': score,
}
exec(compile(ast.Module(body=nodes, type_ignores=[]), 'validation_identity_before', 'exec'), namespace)
result = namespace['evaluate'](
    'synthetic-checkpoint', {}, dataset_sha256='b' * 64, device='cpu')
assert score.call_count == receipt['scorer_calls'] == 1
assert result['split'] == receipt['reported_split'] == 'training_val'
assert result['training_seed'] == receipt['training_seed'] == 7
assert meta['training_dataset_sha256'] != 'b' * 64
print('WM-VALIDATION-IDENTITY BEFORE VERIFIED: different corpus reached training_val scorer; mocked')
PY

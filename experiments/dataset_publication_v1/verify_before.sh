#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python - <<'PY'
import ast
import contextlib
import hashlib
import importlib
import io
import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
from datasets.combine_rollouts import _synth

receipt = json.loads(Path('experiments/dataset_publication_v1/before.json').read_text())
for row in receipt['clis']:
    source = subprocess.check_output(
        ['git', 'show', f"{receipt['reference_commit']}:{row['source']}"], text=True)
    assert hashlib.sha256(source.encode()).hexdigest() == row['source_sha256']
    module = importlib.import_module(row['module'])
    namespace = dict(vars(module))
    factory = Mock(return_value=_synth([0], length=40))
    namespace[row['factory']] = factory
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    exec(compile(ast.Module(body=[node], type_ignores=[]), 'dataset_publication_before', 'exec'), namespace)
    with tempfile.TemporaryDirectory(prefix='dataset_publication_before_selftest_') as tmp:
        output = Path(tmp) / 'historical.npz'
        np.savez(output, historical=np.array([73]))
        before = output.read_bytes()
        argv = [row['module'], *row['flags'], '--out', str(output)]
        with patch('sys.argv', argv), contextlib.redirect_stdout(io.StringIO()):
            namespace['main']()
        assert factory.call_count == 1 and output.read_bytes() != before
        assert row['existing_output_overwritten'] is True
        with np.load(output, allow_pickle=False) as blob:
            assert 'frames' in blob and 'historical' not in blob
print('DATASET-PUBLICATION BEFORE VERIFIED: all 3 generator CLIs overwrote an existing corpus; simulated generation mocked')
PY

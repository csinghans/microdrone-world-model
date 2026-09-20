#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python - <<'PY'
import argparse
import ast
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
from datasets.provenance import file_identity

receipt = json.loads(Path('experiments/wm_publication_v1/before.json').read_text())
source = subprocess.check_output(
    ['git', 'show', f"{receipt['reference_commit']}:eval/eval_wm_checkpoint.py"], text=True)
assert hashlib.sha256(source.encode()).hexdigest() == receipt['source_sha256']
nodes = [node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)
         and node.name in {'main', '_json_ready'}]
score = Mock()
namespace = dict(argparse=argparse, json=json, sys=sys, np=np, Path=Path,
                 DATA='unused', _file_identity=file_identity, evaluate=score)
exec(compile(ast.Module(body=nodes, type_ignores=[]), 'wm_publication_before', 'exec'), namespace)
with tempfile.TemporaryDirectory(prefix='wm_publication_before_selftest_') as tmp:
    root = Path(tmp)
    model, corpus = root / 'synthetic.pth', root / 'synthetic.npz'
    model.write_bytes(b'synthetic checkpoint; no model is loaded')
    np.savez(corpus, frames=np.zeros((1, 1, 1, 1, 3), dtype=np.uint8))
    def fail_npz(stream, **kwargs):
        stream.write(b'partial NPZ')
        raise RuntimeError('synthetic serialization failure')
    for kind in ('npz', 'json'):
        output = root / ('result.' + kind)
        argv = ['probe', '--ckpt', str(model), '--data', str(corpus),
                '--scores-out' if kind == 'npz' else '--out', str(output)]
        score.return_value = {} if kind == 'npz' else {'invalid': object()}
        with patch('sys.argv', argv), patch.object(np, 'savez_compressed', side_effect=fail_npz):
            try:
                namespace['main']()
            except (RuntimeError, TypeError):
                pass
            else:
                raise AssertionError('synthetic fault did not fire')
        assert output.exists() and output.stat().st_size > 0
        if kind == 'npz':
            assert output.read_bytes() == b'partial NPZ'
        else:
            try:
                json.loads(output.read_text())
            except json.JSONDecodeError:
                pass
            else:
                raise AssertionError('expected incomplete JSON')
        assert receipt['partial_final_files'][kind] is True
assert score.call_count == 2
print('WM-PUBLICATION BEFORE VERIFIED: NPZ and JSON serializer errors left partial final files; mocked')
PY

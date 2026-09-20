#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python - <<'PY'
import contextlib
import hashlib
import io
import json
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from datasets.provenance import file_identity
from eval.eval_policy_cells import load_cells

folder = Path('experiments/policy_eval_identity_v1')
receipt = json.loads((folder / 'before.json').read_text())
source = subprocess.check_output(
    ['git', 'show', f"{receipt['reference_commit']}:eval/eval_policy_cells.py"], text=True)
assert hashlib.sha256(source.encode()).hexdigest() == receipt['source_sha256']
namespace = {'__name__': 'policy_cells_before'}
exec(compile(source, 'policy_cells_before', 'exec'), namespace)
with tempfile.TemporaryDirectory(prefix='policy_eval_before_selftest_') as tmp:
    root = Path(tmp)
    spec, out = root / 'cells.json', root / 'results.json'
    rows = [{'id': 'duplicate', 'world': 'classic', 'speed': 1.0,
             'n': 1, 'seed0': seed} for seed in (10, 20)]
    spec.write_text(json.dumps(rows))
    out.write_bytes(b'previous result sentinel')

    def fly(factory, cell, judge, env, **kw):
        return {'crash': 0.0, 'success': 1.0, 'clearance_mean': 1.0,
                'n': 1, 'seed0': cell.seed0}

    with patch('sys.argv', ['eval.eval_policy_cells', '--zip', 'synthetic.zip',
                           '--cells', str(spec), '--out', str(out)]), \
         patch('scripts.research._policy_factory'), \
         patch('scripts.research.run_cell', side_effect=fly) as flown, \
         patch('sim.envs.make_env', return_value=SimpleNamespace(close=lambda: None)), \
         contextlib.redirect_stdout(io.StringIO()):
        namespace['main']()
    record = json.loads(out.read_text())
    observed = {
        'existing_result_replaced': out.read_bytes() != b'previous result sentinel',
        'cells_flown': flown.call_count, 'cells_saved': len(record['cells']),
        'surviving_seed0': record['cells']['duplicate']['seed0'],
        'saved_top_level_keys': sorted(record),
    }
    assert observed == receipt['observed']
print('PCELLS-BEFORE VERIFIED: temporary replacement and duplicate collapse; no flight')

compatibility = json.loads((folder / 'spec_compatibility.json').read_text())
for row in compatibility['specs']:
    assert file_identity(row['path'])['sha256'] == row['sha256']
    cells = load_cells(row['path'])
    assert len(cells) == row['n_cells']
    assert [c.id for c in cells] == row['ids']
assert len(compatibility['specs']) == compatibility['n_files']
assert sum(row['n_cells'] for row in compatibility['specs']) == compatibility['n_cells']
print(f"PCELLS-SPECS VERIFIED: {compatibility['n_files']} files, "
      f"{compatibility['n_cells']} cells; metadata only")
PY

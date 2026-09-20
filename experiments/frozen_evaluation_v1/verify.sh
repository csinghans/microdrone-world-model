#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python - <<'PY'
import ast
import hashlib
import json
import os
import subprocess
import tempfile
from dataclasses import replace
from pathlib import Path

from scripts import research
from scripts.research_selftest import _skill
from skills.base import load_skill

folder = Path('experiments/frozen_evaluation_v1')
before = json.loads((folder / 'before.json').read_text())
source = subprocess.check_output(
    ['git', 'show', f"{before['reference_commit']}:scripts/research.py"], text=True)
assert hashlib.sha256(source.encode()).hexdigest() == before['source_sha256']
nodes = [node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)
         and node.name in {'_load_results', '_frozen_criteria'}]
namespace = {'os': os, 'json': json}
exec(compile(ast.Module(body=nodes, type_ignores=[]), 'frozen_before', 'exec'), namespace)
original = _skill()
changes = {
    'world': replace(original, cells=(replace(original.cells[0], world='moving'),)),
    'speed': replace(original, cells=(replace(original.cells[0], speed=0.6),)),
    'seed0': replace(original, cells=(replace(original.cells[0], seed0=12345),)),
    'n_seeds': replace(original, cells=(replace(original.cells[0], n_seeds=60),)),
    'kwargs': replace(original, cells=(replace(original.cells[0], kwargs={'solo': True}),)),
    'cell_role': replace(original, cells=(replace(original.cells[0], role='guard'),)),
    'recheck_n': replace(original, recheck_n=120),
    'recheck_margin': replace(original, recheck_margin=0.01),
}
with tempfile.TemporaryDirectory(prefix='frozen_eval_before_selftest_') as tmp:
    record = namespace['_load_results'](tmp, original)
    Path(tmp, 'results.json').write_text(json.dumps(record))
    for name, skill in changes.items():
        assert namespace['_load_results'](tmp, skill) == record
    assert list(changes) == before['accepted_changed_fields']
print('FROZEN-EVALUATION-BEFORE VERIFIED: eight changed settings accepted; synthetic')

audit = json.loads((folder / 'legacy_audit.json').read_text())
assert len(audit['records']) == audit['n_records']
for row in audit['records']:
    path = Path(row['path'])
    data = path.read_bytes()
    assert hashlib.sha256(data).hexdigest() == row['sha256']
    record = json.loads(data)
    skill = load_skill(row['skill'])
    assert research._load_results(str(path.parent), skill) == record
    assert namespace['_load_results'](str(path.parent), skill) == record
    assert 'evaluation_frozen' not in record
    assert row['evaluation_identity'] == 'legacy_unrecorded'
    assert row['loader_outcome'] == 'readable'
    assert record['status'] == row['status'] and len(record['knobs']) == row['knobs']
    assert path.read_bytes() == data
print(f"FROZEN-EVALUATION-LEGACY VERIFIED: {audit['n_records']} unchanged readable records")
PY

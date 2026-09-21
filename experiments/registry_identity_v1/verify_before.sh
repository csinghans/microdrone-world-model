#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python - "$@" <<'PY'
import hashlib
import json
import subprocess
import sys
import types
from pathlib import Path

revision = '18fe875'
source = subprocess.check_output(
    ['git', 'show', f'{revision}:sim/scenario_registry.py'], text=True)
module = types.ModuleType('frozen_registry')
sys.modules[module.__name__] = module
exec(compile(source, 'frozen_registry', 'exec'), module.__dict__)
initial = dict(module._REGISTRY)
factory = lambda *args, **kwargs: None

def reset():
    module._REGISTRY.clear()
    module._REGISTRY.update(initial)

module.register('custom', factory, world_id=0)
collision = {'classic_id': module.get('classic').world_id,
             'catalog_at_classic_id': str(module.world_names_array()[0])}
assert collision == {'classic_id': 0, 'catalog_at_classic_id': 'custom'}
reset()
first = module.register('custom', factory)
second = module.register('custom', factory, world_id=7)
assert (first.world_id, second.world_id) == (3, 7)
reset()
builtin = module.register('moving', factory, world_id=8)
assert builtin.world_id == 8
coercions = []
for value in (3.9, -1, True, '6'):
    reset()
    spec = module.register('custom', factory, world_id=value)
    coercions.append({'requested': value, 'stored': spec.world_id})
result = {
    'reference_commit': revision,
    'source': 'sim/scenario_registry.py',
    'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
    'scope': 'Isolated in-memory registry only; no scenarios spawned or artifacts modified.',
    'builtin_collision': collision,
    'same_name_reassignment': [first.world_id, second.world_id],
    'builtin_reassignment': {'moving': builtin.world_id},
    'accepted_invalid_ids': coercions,
}
path = Path('experiments/registry_identity_v1/before.json')
if '--record' in sys.argv:
    with path.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
else:
    assert json.loads(path.read_text()) == result
print('REGISTRY BEFORE VERIFIED: collision, reassignment and four invalid IDs accepted')
PY

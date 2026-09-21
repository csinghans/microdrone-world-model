#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python - "$@" <<'PY'
import hashlib
import json
import subprocess
import sys
from pathlib import Path

folder = Path('experiments/registry_identity_v1')
before = json.loads((folder / 'before.json').read_text())
source = subprocess.check_output(
    ['git', 'show', f"{before['reference_commit']}:{before['source']}"])
assert hashlib.sha256(source).hexdigest() == before['source_sha256']

worker = r'''
import contextlib
import json
import subprocess
import sys
import types
from pathlib import Path

if sys.argv[1] == 'old':
    import sim
    registry = types.ModuleType('sim.scenario_registry')
    registry.__file__ = str(Path('sim/scenario_registry.py').resolve())
    sys.modules[registry.__name__] = registry
    sim.scenario_registry = registry
    source = subprocess.check_output(
        ['git', 'show', f'{sys.argv[2]}:sim/scenario_registry.py'], text=True)
    exec(compile(source, registry.__file__, 'exec'), registry.__dict__)
else:
    from sim import scenario_registry as registry

from skills.base import load_skill
skills = [path.parent.name for path in sorted(Path('skills').glob('*/skill.py'))]
with contextlib.redirect_stdout(sys.stderr):
    for name in skills:
        load_skill(name)
initial = {name: registry.get(name).world_id for name in registry.names()}
with contextlib.redirect_stdout(sys.stderr):
    for name in reversed(skills):
        load_skill(name)
reloaded = {name: registry.get(name).world_id for name in registry.names()}
assert initial == reloaded, 'skill reload changed registered identities'
catalog = registry.world_names_array().tolist()
assert len(set(initial.values())) == len(initial)
assert len(set(catalog)) == len(catalog)
assert all(catalog[wid] == name for name, wid in initial.items())
print(json.dumps({'skills': skills, 'world_ids': initial, 'catalog': catalog,
                  'reload_order': list(reversed(skills))}))
'''

results = []
for implementation in ('old', 'current'):
    process = subprocess.run(
        [sys.executable, '-c', worker, implementation, before['reference_commit']],
        text=True, capture_output=True)
    if process.stderr:
        print(process.stderr, file=sys.stderr, end='')
    if process.returncode:
        print(process.stdout, end='')
        raise SystemExit(process.returncode)
    results.append(json.loads(process.stdout))
assert results[0] == results[1], 'current skill identities differ from the old registry'
paths = [Path('skills/base.py'), *sorted(Path('skills').glob('*/skill.py'))]
for path in paths:
    previous = subprocess.check_output(
        ['git', 'show', f"{before['reference_commit']}:{path.as_posix()}"])
    assert previous == path.read_bytes(), path
result = {
    'scope': 'Load/reload every skill declaration in fresh processes; no scenario spawning, model loading or metrics.',
    'reference_commit': before['reference_commit'],
    'original_registry_sha256': before['source_sha256'],
    'declaration_sha256': {
        path.as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
    **results[1],
}
path = folder / 'compatibility.json'
if '--record' in sys.argv:
    with path.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
else:
    assert json.loads(path.read_text()) == result
print(f"REGISTRY COMPATIBILITY OK: {len(result['skills'])} skills, "
      f"{len(result['world_ids'])} identical world IDs/catalog entries; reverse reload stable")
PY

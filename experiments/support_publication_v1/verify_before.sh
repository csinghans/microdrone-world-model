#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/../.."
"${PYTHON:-python}" - <<'PY'
import contextlib
import io
import json
import subprocess
import tempfile
import types
from pathlib import Path
from unittest.mock import patch

root = Path.cwd()
observations = {}
for name in ('eval_dataset_support', 'eval_veer_support'):
    path = root / 'eval' / (name + '.py')
    source = subprocess.check_output(['git', 'show', f'cbd4549:eval/{name}.py'], text=True)
    module = types.ModuleType('_before_' + name)
    module.__file__ = str(path)
    exec(compile(source, str(path), 'exec'), module.__dict__)
    with tempfile.TemporaryDirectory(prefix='support_publication_before_selftest_') as tmp:
        directory = Path(tmp)
        data, output = directory / 'data.npz', directory / 'report.json'
        data.write_bytes(b'synthetic input; metadata/analysis mocked')
        def invoke(destination, bad=False):
            result = {'n_frames': 0, 'n_rollouts': 0,
                      'world_stratified_bootstrap_support': {'supported': False, 'reason': 'fixture'}}
            if bad:
                result['unsupported'] = object()
            answer = (result, {}) if name == 'eval_veer_support' else result
            with patch('sys.argv', [name, '--data', str(data), '--out', str(destination)]), \
                 patch.object(module, 'load_metadata', return_value={}), \
                 patch.object(module, 'analyze', return_value=answer), \
                 contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                module.main()
        try:
            invoke(output, bad=True)
        except TypeError:
            pass
        else:
            raise AssertionError('fixture did not trigger serialization failure')
        assert output.exists() and output.stat().st_size > 0
        try:
            json.loads(output.read_text())
        except json.JSONDecodeError:
            pass
        else:
            raise AssertionError('unexpectedly complete report')
        try:
            invoke(output)
        except SystemExit as exc:
            assert exc.code == 2
        else:
            raise AssertionError('partial report did not block the retry')
        locked = directory / 'world_model.pth'
        (directory / 'artifacts.lock.json').write_text(json.dumps({'artifacts': [{'dest': locked.name}]}))
        with patch('world_model.checkpoint_io.ROOT', directory):
            invoke(locked)
        assert locked.is_file()
        observations[name] = {'failed_serialization_leaves_invalid_final_json': True,
                              'partial_report_blocks_new_attempt': True,
                              'absent_locked_destination_accepts_json': True}
expected = root / 'experiments/support_publication_v1/before.json'
if expected.exists():
    assert observations == json.loads(expected.read_text())
else:
    with expected.open('x') as stream:
        json.dump(observations, stream, indent=2)
        stream.write('\n')
print('SUPPORT PUBLICATION BEFORE VERIFIED: both CLIs expose partial JSON and accept an absent reserved destination')
PY

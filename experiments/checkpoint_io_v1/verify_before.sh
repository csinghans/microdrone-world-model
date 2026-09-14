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

import numpy as np

from scripts.dataset_identity_selftest import train_fixture

source = subprocess.check_output(
    ['git', 'show', '3884336:scripts/train.py'], text=True)
before = json.loads(Path('experiments/checkpoint_io_v1/before.json').read_text())
assert hashlib.sha256(source.encode()).hexdigest() == before['source']['sha256']
namespace = {'__name__': 'checkpoint_before_selftest'}
exec(compile(source, '3884336:scripts/train.py', 'exec'), namespace)
with tempfile.TemporaryDirectory(prefix='checkpoint_before_selftest_') as tmp:
    target = Path(tmp) / 'world_model.pth'
    sentinel = b'existing synthetic champion'
    target.write_bytes(sentinel)
    namespace['MODEL'] = str(target)
    namespace['train'] = train_fixture
    namespace['_load_or_make'] = lambda *a: {'frames': np.zeros((1,1,2,2,3))}
    args = SimpleNamespace(temporal=False, ground=False, two_frame=False,
        selftest=False, epochs=1, data=None, strips=None, latent_d=None,
        batch=2, seed=0, robust=False, ground_lambda=0.5,
        cf_hard_pool='legacy_masked', executed_moving_weight=1.0, out=None)
    with contextlib.redirect_stdout(io.StringIO()):
        namespace['train_world_model'](args)
    assert target.read_bytes() != sentinel
print('CHECKPOINT-BEFORE VERIFIED: old default replaced temporary sentinel; no fit')
PY

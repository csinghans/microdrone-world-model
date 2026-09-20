#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
"/Users/hans.chen/.cache/microdrone-research-venv/bin/python" -u - <<'PY'
import fcntl
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

root = Path.cwd()
config_path = root / 'experiments/artifactless_ci_v1/baseline.json'
config = json.loads(config_path.read_text())
checkout = Path(config['worktree'])
folder = root / config['output_dir']
folder.mkdir(parents=True, exist_ok=True)

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()

def now():
    return datetime.now(timezone.utc).isoformat()

def save(state):
    with tempfile.NamedTemporaryFile(mode='w', dir=folder, delete=False) as stream:
        json.dump(state, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
        temporary = stream.name
    os.replace(temporary, folder / 'state.json')

def primary_intact():
    return all(digest(root / row['path']) == row['sha256']
               for row in config['primary_artifacts'])

with (folder / 'worker.lock').open('a') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if (folder / 'state.json').exists():
        raise RuntimeError('attempt already exists; preserve it and register a new attempt')
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=checkout, text=True).strip()
    assert revision == config['source_commit']
    assert digest(checkout / '.github/workflows/ci.yml') == config['workflow_sha256']
    assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=checkout, text=True).strip()
    present = [row['path'] for row in config['primary_artifacts']
               if (checkout / row['path']).exists()]
    assert not present
    assert primary_intact()
    probe = """
import importlib, json
from pathlib import Path
root = Path.cwd().resolve()
origins = {}
for name in ('world_model', 'planner', 'datasets', 'eval', 'sim', 'skills', 'scripts'):
    module = importlib.import_module(name)
    paths = [str(Path(p).resolve()) for p in module.__path__]
    assert paths and all(Path(p).is_relative_to(root) for p in paths), (name, paths)
    origins[name] = paths
print(json.dumps(origins))
"""
    origins = json.loads(subprocess.check_output([sys.executable, '-c', probe], cwd=checkout, text=True))
    state = {'status': 'running', 'started': now(), 'worker_pid': os.getpid(),
             'source_commit': revision, 'config_sha256': digest(config_path),
             'worker_sha256': digest(root / 'experiments/artifactless_ci_v1/run.sh'),
             'locked_artifacts_present_at_start': present,
             'python': sys.executable, 'python_version': platform.python_version(),
             'platform': platform.platform(), 'package_origins': origins,
             'versions': {name: version(name) for name in
                          ('torch', 'numpy', 'stable-baselines3', 'sb3-contrib', 'pybullet')},
             'total': len(config['commands']), 'completed': [], 'active': None}
    save(state)
    code = 0
    for index, entry in enumerate(config['commands']):
        name = f"{index:03d}_{entry['argv'][2].replace('.', '_')}"
        log = folder / f'{name}.log'
        state['active'] = {'index': index, 'command': entry, 'started': now(), 'log': str(log)}
        save(state)
        print(f"START {index+1}/{state['total']} {' '.join(entry['argv'])}", flush=True)
        start = time.monotonic()
        with log.open('xb') as stream:
            try:
                process = subprocess.run([sys.executable, '-u', *entry['argv'][1:]], cwd=checkout,
                                         stdout=stream, stderr=subprocess.STDOUT,
                                         timeout=config['timeout_seconds'], check=False)
                code = process.returncode
            except subprocess.TimeoutExpired:
                code = 124
                stream.write(b'\nAUDIT TIMEOUT: command stopped at registered limit\n')
        row = {**state['active'], 'ended': now(), 'elapsed_seconds': time.monotonic()-start,
               'exit_code': code, 'log_sha256': digest(log), 'source_commit': revision}
        with (folder / f'{name}.json').open('x') as stream:
            json.dump(row, stream, indent=2)
            stream.write('\n')
        state['completed'].append(row)
        state['active'] = None
        save(state)
        print(f"EXIT={code} {index+1}/{state['total']} {entry['argv'][2]}", flush=True)
        if code:
            break
    intact = primary_intact()
    state.update(status='passed' if code == 0 and intact else 'failed', ended=now(),
                 exit_code=code if intact else 125, primary_artifacts_intact=intact,
                 tracked_changes=subprocess.check_output(
                     ['git', 'diff', '--name-only'], cwd=checkout, text=True).splitlines())
    save(state)
    print(f"ARTIFACTLESS-CI-DONE EXIT={state['exit_code']} "
          f"completed={len(state['completed'])}/{state['total']}", flush=True)
    sys.exit(state['exit_code'])
PY

#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python - <<'PY'
import json
from pathlib import Path

base = Path('experiments/schedule_layout_v1')
audit = Path('experiments/schedule_support_v1')
read = lambda p: json.loads(p.read_text())
frozen = read(base / 'manifest.json')['sources']
checks = {'scope': 'Saved audit versus original fit and exam receipts', 'fits': []}
for arm in ('legacy', 'world_balanced'):
    report = read(audit / f'{arm}.json')
    original = read(base / 'records' / f'{arm}_train.json')
    assert report['provenance']['dataset']['sha256'] in original['files'].values()
    for path, digest in report['provenance']['sources'].items():
        if path in frozen:
            assert digest == frozen[path], 'audit used changed training/index/oracle code'
    for seed, split in report['splits'].items():
        fit = read(base / 'records' / f'train_{arm}_{seed}.json')['result']['metrics']
        assert split['train']['valid_windows'] == fit['n_train']
        assert split['val']['valid_windows'] == fit['n_val']
        classless = []
        for world, row in split['val']['worlds'].items():
            if not row['labels_at_32']['auc_defined']:
                classless.append(world)
                if world in fit['auc_by_world']:
                    assert fit['auc_by_world'][world] == 0.5
        checks['fits'].append({'arm': arm, 'seed': int(seed), 'n_train': fit['n_train'],
                               'n_val': fit['n_val'], 'classless_val_worlds': classless})
exam = read(audit / 'holdout.json')
scores = read(base / 'records/score_legacy_0.json')['result']['scores']
assert exam['provenance']['dataset']['sha256'] == scores['provenance']['dataset']['sha256']
assert exam['all']['valid_windows'] == scores['n_val_samples']
for world, row in exam['all']['worlds'].items():
    assert {k: row['labels_at_32'][k] for k in ('positive', 'negative')} == scores['label_counts_by_world'][world]
checks['holdout_windows'] = scores['n_val_samples']
checks['status'] = 'PASS'
path = audit / 'verification.json'
if path.exists():
    assert read(path) == checks, 'saved verification differs; preserve it and investigate'
else:
    with path.open('x') as stream:
        json.dump(checks, stream, indent=2)
        stream.write('\n')
print('SCHEDULE-SUPPORT-VERIFIED: all six fit counts, classless fallbacks, independent exam')
PY

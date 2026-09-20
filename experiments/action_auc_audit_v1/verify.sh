#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python -m eval.eval_action_auc_audit --verify
python - <<'PY'
import json
from pathlib import Path

from datasets.provenance import file_identity

folder = Path('experiments/action_auc_audit_v1')
verification = json.loads((folder / 'verification.json').read_text())
for path, digest in verification['files'].items():
    assert file_identity(path)['sha256'] == digest
report = json.loads((folder / 'report.json').read_text())
auc_error = max(abs(sum(p['contribution'] for p in m['pairs']) - m['auc'])
                for row in report['worlds'].values() for m in row['models'])
delta_error = max(abs(d['within'] + d['across'] - d['auc'])
                  for row in report['worlds'].values() for d in row['paired_deltas'])
forward = {
    world: next(p['pairs'] for p in row['models'][0]['pairs']
                if p['positive_group'] == p['negative_group'] == 'forward')
           / row['models'][0]['within']['pairs']
    for world, row in report['worlds'].items()
}
assert auc_error == verification['max_auc_reconstruction_error'] <= 1e-12
assert delta_error == verification['max_delta_reconstruction_error'] <= 1e-12
assert forward == verification['forward_share_of_within_action_pairs']
assert verification['source_verdict'] == report['source_verdict'] == 'NO-GO'
print('ACTION-AUC RECEIPTS VERIFIED: report, summary, figure and exact decomposition')
PY

#!/usr/bin/env bash
set -euo pipefail

# Activate the project environment first. All output names are fixed by the
# registration; refuse existing data/results to prevent a silent remeasurement.
cd "$(dirname "$0")/../.."
python -m scripts.fetch_champions --check
python - <<'PY'
from pathlib import Path
import numpy as np
from PIL import Image
from datasets.generate_rollouts import gen

out = Path('output/metric_integrity_v1')
out.mkdir(parents=True, exist_ok=True)
path = out / 'holdout_64.npz'
if path.exists():
    raise SystemExit('registered dataset already exists; resume scoring manually')
fixture = gen(1, 90, seed=20260912, worlds=('classic',))
frame = fixture['frames'][0, 45]
assert frame.std() > 1, 'blank preflight frame'
# The fixed fixture contains a red pillar, visually checked before this run.
# Detect its actual rendered pixels, not merely scored obstacle coordinates.
red = frame[:, :, 0].astype(float)
rendered = (red > 1.5 * frame[:, :, 1]) & (red > 1.5 * frame[:, :, 2])
assert rendered.mean() > .05, 'registered obstacle not visible in the camera'
Image.fromarray(frame).save(out / 'instrument_frame.png')
print('METRIC-AUDIT-VISION OK: nonblank frame, rendered red obstacle')
data = gen(60, 160, seed=20260913, worlds=('classic', 'dense', 'moving'))
assert np.std(data['frames']) > 1, 'blank vision data'
with path.open('xb') as stream:
    np.savez_compressed(stream, **data)
print('METRIC-AUDIT-DATA OK')
PY

for arm in transit unified; do
  checkpoint=output/world_model.pth
  if [[ "$arm" == unified ]]; then
    checkpoint=output/world_model_unified.pth
  fi
  python -m eval.eval_wm_checkpoint --ckpt "$checkpoint" \
    --data output/metric_integrity_v1/holdout_64.npz \
    --independent-holdout --device cpu \
    --out "experiments/metric_integrity_v1/${arm}_scores.json" \
    --scores-out "output/metric_integrity_v1/${arm}_scores.npz"
  python -m eval.eval_auc_audit \
    --scores "output/metric_integrity_v1/${arm}_scores.npz" \
    --out "experiments/metric_integrity_v1/${arm}_audit.json"
done
python -m scripts.fetch_champions --check
echo METRIC-AUDIT-DONE

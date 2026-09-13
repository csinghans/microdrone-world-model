#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
trap 'status=$?; echo "SCHEDULE-SUPPORT-EXIT=$status"' EXIT
for arm in legacy world_balanced; do
  python -m eval.eval_dataset_support \
    --data "output/schedule_layout_v1/${arm}_train/data.npz" \
    --out "experiments/schedule_support_v1/${arm}.json" \
    --seeds 0,1,2 --epochs 80 --batch 64
done
python -m eval.eval_dataset_support \
  --data output/schedule_layout_v1/holdout/data.npz \
  --out experiments/schedule_support_v1/holdout.json --independent-holdout
echo SCHEDULE-SUPPORT-DONE

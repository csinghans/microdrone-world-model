#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
trap 'status=$?; echo "EXECUTED-WEIGHT-EXIT=$status"' EXIT
python -u -m scripts.schedule_layout_study --campaign executed_weight_v1 --run
echo EXECUTED-WEIGHT-DONE

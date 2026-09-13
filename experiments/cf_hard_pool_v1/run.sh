#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
trap 'status=$?; echo "CF-HARD-POOL-EXIT=$status"' EXIT
python -u -m scripts.schedule_layout_study --campaign cf_hard_pool_v1 --run
echo CF-HARD-POOL-DONE

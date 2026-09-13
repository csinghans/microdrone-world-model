#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
trap 'status=$?; echo "SCHEDULE-LAYOUT-EXIT=$status"' EXIT
python -u -m scripts.schedule_layout_study --run
echo SCHEDULE-LAYOUT-DONE

#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/../.."
mkdir -p output/moving_timing_v1
finish() {
    result=$?
    printf '%s\n' "$result" > output/moving_timing_v1/EXIT
    echo "MOVING-TIMING EXIT=$result"
    if [ "$result" -eq 0 ]; then
        echo "moving-timing-DONE"
        touch output/moving_timing_v1/DONE
    fi
}
trap finish EXIT
"${PYTHON:-python}" -u -m scripts.moving_timing_study --run

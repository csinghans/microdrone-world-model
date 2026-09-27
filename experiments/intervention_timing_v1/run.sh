#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/../.."
mkdir -p output/intervention_timing_v1
finish() {
    result=$?
    printf '%s\n' "$result" > output/intervention_timing_v1/EXIT
    echo "INTERVENTION-TIMING EXIT=$result"
    if [ "$result" -eq 0 ]; then
        echo "intervention-timing-DONE"
        touch output/intervention_timing_v1/DONE
    fi
}
trap finish EXIT
"${PYTHON:-python}" -u -m scripts.intervention_timing_study --run

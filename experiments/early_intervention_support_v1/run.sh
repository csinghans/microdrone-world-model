#!/bin/bash
# Launch with PYTHON=/absolute/path/python; preserve full log and true status.
set -euo pipefail
cd "$(dirname "$0")/../.."
mkdir -p output/early_intervention_support_v1
finish() {
    result=$?
    printf '%s\n' "$result" > output/early_intervention_support_v1/EXIT
    echo "EARLY-INTERVENTION EXIT=$result"
    if [ "$result" -eq 0 ]; then
        echo "early-intervention-DONE"
        touch output/early_intervention_support_v1/DONE
    fi
}
trap finish EXIT
"${PYTHON:-python}" -u -m scripts.early_intervention_study --run

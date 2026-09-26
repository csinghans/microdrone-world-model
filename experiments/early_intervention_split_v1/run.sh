#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/../.."
mkdir -p output/early_intervention_split_v1
finish() {
    result=$?
    printf '%s\n' "$result" > output/early_intervention_split_v1/EXIT
    echo "TIMING-SPLIT EXIT=$result"
    if [ "$result" -eq 0 ]; then
        echo timing-split-DONE
        touch output/early_intervention_split_v1/DONE
    fi
}
trap finish EXIT
"${PYTHON:-python}" -u -m experiments.early_intervention_split_v1.audit --run

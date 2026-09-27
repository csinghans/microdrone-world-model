#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/../.."
"${PYTHON:-python}" -u -m experiments.timing_mixture_audit_v1.audit --run

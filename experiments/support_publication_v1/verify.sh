#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/../.."
bash experiments/support_publication_v1/verify_before.sh
bash experiments/support_publication_v1/verify_compatibility.sh
"${PYTHON:-python}" - <<'PY'
import hashlib
import json
import subprocess
from pathlib import Path
from scripts.schedule_layout_study import verify_files

folder = Path('experiments/support_publication_v1')
receipt = json.loads((folder / 'verification.json').read_text())
for key in ('frozen_files', 'logs', 'locked_artifacts'):
    verify_files(receipt[key])
for path, digest in receipt['instrument_sources'].items():
    original = subprocess.check_output(['git', 'show', f"{receipt['instrument_commit']}:{path}"])
    assert hashlib.sha256(original).hexdigest() == digest, path
print('SUPPORT PUBLICATION ARCHIVE OK: original instrument sources, frozen evidence and protected artifacts')
PY

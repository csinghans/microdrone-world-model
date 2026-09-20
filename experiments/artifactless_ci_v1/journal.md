# Artifactless local CI-command audit — 2026-09-20

**All 116 commands exited 0 on the first attempt:** 97 from the workflow's
pure-math group and 19 from its simulation group. The last two commands
downloaded and hash-verified all nine champions in the isolated checkout,
then passed the gap-flight doctor. No code fix, retry or weaker assertion
was needed. This is local validation of source `d845f79`, not a remote CI run.

The [definition](definition.md), [frozen command list](baseline.json) and
fail-fast [worker](run.sh) were committed at `0980633` before launch. The
detached checkout began without any of the nine locked artifacts. All
project package imports were verified inside that checkout; no primary
workspace checkpoint or corpus was copied into it. Each selftest could
create its own stand-ins, as it would in a fresh clone. The final fetch log
records downloads for all nine locked files, not reuse of primary artifacts.

The [complete receipt](baseline_result.json) records every command, full-log
hash, exit code, elapsed time and source revision, plus package origins and
runtime versions. Total recorded wall time was 90.76 seconds on this host.
The checkout's tracked files and Git status remained clean. All nine
primary-workspace artifact hashes matched before and after the attempt.

The real doctor reports `ok: true`. It retains the existing, nonfatal
`guard:sweep@2.0` sample-size warning (the frozen skill uses n=30; the doctor
recommends n=60). This audit did not change that historical skill or its
bars. Gymnasium emitted its normal float32-bound precision warnings.

Runtime: macOS 26.5.2 arm64, Python 3.14.5, torch 2.14.0, NumPy 2.5.3,
stable-baselines3/sb3-contrib 2.9.0 and pybullet 3.2.7. The workflow declares
Linux/Python 3.12 and CPU torch, so this does not establish platform parity.
Dependency installation and the separate optional training-smoke job were
not run. Selftest-internal small fits/simulation are wiring checks, not new
research draws or model-performance evidence.

Verification:

- `bash experiments/artifactless_ci_v1/verify.sh` checks the committed
  receipt, exact command order against the frozen Git workflow and isolated
  import paths. It requires no model artifact or simulator execution.
- Add `--local` to also check all retained full-log hashes and all nine
  primary model hashes. Logs and per-command receipts live in
  `output/artifactless_ci_v1/baseline/`; the final worker marker is
  `ARTIFACTLESS-CI-DONE EXIT=0 completed=116/116`.
- The checkout is retained at
  `/Users/hans.chen/.cache/microdrone-artifactless-ci-20260920` for inspection.
  The worker rejects reusing its attempt directory, preserving the original
  record. Any future attempt needs a separately recorded configuration.
- Primary-workspace `black --check .` (172 Python files), `ruff check .`
  and `git diff --check` also pass after recording the audit.

No release was tagged, branch pushed, remote workflow dispatched or
scientific verdict revised.

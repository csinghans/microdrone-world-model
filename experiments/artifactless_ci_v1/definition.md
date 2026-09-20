# Artifactless local CI-command audit — 2026-09-20

Run the two selftest command groups from `.github/workflows/ci.yml` in their
declared order, starting from a detached checkout with none of the nine
locked artifacts present. The optional training-smoke job is excluded.
Commands may create their own explicitly scoped selftest stand-ins; the
workflow's final champion-fetch step may download locked assets into the
isolated checkout. Never copy models or corpora from the primary workspace.

This is a local artifact-dependency audit, not a claim of GitHub Actions
success or equivalence to its Linux/Python 3.12 runtime. The existing local
Python 3.14 environment and actual package versions are recorded. Verify
all project package imports resolve inside the detached checkout.

Use a persistent, sequential, fail-fast worker. Record every full command
log, exit code, duration and source revision. Stop at the first error or
30-minute per-command timeout. Preserve failed attempts; any fix/retry must
be separately recorded, never replace a previous log or count a failure as
a scientific negative. Do not lower numeric selftest assertions to get a
green run. There is no research gate, model promotion or release tag here.

Check the primary workspace's locked-artifact hashes before and after the
attempt. The worktree is retained for diagnosis and follow-up. The worker
does not commit source changes or publish to remote services.

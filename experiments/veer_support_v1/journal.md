# Veer support instrument audit

## 2026-09-14 — compatibility verified

The [definition](definition.md) was saved before running the compatibility
audit. This work makes probe support available before future fits, using
the exact geometric selector now shared with training/checkpoint scoring.
It does not run a new model experiment or change any closed verdict.

The [verification receipt](verification.json) compares the original
`016dc94:world_model/training.py` function with the extracted selector.
The original function is stopped before its first tensor construction;
only shape placeholders are supplied for frames. No pixels, checkpoints or
model predictions are read for this audit.

| Saved corpus | Eligible frames | Courses | Archived exports matched |
|---|---:|---:|---:|
| CF exam | 208 | 23 | 6 |
| Executed-weight exam | 190 | 20 | 6 |
| Shared training corpus | 53 | 10 | 0 |

All ordered `(rollout, time)` pairs, safer-side truths and world IDs agree.
The two exam receipts also record the input/export/source hashes:
[CF support](cf_hard_pool_v1.json),
[executed-weight support](executed_weight_v1.json).

CF has two moving probe courses. Executed-weight has one, which reproduces
the existing comparator's reason for undefined world-stratified intervals.
Neither exam has room probe support: this is a yaw-zero pillar oracle.
Two courses in each *observed* stratum is only the comparator's structural
minimum, not adequate precision or a claim about absent worlds. Geometric
selection also does not prove that the camera rendered the corresponding
scene. Keep the separate visual instrument check.

Use the preflight on a future registered exam before fitting:

```bash
python -m eval.eval_veer_support --data path/to/exam.npz --out path/to/preflight.json
```

The output must be new. An insufficient exam is reported, not expanded or
replaced. Freeze required worlds, minimum support and the response to an
insufficient exam in that future registration. No support bar is added to
any historical study. Training recipes and the deployed model shapes are
unchanged; this does not claim a performance improvement.

Validation:

- `python -m world_model.veer_probe`: asymmetric/symmetric geometry, cruise
  filtering, FOV rejection, missing/zero pillar velocities, moving threat,
  empty rooms and ordered/subset selection.
- `python -m scripts.veer_probe_selftest`: exact single/two-frame/GRU input
  construction, normalized actions, memory residual base, ties, empty
  probes without model calls and unchanged Torch RNG state. Toy callables;
  no fitting or checkpoint access.
- `python -m eval.eval_veer_support --selftest`: singleton/zero/sufficient
  structural support, source/export identity, changed truth rejection and
  no-overwrite behavior. An unreadable object-valued frame payload proves
  that the CLI never loads pixels.
- `python -m eval.eval_wm_checkpoint --selftest`: existing two-epoch
  integration passes with selftest-only artifacts, including both optional
  training recipes. Full log:
  `output/research_integrity_selftest/veer_probe_checkpoint_selftest.log`;
  actual process exit 0.
- `bash experiments/veer_support_v1/verify.sh`: original geometry and
  twelve immutable export identities; no scoring or bootstrap. Full log:
  `output/research_integrity_selftest/veer_support_parity.log`; exit 0.
- Both closed-study report selftests and the shared study-runner selftest
  pass. New synthetic checks are included in manual CI. No remote push,
  CI dispatch or release tag is claimed.
- Whole-repository `black --check .` (165 Python files), `ruff check .` and
  `git diff --check` pass. All nine `artifacts.lock.json` assets verify,
  including both protected world-model hashes, before and after the work.

Historical registrations, records and their NO-GOs remain unchanged.

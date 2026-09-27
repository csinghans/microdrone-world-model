# Veer replay v1 journal

## 2026-09-28 — declared instrument replay, closed

- Registration and definition committed at `ce80edb`, before new inference.
  This is an addition to the closed moving_timing_v1 exam, not a new model
  comparison or gate. Six checkpoint hashes were checked against the old
  training receipts. The exporter change is separately recorded at `97479a3`.
- Instrument and seven first-pass preflight checks committed at `6c4efa2`.
  The artifactless replay selftest joins manual CI. Local checks passed;
  remote CI was not dispatched because nothing was pushed.
- A fresh manifest freezes 193 current source/config files, 16 registered
  inputs, runtime and all nine protected hashes before loading exam pixels
  and running inference. It does not rewrite the original study's source
  manifest, which predates the exporter changes.
- Actual probe pixels pass the nonblank test before model calls. Metadata
  geometry reproduces the original full ordered probe for every model.
- Each fixed checkpoint is loaded on CPU and evaluated once with the
  original 1,347-frame batch and frame recipe. Raw arrays are saved before
  correctness parity is enforced. Every pair, world, label and correctness
  flag matches, so no mismatch stop is triggered. The complete run exits 0.
- A separate `--verify` process uses metadata and saved raw probabilities,
  with no model call. It rechecks all input/source/protected/output hashes,
  schema, old-export parity, strict comparisons and all 54 cells; exit 0.
  No rerun, seed selection or added exam course occurred.
- All six models have zero exact ties on all three transit worlds. Moving
  candidate right rankings are 102/99/99 versus controls 28/66/72. The
  truth-side counts identify opposite-side errors where the old flags alone
  could not. This is descriptive evidence, not a training-cause finding.
- Full logs, actual process exits, hashes, raw probabilities and report are
  archived. The five original NO-GOs, default recipe and champions stand.
  No model/flight study or deployment is released.

See [summary](summary.md), [preflight](preflight.json),
[process exits](process_exits.json) and [verification](verification.json).

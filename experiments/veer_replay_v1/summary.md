# Fixed-checkpoint veer replay v1

**Exact probe parity; no exact ties.** All six fixed moving_timing_v1 models
reproduce every original pair, world, safer-side label and strict correctness
flag on the complete 1,347-frame probe. Each model uses the same exam, not
an additional independent sample. The 54 registered model/world/timing cells
and their truth-side splits are in [report.json](report.json); all six raw
probability exports are archived in `artifacts/`.

On moving's 134 frames / 16 courses, the exact direction counts are:

| Seed | Control strict-left | Candidate strict-left | Control strict-right | Candidate strict-right | Ties, either arm |
|---|---:|---:|---:|---:|---:|
| 0 | 106 | 32 | 28 | 102 | 0 |
| 1 | 68 | 35 | 66 | 99 | 0 |
| 2 | 62 | 35 | 72 | 99 | 0 |

Strict-left/right means that side has the lower predicted warn probability;
these are hypothetical-command rankings, not executed policy actions. No
exact ties occur in classic or dense either. Thus incorrect flags on this
fixed probe correspond to opposite-side rankings. The older diagnostic's
tie-aware bounds were necessary given its inputs, and remain valid; the new
measurements now identify the exact counts within those bounds.

On the 101 moving frames whose oracle safer side is left, right-ranked
counts rise 19→76, 37→69 and 50→68. On the 33 safer-right frames, correct
right ranks rise 9→26, 29→30 and 22→31. This resolves the tie ambiguity for
these checkpoints and this exam. It does not identify which training
exposure or gradient caused the directional change, establish behavior on
new courses, or change the registered frame-weighted NO-GO.

All 1,347 actual probe frames pass the preregistered nonblank check:
minimum pixel standard deviation 51.33339209928648, above 1.0. Original
geometry selection is identical. Seven preflight checks, the single CPU
replay and saved-array-only verification exit 0. All 16 registered inputs,
193 current source/config files and nine protected artifacts remain
unchanged across replay. Raw arrays total 85,449 bytes; no model parameters
or deployment components changed. The prior 137.29 KB / estimated 7.71 ms
model bill is unchanged; no new hardware or flight measurement is claimed.

The original five studies remain NO-GO. No fit, new course, optional rerun,
interval, margin bin or replacement gate was used. A next research decision
can examine training exposure using a separately declared metadata audit;
no training knob is released by this replay.

To verify saved results without inference, use the replay's source snapshot
(instrument commit `6c4efa2`, or its result-closure commit) and the exact
registered local inputs:

```bash
python -m experiments.veer_replay_v1.replay --selftest
python -m experiments.veer_replay_v1.replay --verify
```

The manifest deliberately binds the source inventory and runtime. Later
source changes require checking out the original snapshot, not editing the
manifest. `--run` refuses the occupied output path; the completed inference
must not be repeated opportunistically.

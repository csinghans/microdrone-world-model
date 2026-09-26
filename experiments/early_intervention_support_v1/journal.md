# Early-intervention support pilot journal

## 2026-09-27 — Registration

Frozen before generating either arm. Prior held-command audit recovered
windows without adding training action/class course coverage. This pilot
tests intervention timing on paired, isolated random streams. No training
is authorized by its outcome. Definition, seed, counts, instrument checks,
support minima and negative-result response are committed first.

## Instrument preflight

Registration commit: `b56e007`. The new generator options retain shared RNG
and approach timing as defaults, including the old NPZ schema. Synthetic
tests check original schedule draws/RNG state, shifted command sequences,
stream isolation, and rejection of damaged pairing metadata. CI includes
the self-contained study selftest; no champion loads or fitting are needed.

The eight-command preflight passed, including 10 existing publication
regressions, 15 support-requirement regressions, dataset-support and schedule
selftests, whole-repository Black (178 Python files), Ruff and diff check.
Full log: `output/research_integrity_selftest/early_intervention_v1_preflight.log`.
Initial development lint found two unused imports; both were removed before
this preflight and before any generation. The registered simulator parity
and vision checks are the first two stages of the persistent queue.

Reproduce with `PYTHON=/path/to/python bash
experiments/early_intervention_support_v1/run.sh`, preserving full stdout and
stderr. The runner locks against duplicate processes, reuses only receipts
whose hashes verify, and refuses unfinished stage directories. `EXIT` and
`DONE` in its output directory retain process completion state.

## 2026-09-27 — Completed: candidate support sufficient

Instrument commit `1ebacca`; all six stages exited 0 on their first actual
execution. An initial shell background dispatch produced no runner output
or stage; a detached process then ran the queue once. The complete log is
`output/early_intervention_support_v1/run.log`, with final `EXIT=0` and
`early-intervention-DONE`. No worker remains. The four rendering fixtures
passed before any pilot generation; the moving fixture observes the
crosser at its centerline. Four small compatibility fixtures (both role
layouts, with/without randomization) match the pre-change generator exactly
in schema, dtype and every array, including pixels.

The two arms contain **180 paired scenes**, each flown twice. These are
360 simulated trajectories, not 360 independent scene draws. All scene
identities, speeds, initial pixels/positions, passive trajectories, roles
and shifted command prefixes pass exact pairing checks. Each world has
60 courses, including 20 passive; classic has 30 clear courses per arm.

Both veers in dense and moving pass all four candidate minima (20 positive
and 20 negative windows; 3 positive and 3 negative courses per action).
The control fails only dense veer-right: 12 negative windows from 1 course.
The candidate has 148 such windows from 7 courses. Full counts, including
all six actions in every world, are in [summary.md](summary.md) and the two
support reports; every check/deficit is retained in the requirements receipts.

| Required world/action | Control positive/negative courses | Immediate positive/negative courses |
|---|---:|---:|
| dense / veer_left | 9 / 3 | 6 / 7 |
| dense / veer_right | 13 / 1 | 12 / 7 |
| moving / veer_left | 8 / 10 | 9 / 15 |
| moving / veer_right | 9 / 6 | 6 / 11 |

Here negative means no warn-radius crossing in the inclusive horizon-32
window, not successful flight or certified safety. Total eligible windows
are 12,339 control and 13,331 immediate. More useful steering coverage comes
with a tradeoff: forward negative-course counts fall from 45→33 classic,
32→24 dense, and 49→28 moving. Some positive-course counts also fall; the
complete table prevents treating extra safe steering labels as a universal
coverage improvement. Count minima establish presence, not statistical
power, train/validation support or model generalization.

This closes the pilot as **structurally sufficient**, with no fit,
inference, bootstrap, deployment change, extra seeds or promotion. The
shared RNG / approach recipe remains the default. A future separately
registered timing study must freeze seed-partition support and forward,
room/now/veer guards before fitting; this pilot alone releases none of it.
All earlier NO-GOs remain closed. Offline data tooling adds no deployed
parameters, RAM or inference work; the embedded target still needs its own
measurements.

## Verification and replay

`python -m scripts.early_intervention_study --verify` checked all receipts
and file identities, reloaded both pixel corpora to reassert pairing, and
recomputed both metadata-support reports and every requirement result.
It exited 0 without regenerating scenes or changing recorded results.
The additional mocked CLI check confirms both new flags reach the generator.
All nine locked artifact SHA values match before and after the full queue.
Validation is local macOS / Python 3.14, not remote Linux / Python 3.12 CI.

Run `bash experiments/early_intervention_support_v1/verify.sh` with the
recorded environment and source snapshot; it additionally checks the
unaltered committed copies and [verification.json](verification.json).
The full source manifest intentionally rejects later source/runtime drift.
Likewise, the older held-command audit's strict verifier requires its
original source snapshot now that the generator has new explicit options;
its frozen inputs, counts and results have not been rewritten.

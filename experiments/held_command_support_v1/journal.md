# Repeated-command boundaries add windows, not training-course coverage

The [definition](definition.md) and [input registration](registration.json)
were committed at `b8887ec`, before counting the additional windows. The
instrument and synthetic selftest were committed at `a4e343b` before the
first corpus audit. This is retrospective: prior model outcomes were known.
No new performance gate, model inference, resampling or training followed.

The mechanism is present. The shared training corpus contains **1,681**
additional horizon-32 windows whose commanded four-vectors stay exactly
constant across recorded segment boundaries: 8,428 original → 10,109 union
(about 20% more windows). But **none** of the per-world/action positive or
negative distinct-course counts increases. The recovered windows come from
53 already represented courses; they do not create new independent trials.

| Training world | Additional windows | What this adds |
|---|---:|---|
| classic | 341 | More windows from already supported action/class courses |
| dense | 373 | No new negative-course coverage; slow, both veers and climb still have zero negative courses |
| moving | 83 | Forward 32, slow 19, climb 32; zero new windows for either veer |
| room | 884 | More windows, with every action/class course count unchanged |

The closed executed-weight exam has 2,191 additional available windows:
12,179 → 14,370. There are a few class/course coverage increases, but dense
veer-left still has no negative windows and moving veer-right recovers no
windows. These windows were **not** added to any archived score, interval or
guard. All original model verdicts remain NO-GO. Every action, including
unobserved room scan/lift actions, appears in the [generated summary](summary.md)
and [full count report](report.json).

This weakens the case for using repeated-command recovery alone to address
the current steering-support limitation on this training corpus. It does
not establish that extra overlapping supervision can never improve a model.
No training knob is released by this audit. A future action-specific study
needs suitably varied courses and frozen support requirements; it cannot
claim new independent evidence just from admitting more windows.

A future implementation must also preserve the original split identity:
passive stratification uses `seg.max()==0`, so rewriting segment IDs can
change the partition. At fixed epochs, extra training windows can increase
optimizer steps and CF/now sampling. Those effects belong in a new recipe
and registration, not a retrospective change to this corpus or any gate.

Verification:

- `python -m eval.eval_held_command_support --selftest` checks an explicit
  per-window oracle at horizons 1/4/8/32, actual switches, repeated commands,
  the existing inclusive endpoint, exact equality down to a floating-point
  increment, both action catalogs and malformed metadata. A hand-counted
  example verifies positive/negative course overlap and newly covered
  classes; an NPZ with unreadable object-valued frames verifies metadata-only
  loading. This selftest is included in manual CI's fast group.
- For both fixed corpora, original pairs and warn labels exactly match
  `_index_samples`, and every world's original class counts match the
  committed generation receipt. Actions match their catalog vectors and
  speeds; accepted original windows contain constant commands. Input and
  reference-source hashes are checked before and after analysis.
- `bash experiments/held_command_support_v1/verify.sh` recomputes only saved
  metadata accounting, compares the existing report/summary and verifies the
  frozen file hashes. It fits no model and overwrites no artifact.
- The first instrument check passed its selftest and Black, then Ruff found
  eight overlong display strings. That log is retained; splitting the strings
  fixed lint before the instrument commit and before any corpus counting.
  The final whole-repo Black (177 files), Ruff and whitespace checks pass.
- The first corpus run and subsequent fixed-input verification exit 0.
  Full log/source/input/output identities and the nine unchanged locked
  artifact hashes are in [verification.json](verification.json).

This audit adds no deployed parameters, RAM requirement or inference work
to the 512 KB / approximately 8 ms target. It measures available commanded
intent in saved metadata, not rendered perception, statistical power,
hardware latency or flight performance. No new research corpus, archived
result edit, remote push or release was performed.

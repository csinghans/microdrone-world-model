# Executed/CF agreement v1 — fixed metadata diagnostic

The timing model study and timing-mixture audit are closed and unblinded.
The remaining dense-right loss occurs inside the immediate exam block in
all three seeds. This diagnostic tests a candidate explanation: the executed
trajectory and kinematic counterfactual (CF) losses may assign conflicting
warn@32 targets to the same recorded frame and commanded action.

Freeze this scope before computing agreement. Use only the two existing
276-course timing-study training corpora and its 1,440-course common exam.
No new pixels, model scores, inference, training, generation or bootstrap.
Do not change the oracle, stored labels, original index, splits or verdicts.

Instrument checks precede interpretation: fixed horizons [4,8,16,32], warn
radius 0.7, CTRL_HZ 48, dataset/catalog/command identities and finite transit
positions/distances. Reconstruct recorded instantaneous transit clearances
from saved positions and pillars drifting by t/48 times their velocities,
using the empty-pillar sentinel 9.0. Require maximum error ≤1e-4 metres per
input; otherwise archive instrument failure and stop the diagnostic. Room
clearances use different geometry and are excluded from this comparison.

For each original primary cell (dense/moving × left/right):

- At each fixed training seed 0/1/2, inspect only that arm's original training
  courses and eligible held-command windows. Preserve exact memberships.
- In the exam, inspect the approach and immediate blocks separately. Keep
  their course identities and fixed boundaries; do not select extra slices.
- Join the stored executed warn@32 label to CF warn@32 for that exact
  frame's executed action and speed. Count the full 2×2 executed/CF label
  matrix separately for answerable and masked CF frames, with windows and
  distinct contributing courses in every cell. Record disagreement rate
  among answerable windows, with null for an empty denominator. Missing
  classes or small counts remain visible, not replaced by a fallback.

Masked CF labels receive no CF loss and are not counted as direct conflicting
supervision. Counts on answerable windows describe available conflicting
targets, not actual sampled loss/gradient mass or proof of a learned mechanism.
Windows overlap and course counts across matrix cells can overlap. The
kinematic oracle idealizes commanded velocity; flown PID trajectories need
not follow it exactly. A disagreement is not by itself an implementation bug.

For every input's full geometric veer probe, report support by transit world,
agreement between its safer-side truth and CF left/right warn@32 labels,
and whether both candidate labels are answerable. Also report frame/course
intersection between each primary action's held windows and the geometric
probe. This checks the relationship of the two metrics' domains; it cannot
compare hypothetical flown left/right futures, since no forks are generated.

Archive every input/seed/cell and all instrumentation readings. All zero or
negative findings close the diagnostic just as informative ones do. Preserve
the model-study NO-GO, approach default and all nine locked artifacts. No
outcome releases a fit, changes a bar, establishes causality or certifies
flight. Additional slicing or a training intervention needs a new scope or
registration, respectively.

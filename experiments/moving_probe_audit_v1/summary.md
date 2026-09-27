# Moving probe audit v1 — exploratory findings

All 27 world/timing/seed cells and the twelve original pooled/world probe
aggregates reconstruct from the unchanged saved exports. Maximum accounting
error is **6.94e-17**. Both the first run and
its exact numeric verification exit 0. The closed model-study verdict remains
**NO-GO**; this audit introduces no performance gate or model inference.

## Where moving loses correctness

The moving probe has 134 frames from 16 courses: approach contributes 32
frames / five courses and immediate 102 / eleven. The immediate block has
a larger negative frame-accuracy delta in every seed; the approach block
improves at seed 0 and declines at seeds 1/2. These post-hoc block readings
have sparse course support, especially by truth direction, and no new
confidence or power claim is made.

| Moving block | Seed | Control correct | Candidate correct | Lost / gained frames | Declining / improving / unchanged courses | Frame delta | Equal-course delta |
|---|---:|---:|---:|---:|---:|---:|---:|
| approach | 0 | 15/32 | 17/32 | 5 / 7 | 2 / 2 / 1 | +0.062500 | +0.092857 |
| approach | 1 | 20/32 | 17/32 | 5 / 2 | 3 / 0 / 2 | −0.093750 | −0.164286 |
| approach | 2 | 19/32 | 18/32 | 3 / 2 | 2 / 1 / 2 | −0.031250 | +0.019048 |
| immediate | 0 | 76/102 | 34/102 | 54 / 12 | 7 / 1 / 3 | −0.411765 | −0.371056 |
| immediate | 1 | 73/102 | 45/102 | 30 / 2 | 5 / 2 / 4 | −0.274510 | −0.151954 |
| immediate | 2 | 54/102 | 46/102 | 16 / 8 | 5 / 3 / 3 | −0.078431 | +0.070141 |
| all | 0 | 91/134 | 51/134 | 59 / 19 | 9 / 3 / 4 | −0.298507 | −0.226083 |
| all | 1 | 93/134 | 62/134 | 35 / 4 | 8 / 2 / 6 | −0.231343 | −0.155807 |
| all | 2 | 73/134 | 64/134 | 19 / 10 | 7 / 4 / 5 | −0.067164 | +0.054174 |

Across all moving frames, candidate correctness decreases on 9/8/7 of the
16 courses at seeds 0/1/2, while 3/2/4 courses improve. The equal-course mean
delta is negative at seeds 0/1 but positive at seed 2. At seed 2 this differs
from the registered frame-weighted decline: course length affects the result.
This is a different descriptive estimand, not a replacement gate or a rescue
of the original failure. Every course and additive contribution is retained
in [report.json](report.json); no course was excluded.

## Safer-side asymmetry and what the export can identify

Across moving, 101 frames / eleven courses have safer-left truth and 33
frames / five courses have safer-right truth. The immediate block contributes
79 left-truth frames / eight courses and 23 right-truth frames / three courses.
The approach block has 22/3 left and 10/2 right. A constant strict-left
reference would match 101/134 = 0.753731 of this fixed probe; constant right
would match 0.246269. These describe the selected truth distribution, not
flight policies, a chance-significance test or a new success criterion.

| Seed | Correct on safer-left frames: control → candidate | Correct on safer-right frames: control → candidate | Strict-left count bounds: control → candidate | Candidate strict-right count bounds | Candidate possible ties |
|---|---:|---:|---|---|---|
| 0 | 82 → 25 (of 101) | 9 → 26 (of 33) | [82, 106] → [25, 32] | [26, 102] | [0, 83] |
| 1 | 64 → 32 (of 101) | 29 → 30 (of 33) | [64, 68] → [32, 35] | [30, 99] | [0, 72] |
| 2 | 51 → 33 (of 101) | 22 → 31 (of 33) | [51, 62] → [33, 35] | [31, 99] | [0, 70] |

Left-truth correctness falls in all seeds, while right-truth correctness
rises. The strict-left preference bounds do not overlap between control
and candidate in any seed: fewer strict-left rankings are identifiable
even without margins. This does **not** identify how much of the change is
a strict-right preference versus equal predicted scores. The strict-right
bounds overlap between arms, and none of the possible tie counts is an
observed tie measurement. Marginal bounds cannot all be attained jointly.

The scoring implementation uses `p_left < p_right` for left-truth success
and the reverse strict inequality for right-truth success. A tie fails
either case. Existing exports retain truth and correctness only, so coding
every error as an opposite-direction decision would fabricate observations.
No missing probabilities or margins were inferred.

## All registered world/block readings

Frame-accuracy deltas below use each cell denominator; the report separately
preserves contributions under each full-world denominator.

| World / block | Frames / courses | Left-truth / right-truth frames | Seed 0 delta | Seed 1 delta | Seed 2 delta |
|---|---:|---:|---:|---:|---:|
| classic / approach | 164 / 30 | 91 / 73 | −0.298780 | −0.103659 | +0.164634 |
| classic / immediate | 184 / 25 | 88 / 96 | −0.108696 | +0.114130 | +0.173913 |
| classic / all | 348 / 55 | 179 / 169 | −0.198276 | +0.011494 | +0.169540 |
| dense / approach | 515 / 55 | 243 / 272 | +0.106796 | +0.005825 | +0.025243 |
| dense / immediate | 350 / 36 | 194 / 156 | +0.222857 | +0.011429 | +0.108571 |
| dense / all | 865 / 91 | 437 / 428 | +0.153757 | +0.008092 | +0.058960 |
| moving / approach | 32 / 5 | 22 / 10 | +0.062500 | −0.093750 | −0.031250 |
| moving / immediate | 102 / 11 | 79 / 23 | −0.411765 | −0.274510 | −0.078431 |
| moving / all | 134 / 16 | 101 / 33 | −0.298507 | −0.231343 | −0.067164 |

## Interpretation and continuation

This locates an observed failure in the immediate block and left-truth
examples, and shows the frame-versus-course weighting distinction. It does
not explain which training targets, batches or gradients caused it. No new
data, images, fit, inference, bootstrap or cross-study score comparison was
used. The architecture, 512 KB / approximately 8 ms constraints and all nine
protected artifacts are unaffected. The old NO-GO and default recipes stand.

For future measurements, retain the two raw veer scores alongside strict
correctness so exact ties and directional preferences are observable. Such
an exporter change requires compatibility tests; rescoring fixed checkpoints
would require its own declared instrument study. This audit releases neither
rescoring nor training and claims no direction-collapse mechanism.

Run `python -m experiments.moving_probe_audit_v1.audit --verify` for exact
reproduction from the frozen inputs. [Registration](registration.json),
[definition](definition.md), [preflight](preflight.json),
[verification](verification.json) and [journal](journal.md) preserve provenance.
The new Python module changes the old model study’s strict file inventory.
Its original 192 saved source hashes were all verified unchanged; that
manifest and every recorded number were left intact.

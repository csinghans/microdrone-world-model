# Moving-only timing v1 — NO-GO

All 22 stages completed on their first study execution with actual exit 0.
The support gate passed before six fresh 80-epoch fits and six CPU scorings.
Every checkpoint used the same new 1,440-course / 100,548-window exam.
Full verification recomputed the support reports, raw-score endpoints,
2,000-draw primary bootstraps and the decision with exact saved-result parity.
No additional fitting, inference, seed or course was used for verification.

The equal-weight moving left/right AUC@32 primary improves by
**+0.010130 on average**, below the frozen **+0.03** bar.
Seed 2 declines, violating the required positive improvement in every seed.
Moving geometric veer accuracy breaks its −0.05 guard in all three seeds.
Dense left-veer also declines beyond −0.02 in seeds 1/2, despite its training
data remaining identical between arms. These failures close **NO-GO**.

| Primary moving-action AUC@32 | Approach | Moving-only immediate | Delta | Conditional course-bootstrap 95% interval |
|---|---:|---:|---:|---|
| Seed 0 | 0.720687 | 0.765666 | +0.044979 | [+0.004744, +0.084784] |
| Seed 1 | 0.736188 | 0.761315 | +0.025127 | [−0.012608, +0.062211] |
| Seed 2 | 0.783309 | 0.743593 | −0.039716 | [−0.072277, −0.008291] |

The three-seed delta range is [−0.039716, +0.044979].
The +0.03 threshold applies to the three-seed mean; the per-seed primary
requirement is strictly greater than zero. Each fixed pair has 2,000 valid
bootstrap replicates and zero undefined ones, drawing all 210 moving courses
per timing block with shared course multiplicities across models/actions.
These intervals condition on the fixed checkpoint pair. They do not estimate
variation over training runs or modify any registered point-estimate gate.

## Every behavioral guard

Deltas are moving-only immediate minus approach. **Fail** marks a value
below its registered floor; a pass allows the stated tolerance, not a claim
of no decline. Exact baseline/candidate readings are retained in [report.json](report.json).

| Guard delta | Seed 0 | Seed 1 | Seed 2 | Floor |
|---|---:|---:|---:|---:|
| Moving action AUC: moving/veer_left | +0.033015 | +0.034241 | −0.039738 **fail** | -0.02 |
| Moving action AUC: moving/veer_right | +0.056944 | +0.016014 | −0.039693 **fail** | -0.02 |
| Dense action AUC: dense/veer_left | +0.082141 | −0.078838 **fail** | −0.049461 **fail** | -0.02 |
| Dense action AUC: dense/veer_right | −0.019044 | +0.008434 | +0.023203 | -0.02 |
| Moving timing-block AUC: moving/veer_left/approach | +0.023571 | +0.026093 | −0.067203 **fail** | -0.02 |
| Moving timing-block AUC: moving/veer_left/immediate | +0.015531 | +0.035698 | −0.023243 **fail** | -0.02 |
| Moving timing-block AUC: moving/veer_right/approach | +0.171305 | +0.030320 | −0.014341 | -0.02 |
| Moving timing-block AUC: moving/veer_right/immediate | −0.015281 | −0.008678 | −0.057686 **fail** | -0.02 |
| Pooled-world AUC: classic | +0.045559 | +0.044484 | −0.005053 | -0.02 |
| Pooled-world AUC: dense | +0.040365 | +0.017939 | −0.002977 | -0.02 |
| Pooled-world AUC: moving | +0.085071 | +0.126498 | −0.014237 | -0.02 |
| Pooled-world AUC: room | +0.041677 | +0.119591 | −0.002058 | -0.02 |
| Forward AUC: classic | +0.049811 | +0.080026 | −0.002128 | -0.02 |
| Forward AUC: dense | +0.051305 | +0.036404 | +0.002154 | -0.02 |
| Forward AUC: moving | +0.095337 | +0.170808 | −0.007511 | -0.02 |
| Danger-now AUC: all | +0.049011 | +0.048704 | −0.007992 | -0.02 |
| Geometric veer accuracy: all | +0.017817 | −0.014848 | +0.074981 | -0.05 |
| Geometric veer accuracy: classic | −0.198276 **fail** | +0.011494 | +0.169540 | -0.05 |
| Geometric veer accuracy: dense | +0.153757 | +0.008092 | +0.058960 | -0.05 |
| Geometric veer accuracy: moving | −0.298507 **fail** | −0.231343 **fail** | −0.067164 **fail** | -0.05 |

In total, 13 of 67 decision checks fail, including the primary mean and
seed-2 primary positivity. All pooled-world, forward and danger-now AUC
guards pass. Pooled geometric ranking also passes in all seeds while the
moving-world ranking guard fails in all seeds: pooled ranking would conceal
local loss. Classic ranking fails at seed 0. Dense-right action guards pass
in all seeds, but dense-left fails at seeds 1/2. At seed 2, both pooled moving
action guards and three of four moving timing-block guards fail.

All six architecture bills are equal: **137.290039 KB** analytic int8
memory, **3,856,768 MACs/decision**, and **7.713536 ms** at an assumed
0.5 GMAC/s. They pass the 512 KB / 8 ms bars. This does not measure hardware
latency, quantization parity or flight performance.

## Support and single-knob scope

The two 276-course development corpora have identical scene identities and
221/55 training/validation memberships at every registered seed. Candidate
data replaces only the 60 complete moving rows, including 20 passive rows
which remain identical. Classic/dense/room arrays are unchanged. Dense
steering training support remains sparse and is not claimed to be repaired.

All training/exam support floors passed before fits. Moving action-by-timing
exam cells have at least 22 positive and negative courses, above ten.
The geometric probe has 1,347 frames / 162 courses: classic 348/55, dense
865/91, moving 134/16. These are coverage floors, not power or deployment
guarantees. See [the preflight](preflight.md) and [complete counts](support/).

| Arm | Seed | Training windows | Nominal optimizer steps over 80 epochs |
|---|---:|---:|---:|
| approach | 0 | 14,202 | 17,760 |
| approach | 1 | 14,261 | 17,840 |
| approach | 2 | 14,283 | 17,920 |
| moving_immediate | 0 | 14,432 | 18,080 |
| moving_immediate | 1 | 14,519 | 18,160 |
| moving_immediate | 2 | 14,545 | 18,240 |

Extra eligible windows, optimizer steps and CF/now exposures are registered
consequences of the timing recipe, not an isolated gradient or label-quality
intervention. Internal validation did not select an epoch, seed or model.

## Research consequence

Restricting the data change to moving does not establish a reliable
action-specific benefit: two primary deltas rise and one falls. Every
registered moving geometric-ranking delta is negative beyond its guard.
Preserving nonmoving arrays is insufficient to guarantee preserved nonmoving
scores, as shown by dense-left and classic-ranking failures. These findings
do not identify a training mechanism; MPS point estimates may vary by run.

The earlier all-world timing study used a different independent exam and
fresh model draws. It remains closed; this is not a direct three-arm ablation
and does not demonstrate that one timing recipe causally dominates the other.
Executed-action AUC and the forward-frame geometric probe measure different
questions. Neither metric substitutes for the other.

Keep default approach timing and the existing champions. No flight gate,
replacement seed, extra exam course, optional recheck or promotion follows.
A future diagnostic must declare its exploratory scope before slicing the
saved scores. Any further model trial needs a new single-knob registration
and independent exam; this result does not automatically release one.

## Evidence

Run `PYTHON=/absolute/path/python bash experiments/moving_timing_v1/verify.sh`
to verify the original source/runtime, all logs/exits, output hashes and nine
protected artifacts, then recompute support and saved-score readings without
fitting or inference. The frozen tracked-Python inventory intentionally stops
if later modules are added; use the original source snapshot rather than
weakening this manifest. Exact numbers: [report](report.json). Execution and
closure: [verification](verification.json), [journal](journal.md),
[registration](registration.json) and [definition](definition.md).

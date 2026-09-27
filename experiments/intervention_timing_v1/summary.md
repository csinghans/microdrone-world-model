# Intervention timing v1 — NO-GO

All 23 stages completed with actual exit 0 on their first study execution.
The support gate passed before all six fresh 80-epoch fits. The two arms
share 276 paired development scenes and identical 221/55 train/validation
course memberships at seeds 0/1/2. All models use a separate fixed exam of
1,440 courses / 101,238 eligible held-command windows. No model or seed was
selected using internal validation.

Immediate intervention improves the four-cell primary macro in every seed,
but the mean **+0.022125** misses the frozen **+0.03** bar. Dense right-veer
declines beyond the −0.02 guard in **all three seeds**; dense left-veer also
breaks its guard at seed 0. These are sufficient reasons for NO-GO.

| Warn AUC@32 delta, immediate − approach | Seed 0 | Seed 1 | Seed 2 |
|---|---:|---:|---:|
| Dense / left | −0.023661 **fail** | +0.002023 | −0.005886 |
| Dense / right | −0.052571 **fail** | −0.026024 **fail** | −0.025885 **fail** |
| Moving / left | +0.142379 | +0.145285 | +0.067489 |
| Moving / right | +0.010177 | +0.017566 | +0.014601 |
| Primary: equal-weight mean of four cells | +0.019081 | +0.034713 | +0.012580 |
| Primary conditional course-bootstrap 95% interval | [−0.014199, +0.050791] | [+0.002459, +0.066500] | [−0.015966, +0.043440] |

Each fixed checkpoint pair has 2,000 valid bootstrap replicates and zero
undefined ones, stratified by world and timing block with shared course
draws across actions. These intervals describe exam-course uncertainty
conditional on that pair, not training-population uncertainty. The seed
mean/range is descriptive; no interval changes the frozen point-estimate bars.

## Every other registered guard

| Guard delta | Seed 0 | Seed 1 | Seed 2 | Floor |
|---|---:|---:|---:|---:|
| Pooled classic AUC | +0.019694 | +0.051779 | −0.007355 | −0.02 |
| Pooled dense AUC | +0.018700 | +0.024217 | −0.001709 | −0.02 |
| Pooled moving AUC | +0.066088 | +0.115788 | +0.032343 | −0.02 |
| Pooled room AUC | +0.017481 | +0.174135 | +0.015183 | −0.02 |
| Classic forward AUC | +0.023644 | +0.073040 | −0.019255 | −0.02 |
| Dense forward AUC | +0.049125 | +0.042083 | −0.005831 | −0.02 |
| Moving forward AUC | +0.048979 | +0.138239 | +0.028947 | −0.02 |
| Danger-now AUC | −0.005355 | +0.034657 | −0.006706 | −0.02 |
| Pooled geometric veer accuracy | +0.124644 | +0.110399 | +0.152422 | −0.05 |
| Classic geometric veer accuracy | +0.051765 | +0.101176 | +0.350588 | −0.05 |
| Dense geometric veer accuracy | +0.139651 | +0.071072 | +0.062344 | −0.05 |
| Moving geometric veer accuracy | +0.231638 | +0.310734 | +0.084746 | −0.05 |

All guards in this second table pass. Seed-2 classic forward is close to its
floor but remains a pass under the unchanged rule; no optional recheck is
registered. Six architecture bills match: **137.290039 KB** analytic int8
memory, **3,856,768 MACs/decision**, **7.713536 ms** at the assumed 0.5 GMAC/s.
This is not hardware timing, quantization parity or flight certification.

## Prospective exam support

| Primary cell | Positive windows / courses | Negative windows / courses |
|---|---:|---:|
| Dense / left | 1,651 / 94 | 361 / 30 |
| Dense / right | 1,638 / 90 | 403 / 29 |
| Moving / left | 898 / 60 | 970 / 65 |
| Moving / right | 645 / 45 | 1,313 / 76 |

Every required action, forward, pooled world and now cell exceeds the
registered 100-positive/100-negative and ten-course-per-class floors.
The geometric probe contains **1,404 frames / 173 courses**: classic 425/72,
dense 802/82, moving 177/19, each above 40 frames / ten courses. These floors
address the earlier absent/singleton support problem; they do not prove
statistical power, independent real-world coverage or deployment safety.

Candidate training passes all 12 registered steering cells. Both arms'
training world/class minima pass. Full train/validation support remains in
[the archived reports](support/); internal validation still is not the
registered decision exam. Immediate training has more eligible windows:
14,997/15,058/15,122 versus approach 14,202/14,261/14,283 across the three
seeds. Fixed 80 epochs therefore mean 18,800/18,880/18,960 optimizer steps
versus 17,760/17,840/17,920, with corresponding CF/now sampling changes.
Those are consequences of the timing recipe, not an isolated label-quality
or gradient-mass intervention.

## What this changes

The recipe has directional benefits on moving actions and the geometric
ranking probe in all three registered seeds, alongside a dense right-action
regression in all three. Exact third decimals may vary under MPS. Pooled
dense AUC improves in seeds 0/1 while its right-action AUC declines; a pooled
score alone would conceal the guard failure. Geometric ranking and executed
action AUC measure different questions and cannot substitute for each other.
The cause of the dense-right loss is not established by these metrics.

Keep the default approach recipe and all champion artifacts. Close this
study without added seeds/courses, changed bars, replacement fits or flight
promotion. A future diagnostic may examine the dense-right failure on fixed
saved scores and development metadata, clearly labeled exploratory; a new
training comparison needs its own registration and independent exam.

Run `PYTHON=/absolute/path/python bash experiments/intervention_timing_v1/verify.sh`
to verify original source/runtime, all logs/exits and locked hashes, then
recompute support, action metrics, bootstrap and verdict from saved metadata
and score exports without training or inference. [Report](report.json),
[preflight](preflight.json), [registration](registration.json),
[definition](definition.md) and [journal](journal.md) retain exact evidence.

# schedule_layout_v1 — NO-GO

Generated from [the complete raw report](records/report.json) by
`python -m eval.eval_schedule_report`. No new scoring or resampling.

3 paired training seeds; legacy control versus
world_balanced candidate. Each fit uses 96 transit +
96 shared room rollouts and 80 epochs. All six models score the same
186 independent courses (12,117 overlapping valid windows).
D64, 64px, single-frame input.

Moving mean AUC delta **-0.0551**;
registered minimum **+0.0300**.
Every seed also needs positive moving delta and every per-seed guard.

| Seed | Moving control | Candidate | Delta | Course-bootstrap 95% interval |
|---|---:|---:|---:|---:|
| 0 | 0.7440 | 0.7572 | +0.0133 | [-0.0448, +0.0757] |
| 1 | 0.7323 | 0.6578 | -0.0745 | [-0.1710, +0.0241] |
| 2 | 0.7294 | 0.6252 | -0.1042 | [-0.1782, -0.0252] |

Intervals resample whole courses, paired between the fixed models
and stratified by world (2,000 resamples, seed 0). They describe
test-course uncertainty, not uncertainty across training draws.
The three-seed mean/range is descriptive, not a confidence interval.

| World | Mean paired delta | Range across three training seeds |
|---|---:|---:|
| classic | +0.0034 | [-0.0596, +0.0582] |
| dense | -0.0011 | [-0.0492, +0.0253] |
| moving | -0.0551 | [-0.1042, +0.0133] |
| room | -0.0361 | [-0.1171, +0.0461] |
| all | -0.0131 | [-0.0589, +0.0303] |

## Every guard, every seed

Candidate minus control; **bold** means a failed registered guard.

| Seed | Classic | Dense | Room | Danger-now | Veer ranking |
|---|---:|---:|---:|---:|---:|
| 0 | +0.0582 | +0.0205 | +0.0461 | +0.0141 | +0.2484 |
| 1 | +0.0115 | +0.0253 | **-0.0373** | **-0.0548** | +0.0573 |
| 2 | **-0.0596** | **-0.0492** | **-0.1171** | **-0.0378** | **-0.2229** |

Minimum deltas: classic/dense/room and danger-now −0.02; veer −0.05.
Each veer reading uses the same 157 independent-exam probe frames.
These selected frames are not independent flights.

## Full embedded bill

All six models have the same **137.29 KB** analytic
int8 bill: 81.29 KB weights + 28 KB peak activations +
28 KB workspace, within 512 KB.
3,856,768 MACs/decision give an estimated
**7.71 ms** at the existing assumed
0.5 GMAC/s. This is an analytic int8 estimate; no hardware timing,
quantization-parity evaluation or closed-loop promotion was performed.

## End-of-training instruments

These are internal training-validation diagnostics, not common-exam
metrics. Latent MSE has a different learned scale in each model.

| Arm | Seed | MSE@32 | No-op@32 | Std median | Std max | Mean abs latent |
|---|---|---:|---:|---:|---:|---:|
| legacy | 0 | 0.6733 | 0.9228 | 1.2309 | 1.6986 | 1.5988 |
| legacy | 1 | 1.6665 | 2.1119 | 1.4647 | 1.7776 | 1.6517 |
| legacy | 2 | 1.0868 | 1.6790 | 1.4871 | 2.0137 | 2.5288 |
| world_balanced | 0 | 0.4682 | 0.9217 | 1.2522 | 1.6969 | 1.3446 |
| world_balanced | 1 | 1.2386 | 2.4885 | 1.5482 | 2.6581 | 1.2783 |
| world_balanced | 2 | 4.5338 | 6.3978 | 2.5691 | 6.5142 | 16.1382 |

Balanced seed 2 has a large endpoint absolute latent value and
breaks every behavioral guard. This association does not identify a
cause: balanced seed 1 also loses moving/room/now performance while
its absolute latent value is smaller than its control's. All six
fits improve their own MSE@32 over their own no-op, which therefore
does not certify common-exam decision quality.

The role-coverage repair remains verified. This fixed-rollout,
fixed-epoch learning recipe failed its improvement test. It changes
generator RNG consumption, held-window support and internal splits
as well as roles, so the study does not isolate a universal causal
effect of role balance. Preserve the NO-GO, every draw and all bars.
No seed replacement, sample expansion or champion promotion.

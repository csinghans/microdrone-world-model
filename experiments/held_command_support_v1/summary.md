# Repeated-command window support

Saved metadata only. Original indices, labels and closed NO-GOs are unchanged.
Recovered windows cross a segment boundary while the commanded four-vector
stays exactly constant over the existing inclusive horizon-32 window.

| Corpus / world | Original windows | Recovered | Union | Same-command boundaries |
|---|---:|---:|---:|---:|
| training / classic | 1470 | 341 | 1811 | 11 |
| training / dense | 1490 | 373 | 1863 | 13 |
| training / moving | 1506 | 83 | 1589 | 3 |
| training / room | 3962 | 884 | 4846 | 33 |
| executed_exam / classic | 2896 | 384 | 3280 | 15 |
| executed_exam / dense | 2879 | 495 | 3374 | 17 |
| executed_exam / moving | 2989 | 469 | 3458 | 16 |
| executed_exam / room | 3415 | 843 | 4258 | 28 |

## training: every action

Positive / negative distinct-course counts are original → union.
Recovered windows can come from courses already represented; counts
overlap across actions/classes and must not be summed as independent trials.

| World / action | Recovered + / − windows | Positive courses | Negative courses |
|---|---:|---:|---:|
| classic / forward | 89 / 166 | 10 → 10 | 25 → 25 |
| classic / slow | 22 / 0 | 3 → 3 | 4 → 4 |
| classic / veer_left | 31 / 1 | 5 → 5 | 6 → 6 |
| classic / veer_right | 0 / 0 | 2 → 2 | 1 → 1 |
| classic / climb | 0 / 0 | 1 → 1 | 1 → 1 |
| classic / hover | 0 / 32 | 2 → 2 | 5 → 5 |
| dense / forward | 230 / 11 | 24 → 24 | 9 → 9 |
| dense / slow | 0 / 0 | 4 → 4 | 0 → 0 |
| dense / veer_left | 32 / 0 | 4 → 4 | 0 → 0 |
| dense / veer_right | 32 / 0 | 7 → 7 | 0 → 0 |
| dense / climb | 32 / 0 | 3 → 3 | 0 → 0 |
| dense / hover | 36 / 0 | 6 → 6 | 1 → 1 |
| moving / forward | 7 / 25 | 13 → 13 | 26 → 26 |
| moving / slow | 19 / 0 | 5 → 5 | 2 → 2 |
| moving / veer_left | 0 / 0 | 6 → 6 | 2 → 2 |
| moving / veer_right | 0 / 0 | 3 → 3 | 2 → 2 |
| moving / climb | 32 / 0 | 5 → 5 | 3 → 3 |
| moving / hover | 0 / 0 | 1 → 1 | 3 → 3 |
| room / forward | 0 / 64 | 9 → 9 | 19 → 19 |
| room / reverse | 116 / 24 | 18 → 18 | 19 → 19 |
| room / strafe_left | 103 / 70 | 12 → 12 | 24 → 24 |
| room / strafe_right | 0 / 96 | 9 → 9 | 18 → 18 |
| room / slow | 96 / 110 | 5 → 5 | 21 → 21 |
| room / hover | 8 / 197 | 2 → 2 | 26 → 26 |
| room / yaw_left | 0 / 0 | 0 → 0 | 0 → 0 |
| room / yaw_right | 0 / 0 | 0 → 0 | 0 → 0 |
| room / up | 0 / 0 | 0 → 0 | 0 → 0 |
| room / down | 0 / 0 | 0 → 0 | 0 → 0 |

## executed_exam: every action

Positive / negative distinct-course counts are original → union.
Recovered windows can come from courses already represented; counts
overlap across actions/classes and must not be summed as independent trials.

| World / action | Recovered + / − windows | Positive courses | Negative courses |
|---|---:|---:|---:|
| classic / forward | 0 / 113 | 13 → 13 | 33 → 33 |
| classic / slow | 0 / 0 | 3 → 3 | 7 → 7 |
| classic / veer_left | 63 / 74 | 8 → 8 | 9 → 9 |
| classic / veer_right | 51 / 0 | 3 → 3 | 2 → 2 |
| classic / climb | 27 / 39 | 2 → 3 | 5 → 5 |
| classic / hover | 17 / 0 | 3 → 3 | 11 → 11 |
| dense / forward | 265 / 13 | 33 → 33 | 16 → 17 |
| dense / slow | 20 / 0 | 7 → 7 | 1 → 1 |
| dense / veer_left | 0 / 0 | 9 → 9 | 0 → 0 |
| dense / veer_right | 98 / 12 | 12 → 12 | 1 → 2 |
| dense / climb | 64 / 0 | 9 → 9 | 1 → 1 |
| dense / hover | 0 / 23 | 6 → 6 | 2 → 2 |
| moving / forward | 120 / 216 | 24 → 24 | 33 → 36 |
| moving / slow | 0 / 0 | 6 → 6 | 4 → 4 |
| moving / veer_left | 32 / 0 | 8 → 8 | 4 → 4 |
| moving / veer_right | 0 / 0 | 3 → 3 | 4 → 4 |
| moving / climb | 32 / 32 | 6 → 6 | 5 → 5 |
| moving / hover | 20 / 17 | 5 → 5 | 8 → 9 |
| room / forward | 151 / 32 | 18 → 18 | 16 → 16 |
| room / reverse | 94 / 49 | 12 → 12 | 12 → 12 |
| room / strafe_left | 32 / 128 | 11 → 11 | 15 → 15 |
| room / strafe_right | 32 / 32 | 16 → 16 | 14 → 14 |
| room / slow | 7 / 126 | 12 → 12 | 23 → 23 |
| room / hover | 128 / 32 | 12 → 12 | 14 → 14 |
| room / yaw_left | 0 / 0 | 0 → 0 | 0 → 0 |
| room / yaw_right | 0 / 0 | 0 → 0 | 0 → 0 |
| room / up | 0 / 0 | 0 → 0 | 0 → 0 |
| room / down | 0 / 0 | 0 → 0 | 0 → 0 |

Full original/recovered/union class and course counts: [report](report.json).
No extra samples were admitted to training or evaluation. This establishes
available commanded-intent support, not model quality, rendering, causal
benefit or statistical power. No bootstrap or model-promotion gate follows.
A future recipe must preserve split identity and account for changes in
optimizer-step and CF/now sampling counts. See [registration](definition.md).

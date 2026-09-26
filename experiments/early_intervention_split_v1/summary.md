# Timing-pilot split support

Fixed seeds 0/1/2; unchanged splitter and course IDs; no fitting or new data.
Both arms have exactly equal train/validation memberships for every seed.
The original whole-corpus pilot is unchanged. This diagnostic applies its
same 20-window / 3-course per-class minima within each partition.

| Arm | Partition | Satisfied action cells / 4 |
|---|---|---:|
| approach | splits/0/train | 2 / 4 |
| approach | splits/0/val | 0 / 4 |
| approach | splits/1/train | 2 / 4 |
| approach | splits/1/val | 0 / 4 |
| approach | splits/2/train | 3 / 4 |
| approach | splits/2/val | 0 / 4 |
| immediate | splits/0/train | 4 / 4 |
| immediate | splits/0/val | 0 / 4 |
| immediate | splits/1/train | 4 / 4 |
| immediate | splits/1/val | 1 / 4 |
| immediate | splits/2/train | 4 / 4 |
| immediate | splits/2/val | 1 / 4 |

## All required executed-action cells

Counts are positive / negative; courses can overlap across classes/actions.

| Arm | Partition | World | Action | Windows | Courses | Deficits |
|---|---|---|---|---:|---:|---|
| approach | splits/0/train | dense | veer_left | 103/11 | 7/2 | negative: 9, negative_rollouts: 1 |
| approach | splits/0/train | dense | veer_right | 189/0 | 11/0 | negative: 20, negative_rollouts: 3 |
| approach | splits/0/train | moving | veer_left | 96/95 | 6/6 | none |
| approach | splits/0/train | moving | veer_right | 113/76 | 8/5 | none |
| approach | splits/0/val | dense | veer_left | 18/16 | 2/1 | positive: 2, negative: 4, positive_rollouts: 1, negative_rollouts: 2 |
| approach | splits/0/val | dense | veer_right | 33/12 | 2/1 | negative: 8, positive_rollouts: 1, negative_rollouts: 2 |
| approach | splits/0/val | moving | veer_left | 31/77 | 2/4 | positive_rollouts: 1 |
| approach | splits/0/val | moving | veer_right | 17/1 | 1/1 | positive: 3, negative: 19, positive_rollouts: 2, negative_rollouts: 2 |
| approach | splits/1/train | dense | veer_left | 88/11 | 6/2 | negative: 9, negative_rollouts: 1 |
| approach | splits/1/train | dense | veer_right | 172/12 | 9/1 | negative: 8, negative_rollouts: 2 |
| approach | splits/1/train | moving | veer_left | 49/128 | 4/8 | none |
| approach | splits/1/train | moving | veer_right | 126/71 | 8/5 | none |
| approach | splits/1/val | dense | veer_left | 33/16 | 3/1 | negative: 4, negative_rollouts: 2 |
| approach | splits/1/val | dense | veer_right | 50/0 | 4/0 | negative: 20, negative_rollouts: 3 |
| approach | splits/1/val | moving | veer_left | 78/44 | 4/2 | negative_rollouts: 1 |
| approach | splits/1/val | moving | veer_right | 4/6 | 1/1 | positive: 16, negative: 14, positive_rollouts: 2, negative_rollouts: 2 |
| approach | splits/2/train | dense | veer_left | 82/27 | 7/3 | none |
| approach | splits/2/train | dense | veer_right | 190/12 | 11/1 | negative: 8, negative_rollouts: 2 |
| approach | splits/2/train | moving | veer_left | 93/126 | 6/8 | none |
| approach | splits/2/train | moving | veer_right | 113/51 | 8/4 | none |
| approach | splits/2/val | dense | veer_left | 39/0 | 2/0 | negative: 20, positive_rollouts: 1, negative_rollouts: 3 |
| approach | splits/2/val | dense | veer_right | 32/0 | 2/0 | negative: 20, positive_rollouts: 1, negative_rollouts: 3 |
| approach | splits/2/val | moving | veer_left | 34/46 | 2/2 | positive_rollouts: 1, negative_rollouts: 1 |
| approach | splits/2/val | moving | veer_right | 17/26 | 1/2 | positive: 3, positive_rollouts: 2, negative_rollouts: 1 |
| immediate | splits/0/train | dense | veer_left | 78/66 | 5/6 | none |
| immediate | splits/0/train | dense | veer_right | 99/132 | 8/6 | none |
| immediate | splits/0/train | moving | veer_left | 78/141 | 7/10 | none |
| immediate | splits/0/train | moving | veer_right | 59/173 | 5/9 | none |
| immediate | splits/0/val | dense | veer_left | 15/19 | 1/1 | positive: 5, negative: 1, positive_rollouts: 2, negative_rollouts: 2 |
| immediate | splits/0/val | dense | veer_right | 37/16 | 4/1 | negative: 4, negative_rollouts: 2 |
| immediate | splits/0/val | moving | veer_left | 51/76 | 2/5 | positive_rollouts: 1 |
| immediate | splits/0/val | moving | veer_right | 8/41 | 1/2 | positive: 12, positive_rollouts: 2, negative_rollouts: 1 |
| immediate | splits/1/train | dense | veer_left | 67/48 | 4/4 | none |
| immediate | splits/1/train | dense | veer_right | 87/131 | 9/6 | none |
| immediate | splits/1/train | moving | veer_left | 70/135 | 6/10 | none |
| immediate | splits/1/train | moving | veer_right | 47/190 | 5/10 | none |
| immediate | splits/1/val | dense | veer_left | 26/37 | 2/3 | positive_rollouts: 1 |
| immediate | splits/1/val | dense | veer_right | 49/17 | 3/1 | negative: 3, negative_rollouts: 2 |
| immediate | splits/1/val | moving | veer_left | 59/82 | 3/5 | none |
| immediate | splits/1/val | moving | veer_right | 20/24 | 1/1 | positive_rollouts: 2, negative_rollouts: 2 |
| immediate | splits/2/train | dense | veer_left | 58/81 | 4/6 | none |
| immediate | splits/2/train | dense | veer_right | 104/130 | 9/6 | none |
| immediate | splits/2/train | moving | veer_left | 98/151 | 6/11 | none |
| immediate | splits/2/train | moving | veer_right | 50/171 | 4/9 | none |
| immediate | splits/2/val | dense | veer_left | 35/4 | 2/1 | negative: 16, positive_rollouts: 1, negative_rollouts: 2 |
| immediate | splits/2/val | dense | veer_right | 32/18 | 3/1 | negative: 2, negative_rollouts: 2 |
| immediate | splits/2/val | moving | veer_left | 31/66 | 3/4 | none |
| immediate | splits/2/val | moving | veer_right | 17/43 | 2/2 | positive: 3, positive_rollouts: 1, negative_rollouts: 1 |

## Geometric veer-probe support

| Arm | Partition | World | Frames | Courses | Left/right safer frames |
|---|---|---|---:|---:|---:|
| approach | all | classic | 84 | 14 | 31/53 |
| approach | all | dense | 111 | 15 | 69/42 |
| approach | all | moving | 20 | 2 | 20/0 |
| approach | splits/0/train | classic | 65 | 11 | 12/53 |
| approach | splits/0/train | dense | 89 | 11 | 60/29 |
| approach | splits/0/train | moving | 10 | 1 | 10/0 |
| approach | splits/0/val | classic | 19 | 3 | 19/0 |
| approach | splits/0/val | dense | 22 | 4 | 9/13 |
| approach | splits/0/val | moving | 10 | 1 | 10/0 |
| approach | splits/1/train | classic | 64 | 11 | 26/38 |
| approach | splits/1/train | dense | 70 | 10 | 36/34 |
| approach | splits/1/train | moving | 20 | 2 | 20/0 |
| approach | splits/1/val | classic | 20 | 3 | 5/15 |
| approach | splits/1/val | dense | 41 | 5 | 33/8 |
| approach | splits/1/val | moving | 0 | 0 | 0/0 |
| approach | splits/2/train | classic | 79 | 13 | 31/48 |
| approach | splits/2/train | dense | 90 | 12 | 62/28 |
| approach | splits/2/train | moving | 20 | 2 | 20/0 |
| approach | splits/2/val | classic | 5 | 1 | 0/5 |
| approach | splits/2/val | dense | 21 | 3 | 7/14 |
| approach | splits/2/val | moving | 0 | 0 | 0/0 |
| immediate | all | classic | 52 | 9 | 29/23 |
| immediate | all | dense | 70 | 9 | 45/25 |
| immediate | all | moving | 71 | 5 | 16/55 |
| immediate | splits/0/train | classic | 38 | 7 | 15/23 |
| immediate | splits/0/train | dense | 57 | 7 | 45/12 |
| immediate | splits/0/train | moving | 58 | 4 | 3/55 |
| immediate | splits/0/val | classic | 14 | 2 | 14/0 |
| immediate | splits/0/val | dense | 13 | 2 | 0/13 |
| immediate | splits/0/val | moving | 13 | 1 | 13/0 |
| immediate | splits/1/train | classic | 46 | 7 | 24/22 |
| immediate | splits/1/train | dense | 34 | 5 | 17/17 |
| immediate | splits/1/train | moving | 71 | 5 | 16/55 |
| immediate | splits/1/val | classic | 6 | 2 | 5/1 |
| immediate | splits/1/val | dense | 36 | 4 | 28/8 |
| immediate | splits/1/val | moving | 0 | 0 | 0/0 |
| immediate | splits/2/train | classic | 52 | 9 | 29/23 |
| immediate | splits/2/train | dense | 62 | 7 | 38/24 |
| immediate | splits/2/train | moving | 71 | 5 | 16/55 |
| immediate | splits/2/val | classic | 0 | 0 | 0/0 |
| immediate | splits/2/val | dense | 8 | 2 | 7/1 |
| immediate | splits/2/val | moving | 0 | 0 | 0/0 |

Zero/singleton worlds are explicit. No resampling or probe gate was run.
Count presence does not establish statistical power, model performance or flight safety.
No seed selection, new draws, relaxed bars or training follows this audit.

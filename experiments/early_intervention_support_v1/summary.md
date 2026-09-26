# Early-intervention support pilot

Exactly paired scene identities, initial pixels and passive trajectories.
No fitting, inference, bootstrap or model promotion.

Control: **insufficient**; immediate: **satisfied**.

Counts are positive / negative. Courses can overlap across labels/actions.
The fixed minima are structural presence checks, not statistical power.

| World | Action | Control windows | Immediate windows | Control courses | Immediate courses | Negative course delta |
|---|---|---:|---:|---:|---:|---:|
| classic | forward | 1008/1921 | 984/1872 | 23/45 | 17/33 | -12 |
| classic | slow | 75/148 | 46/263 | 5/7 | 3/13 | +6 |
| classic | veer_left | 94/126 | 127/240 | 5/8 | 8/13 | +5 |
| classic | veer_right | 105/79 | 60/240 | 7/7 | 5/15 | +8 |
| classic | climb | 163/153 | 84/288 | 9/8 | 8/18 | +10 |
| classic | hover | 198/79 | 41/267 | 10/5 | 2/12 | +7 |
| dense | forward | 2519/507 | 2493/460 | 45/32 | 42/24 | -8 |
| dense | slow | 181/0 | 150/139 | 14/0 | 11/10 | +10 |
| dense | veer_left | 121/27 | 93/85 | 9/3 | 6/7 | +4 |
| dense | veer_right | 222/12 | 136/148 | 13/1 | 12/7 | +6 |
| dense | climb | 303/12 | 237/211 | 18/2 | 14/12 | +10 |
| dense | hover | 186/29 | 78/206 | 11/2 | 5/11 | +9 |
| moving | forward | 1556/1318 | 1611/1222 | 27/49 | 28/28 | -21 |
| moving | slow | 82/188 | 32/277 | 7/14 | 3/16 | +2 |
| moving | veer_left | 127/172 | 129/217 | 8/10 | 9/15 | +5 |
| moving | veer_right | 130/77 | 67/214 | 9/6 | 6/11 | +5 |
| moving | climb | 158/49 | 37/279 | 11/6 | 2/16 | +10 |
| moving | hover | 111/103 | 62/236 | 10/8 | 4/15 | +7 |

Close pilot; no extra seed/rollouts or automatic training.

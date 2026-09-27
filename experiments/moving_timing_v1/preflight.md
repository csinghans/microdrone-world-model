# Moving-only timing — support preflight

**READY.** All nine prerequisite stages completed with actual exit 0.
Every registered support requirement passed before any fitting. Six fresh
80-epoch fits are released; this document contains no model-performance result.

Both arms contain 276 exactly paired development scenes. Only complete
moving-world rows are replaced in the candidate. Classic/dense/room arrays
and 20 passive moving rows remain identical; all three seeds preserve the
original 221-course training / 55-course validation memberships.

The common independent exam contains **1,440 courses / 100,548 held-command
windows**. Its exact initial-scene fingerprints are disjoint from both
development arms and the previous timing exam. All four new rendering
fixtures pass the frozen pixel thresholds.

| Exam cell | Positive windows | Negative windows | Positive courses | Negative courses |
|---|---:|---:|---:|---:|
| Moving left, pooled | 950 | 1,214 | 62 | 74 |
| Moving right, pooled | 880 | 1,076 | 58 | 61 |
| Moving left, approach | 544 | 367 | 34 | 22 |
| Moving left, immediate | 406 | 847 | 28 | 52 |
| Moving right, approach | 445 | 325 | 30 | 23 |
| Moving right, immediate | 435 | 751 | 28 | 38 |
| Dense left, pooled | 1,466 | 290 | 93 | 24 |
| Dense right, pooled | 1,489 | 406 | 88 | 27 |

Each row clears 100 windows and ten courses per class. All pooled-world,
transit-forward and pooled danger-now requirements also pass. The geometric
veer probe has 1,347 frames / 162 courses: classic 348/55, dense 865/91,
moving 134/16. Every transit world clears 40 frames / ten courses.
Class/action course counts overlap; they must not be summed as independent
examples. These floors establish coverage, not statistical power.

The training action checks pass in both arms at seeds 0/1/2. Complete
training/validation counts, including unchanged sparse dense steering
support, are retained in [support/](support/). More supported exam cells do
not imply that the candidate has learned them.

| Published corpus | SHA-256 |
|---|---|
| Approach development | `890fa92ee38ff064ec8524e0f168693781eb9c90f7f7c1f0a17b4c7255a415b3` |
| Moving-only immediate development | `cca80c172314947eaf856ddc85ccff5e247098cde5bab164b73f3abb5d61a409` |
| Common independent exam | `e22291eb3ee6b72a3e8bbeac28dc5bb976c3dc1c2d39dabc96dcb94e48bbb058` |

The published approach arrays equal their registered source arrays; the
NPZ hash differs because explicit per-world study metadata was added.
Evidence: [support gate](support/report.json),
[verification](preflight_verification.json), [manifest](manifest.json),
[registration](registration.json), and [journal](journal.md).

After the complete queue exits, `python -m scripts.moving_timing_study --verify`
checks stage exits, complete-log/output hashes, source/runtime/input identity,
all nine protected artifacts, and recomputes support and saved-score readings
without fitting or inference. Verify the source snapshot that generated the
manifest; adding new Python modules later intentionally changes its inventory.

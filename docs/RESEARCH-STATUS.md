# Research status — 2026-09-29

**Next: compare champion, unified and the actual `wm_96d128` checkpoint on
a role-complete independent exam, then choose a single-knob study with a
declared precision or power plan.**

The existing independent 60-rollout audit measured unified AUC@32 at
**0.818842 overall, 0.838850 classic, 0.811430 dense and 0.773229 moving**.
These are different exams from its historical 0.92/0.95 validation readings.
Correcting tied-score AUC changed none of these four float-model readings.
[Measured journal and provenance](https://github.com/csinghans/microdrone-world-model/blob/888daaf8265f16f52e6dad2b05b8788eea56aec6/experiments/metric_integrity_v1/journal.md).
That draw does not replace the proposed role-complete three-model exam.

Five matched training studies are closed NO-GO. The last, moving-only
intervention timing, completed all six fits and scorings: mean moving-action
delta **+0.010130** misses **+0.03**, seed 2 declines, and moving-ranking
guards fail in all seeds. Preserve the approach default and existing
champions. [Complete result](https://github.com/csinghans/microdrone-world-model/blob/888daaf8265f16f52e6dad2b05b8788eea56aec6/experiments/moving_timing_v1/summary.md).
The [archive status](https://github.com/csinghans/microdrone-world-model/blob/888daaf8265f16f52e6dad2b05b8788eea56aec6/docs/RESEARCH-STATUS.md)
links every original registration and result; this compact index imports no
raw study receipts.

The first three studies' seed ranges are approximately 0.117, 0.255 and
0.141, against +0.03/+0.05 bars. A shared exam removes changes of exam
between arms but retains finite-course uncertainty. The fourth study changed
both exam and endpoint; its narrower range alone does not identify which
change helped. Future fits must declare the estimand, course and training-seed
uncertainty, and precision/power assumptions before measurement. Existing
bars and negative results remain unchanged.

The two locked WMs are available. The third checkpoint,
`experiments/perception_v2/artifacts/wm_96d128.pth`, has not been located in
the current executor; its accessible artifact location has been requested.
Before scoring, verify all three hashes, checkpoint frame recipes, rendered
nonblank pixels, source independence and world-by-role/class coverage.
Account for each model against 512 KB and approximately 8 ms per decision.
The resulting comparison should guide the original larger-diet, 96-pixel
closed-loop or center-drift direction. No new training gate is released.

See [review response](REVIEW-RESPONSE-2026-09-29.md) for isolated fixes,
legacy parity, delivery links and remaining work.

# Research continuation state — 2026-09-21

The three matched training studies below are **closed NO-GO**. Their common
exam machinery is implemented and exercised; no candidate earned promotion.
The remaining research question is which action-specific failure a new
single-knob study can resolve with adequate course support and the embedded
budget intact. No new training study is registered or running at this review.

This is a living continuation index, reviewed against `b2b7c69`. Original
registrations, stage receipts and journals are the evidence of record; this
page neither replaces them nor changes a gate. Recheck Git and processes
on resumption. Old queue files and PIDs do not establish active work.

## Closed scientific evidence

Each study used six fresh 80-epoch fits, paired seeds 0/1/2, and its own
186-course independent exam shared by all six models. Exams differ between
studies: compare arms within a study, not absolute scores across studies.

| Study / single knob | Primary deltas, seeds 0 / 1 / 2 | Why NO-GO |
|---|---|---|
| [schedule_layout_v1](../experiments/schedule_layout_v1/summary.md): legacy → world-balanced roles | Moving AUC +0.0133 / −0.0745 / −0.1042; mean −0.0551 | Mean misses +0.03; seed 1 room/now guards fail and seed 2 fails all behavioral guards |
| [cf_hard_pool_v1](../experiments/cf_hard_pool_v1/summary.md): masked-vector → answerable-label contrast sampling | Veer accuracy +0.0481 / −0.0913 / +0.1635; mean +0.0401 | Mean misses +0.05; seed 1 ranking declines and seed 0 classic/moving/room/now guards fail |
| [executed_weight_v1](../experiments/executed_weight_v1/summary.md): moving executed-loss weight 1.0 → 2.25 | Moving AUC −0.0184 / +0.1227 / +0.0752; mean +0.0598 | Mean passes +0.03, but seed 0 positivity and seed 1 dense/veer guards fail |

Keep `world_balanced` as the structural role-coverage repair, without claiming
a performance upgrade. CF sampling stays `legacy_masked`; executed-loss
weight stays 1.0. Preserve all seeds and failed guards. These closed studies
authorize no replacement draws, added exam courses, altered bars or flight
gate. Recorded course-bootstrap intervals condition on fixed checkpoint
pairs; three-seed means/ranges are not training-population uncertainty.

All three studies retain the same **137.29 KB analytic int8 bill** and
3,856,768 MACs/decision: **7.71 ms at an assumed 0.5 GMAC/s**, against the
project's 512 KB / approximately 8 ms target. These are estimates, without
hardware timing, quantization-parity or flight certification for these fits.

## What the support audits established

- [metric_integrity_v1](../experiments/metric_integrity_v1/journal.md): on
  60 courses / 4,083 windows, both locked float WMs have zero cross-class
  score ties and zero old-to-corrected AUC change. This covers those models
  and that draw, not the historical 96-pixel or quantized candidates.
- [schedule_support_v1](../experiments/schedule_support_v1/journal.md):
  moving executed windows fall 2,816→1,506 as non-forward categories appear.
  Legacy seed-0 dense validation has 158 positives and no negatives: its
  numeric 0.5 is the compatibility fallback, not measured chance ranking.
  Class-support logging exposes this without rewriting old results.
- [veer_support_v1](../experiments/veer_support_v1/journal.md): the CF exam
  has 208 eligible frames / 23 courses, including two moving courses; the
  executed-weight exam has 190 / 20, including one moving course. Both
  satisfy their frozen pooled bar. The latter's world-stratified veer
  intervals remain undefined because the moving stratum is a singleton.
  Keep the missing intervals and the original NO-GO; do not expand the exam.
- [action_auc_audit_v1](../experiments/action_auc_audit_v1/summary.md): the
  six saved executed-weight exports reconstruct every original AUC/delta
  from action-pair contributions. Moving's mean +0.059825 comprises
  +0.032170 within-action and +0.027656 across-action contributions; seed 0
  loses in both. **97.10% of moving's same-action score pairs are
  forward/forward.** Dense veer-left has zero negative windows; several
  other dense actions have negative windows from only one course.

The decomposition is accounting on a fixed exam, not a causal explanation
or a steering certificate. Within-action comparisons still mix scenes and
speeds; across-action comparisons may contain useful information. Window
pairs are not independent trials, and course counts can overlap across
actions/classes. Objective weight mass is not measured gradient mass.

## Next research decision

Prioritize a specific steering/action failure with a falsifiable mechanism.
The following is preparation for a new registration, **not** a registered
study or a reason to reopen any closed experiment:

1. Name the endpoint, required worlds/actions and one training knob. Freeze
   control/candidate recipes, all training seeds, guards, source revision,
   embedded bill and the response to insufficient support before fitting.
2. Verify rendered geometry is visible. For new corpora, explicitly freeze
   `world_balanced`; use `legacy` only for an identified historical recipe.
   Indoor Active Search uses its established robust speed 0.6.
3. Use `eval.eval_dataset_support` for the actual corpus and seed partitions,
   then `eval.eval_support_requirements` with registered positive/negative
   window **and course** minima. The [support guide](SUPPORT-REQUIREMENTS.md)
   explains exact fields and exit codes. It supplies no scientific defaults.
   If veer ranking is an endpoint or guard, also run `eval.eval_veer_support`
   and register required-world support, rather than relying on a pooled count.
4. Retain the preflight receipt and obey its frozen insufficiency response.
   These tools do not establish power, independence or rendered vision.
   Do not redraw until passing or weaken bars after observing support.
5. Score all registered matched seeds on one independent common exam.
   Preserve complete logs, actual process exits and input/output identities.
   Stop conditional stages with `research step` or a fail-fast persistent
   queue. An offline improvement still needs its own later flight study.

The [evidence audit](RESEARCH-AUDIT-2026-09-13.md) separates earlier
perception/temporal observations from explanations still unproved. Do not
substitute the deployed 64-pixel WMs for unavailable historical candidates
or reuse an old control whose recipe differs from a new treatment.

## Reliability now in place

| Boundary | Implemented protection and evidence |
|---|---|
| Research continuation | [Frozen evaluation](../experiments/frozen_evaluation_v1/journal.md): ordered cells and recheck settings saved before the first knob; 23 runner regressions. Legacy records remain readable but require original registration evidence before new measurements. |
| Dataset generation | [Corpus publication](../experiments/dataset_publication_v1/journal.md): all three CLIs reject existing/reserved outputs before simulation and publish complete NPZs atomically; selftest replacement is explicitly scoped. |
| Model persistence | [WM](../experiments/checkpoint_io_v1/journal.md) and [policy](../experiments/policy_checkpoint_v1/journal.md): candidate defaults, protected locked paths and atomic fresh outputs; recurrent filenames retain `_recurrent`. Historical standalone save sites keep their own implementations. |
| Policy recipe and evaluation | [CLI recipe](../experiments/policy_recipe_v1/journal.md) forwards seed/world lists; [policy evaluation](../experiments/policy_eval_identity_v1/journal.md) records policy/WM/cell identities and rejects duplicate cells. |
| Training/validation identity | [Original-corpus validation](../experiments/wm_validation_identity_v1/journal.md) rejects known different training-file hashes; independent holdouts reject known exact reuse. Unknown legacy identities are explicit. Different bytes do not prove disjoint courses. |
| WM score exports | [Publication](../experiments/wm_publication_v1/journal.md) is atomic per file; the JSON/NPZ pair is not a transaction. Completion requires exit 0 and all requested outputs with matching metadata. |
| Paired comparison | [Score schema](../experiments/score_schema_v1/journal.md) rejects malformed course/action-probe identities before metrics/resampling; all 18 archived exports / nine pairs remain accepted and unchanged. |
| Prospective support | [Requirements checker](../experiments/support_requirements_v1/journal.md) binds explicit action/class count bars to report/corpus hashes; insufficient support exits 10 and stops a fail-fast queue. |

These are offline instrument repairs. They add no deployed parameters or
inference work and establish no new performance result. Frozen scientific
records remain unchanged. All nine artifacts match `artifacts.lock.json`;
keep the transit and unified WM as separate protected artifacts.

## Verification and resumption

The [artifactless audit](../experiments/artifactless_ci_v1/journal.md) ran
all **116** fast workflow commands from frozen source `d845f79`, with no
locked artifacts initially present; every command exited 0 on its first
attempt. That is a local macOS/Python 3.14 run, not Linux/Python 3.12 CI or
the optional training smoke. Later repairs have their own linked regression
receipts; do not extend the frozen audit's coverage claim to newer commands.
The [latest code receipt](../experiments/dataset_publication_v1/verification.json)
records passing corpus/identity regressions, transit/indoor simulator smokes,
whole-repo Black/Ruff (176 Python files), and all nine locked hashes.

Local Python: `/Users/hans.chen/.cache/microdrone-research-venv/bin/python`
(3.14.5, torch 2.14.0, NumPy 2.5.3, pybullet 3.2.7). Declared conda/CI
Python remains 3.12. Study outputs are under `output/<study>/`; committed
receipts are under `experiments/<study>/`. Integrity-test logs are under
`output/research_integrity_selftest/`. Report selftests validate saved
decisions without refitting or rescoring:

```bash
python -m eval.eval_schedule_report --selftest
python -m eval.eval_cf_sampler_report --selftest
python -m eval.eval_executed_weight_report --selftest
```

All three report checks pass in this review. The action audit's strict
`--verify` also compares instrument hashes and stops on the newer comparator
source. Its [dated continuation check](../experiments/action_auc_audit_v1/journal.md#2026-09-21-continuation-check-values-match-source-identity-changed)
verifies original source/output hashes separately and confirms unchanged
accounting under the current code, without replacing historical records.

Check current processes before launching work; no worker was active at this
review. The existing task owns the hourly follow-up. No remote push or
release was performed in this research-integrity work. Before any later
push, run whole-repository lint and dispatch manual CI as `AGENTS.md`
requires. Release tags remain the user's decision.

# Research continuation state — 2026-09-28

All five matched model studies below are **closed NO-GO**. The latest
[moving-only timing study](../experiments/moving_timing_v1/summary.md) completed
all 22 stages, six fresh fits and six scorings after support passed. Its
moving left/right primary deltas are +0.0450 / +0.0251 / −0.0397: mean
+0.0101 misses +0.03 and seed 2 fails positivity. Moving geometric ranking
breaks its guard in every seed; dense-left action AUC fails seeds 1/2 despite
identical nonmoving training data. Pooled-world, forward, now and pooled
ranking guards all pass, illustrating the local failures they would miss.

The full source/input/runtime, 22 stage exits/log hashes, support reports,
saved-score endpoints and bootstrap were verified without fitting or
inference. All nine protected artifacts match their locked hashes. No
experiment worker remains active at closure. No candidate is promoted and
no further model or flight experiment has been released. See its
[journal](../experiments/moving_timing_v1/journal.md) and
[verification](../experiments/moving_timing_v1/verification.json).

The subsequent [probe diagnostic](../experiments/moving_probe_audit_v1/summary.md)
is complete: all 27 cells reconstruct the twelve original probe aggregates.
Immediate-block moving accuracy declines in every seed. Correctness on
left-safer frames falls while right-safer correctness rises; strict-left
preference bounds decrease in all seeds. Exact opposite-direction versus
tie counts cannot be recovered from the saved correctness flags. Seed 2's
equal-course accuracy improves while its registered frame-weighted accuracy
declines; this alternative weighting does not change the NO-GO.

This is a living continuation index, continued from `9ac59ae`. Original
registrations, stage receipts and journals are the evidence of record; this
page neither replaces them nor changes a gate. Recheck Git and processes
on resumption. Old queue files and PIDs do not establish active work.

## Closed scientific evidence

Each study used six fresh 80-epoch fits, paired seeds 0/1/2, and its own
independent exam shared by all six models: 186 courses in the first three
studies and 1,440 in each timing study. Exams differ between studies:
compare arms within a study, not absolute scores across studies.

| Study / single knob | Primary deltas, seeds 0 / 1 / 2 | Why NO-GO |
|---|---|---|
| [schedule_layout_v1](../experiments/schedule_layout_v1/summary.md): legacy → world-balanced roles | Moving AUC +0.0133 / −0.0745 / −0.1042; mean −0.0551 | Mean misses +0.03; seed 1 room/now guards fail and seed 2 fails all behavioral guards |
| [cf_hard_pool_v1](../experiments/cf_hard_pool_v1/summary.md): masked-vector → answerable-label contrast sampling | Veer accuracy +0.0481 / −0.0913 / +0.1635; mean +0.0401 | Mean misses +0.05; seed 1 ranking declines and seed 0 classic/moving/room/now guards fail |
| [executed_weight_v1](../experiments/executed_weight_v1/summary.md): moving executed-loss weight 1.0 → 2.25 | Moving AUC −0.0184 / +0.1227 / +0.0752; mean +0.0598 | Mean passes +0.03, but seed 0 positivity and seed 1 dense/veer guards fail |
| [intervention_timing_v1](../experiments/intervention_timing_v1/summary.md): approach → immediate nonpassive commands | Four-cell steering AUC macro +0.0191 / +0.0347 / +0.0126; mean +0.0221 | Mean misses +0.03; dense right action breaks −0.02 guard in all seeds, dense left also fails seed 0 |
| [moving_timing_v1](../experiments/moving_timing_v1/summary.md): only moving rows use immediate commands | Moving left/right AUC macro +0.0450 / +0.0251 / −0.0397; mean +0.0101 | Mean and seed-2 positivity fail; moving ranking fails all seeds, dense-left fails seeds 1/2, plus classic-ranking and seed-2 action/block guards |

Keep `world_balanced` as the structural role-coverage repair, without claiming
a performance upgrade. CF sampling stays `legacy_masked`; executed-loss
weight stays 1.0; intervention timing stays `approach`. Preserve all seeds
and failed guards. These closed studies
authorize no replacement draws, added exam courses, altered bars or flight
gate. Recorded course-bootstrap intervals condition on fixed checkpoint
pairs; three-seed means/ranges are not training-population uncertainty.

All five studies retain the same **137.29 KB analytic int8 bill** and
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
- [held_command_support_v1](../experiments/held_command_support_v1/journal.md):
  repeated commands across segment boundaries make 1,681 additional training
  windows available (8,428→10,109), but add no per-world/action positive or
  negative course coverage. Moving gains only 83 windows and neither veer
  gains any. The closed exam has 2,191 additional available windows; none
  was added to a model score. The current index, split and NO-GOs remain.
- [early_intervention_support_v1](../experiments/early_intervention_support_v1/journal.md):
  180 paired scenes, with the sole varied knob being approach versus immediate
  intervention timing. Isolated scene/schedule/noise streams prevent timing
  from changing later scenes. The candidate passes all frozen dense/moving
  veer class/course minima; control fails dense veer-right, with 12 negative
  windows / 1 course versus candidate 148 / 7. Required negative-course
  counts rise 3→7 and 1→7 in dense, 10→15 and 6→11 in moving (left/right).
  Forward negative-course coverage falls in all three worlds. This closes a
  data-feasibility pilot, not a model gate, and authorizes no automatic fit.
- [early_intervention_split_v1](../experiments/early_intervention_split_v1/journal.md):
  using the unchanged splitter at seeds 0/1/2, both arms have identical
  144-course training / 36-course validation memberships. Under the same
  pilot count minima, candidate training passes 12/12 action cells, versus
  control 7/12; validation passes only 2/12 versus 0/12. Both arms have moving
  validation veer-probe courses 1/0/0, despite candidate full-corpus support
  of 71 frames / 5 courses. No seed was selected and no new data or fit ran.
  This diagnostic is insufficient; the whole-corpus pilot remains sufficient.
- [timing_mixture_audit_v1](../experiments/timing_mixture_audit_v1/summary.md):
  exploratory accounting after the timing model study closed. Dense-right
  AUC still falls within the immediate exam block in every seed
  (−0.0671/−0.0481/−0.0351), with 45 positive / 25 negative courses; both
  within-block and cross-block contributions are negative. Dense approach
  negatives remain sparse (left five courses, right four). Moving-right
  seed 0 loses AUC in both blocks while its pooled AUC rises. All 12 original
  action-cell deltas reconstruct, maximum error 1.25e-16. No new inference,
  training, exam, interval or performance gate was introduced.
- [executed_cf_agreement_v1](../experiments/executed_cf_agreement_v1/summary.md):
  metadata-only follow-up verifies instantaneous geometric clearances and
  compares executed versus CF warn@32 targets. Immediate-exam dense-right
  has 84 answerable disagreements / 690 windows from ten courses, all flown
  dangerous / CF safe. Candidate training has only 5/6/6 conflicts across
  seeds, mostly the opposite direction; this is not an established cause
  of its regression. CF truth matches every geometric-probe frame, while
  primary executed-action windows share no frames with that forward-frame
  probe. No predictions, new data or models were evaluated here.
- [cf_score_attribution_v1](../experiments/cf_score_attribution_v1/summary.md):
  the subsequent fixed-score join reconstructs all 36 action/block/seed
  cells. Immediate-exam dense-right loses on comparisons without conflicting
  windows in every seed (contributions −0.0709/−0.0399/−0.0317); conflict
  comparisons contribute +0.0037/−0.0082/−0.0035. Agree/agree and masked/agree
  pair rankings both decline. The regression is not confined to conflicting
  exam examples, but this does not exclude training conflicts affecting
  other examples through shared parameters. No new inference or fit ran.

The decomposition is accounting on a fixed exam, not a causal explanation
or a steering certificate. Within-action comparisons still mix scenes and
speeds; across-action comparisons may contain useful information. Window
pairs are not independent trials, and course counts can overlap across
actions/classes. Objective weight mass is not measured gradient mass.

## Next research decision

The moving-only timing recipe did not retain a reliable steering gain while
protecting the other metrics. Moving geometric ranking fell by
0.2985 / 0.2313 / 0.0672 across seeds on 134 frames from 16 courses, even as
executed moving-action AUC rose in seeds 0/1. Pooled ranking passed because
it aggregates worlds; it does not establish preserved moving decisions.
Identical nonmoving arrays also did not prevent dense-left/classic-ranking
failures. The recipe changes eligible windows, optimizer steps and CF/now
exposures under fixed epochs; these results do not isolate their mechanism.

The separately declared `moving_probe_audit_v1` now locates that loss.
Moving's approach block contains 32 frames / five courses; its immediate
block 102 / eleven. Immediate accuracy deltas are −0.4118 / −0.2745 / −0.0784.
Across moving, correct counts on 101 left-safer frames fall 82→25, 64→32,
51→33, while those on 33 right-safer frames rise 9→26, 29→30, 22→31.
Losses occur across 9/8/7 of 16 courses. The exact cause is still open.

The [raw-score exporter improvement](../experiments/veer_score_export_v1/journal.md)
is now implemented: future exports retain both veer probabilities alongside
correctness. Artifactless tests cover strict ties, invalid probabilities,
mixed legacy/new comparisons and NPZ roundtrip; all 30 legacy exports remain
unchanged and accepted. A false flag includes ties under the current strict
comparison, so treating it as an opposite-side prediction would fabricate
evidence. Any rescoring of fixed checkpoints needs a new declared instrument
study; neither this diagnostic nor the exporter change performed it. A separate
metadata exposure audit could address sampling before another training knob.
Do not turn diagnostic slices or alternate course weighting into new gates.
Any model comparison still needs one falsifiable knob, a fresh independent
exam, immutable guards and the 512 KB / approximately 8 ms budget. No further
fit or flight study is released here.

Adding this diagnostic module intentionally changes the model study's strict
tracked-Python inventory. Its 192 original saved source hashes and inputs
were verified unchanged, with all nine protected artifacts intact. Use its
original source snapshot to run the old strict verifier; do not edit the
manifest to admit subsequent modules. The later raw-score exporter changes
three shared source files as well; historical strict verifiers now need their
original revisions for both source bytes and inventory. Their manifests and
recorded scientific results remain intact.

The earlier all-world timing study remains a separate closed comparison.
Its dense-right loss was found inside timing blocks and beyond conflicting
CF/executed examples. That establishes a diagnostic location, not a cause.
Different exams and fresh model draws mean the two timing studies are not
a controlled three-arm ablation. Further diagnostic slices must declare
their exploratory scope; reused scores become development evidence, never
the independent exam for a later training trial.

The current internal validation partitions remain an incomplete
action-specific/per-world veer exam; they were not used for model selection.
The pilot uses 180 scene pairs, not 360 independent courses; its two corpora
are development data, never independent exams for one another. Defaults
remain shared RNG and approach timing.
The earlier all-world timing study used 276 development courses per arm and a
separate 1,440-course exam. All registered support checks passed, including
100 windows and ten courses per class in each required AUC cell. Its
geometric probe has 1,404 frames / 173 courses, including 177 / 19 in moving.
At closure, all 23 stages, raw-score metrics, support counts and bootstrap
results were recomputed/verified by its [evidence script](../experiments/intervention_timing_v1/verify.sh).
That strict verifier freezes the complete tracked-Python inventory; the
new additive diagnostic modules change that inventory. The timing audit
verifies every original saved source/input hash and reconstructs all original
primary-cell readings without editing the old manifest or results.
Do not add seeds/courses or retry a failed performance guard. Any new model
study needs its own registration and independent exam. The following
discipline continues to apply:

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
| Corpus world identity | [Combined catalogs](../experiments/combined_world_identity_v1/journal.md): remap by source names so dynamic transit ID 3 cannot become room; reject malformed identities. Six canonical fixtures and their serialized NPZs match the old combiner byte for byte. |
| Scenario registration | [Stable registry](../experiments/registry_identity_v1/journal.md): reject ID collisions/reassignment before mutation; allow factory updates at a stable ID. All 15 existing skills retain the old catalog's 17 world IDs. |
| Model persistence | [WM](../experiments/checkpoint_io_v1/journal.md) and [policy](../experiments/policy_checkpoint_v1/journal.md): candidate defaults, protected locked paths and atomic fresh outputs; recurrent filenames retain `_recurrent`. Historical standalone save sites keep their own implementations. |
| Policy recipe and evaluation | [CLI recipe](../experiments/policy_recipe_v1/journal.md) forwards seed/world lists; [policy evaluation](../experiments/policy_eval_identity_v1/journal.md) records policy/WM/cell identities and rejects duplicate cells. |
| Training/validation identity | [Original-corpus validation](../experiments/wm_validation_identity_v1/journal.md) rejects known different training-file hashes; independent holdouts reject known exact reuse. Unknown legacy identities are explicit. Different bytes do not prove disjoint courses. |
| WM score exports | [Publication](../experiments/wm_publication_v1/journal.md) is atomic per file; the JSON/NPZ pair is not a transaction. Completion requires exit 0 and all requested outputs with matching metadata. |
| Paired comparison | [Score schema](../experiments/score_schema_v1/journal.md) rejects malformed course/action-probe identities before metrics/resampling; all 18 archived exports / nine pairs remain accepted and unchanged. |
| Prospective support | [Requirements checker](../experiments/support_requirements_v1/journal.md) binds explicit action/class count bars to report/corpus hashes; insufficient support exits 10 and stops a fail-fast queue. |
| Support-report persistence | [Publication repair](../experiments/support_publication_v1/journal.md): both metadata producers protect reserved/existing destinations, atomically publish complete JSON and recheck input/source identities. Eleven artifactless regressions include abrupt writer termination; four archived support reports retain exactly the same values. |
| Distance validity | [Finite-input repair](../experiments/support_distance_v1/journal.md): reject nonfinite distance matrices and invalid danger-now radii before indexing/oracle work; preserve signed room clearances. Seventeen malformed cases are rejected and four valid archived corpora retain all complete/split counts. |

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
The [dataset-publication receipt](../experiments/dataset_publication_v1/verification.json)
records passing corpus/identity regressions, transit/indoor simulator smokes,
whole-repo Black/Ruff (176 Python files), and all nine locked hashes.
The later [combined-identity receipt](../experiments/combined_world_identity_v1/verification.json)
adds catalog/CLI/compatibility checks, with the same full-repo lint and
artifact protection. It generates no new research corpus or model score.
The [held-command audit receipt](../experiments/held_command_support_v1/verification.json)
records its new metadata-only selftest, original-index/label agreement on
both fixed corpora, exact report verification and passing lint (177 files).
The [timing-pilot receipt](../experiments/early_intervention_support_v1/verification.json)
adds exact old-generator simulator parity in four settings, rendered fixtures,
pair-identity checks, support recomputation and whole-repo lint (178 files).
All six actual pilot stages exited 0; the control's insufficient support is
retained as a scientific observation, not treated as a tool failure.
The [split-audit receipt](../experiments/early_intervention_split_v1/verification.json)
adds an artifactless probe/accounting selftest, exact partition membership
and full-corpus reconciliation, deterministic metadata replay and whole-repo
lint (179 files). Its first synthetic fixture failure is retained separately;
the actual audit exited 0 and recorded both arms' insufficient split support.
The [support-publication receipt](../experiments/support_publication_v1/verification.json)
adds failure/race/source-drift tests, unchanged-core AST checks, four archived
report comparisons and full lint (180 files). It changes report persistence
and provenance, with no new model result.

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

All three report checks passed at the September 21 review. The action audit's strict
`--verify` also compares instrument hashes and stops on the newer comparator
source. Its [dated continuation check](../experiments/action_auc_audit_v1/journal.md#2026-09-21-continuation-check-values-match-source-identity-changed)
verifies original source/output hashes separately and confirms unchanged
accounting under the current code, without replacing historical records.
The timing options also change the generator source hash pinned by the
held-command audit. Its strict replay requires the original source snapshot;
the archived data, report and scientific conclusions remain unchanged.
The support-publication repair likewise changes hashes pinned by the timing
audits. Their strict source replay uses the original snapshot; the explicit
[compatibility receipt](../experiments/support_publication_v1/compatibility.json)
confirms all saved timing-pilot support values under the unchanged analysis
functions without rewriting the original records.
The later distance validator deliberately changes `analyze`; the preceding
publication-only AST verifier therefore uses its original source snapshot.
The [distance compatibility receipt](../experiments/support_distance_v1/compatibility.json)
confirms unchanged counts on four valid corpora, including signed indoor data.

Check current processes before launching work; no worker was active at this
review. The existing task owns the hourly follow-up. No remote push or
release was performed in this research-integrity work. Before any later
push, run whole-repository lint and dispatch manual CI as `AGENTS.md`
requires. Release tags remain the user's decision.

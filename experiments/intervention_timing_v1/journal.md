# Intervention timing v1 journal

## 2026-09-27 — registration and instrument preparation

Registration committed as `f8acc83`, before new generation, fitting or scoring.
The [definition](definition.md) freezes the four action-specific primary
cells, forward/world/now/veer guards, all six training runs and the response
to insufficient support. This is a new model study using the closed pilot
as development data, with a new common exam; no old experiment is reopened.

The new runner reuses the established model fitting/scoring routines, while
adding an explicit preflight gate and paired data recipes. Source/runtime,
input and all nine locked artifact identities are frozen in a manifest;
each stage requires a complete process log, actual zero exit and immutable
output receipt before the next stage. Every fit uses a fresh study path.

Instrument development initially failed a synthetic support fixture because
it omitted the support checker's required horizon/count schema. The full
failure log is retained at
`output/research_integrity_selftest/intervention_timing_v1_initial_selftest.log`
(actual selftest exit 1). Corrected fixtures exercise the actual strict
schema. During source review, room-local world-ID remapping and distinct
room/transit action catalogs were handled explicitly before any study data
was generated. No scientific reading was produced by the failed selftest.

The evaluator tests tied scores, undefined classes, every individual guard,
memory/latency vetoes, missing/nonfinite/inconsistent metrics, all seed
identities and exact export-to-corpus/probe coverage. Its primary bootstrap
is checked against a separate pairwise AUC oracle with shared course draws,
duplicate multiplicity and a course containing no primary windows. The
runner tests support boundaries, world/action failures, room remapping and
the no-fit response to insufficient support. These use synthetic data, no
locked checkpoint or model fitting.

The [prelaunch verification](prelaunch_verification.json) records ten checks,
all exit 0: the new runner/evaluator, six dependency selftests, whole-repo
Black (182 Python files), Ruff and diff whitespace. All nine locked artifact
hashes match. These are local macOS/Python 3.14 checks, not remote CI.
Runtime records belong in `records/`; support receipts and models belong
in `output/intervention_timing_v1/`. An active queue is not a result.

## 2026-09-27 — completed, NO-GO

Instrument source `ecb5796` launched one persistent background queue. All
23 registered stages completed on their first execution, each with actual
process exit 0 and a complete log. The outer queue records EXIT=0 and the
`intervention-timing-DONE` marker. There are no active workers or pending
fits, and no harness repair, scientific redraw or bar change was needed.

Rendering, exact training pairing and split preservation passed. All
prospective support floors passed on the first independent exam: 1,440
courses, 101,238 prediction windows and 1,404 geometric probe frames from
173 courses. The moving probe alone has 177 frames / 19 courses. All six
fresh 80-epoch fits then ran, followed by all six CPU score exports.

Primary macro deltas at seeds 0/1/2 are **+0.0190812092, +0.0347126303,
+0.0125798680**; mean **+0.0221245692** misses +0.03. Dense-right deltas are
**−0.0525712225, −0.0260235353, −0.0258849229**, all below −0.02. Dense-left
also fails seed 0 (−0.0236606371). Every other registered guard passes,
including pooled and per-world geometric ranking. This closes **NO-GO**;
the full [summary](summary.md) includes every action/guard and interval.

Each fixed pair's primary bootstrap has 2,000 valid draws / zero undefined
draws. The interval crosses zero for seeds 0/2; none prices training-draw
uncertainty. No bootstrap changes the verdict. All six bills remain
137.290039 KB / 3,856,768 MACs, estimated 7.713536 ms at 0.5 GMAC/s, without
hardware or flight certification.

The [evidence verifier](verify.sh) exited 0: all 23 receipts and actual
process-log identities pass, and it recomputes the entire preflight plus
all paired metrics/bootstrap/verdict from saved metadata and scores with
exact numeric parity. It performs no fitting or inference. All nine locked
artifact hashes still match. The full verifier log is retained at
`output/research_integrity_selftest/intervention_timing_v1_evidence_verify.log`.

Keep the approach default and champions. The next scientific question is
why dense-right discrimination loses while the geometric turn probe gains.
That requires a clearly exploratory diagnostic or a separately registered
new study, not rerunning these seeds or increasing this closed exam.

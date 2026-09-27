# Executed/CF agreement v1 journal

## 2026-09-27 — completed fixed metadata diagnostic

Registration `e04b52b` preceded target-agreement measurement. Instrument
`1c00412` adds only this audit and an artifactless CI selftest. It reuses
the original index, splitter, CF oracle and geometric selector without edits.
All seven [preflight checks](preflight_checks.json) pass on their first
recorded executions, including Black/Ruff across 184 Python files. Synthetic
fixtures independently distinguish geometry errors from visible conflicting
targets, masked disagreements and empty denominators.

The first audit and exact verification both exit 0, with full logs and exit
records in `output/executed_cf_agreement_v1/`. No real-data harness repair,
replacement measurement, extra slicing or change of tolerance was needed.
All nine geometry comparisons (three transit worlds × three input corpora)
pass the frozen 1e-4 m maximum-clearance error; largest error is
4.3074745859073005e-7 m. Stored training course memberships remain identical.

Immediate-exam dense-right has 84 answerable E1→CF0 disagreements among 690
windows, from ten courses; 464 additional windows are CF-masked. Candidate
training dense-right instead has 5/6/6 answerable disagreements at seeds
0/1/2, from 1/2/2 courses, mostly the opposite E0→CF1 direction. Control
training dense-right has zero. These are available-target counts, not
measured loss/gradient or score effects. All other original primary cells
are retained in the [summary](summary.md) and full report, including
moving-left's greater training disagreement despite improved model AUC.

Every selected geometric-probe frame agrees with CF safer-side truth and
has both labels answerable. No primary left/right held-window set shares
a frame with that forward-frame probe; some courses overlap. This makes
the distinction between the two evaluation domains explicit without
claiming that either metric is invalid or proves flight performance.

Nine protected artifact hashes and all original source/input identities
remain unchanged. The parent study's complete tracked-Python inventory now
contains two additional audit modules; no original manifest/result was
rewritten to hide that difference. This audit verifies all original saved
source hashes directly, independently of additional tracked modules.

Close this exploratory diagnostic. There is no new inference, fit, generated
course, score slice, bootstrap, promotion or default change. A further score
join or a training intervention requires a new declared scope/registration.

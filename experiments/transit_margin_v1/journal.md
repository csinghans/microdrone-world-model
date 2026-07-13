# transit_margin_v1 — the trigger's thresholds, refit on the quantized landscape

**Opened:** 2026-07-13 · **Prior:** `experiments/int8_parity_v1/`
(Q1, closed). B4's final verdict mapped the mechanism completely and
named exactly two legitimate re-openings: **re-fit the trigger's
MARGIN_WM/backstop on the QUANTIZED probability landscape (the
decision-layer analogue of temperature — the likeliest cheap win)**,
or QAT. This campaign is the first, as its own registration. The
public stake: README ships the sentence "the transit trigger does not
[fly quantized] — yet".

## The inherited map (Q1, all measured)

WMPolicy triggers an evasion when `edge ≥ MARGIN_WM (0.4)` OR
`imminent ≥ 0.5` — both float-tuned constants. Under PTQ the four
arms each fixed one clause and broke the other:

| arm | pooled Δcrash (bar +0.030) | false-evasion (float 0.028 pooled) |
|---|---|---|
| int8pc + split (K1c) | +0.083 ✗ | 0.056 ✓ |
| int8pc + split + p16 (K1d) | +0.000 ✓ | 1.000 ✗ |

False-evasion is an ANY-over-run statistic (one spurious margin among
~300 decisions flips a whole clear flight), and each arm shifts the
per-decision (edge, imminent) DISTRIBUTION differently — while the
thresholds stay where the float distribution put them. Hypothesis:
the thresholds are simply sitting at the wrong quantiles of the
quantized distributions, and moving them to the SAME OPERATING POINT
the float trigger occupies buys both clauses at once.

## K1 (one knob per arm): quantile-matched threshold refit

**The rule (frozen, closed-form, no search):** fly TRAIN flights
(seeds 3000+, n=40 → 28 in-path + 12 clear, disjoint from both exam
blocks and from every calibration corpus) with per-decision (edge,
imminent) traces, for the float components and for each arm. Compute
the float trigger's operating quantiles over ALL train decisions:
q_edge = P(edge_float ≥ 0.4), q_imm = P(imm_float ≥ 0.5). Each arm's
refit thresholds are the SAME quantiles of ITS OWN trace
distribution: MARGIN′ = Q_{1−q_edge}(edge_arm), IMM′ =
Q_{1−q_imm}(imm_arm). Marginal matching only — the OR-trigger's joint
rate is not exactly preserved; stated, not hidden. No parameter
search, no per-arm freedom beyond the two closed-form quantiles;
refit values are REPORTED.

**Arms (both pre-named survivors):** `int8pc+split` and
`int8pc+split+p16`. One refit each.

**Exam (unchanged, frozen):** re-fly both B4 blocks (seed0=1000 and
2000, n=60 each → pooled 84 in-path / 36 clear) with refit
thresholds. Float reference = the RECORDED same-tool arms (crash
17/84 = 0.202; false-evasion pooled 1/36 = 0.028) — the K1b/K1c
precedent.

**Bars (B4's own clauses, unchanged):** an arm PASSES iff pooled
Δcrash ≤ +0.030 AND false-evasion ≤ 0.10. Either arm passing ⇒ the
quantized transit trigger reaches closed-loop parity ⇒ the README's
"yet" is closable (artifact/deployment changes = owner's call).
Both failing ⇒ the cheap win is dead; the last named road is QAT
(priced, owner-gated), and the trigger-symmetry story gains its
final panel: not even operating-point transplantation tames an
any-trigger under PTQ.

**Machinery (defaults bit-identical, selftest-pinned):** `WMPolicy`
gains `margin=None / imm_thr=None / trace=None` (None ⇒ today's
constants, no trace); `eval_closed_loop.evaluate` gains
`wm_kwargs=None` passthrough; `eval_int8_parity` gains `--k2-margin`
(trace collection → closed-form refit → B4 re-fly → verdict).

## Status

- [x] Pre-registration (this file, before any number)
- [ ] K1: traces → refit (reported) → B4 re-fly both blocks → verdict

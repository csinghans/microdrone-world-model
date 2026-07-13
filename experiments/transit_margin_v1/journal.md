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

## K1 results (2026-07-13 — k2m_results.json)

Float operating point over 1,483 train decisions: P(edge ≥ 0.4) =
0.0472, P(imm ≥ 0.5) = 0.0182.

| arm | refit (margin / imm) | crash (Δ vs 0.202) | FE | verdict |
|---|---|---|---|---|
| int8pc+split | 0.4116 / 0.5645 | 0.2857 (**+0.083**) | 0.0556 ✓ | FAIL — and the refit was a NO-OP |
| int8pc+split+p16 | 0.4204 / 0.5123 | 0.2500 (**+0.048**) | **0.0556 ✓ (was 1.000)** | FAIL as written — borderline |

**Two deaths, two mechanisms:**
- The split arm's trace quantiles sit almost exactly on the float
  constants — its thresholds were never miscalibrated, so its +0.083
  crash excess is confirmed as DISTRIBUTIONAL damage at dangerous
  decision points (K1c's ReLU-remix mechanism, now measured a second
  way). No recheck: its pooled estimate already came from K1c's own
  pooling. REFUTED outright for this arm.
- The p16 arm is the first configuration EVER to hold both clauses
  near-simultaneously: a +0.02/+0.01 threshold shift collapsed
  false-evasion from the all-or-nothing 1.000 to EXACTLY the float
  value (the clear-run margin mass sat just above the old thresholds
  — the ANY-statistic flips whole flights on that sliver), at the
  price of +4 crashes in 84 (Δ+0.048, bar +0.030, inside the float
  CI ±0.086). This is K1c-block-1's exact situation, and the house
  rule applies: **borderline inside the reference CI → pool a fresh
  block, never replace.**

## K1 recheck (pre-registered before the block flies)

One fresh block, seed0=4000, n=60 (42 in-path / 18 clear), FLOAT and
the p16 arm flown same-run on paired seeds. **The refit thresholds
are FROZEN at 0.4204 / 0.5123 — nothing is refit on new data.**
Pooled verdict over n=126 in-path / 54 clear, same bars:
- pooled Δcrash ≤ +0.030 — integer form: (21 + a) − (17 + f) ≤ 3.78,
  i.e. the arm needs **a ≤ f − 1** on the fresh block (at least one
  fewer crash than float);
- pooled FE ≤ 0.10 — (2 + x)/54, i.e. x ≤ 3 fresh false-evasions.
PASS ⇒ parity by pooling, the campaign lands. FAIL ⇒ REFUTED stands:
thresholds recover the operating point but not the distribution's
shape near the trigger; the last named road is QAT (owner-gated), and
the trigger-symmetry story gains its final panel.

## Status

- [x] Pre-registration (this file, before any number)
- [x] K1: refit + both blocks → **split REFUTED outright (refit
      no-op = threshold story dead for it); p16 borderline
      (FE 1.000 → 0.0556, Δcrash +0.048)** → house recheck
- [ ] K1 recheck: fresh block @4000, frozen thresholds, pooled n=126

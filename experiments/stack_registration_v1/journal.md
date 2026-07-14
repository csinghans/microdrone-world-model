# stack_registration_v1 — adopting the mgap RL arm into the deployed lineup

**Opened:** 2026-07-14 · **Owner sanction:**「go terminal-commit 訓練臂」
— read per the mgap_rl_v1 review verdict: the terminal-commit arm's two
training incarnations are both closed (BC 11.1 %, RL 8.9 % — the
perception tax), and what the review left open is exactly this:
*"adoption is deferred to the stack's own registration, which will
judge components by the stack's exam, not by this arm's missed
ambition."* This file is that registration.

**The stack under registration (one slot changes):** HYBRID with
`moving_gap = experiments/mgap_rl_v1/artifacts/ppo_mgap_rl.zip`
(the RL-from-success arm: mgap seam 17.2 → 8.9 % true, conditional
0.887 → 0.938, wins 97/120 = 0.808 pooled — the best graduation-level
composite measured on this line). Every other slot, the settle brake,
and every champion sha: untouched.

**Prior evidence (why this registration exists):** the arm's own
pooled n=120 fresh-course graduation already measured the whole
lineup with this exact swap — genuine mgap lift, slalom guard
comfortable (0.855 vs 0.82 true-rate anchor), no coupling damage,
the held re-DAgger ticket never spent. The formal below is the
ceremony of record, not the discovery.

**Honest target statement:** the arm's measured value is +2.5–3 TRUE
points on the k=3 gate (true composite ~0.775–0.78 → ~0.80–0.81).
The 0.84 challenge line stays OPEN beyond this registration — the
slalom half of that ambition died in slalom_rl_v1 (honest double
negative). This registration banks the half that exists.

## Bars (frozen before any number)

- **Instrument check (not a bar, logged):** `eval_integration
  --selftest` green (pins `--swap` semantics) + wiring smoke n=10
  @**156000** with the swap — the lineup loads and flies; no read of
  any bar from it.
- **FORMAL n=100 @ the standing 110000 exam** (one read — this is
  the registration's single spend of exam hygiene):
  `eval_integration --suite 100 --contender hybrid
  --swap moving_gap=<the zip> --seed0 110000`.
- **PASS = score ≥ 80** (record 79 + 1; predicted band 80–84 from
  true ~0.80–0.81) **AND all guards**, every anchor a pooled true
  rate minus a 0.05 draw allowance (the standing anchor rule, third
  bite's lesson):
  - slalom conditional ≥ **0.767** (true 0.817)
  - door ≥ **0.919** (true 0.969), gap ≥ **0.912** (true 0.962),
    opening_door ≥ **0.888** (true 0.938)
  - **mgap conditional ≥ 0.887** — the OLD slot's true rate: the
    adoption claim itself must show on the exam, else the swap
    bought paper only.
- **GRAY = 78–79 with guards green:** no promotion on a tie-or-worse
  draw; the read banks as evidence beside the n=120 pool; any second
  attempt needs fresh justification (never a re-read of 110000).
- **REFUTED = < 78 or any guard tripped:** record stays 79; the arm
  stays evidence.
- **On PASS (promotion, the R3 precedent):** `HYBRID["moving_gap"]`
  in `eval/eval_integration.py` re-points at the RL zip (in place,
  sha-stable, like `_SLALOM_R3`); `scripts/gate.py` TRANSIT_RECORD
  re-anchors to the new formal JSON; scorecard quick layer re-run
  green; CHANGELOG. The k=6 read (0.500) is a different, unpromoted
  instrument and does not move.

**Seeds:** 156000 = wiring smoke (spent here); 110000 = the one
formal read. 152000+ (re-DAgger ticket) untouched.

## Instrument checks

`eval_integration --selftest` green (swap semantics pinned); wiring
smoke n=10 @156000: 9/10, lineup loads and flies. No bar read.

## Formal verdict (n=100 @110000, one read) — PASS

`formal_n100.json`: **score 85/100** (PASS ≥ 80; predicted band
80–84 — the draw sits one point above the band's top, ~+1σ on true
~0.80–0.81, noted honestly: the TRUE gain is the arm's pooled n=120
measurement, the 85 is this exam's draw of it). Guards, all green,
every anchor a pooled true rate:

| slot | formal conditional | guard | |
|---|---|---|---|
| **moving_gap (the swap)** | **52/55 = 0.9455** | ≥ 0.887 (old true) | ✓ the adoption claim shows |
| slalom | 66/72 = 0.9167 | ≥ 0.767 | ✓ |
| door | 50/51 = 0.9804 | ≥ 0.919 | ✓ |
| gap | 54/57 = 0.9474 | ≥ 0.912 | ✓ |
| opening_door | 49/51 = 0.9608 | ≥ 0.888 | ✓ |

**Promoted 2026-07-14** (the R3 precedent): `HYBRID["moving_gap"]` →
`experiments/mgap_rl_v1/artifacts/ppo_mgap_rl.zip`
(sha256 `2bbedc5c83955c51321d5b629d0aade388324be880504213e49f3a91d13ab916`);
`scripts/gate.py` TRANSIT_RECORD → this campaign's `formal_n100.json`;
README + CHANGELOG carry 85/100 with lineage 79 → 72. The 79/100
record file stays in the tree as lineage. Publishing the zip to the
champions release awaits the owner's explicit release word.

The arc, for the ledger: the k6 investigation found the flinch (K5),
the oracle priced it (K6, +11 at k=6), two training arms measured the
perception tax (BC 11.1 %, RL 8.9 % vs ~4 %), the arm's own
registration refused it by 0.4 — and THIS registration, judging by
the stack's exam instead of the arm's ambition, banked the half of
the oracle's gain that perception permits: **79 → 85**.

## Status

- [x] Pre-registration (this file, before any number)
- [x] Instrument: selftest + wiring smoke @156000 (9/10, loads clean)
- [x] Formal n=100 @110000: **85/100 PASS, guards all green →
      PROMOTED; gate of record re-anchors 79 → 85**

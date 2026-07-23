# assist_v3 — the certified takeover: does a better relief pilot flip the ladder's sign?

Opened 2026-07-23, on the chapter's banked law (assist_v2, commit
a1baba4): *a guardian is only as good as its eyes in context and the
pilot it swaps in.* v1 flew the ladder with the weakest relief pilot in
the house (WMPolicy hand-MPC, vision-only) and the ladder poisoned the
cockpit. v2 removed the ladder and halved the harm. The oracle contrast
showed escalation is PROTECTIVE when the takeover pilot is good. This
campaign swaps in the strongest takeover artifact the repo owns — the
transit champion (`ppo_wm_policy_edge_hard_xp`, latent-consistent on the
champion WM) — and asks whether the ladder's sign flips where that
artifact is measured-better than the pilot.

The measured context split, from v1's full-auto reference on these very
seeds: the champion flies CLASSIC at 0.00 crash (better than every
persona, incl. novice 0.10-0.15) and DENSE at 0.40-0.45 (WORSE than
every persona, 0.15-0.30). If the law is right, the champion-takeover
ladder should help on classic and still fail dense — the sign should
follow the takeover-quality split, not the ladder.

## Pre-registration (committed before any number)

### Protocol

- Arm: `ladder_champion` — full ladder (escalation ON, deployed
  triggers), guardian eyes = champion WM, AUTO rung = ChampionTakeover
  (the champion policy with its 12-decision history stack riding the
  EXECUTED command via `exec_feedback` — the dispatch law, asserted in
  the authority selftest). One knob vs v1's wm_champion arm: the AUTO
  artifact. Latent-consistent by construction (champion WM everywhere).
- Cells: the full grid (12 + moving diagnostic), n = 20 paired,
  **the same probe seeds a third time, deliberately** — v1 (ladder +
  weak takeover), v2 (no ladder) and v3 (ladder + strong takeover)
  become three arms of one paired experiment on identical courses and
  pilot streams. No bars were ever frozen on these seeds; the
  certification gate, if released, flies fresh (+500, still virgin).
  Full-auto reference not reflown (v1's column stands, same seeds).

### Pre-registered predictions (falsifiable)

- **P1 (the sign lives in the takeover, classic half):** pooled on the
  six classic cells, `added <= 4` AND `dcrash <= 0`. Baselines on the
  same seeds: v1 wm_champion classic added 30; v2 veto-only classic
  added 14. Mechanism: most v1 classic harm was flights escalated into
  a weak flyer; escalated flights now inherit a 0.00-crash artifact, so
  residual harm ~= the pre-escalation veto window only.
- **P2 (net guardian value where takeover is certified-better):** on
  classic@1.5/novice (the one usable classic cell, crash_u 0.15):
  `prevented >= 2` AND `added <= 1`.
- **P3 (the sign lives in the takeover, dense half):** pooled dense
  `added >= 5` — a 0.40-crash relief pilot cannot clear the sacred
  guard no matter how good the ladder is. If REFUTED (dense added < 5),
  that is an upside surprise worth its own analysis before any claim.
- **P4 (moving diagnostic, unbarred):** `added == 0` AND `dcrash <= 0`
  — v1's wm_champion arm already helped on moving (-0.200) with the
  WEAK takeover; the strong takeover should not be worse. (Champion
  full-auto ref on moving: 0.35 vs pilot 0.50.)

### Frozen decision rules

1. **Certification release (classic-scoped config):** IF pooled on the
   six classic cells: `added == 0` AND `dcrash <= 0` AND median
   `frac_auto` over clean-unassisted seeds `<= 0.5` (the guardian must
   not confiscate the stick on flights that needed nothing) — THEN
   freeze gate bars FROM this probe in their own commit and fly the
   certification gate on fresh seeds (+500), n = 30 paired, classic
   cells only. ELSE: record, close v3. Note the strictness split: P1
   (<=4) measures the MECHANISM; certification demands the sacred 0.
2. **K1 (analysis-only, zero new flights):** released iff P1 AND P3
   both hold. Compose the context-scoped deployment ledger from
   measured cells — ladder_champion on classic + veto-only (v2) on
   dense — and report it as the honest "what could ship" table, with
   the deployment caveat stated: the context split is sim-labelled;
   a real drone needs an online context signal (a dispatch-class
   classifier is the named candidate) before any such scoping is a
   product claim.
3. FI is reported, not barred: on a ladder arm FI saturates
   mechanically (any escalated seed counts), so the freedom meters of
   record are `frac_auto` on clean seeds + handback availability.

### Honesty clauses

Inherited from assist_v1/v2 verbatim (closed-loop divergence after
first intervention; mechanisms reproduce, third decimals don't; FI is
a freedom meter, not a harm meter). New for v3: the champion policy is
the DEPLOYED transit artifact — if this arm certifies, the assisted
mode's AUTO rung binding changes from WMPolicy to the champion pair,
which is a `planner/flight_mode` + docs change gated on the
certification, never a silent swap.

---

(verdict lands below when the probe completes)

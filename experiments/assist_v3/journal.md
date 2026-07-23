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

---

## Probe verdict — 2026-07-23: P3/P4 confirmed, P1/P2 refuted; no certification; the law holds at cell granularity

Flown as pre-registered (n=20 paired, the same seeds, single arm
ladder_champion; probe_champion_takeover.json).

| prediction | bar | read | verdict |
|---|---|---|---|
| P1 classic: takeover flips the sign | added <= 4 AND dcrash <= 0 | **11**, +0.058 | **REFUTED** |
| P2 net value on classic@1.5/novice | prev >= 2 AND add <= 1 | 2 / **2** | **REFUTED** (by one crash) |
| P3 dense still fails | added >= 5 | 16 | **CONFIRMED** |
| P4 moving no-worse | add == 0 AND dcrash <= 0 | 0, -0.150 | **CONFIRMED** |

Certification: NOT released (classic added 11 != 0; the frac_auto
clause goes untested — the added clause already fails; classic means
0.24-0.51 reported for the record). K1: NOT released (P1 refuted).

### What the third campaign bought

1. **The takeover-quality monotone, on identical seeds** (classic
   pooled added): weak-takeover ladder 22-30 (v1) -> no ladder 14 (v2)
   -> champion ladder **11** (v3). Harm falls monotonically with
   takeover quality — the law's direction confirmed — but the sacred
   guard stays unmet: the residual classic harm is the veto window +
   authority transitions, the same magnitude v2 measured with no
   ladder at all. Closing IT is an eyes problem, not an authority
   problem.
2. **The sign follows the pilot-vs-relief differential, cell by
   cell.** dense@1.5/novice (pilot 0.80 vs champion 0.45 — the relief
   is STRONGER): dcrash -0.200, prevented 5, added 1, lead 1479 ms —
   the chapter's first genuinely helped hard cell. dense@1.5/average
   (pilot 0.25 vs 0.45 — the relief is WEAKER): +0.200, added 5. The
   guardian helps exactly where its relief pilot outflies THIS pilot,
   not where the world is easy. That is the banked law, now visible at
   cell granularity.
3. **Moving stays a quiet win for champion-eyes arms** (v1 -0.200,
   v3 -0.150, prevented 3, added 0 — diagnostic column, logged).
4. The measured "who is it FOR" pocket: with today's stack, assistance
   pays for pilots WORSE than the relief artifact in that context
   (the novice-at-speed-in-clutter cell), and taxes pilots better than
   it. Deployment would need an online estimate of BOTH context and
   pilot quality — named, not claimed.

### Disposition

assist_v3 closes as the third recorded negative. The authority side of
the chapter is now exhausted honestly: ladder off/on and takeover
weak/strong are all priced on identical seeds. Every remaining road
runs through the EYES — the dense over-report and a guardian-specific
trigger operating point are representation-class work (v0.14's named
quarterly road). The chapter's law survives its third test and gains
its finest-grained evidence.

Run-to-run caveat: mechanisms reproduce, third decimals don't; n=20.

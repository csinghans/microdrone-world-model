# assist_v4 — the last cheap eyes knob: the hard-veto operating point

Opened 2026-07-23, on assist_v3's close (commit be2f885): the authority
side is exhausted (ladder off/on, takeover weak/strong — all priced on
identical seeds), every remaining road runs through the EYES. Before the
representation-class road opens, the house rule applies: **kill the last
cheap knob first** (the clutter_governor precedent that closed the dense
frontier's cheap-knob era). Three campaigns swept the escalation margin
and the ladder shape; the HARD trigger — `imm_thr`, the threshold every
veto fires through, where ALL of v2's residual harm originates — has sat
at the deployed 0.5 throughout. This campaign sweeps it.

Mechanism question: v1 named the dense over-report as the veto's false
trigger. If the over-report is a mild inflation, a stricter threshold
(0.7 / 0.9) should cut the false fires faster than the true saves — a
certifiable operating pocket could exist. If the over-report SATURATES
(the known blind-spot mechanism: "when the drone is already deep in
trouble every candidate saturates together" — and its converse, clutter
pushing clean threading to high crit), thresholds change little and the
cheap-knob era of this chapter closes.

## Pre-registration (committed before any number)

### Protocol

- Arm: `wm_unified`, VETO-ONLY (escalate=False — v2's configuration,
  the cleanest reader of trigger quality; no takeover confound), at
  `imm_thr` in {0.7, 0.9}. The deployed 0.5 level is v2's committed
  record on the same seeds (added 29, prevented 16 static; per-cell
  table in experiments/assist_v2/). Everything else at deployed
  constants.
- Cells: the full grid (12 + moving diagnostic), n = 20 paired, the
  same probe seeds — the fourth arm-set of one paired experiment. No
  bars were ever frozen on these seeds; a certification gate, if
  released, flies fresh (+500, still virgin). No full-auto reference
  reflown.

### Pre-registered predictions (falsifiable)

- **P1 (dose-response on harm):** pooled static `added` falls
  monotonically: added(0.9) <= added(0.7) <= 29.
- **P2 (the saves die slower than the harm, or not):** pooled static
  `prevented` at 0.7 >= 8 (half of v2's 16). If prevention collapses
  faster than harm, the trigger has no useful operating region.
- **P3 (the pocket exists?):** SOME level achieves pooled static
  `added <= 2` AND `prevented >= 3`. Honest prior: REFUTED — the
  saturation mechanism predicts high-crit false fires survive 0.9 in
  dense, and classic@1.5's mid-thread disruptions fire at
  already-high crit. The data may surprise us; that is what the probe
  is for.
- **P4 (moving diagnostic, unbarred):** added stays 0 at every level
  (raising the threshold can only quiet the already-quiet mover arm).

### Frozen decision rules

1. **Certified operating point** = the LOWEST swept level achieving
   pooled static `added == 0` AND pooled static `prevented >= 3`.
   If one exists: freeze gate bars FROM this probe in their own
   commit; certification gate flies the v1-primary + any
   added==0-with-prevented>0 cells at that level, n = 30 paired,
   fresh seeds (+500). If none: **the assisted chapter's cheap-knob
   era closes** — the eyes road is representation-class only, and the
   chapter's standing verdict (mechanically sound ladder, no
   deployable WM trigger) becomes final for this WM generation.
2. FI / override_rate reported at every level (the freedom side of the
   dose-response curve — the journal's ADAS tradeoff figure), never
   barred.

### Honesty clauses

Inherited from assist_v1-v3 verbatim. The sweep is TWO levels plus the
committed 0.5 record — a dose-response read, not a search; the
selection rule is frozen above, before any number, and picks by rule,
not by taste.

---

(verdict lands below when the probe completes)

---

## Probe verdict — 2026-07-23: P1/P2 confirmed, P3/P4 refuted; no operating point; the cheap-knob era closes

Flown as pre-registered (n=20 paired, same seeds, veto-only wm_unified
at imm_thr 0.7 and 0.9; probe_imm07.json / probe_imm09.json; v2's
committed record is the 0.5 dose point).

| prediction | bar | read | verdict |
|---|---|---|---|
| P1 harm monotone | added(0.9) <= added(0.7) <= 29 | 9 <= 21 <= 29 | **CONFIRMED** |
| P2 saves survive 0.7 | prevented(0.7) >= 8 | 9 | **CONFIRMED** |
| P3 the pocket exists | some level: added <= 2 AND prev >= 3 | 21/9, 9/6 | **REFUTED** (per the honest prior) |
| P4 moving stays quiet | added == 0 at every level | 1 @0.7, 0 @0.9 | **REFUTED** (one crash, noise-scale, bar is the bar) |

Selection rule: NO level achieves pooled added == 0 with prevented >= 3
— **no certification. The assisted chapter's cheap-knob era closes.**

### The dose-response, read

- The trigger can be made QUIET, not ACCURATE: harm falls 29 -> 21 -> 9
  but never reaches 0 — at 0.9 the dense cells still add 6 (the
  saturation mechanism confirmed: clutter pushes clean threading's crit
  past any threshold). Prevention falls with comparable elasticity
  (16 -> 9 -> 6): there is no separating operating region on this
  ROC. At 0.9 classic goes fully quiet (override_rate 0.00-0.06,
  added 0-1) — and prevents nothing there either.
- The recurring pocket signature, third appearance: dense@1.5/novice
  reads prevented 4 / added 0 at 0.9 (v3's champion ladder read -0.200
  on the same cell; v2 read 2/2). For the WORST pilot in the WORST
  place, even imperfect help pays; everywhere else it taxes. A single
  n=20 cell is reported, never cherry-picked into a bar.
- Freedom side for the record (override_rate, dense@1.5 range):
  0.33-0.46 @0.5 -> 0.20-0.37 @0.7 -> 0.10-0.20 @0.9.

### Disposition — the chapter's standing verdict becomes final for this WM generation

Four campaigns, four honest negatives, every cheap knob priced on one
paired seed set: the ladder shape (v1), the takeover rung (v2, v3), and
the trigger operating point (v4). The law survived every test and
gained cell-level and dose-level evidence. What remains is exactly what
v0.14 named for the autonomy chapter: REPRESENTATION — eyes that do not
saturate in clutter. Until that generation of WM exists, the assisted
chapter ships what it has: a certified authority machine, a keyboard
cockpit, a paired-seed instrument set, and a law with a price list.

Run-to-run caveat: mechanisms reproduce, third decimals don't; n=20.

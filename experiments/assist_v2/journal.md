# assist_v2 — pricing the rungs: the veto-only ablation

Opened 2026-07-23, on assist_v1's recorded negative (`gate(assist_v1):
probe — NO-GO`, commit 5aa4634). v1 named two candidate mechanisms for the
WM guardian's added crashes: (1) the ESCALATION rung hands a privileged
pilot to a vision-only autopilot that is worse in dense; (2) the measured
dense over-report fires the imminent VETO on normal gap-threading. The two
were confounded in the full ladder. This campaign un-confounds them with
one zero-training knob: `escalate=False` — the momentary hard veto stays,
the AUTO rung never arms. **Every rung of the authority ladder gets its
own price.**

## Pre-registration (committed before any number)

### Protocol

- Arms: `wm_unified` (the contender's eyes) and `oracle` (perfect eyes),
  both veto-only. `wm_champion` is dropped (v1 priced it at ladder level:
  same failure shape as unified; its one curiosity — moving@1.0 helped —
  stays a logged v1 note).
- Cells: the full v1 grid (12 + moving diagnostic), n = 20 paired.
- **Seeds: THE SAME v1 probe seeds (800000 + cell_idx*1000 + i),
  deliberately.** This makes full-ladder (v1 record) vs veto-only (this
  probe) an arm-vs-arm comparison on identical courses and identical pilot
  streams — per-seed attributable, like every pairing in this track. No
  bars were ever frozen on these seeds (v1's gate never opened), so no
  gate read is being double-dipped; any v2 CERTIFICATION gate flies fresh
  seeds (+500, still virgin). The full-auto reference is not reflown
  (--no-ref): v1's column stands on the same seeds.
- Triggers: deployed constants (imminent 0.5, fence 2.4, hold 6 decisions).
  The escalation margin is moot with the ladder off.

### Pre-registered predictions (falsifiable, wm_unified unless stated)

- **P1 (the takeover was the dominant poison):** pooled `added` across the
  12 static cells <= 3 — i.e. <= ~20% of v1's full-ladder 18. Rationale:
  in a STATIC world a momentary brake/veer substitution is locally safe;
  the systemic harm came from swapping the flyer.
- **P2 (the over-report is trigger-level, not ladder-level):** FI stays
  > 0.5 on every dense cell — vetoes still fire on clean threading; the
  ladder was not the reason the eyes cry wolf.
- **P3 (a modest real guardian survives on the recoverable cells):** on
  v1's two primary cells (classic@1.5/novice, dense@1.0/novice),
  veto-only wm_unified achieves `added == 0` AND `prevented >= 1`.
- **P4 (braking is NOT intrinsically safe against movers):** the
  moving@1.0 diagnostic shows `added >= 1` — a hover/slow substitution in
  front of a crosser is its own hazard; the static-world safety of the
  veto does not generalize. Diagnostic column, never barred.

### Decision rules (frozen before numbers)

1. **Certification release:** IF veto-only wm_unified achieves pooled
   `added == 0` across ALL 12 static cells AND FI <= 0.15 pooled on the
   six classic cells, a deployable "veto-only assist" configuration
   exists: freeze gate bars FROM this probe in their own commit and fly
   the certification gate on fresh seeds (+500). ELSE: record the
   attribution and close v2 — no gate, no bars.
2. **K1 (analysis-only, zero new flights):** released iff P1 holds.
   Compare v1 full-ladder vs v2 veto-only on the six CLASSIC cells (same
   seeds): if the full ladder added more crashes than veto-only even
   where the champion full-auto reference is clean (0.00), the harm is
   the DEPLOYED AUTO rung (WMPolicy hand-MPC), not autonomy per se — the
   "humility gate" must key on the certified takeover artifact, and the
   named follow-up is a champion-policy takeover arm (latent-consistent:
   champion policy on champion WM, i.e. the wm_champion stack), which
   would need its own campaign.

### Honesty clauses

Inherited from assist_v1 verbatim: paired arms diverge after the first
intervention (closed-loop comparison, not per-decision counterfactuals);
mechanisms reproduce, third decimals don't; the WM's collision domain is
pillar transit; FI counts ANY override on a clean seed — it is a freedom
meter, not a harm meter (the harm meter is `added`).

---

(verdict lands below when the probe completes)

---

## Probe verdict — 2026-07-23: P2 confirmed, P1/P3/P4 refuted; no certification; the rungs are priced

Flown as pre-registered (n=20 paired, the SAME v1 seeds, arms
wm_unified/oracle, ladder OFF; probe_veto_only.json). The unassisted arm
reproduced v1's crash_u BIT-FOR-BIT on all 13 cells — the paired
protocol's cross-campaign determinism is itself now a measured fact.

| prediction | bar | read | verdict |
|---|---|---|---|
| P1 takeover-dominant | pooled added <= 3 (12 static cells) | **29** | **REFUTED** |
| P2 trigger-level over-report | dense FI > 0.5 everywhere | 0.57-1.00 | **CONFIRMED** |
| P3 modest guardian on primary cells | added==0 AND prev>=1 | 2/6 and 3/2 (prev/add) | **REFUTED** |
| P4 braking unsafe vs movers (wm arm) | moving added >= 1 | added=0, prev=1 | **REFUTED** |

Prereg drafting flaw, recorded: P1's annotation ("~20% of v1's 18")
mis-scoped the v1 baseline — 18 was the primary-cells pool; the 12-cell
full-ladder pool is 64. The BAR (<= 3) is what binds, and the verdict is
identical under any reading (29 > 13 > 3).

### The attribution, priced

- **The ladder owns roughly half the harm:** full-ladder added 64 ->
  veto-only 29 on identical seeds. Removing the takeover also removed the
  catastrophic tail (dense@1.0/average: 10 added -> 0).
- **The naked veto's price scales with speed:** veto_unified @1.0 =
  prevented 7 / added 5 (near break-even, added 0 across ALL of
  classic@1.0); @1.5 = prevented 9 / **added 24**. A 0.5 s substitution
  hold at 1.2 m/s displaces ~0.6 m mid-thread — the intervention is
  itself a speed-class trajectory perturbation.
- **Perfect eyes flip the ladder's sign:** on dense@1.0 the full-ladder
  ORACLE (added 0/3/0 by persona) beat the veto-only ORACLE (3/4/1) —
  when the takeover pilot is good, escalation is protective; when it is
  bad (v1's vision-only WMPolicy), it is the dominant poison. **The
  guardian is only as good as (a) its eyes in context and (b) the pilot
  it swaps in.** That sentence is the chapter's measured law.
- **P4's inversion is honest blindness:** the WM arm barely fires on
  movers (override_rate 0.06 — the v2 single-frame latent carries no
  velocity), so it barely harms and occasionally brakes usefully
  (dcrash -0.05). The predicted brake-into-crosser mechanism surfaced in
  the ORACLE arm instead (added 3): its constant-velocity forward sim is
  wrong geometry for movers — the instrument's static-only label, now
  measured. Preventions with leads 552-632 ms on the primary cells show
  the anticipation channel works when the eyes are right.

### Disposition (per the frozen decision rules)

Certification rule: NOT released (added 29 != 0; classic FI 0.25-0.94 vs
<= 0.15). K1: NOT released (P1 refuted). **assist_v2 closes with the
attribution complete and no deployable configuration.** The assisted
chapter's honest state after two campaigns: the authority ladder is
mechanically sound (safety rows green; the oracle proves the ceiling),
but at today's calibration and takeover quality NO WM-triggered
intervention clears the added==0 sacred guard on transit worlds. The
priced follow-up roads, each its own future campaign:

1. **A certified takeover artifact** — the champion policy on the
   champion WM (latent-consistent wm_champion stack) as the AUTO rung,
   gated on the full-auto reference for the context; the oracle contrast
   says this is where the ladder's sign lives.
2. **Eyes before authority** — the dense over-report is the same
   context-conditional miscalibration head_calibration measured;
   a guardian-specific operating point is representation-class work
   (v0.14's named quarterly road), not a threshold sweep (v1's margin
   sweeps already refuted the cheap version).
3. **Speed-scoped assistance** — the veto is near-break-even at 0.8 m/s
   and harmful at 1.2 m/s; any future deployment claim scopes to the
   measured speed pocket, mirroring the indoor track's ROBUST_SPEED
   discipline.

Run-to-run caveat: mechanisms reproduce, third decimals don't; n=20/cell.

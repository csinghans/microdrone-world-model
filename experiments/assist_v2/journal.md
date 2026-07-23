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

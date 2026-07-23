# assist_v1 — the Level-3 chapter: what does anticipation buy a HUMAN pilot?

Opened 2026-07-23. Transit and indoor search fly Level-4 — the AI holds the
stick end to end. This campaign opens the third chapter: a pilot flies, the
world model watches every command ("and if THIS command is held?"), and an
authority ladder (`planner/authority`) intervenes — momentary substitution
on the imminent backstop, escalation to AUTO on sustained danger, gated
handback. The repo's wedge, spent on someone else's intent: **how much of a
pilot's crash mass can 0.67 s of embedded anticipation buy back, and at
what price in freedom?**

## Pre-registration (committed before any probe number)

### The instrument: the synthetic pilot family (`assist/pilot.py`)

Privileged-vision, imperfect-execution pilots — OracleField competence core
+ a frozen pipeline (distraction -> fat-thumb noise -> reaction delay),
deterministic per (persona, seed). Personas are instrument constants,
frozen with the tool:

| persona | delay (ticks @12 Hz) | noise_p | distract_p / len | deadband |
|---|---|---|---|---|
| expert  | 1 (83 ms)  | 0.00 | 0.005 / 4  | 0.12 m |
| average | 2 (167 ms) | 0.03 | 0.020 / 6  | 0.18 m |
| novice  | 4 (333 ms) | 0.08 | 0.040 / 10 | 0.25 m |

Bring-up rule (pre-declared): this table may be adjusted ONCE, on the
uncommitted bring-up smoke (scratch seeds 850000, outside every measured
block), if Stage A's usable band comes up empty; after this commit it is
frozen.

**Bring-up smoke, flown 2026-07-23** (n=6/cell, scratch seeds, six corner
cells — instrument validation only, no committed claims): crash_u =
classic@1.0 expert 0.00 / novice 0.17; classic@1.5 average 0.00;
dense@1.0 average 0.17; dense@1.5 expert 0.83 / novice 0.83. The dynamic
range spans the usable band and dense is usable at BOTH speeds, so the
table freezes AS-IS — the one permitted adjustment goes unspent. Note
dense@1.5 sits at the band's top edge even for the expert persona,
consistent with v0.14's kinematic-floor verdict; the oracle arm exists to
price exactly that.

### Cells and seeds

- Grid: personas {novice, average, expert} x worlds {classic, dense} x
  speeds {1.0, 1.5} = 12 cells, plus ONE labelled diagnostic column
  `moving@1.0/average` (the v2 latent carries no mover velocity — measured
  boundary, so the moving read is reported, never barred).
- n = 20 paired per cell per arm at the probe; seeds
  `800000 + cell_idx*1000 + i` (virgin block, ledger-disjoint — asserted in
  `eval.eval_assist_gate` selftest). Gate seeds = probe + 500, never reused.

### Arms (Stage B), all zero-training

- `wm_unified` — THE CONTENDER: vision-only Guardian on
  `world_model_unified.pth` (the stronger anticipator, AUC@32 0.931, and
  the embedded-path artifact), WMPolicy takeover on the SAME latent.
- `wm_champion` — control on `output/world_model.pth` (unified carries a
  6% false-evasion prior from v0.8; the control prices it).
- `oracle` — PRIVILEGED CEILING, never a contender: constant-velocity
  forward sim of each menu command over the WM's own horizons, emitted in
  the collision heads' vocabulary; same ladder, perfect eyes. Crashes even
  THIS arm cannot prevent are kinematically committed (the v0.14 lesson:
  by the time any signal fires, the conflict may already be committed).
- Full-auto reference column: the transit champion
  (`ppo_wm_policy_edge_hard_xp`, champion WM) on the same seeds, per
  (world, speed) — the Level-4 datum the Level-3 numbers sit against.
- Triggers fly the DEPLOYED constants (margin 0.4, imminent 0.5,
  escalate 3-of-5, handback 12-clear). One labelled characterization sweep
  margin in {0.3, 0.4, 0.5} on `wm_unified` only — it informs the journal
  (the ADAS tradeoff curve), never the bars.

### The paired protocol and its honesty clause

Each seed is flown bare and guardian-wrapped with the SAME pilot rng:
`prevented` / `added` / `false_intervened` are per-seed attributable. The
arms are identical up to the first intervention; after divergence the
comparison is between closed-loop systems, not per-decision counterfactuals
— worded once here, inherited by every claim. Run-to-run variance:
mechanisms reproduce, third decimals don't (two-tier claim language).

### Stage A — the pilot map (instrument validation, rules pre-declared)

- A cell is USABLE iff unassisted `crash_u in [0.15, 0.85]` (mass to
  prevent; not hopeless).
- Coherence (reported, not gated): crash_u monotone
  novice >= average >= expert within each world x speed.
- If NO dense cell is usable, the single bring-up adjustment fires and
  Stage A reruns on a fresh sub-block (+100) — recorded as instrument
  repair, OracleFieldSlow-style.

### Frozen selection rules (declared before numbers exist)

1. PRIMARY GATE CELLS = usable cells where the oracle arm cuts at least
   half the paired crash mass (`oracle_dcrash <= -0.5 * crash_u`). Cells
   the oracle cannot halve are the kinematic floor at that speed —
   reported, excluded from bars.
2. GATE WM = the WM arm (unified vs champion) with the larger pooled
   `prevented` on primary cells, subject to pooled `added == 0` AND pooled
   `FI <= 0.15`; tie -> unified (the embedded-path artifact).
3. K0 BARS are frozen FROM the probe in their own follow-up commit
   (the indoor-gate pattern). Non-binding priors, for calibration only:
   rel_cut >= 0.5 on primary cells; FI <= 0.15; override_rate <= 0.15;
   goal_pct <= +0.20; added == 0 (sacred-guard shape — assistance must
   never create a crash the pilot avoided).

### K0 (shape frozen now; numbers frozen post-probe)

- Hypothesis: on the primary cells, the zero-shot vision-only WM guardian
  cuts the paired crash rate by >= X% relative while overriding <= Y% of
  decisions, with ZERO crashes added on paired clean seeds.
- Read: n = 30 paired per primary cell, fresh seeds (probe + 500).
  Borderline (within 0.08 of any bar) -> fresh block, POOLED to n = 60
  (pool, never replace).
- Report alongside (context columns, not bars): oracle recovery fraction
  (`dcrash / oracle_dcrash`), guardian lead_ms, the full-auto reference,
  handback latency distribution, escalation/chatter counts.

### K1 (conditional — the release condition is the pre-registration)

Released ONLY if K0's traces show >= 30% of residual assisted crashes
carrying the re-entry chatter signature (>= 2 override onsets within 12
decisions before the crash). One knob: the escalation ablation — v1 flies
the full ladder (escalate 3-of-5); K1 flies `escalate=False` (veto-only)
on the same cells to price what the takeover rung itself buys. Same bar
shape, fresh sub-block.

### What would refute the chapter's premise

If the oracle arm cannot cut half the crash mass on ANY cell, the pilot's
crashes are kinematically committed before any 0.67 s trigger can fire —
then assisted flight at these speeds is a horizon problem (a WM_HORIZONS
retrain question), not a guardianship problem, and the honest verdict says
so. If the oracle can but `wm_unified` recovers < half of the oracle's cut,
the gap is perception, and the next knob is eyes, not authority.

---

(verdict blocks land below as the campaign runs)

---

## Probe verdict — 2026-07-23: NO-GO for K0 (no qualifying WM arm); the oracle prices two recoverable cells

Flown as pre-registered: n=20 paired/cell, seeds 800000+, three arms +
full-auto reference, deployed triggers; margin {0.3, 0.5} characterization
sweeps on `wm_unified` (probe_results.json, probe_margin03/05.json).

### Stage A — the pilot map

| cell | crash_u | | cell | crash_u |
|---|---|---|---|---|
| classic@1.0 nov/avg/exp | 0.10 / 0.00 / 0.00 | | dense@1.0 nov/avg/exp | 0.30 / 0.15 / 0.30 |
| classic@1.5 nov/avg/exp | 0.15 / 0.00 / 0.05 | | dense@1.5 nov/avg/exp | 0.80 / 0.25 / 0.65 |

Usable band [0.15, 0.85]: **7 cells** (classic@1.5/novice + all six dense).
COHERENCE VIOLATION (reported, per prereg): expert > average in BOTH dense
speeds — the tight deadband (0.12 m) tracks gap centres aggressively and
buys more lateral exposure than average's slack (0.18 m); the "skill"
dial inverts in clutter. The instrument is honest about it; personas stay
frozen.

### Rule 1 — primary cells (oracle must halve the crash mass)

Qualify: **classic@1.5/novice** (oracle dcrash -0.100 <= -0.075) and
**dense@1.0/novice** (-0.250 <= -0.150). Everything else fails the halving
rule — notably dense@1.5/novice (crash_u 0.80, oracle only -0.200 vs the
required -0.400): at 1.2 m/s in dense, most pilot crashes are
kinematically committed before ANY 0.67 s trigger can help — the v0.14
floor, now measured from the assistance side. dense@1.5/average is worse:
even the PERFECT-EYES ladder adds crashes (+0.200, added=5).

### Rule 2 — gate-WM qualification: BOTH ARMS DISQUALIFIED

Pooled on the primary cells (n=40 paired):

| arm | prevented | added | FI | override_rate_clean |
|---|---|---|---|---|
| wm_unified | 2 | **18** | 0.93-1.00 | 0.41-0.48 |
| wm_champion | 3 | **20** | 0.82-1.00 | 0.42-0.47 |
| oracle (ceiling) | 7 | 0 | 0.53-0.57 | 0.08-0.16 |

The frozen rule demands pooled added == 0 and FI <= 0.15. Neither WM arm
comes close; **K0 never opens**. Margin 0.3/0.5 sweeps barely move any of
it (added stays 3-12 across dense cells at every margin) — this is not a
threshold artifact.

### What failed, named from the traces we do have

1. **The takeover rung hands a better flyer to a worse one.** Escalations
   ran 15-20/20 seeds in the hot cells (frac_auto 0.45-0.77). The pilots
   are privileged by construction (a human sees the scene); the takeover
   autopilot is vision-only, and vision-only autonomy crashes at 0.40-0.45
   in dense (the full-auto reference, same seeds) — WORSE than every
   unassisted persona at dense@1.0 (0.15-0.30). The ladder converts
   sustained warn-edge into a pilot swap that lowers the cockpit's skill.
   The oracle arm masks this by construction (its takeover pilot is also
   privileged) — and still over-escalates at dense@1.5/average.
2. **The dense over-report drives the triggers.** head_calibration
   measured the miscalibration as context-conditional (dense over-reports);
   here that surfaces as imminent fires on normal gap-threading veers:
   override_rate_clean 0.29-0.50 and FI 0.82-1.00 across dense for both WM
   arms, vs the oracle's 0.02-0.16.
3. **Anticipation itself is NOT refuted.** Where the oracle prevented
   crashes it moved 333-880 ms before the counterfactual impact (7
   preventions, added=0, on the primary cells) — inside the WM's own
   horizon budget. Per the pre-registered refutation clause: the gap is
   PERCEPTION (and the takeover asymmetry), not guardianship.
4. classic@1.0/novice is the one cell where the contender behaved as
   designed (dcrash -0.050, added=0, lead 396 ms) — sparse world, low
   speed; it sits below the usable band, so it seeds no bar.
5. moving@1.0 diagnostic: wm_champion HELPED (-0.200, prevented=4,
   added=0, FI=0.20) with modest overrides — a single-cell curiosity
   consistent with the champion's moving-world training diet; logged, not
   interpreted further (n=20, diagnostic column).

### Disposition (per pre-registration)

K0 cannot fly: no bars are frozen, no gate seeds are spent. K1's release
condition (a K0 trace signature) is unevaluable — K1 stays unreleased.
**assist_v1 closes as a recorded negative with a priced map.** What the
map buys the next campaign (its own prereg, new version):

- **Veto-only ladder** (escalate=False): the probe's confound-free
  discriminator between "eyes fire too often" and "takeover makes it
  worse" — the machine already supports it as a constructor flag.
- **A humility gate on escalation**: only hand over when the autopilot is
  EXPECTED to outfly the pilot in this context (dense says it is not) —
  e.g. gate the AUTO rung on the full-auto reference for the world class.
- **Eyes before authority**: the dense over-report is the same wall
  head_calibration hit; a guardian-specific operating point (per-context
  trigger, or the wall clears only with representation work) is the
  quarterly-class road v0.14 already named.
- The interactive demo and the `assisted` FlightMode stay shipped and
  green — the authority LADDER is sound (10/10 safety rows, zero added
  crashes for the silent/oracle configurations on classic@1.0); what is
  not deployable is the WM-triggered escalation in dense at these
  calibrations, and the mode's default world/persona demo remains honest
  (it flies, with visible over-intervention — the article's point).

Run-to-run caveat: single probe, n=20/cell, MPS-class variance — the
MECHANISMS above reproduce (sign and structure); third decimals will not.

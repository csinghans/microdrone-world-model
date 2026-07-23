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

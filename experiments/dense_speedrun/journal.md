# dense-speedrun — attack the oldest frontier, honestly (P5)

## Pre-registration (2026-07-07, before any number exists)

The dense floor (champion crash 17 % @0.8 m/s, 27 % @1.2 m/s since
v0.3) is the repo's stated open frontier. It has survived grounding
(two λ doses), calibration (C0), and — as of lambda_multiseed — the
retro-read that says the model axis never moved. The standing blame
("FOV physical limit: every evasion steers into unseen space") has
never actually been *isolated* from its rival ("the learner can't use
what the obs contains"). The imitation stack now lets us split them.

**Cells (frozen):** world `dense`, speed factors {1.0, 1.5, 2.0}
(= 0.8/1.2/1.6 m/s), n = 30 per read, seed0 = 7000 (the standing
dense exam seeds). Primary currency: success = reached ∧ ¬crashed;
crash % reported alongside (the frontier's historical currency).
Borderline (±0.08 of any bar) → fresh block, POOLED n = 60.

**Stage 0 — the probe (no training).** Two arms, same cells, same
runner (`run_scenario_episode`), path recorded:
1. **OracleField** — NEW privileged scripted pilot (reads pillar
   layout, greedy lane-clearance side-step, same action set /
   decision cadence). Its number is the arena ceiling, honestly a
   LOWER bound (scripted quality is a confound — but dense is a
   spatial task, where Weave/Dodge scripted ceilings held; the
   timing-task caveat from the door arc does not apply).
2. **Champion** (`ppo_wm_policy_edge_hard_xp.zip` + standing model)
   — measured-only red baseline. Its 1.0/1.5 cells double as an
   instrument replication check against the v0.3 record (crash
   17 %/27 %); a gross mismatch (beyond binomial n=30) = bug hunt
   before any verdict.

**Failure taxonomy (the campaign's real deliverable, mechanical from
path + layout):** each non-success classified as timeout | crash at
in-path-1 (pillar x ∈ [1.0,1.6]) | in-path-2 (x ∈ [1.9,2.5]) | side
clutter (|py| ≥ 0.55); crashes additionally flagged **blind-side** if
they occur within 3 decisions after a veer direction change (the
world's design thesis: evasion steers into unseen space).

**Frozen verdict rules:**
- Per cell, K1 unlocks iff OracleField success ≥ 0.70 there
  (dodgeball convention: bars only where the arena is priced
  flyable). Ceiling < 0.70 at 2.0 = "dynamics/action-set wall at
  speed" — recorded, no training thrown at it.
- **K1 (conditional, `research step` only): BC-distill OracleField**
  (collect on dense, seeds 40000+, disjoint from exams; distill.py
  machinery verbatim). Bars, probe-priced: success ≥ 0.70 × ceiling
  (cell) at pooled n ≥ 60. BC val-accuracy floor 0.80 gates entry to
  the closed-loop exam (chain_distill convention).
- **The mechanism split (why this campaign exists):**
  - BC val < 0.65 with a healthy teacher → the information is NOT in
    the obs — the FOV wall is real, confirmed for the first time at
    the data layer (not by elimination).
  - BC val ≥ 0.80 but closed-loop ≪ ceiling → drift/learner wall —
    the FOV story weakens; the two-leg recipe (on-policy FT) becomes
    the named follow-up.
  - BC flies near ceiling → the floor falls to imitation like the
    slalom wall did; dense stops being a frontier.
- No promotion path in this campaign: the champion stack is
  untouched; any artifact is best-so-far only. Guards not applicable
  (nothing merges into anything).

Cost: probe 180 episodes ≈ 30-60 min background; K1 (if unlocked)
one collect + one BC + two exams ≈ 1-1.5 h.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01GGt7SZ3GgNrbrXFrC5UWcn

## Stage-0 verdict: the ceiling is refuted — the champion IS the map (2026-07-07)

| speed | oracle success | champion success | champion crash (record) |
|---|---|---|---|
| x1.0 | 0.867 | 0.833 | 0.167 (v0.3: 17 % ✓ exact) |
| x1.5 | 0.367 | **0.733** | 0.267 (v0.3: 27 % ✓ exact) |
| x2.0 | 0.100 | **0.433** | 0.467 (first read) |

**Replication:** exact on both standing cells (same seeds, deterministic
runner) — instrument sound, no bug hunt owed.

**The pre-registered lower-bound caveat fired, and it is the finding.**
The learned champion beats the privileged scripted pilot 2x at x1.5
and 4x at x2.0. OracleField flies forward/veer only; the champion has
the full action set — and its 10 % timeouts at x2.0 say it *slows on
purpose*, trading transit time for lateral budget. A scripted ceiling
is only a ceiling where scripting is easy: the exact DUAL of the
slalom lesson (there, the script crushed RL; here, the learned flyer
crushes the script). **Speed management under momentum is a learned
skill our scripts do not have** — the door-arc law ("scripted pilots
lose timing tasks") extends to continuous speed-vs-clearance trades.

**The taxonomy answers the campaign's mechanism question:**
- The champion handles IN-PATH threats at every speed (4 in-path
  crashes across all 90 episodes). The "FOV physical limit" story, as
  usually told (evasion outruns vision on the threats ahead), is NOT
  where the failure mass lives.
- Its failure mass at speed is **side clutter** (13/14 crashes at
  x2.0) plus deliberate-slowness timeouts. The FOV blame survives
  REFINED: what kills is the 0.55-1.2 m off-axis band — FOV-edge
  space entered during sustained evasion — not the well-seen in-path
  pillars. The oracle's in-path-1 pileup (16 @x2.0) is the script's
  momentum-blindness, not an arena property.

**Frozen-rule application (no discretion exercised):** K1 unlock
required oracle ceiling ≥ 0.70 — true only at x1.0, where the teacher
(0.867) offers nothing over the incumbent (0.833) through a lossy
clone. At the speed cells the teacher is *worse than the incumbent*.
**K1 is dead in every cell; no training thrown; the campaign closes
at stage 0** with the map as the deliverable — the P5 "Done" clause
(sharpen the frontier's mechanism, even if no bar passes) is met.

**What the map now says (ledger material):**
- Cruise: the frontier is essentially CLOSED — champion 0.833 vs
  scripted 0.867, both dying only on side clutter.
- Speed: dense@1.5 is flyable ≥ 0.733 and dense@2.0 ≥ 0.433 *by
  existence proof* (the champion itself); true headroom is unknown —
  the repo currently has NO valid ceiling instrument at speed.
- Named follow-ups (each needs fresh pre-registration, neither
  scheduled): (a) champion-as-teacher two-leg at speed (BC the
  champion, on-policy FT at x1.5/x2.0 — the odoor recipe pointed at
  speed); (b) an oracle that may SLOW (instrument repair, to price
  headroom honestly before any training bet).

Cost: 2 x 180 episodes (one arm-signature harness fix between),
~75 min wall, zero training.

## Stage 0b pre-registration: instrument repair — an oracle that may slow (2026-07-07, before any number)

Stage 0 left the repo with no valid ceiling instrument at speed; the
named cheap successor runs BEFORE any training bet. **OracleFieldSlow**
= the stage-0 gap-tracker plus one rule: when the lateral error to the
held target is large while the next blocking plane is near (urgency),
interleave `slow` decisions with the veer — trading forward momentum
for bend rate, the trick the champion's 10 % timeouts suggest it
learned. Same cells, same seeds (n=30, seed0=7000); slow-arm only
(the other two arms are committed in probe.json, deterministic).

**Frozen interpretation (dense@1.5 headline, @2.0 secondary):**
- ceiling_slow ≥ 0.85 @1.5 → real headroom over the champion's 0.733;
  the champion-as-teacher two-leg campaign earns bars priced at
  0.70 x ceiling_slow (its own pre-registration still required).
- ceiling_slow ≤ champion + 0.05 → the champion already sits AT the
  arena ceiling; dense closes end-to-end (cruise closed at stage 0,
  speed closed here) and the two-leg successor dies before birth.
- Between → headroom marginal; recorded, successor stays unscheduled.

An honest boundary as before: a scripted slow rule is ONE point in
policy space — this ceiling stays a lower bound, and a refuted-again
outcome (slow-oracle ≤ plain oracle) is itself reportable (the trick
is harder than one rule).

## Stage 0b verdict: the instrument is refuted AGAIN — no branch may fire (2026-07-07)

| speed | plain oracle | slow oracle | champion |
|---|---|---|---|
| x1.0 | 0.867 | 0.833 | 0.833 |
| x1.5 | 0.367 | **0.367** | 0.733 |
| x2.0 | 0.100 | 0.167 | 0.433 |

The pre-registered honest-boundary sentence fired, not the branches:
**slow-oracle ≈ plain oracle everywhere** (identical at the x1.5
headline; +2 episodes at x2.0; −1 at cruise). The letter of the
lower branch (ceiling_slow ≤ champion + 0.05) is technically
satisfied, but drawing "the champion sits at the arena ceiling" from
an instrument that reads BELOW the known flyer would be dishonest —
an instrument under the champion upper-bounds nothing. **No headroom
conclusion is drawn.**

What the failure teaches (and it is the campaign's second law-grade
reading): the one rule DID fire — 10 % timeouts at x2.0 say the slow
interleave engaged — it paid the time cost without buying the
clearance. Slowing *once urgency is already true* is too late; the
champion's advantage is not "it slows" but WHERE and WHEN it slows,
upstream of the emergency. **Speed management is a timing skill, and
the door-arc law holds: scripted pilots lose timing tasks unless
handed the true clock.** Two script generations, one refrain.

**Standing state of the dense frontier (final for this campaign):**
- Cruise: closed (champion 0.833 vs scripts 0.833-0.867, all deaths
  side-clutter).
- Speed: the champion (0.733 @x1.5, 0.433 @x2.0) is simultaneously
  the best-known flyer AND the only valid instrument; true headroom
  UNKNOWN — the repo has now spent two honest attempts failing to
  build a speed ceiling and records the instrument gap as real.
- The champion-as-teacher two-leg successor stays UNSCHEDULED (the
  middle branch's disposition): if opened later, its bars must be
  priced without a ceiling — against the existence numbers plus a
  margin, the honest second-best.

Cost of 0b: 90 episodes, ~25 min, zero training. Campaign CLOSED.

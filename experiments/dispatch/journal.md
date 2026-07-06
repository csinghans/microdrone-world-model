# dispatch — one drone, six frozen experts, a classifier chooses

## Pre-registration (2026-07-06, before any number exists)

The measured background: merging skills into one net taxes or destroys
them (RL confiscation, pot boundary tax, FT corrosion — all gated this
week), and the identifiability failure is measured too (dodgeball-v2:
an ambiguous opening makes one net play the majority move). Dispatch
sidesteps both: **specialists stay frozen; a small classifier head over
the same 12-decision observation stream picks who flies.**

Frozen design (`planner/dispatch.py`, selftested): six classes/experts
(classic=general champion, gap=KD1, mover=mgap-v2 K3 — it also owns
closing-door, odoor=opening K3, slalom=the chain-distill clone,
dodgeball=the dodge-distill clone); hysteresis = majority-of-5 with
switch at >= 3/5; **default = the dodgeball expert (hover-biased)** —
costs are asymmetric: waiting is recoverable, advancing out of a
station box is not (the dodgeball-v2 lesson, designed against).
Collection = each expert flying its own world (the runtime distribution
under correct dispatch), seeds 60000+ (virgin).

**Phase 1 — the meters (gate to phase 2):** per-world episode-level
FINAL identification accuracy, floor **>= 0.85 on every world** (15 val
episodes/world), plus identification latency (median decisions to
stable-correct; reported, no bar). Below the floor on any world → the
dispatch road closes at the meter (a representation verdict).

**Phase 2 — the union exam:** the dispatcher flies, as ONE policy,
every cell some catalog artifact holds solo — each judged by its OWN
skill's predicates and frozen bar:

| cell | bar | solo holder (record) |
|---|---|---|
| gap@1.0 | success >= 0.85 | KD1 (0.87-0.93) |
| mgap@1.0 | >= 0.70 | mgap-v2 K3 (0.85-0.93) |
| door@1.0 | >= 0.70 | K3 zero-shot (0.93) |
| odoor@1.0 | >= 0.60 | opening K3 (0.70-0.74) |
| slalom3@1.0 | >= 0.70 | chain-distill clone (0.967) |
| dodge@v1.8 | >= 0.55 | dodge clone (0.60) |
| guard:cluttered | crash <= 0.05 | general champion |
| guard:sweep@2.0 | crash <= 0.10 | general champion |

dodge@v1.0 flies as a measured DIAGNOSTIC (no artifact holds it — the
dodgeball crown is vacant there; the dispatcher cannot create skill
that does not exist).

**Frozen signature. Crown** = 8/8 over their own bars — the catalog's
first cross-arena title: one policy entry holding every bar any
specialist holds. **Support** = >= 6/8 with no arena at zero — dispatch
works, boundary costs visible and priced. **Refuted** = any home cell
collapses by > 20 points against its solo record — misclassification
cascades poison the very skills dispatch was meant to preserve.

Cost: phase 1 ~550 collection episodes + minutes of training; phase 2
= 9 cells x n=30 with a 6-expert ensemble per decision (~6x compute
per decision — wall-clock only; a deployment shares the encoder pass).

## Phase 1 meters — the gate does not pass (2026-07-06)

| world | final acc (floor 0.85) | latency (median dec.) | never-stable /15 |
|---|---|---|---|
| dodgeball ×4 | **1.00** ✓ | 0 | 0 |
| gap | 0.933 ✓ | 3.5 | 1 |
| classic | 0.867 ✓ | 4.0 | 2 |
| door | 0.867 ✓ | 2.0 | 2 |
| slalom | 0.867 ✓ | 2.0 | 2 |
| moving_gap | **0.800 ✗** | 2.0 | 3 |
| opening_door | **0.667 ✗** | 34.0 | 5 |

Two worlds under the frozen floor → **phase 2 does not launch; the
campaign closes at the meter**, per its own rule.

The failure shapes are the finding:

1. **opening_door's identity is temporally hidden.** It opens as a
   near-sealed wall and only becomes distinctive once the door starts
   moving — median stable-identification at decision 34 (~2.8 s), and
   5/15 episodes never stabilize. A per-decision classifier with a
   5-vote window cannot see "what this world is about to do".
2. **The confusable set is the single-fence family** (gap / moving_gap
   / opening_door) — the third independent sighting of that boundary
   (the generalist pot paid its tax there; the K1 remedy failed there).
3. Honest note: dodgeball's perfect 0-latency score is partly the
   default's gift (the hover-biased default IS the dodgeball expert).

**The v2 design writes itself, and it is cheaper, not more complex:**
the mgap-v2 K3 artifact ALREADY holds, at gated readings, every
single-fence bar in the union — gap 0.90-0.97 (bar 0.85), mgap
0.85-0.93 (0.70), closing door 0.93 zero-shot (0.70), opening door
~0.70 zero-shot (0.60, measured in the odoor campaign). **Merge the
confusable family into ONE 'fence' class flown by K3** and the roster
falls to four visually-distinct classes (classic / fence / slalom /
dodgeball) — no single-fence discrimination needed at all. Fresh
pre-registration required; seeded in the ledger.

## dispatch-v2 pre-registration (2026-07-06, before any v2 number exists)

One design delta vs v1, dictated by v1's meter verdict: **the
single-fence family collapses into one class** flown by mgap-v2 K3,
which already holds every fence bar at gated readings (gap 0.90+ /
mgap 0.85-0.93 / closing door 0.93 zero-shot / opening door ~0.70
zero-shot). Roster: classic / fence / slalom / dodgeball — every
remaining boundary is between visually distinct families. Everything
else is IDENTICAL and stays frozen: hover-biased default, majority-of-5
hysteresis, the same two phase-1 meters with the same 0.85 floor on
every world, the same union exam with each cell's own skill bar, the
same crown (8/8) / support (>= 6/8, no arena at zero) / refuted (any
home cell 20+ points under its solo record). New collection series
(seeds 70000+), classifier artifact versioned
(dispatch_classifier_v2.pth). Known residual risk, named: the
classic ↔ fence(sealed-opening-door) boundary — a wall of pillars is
the one place the four families may still look alike; the meters
gate it.

### v2 phase 1 — perfect meters; the gate passes (2026-07-06)

Every world at **1.00** final identification, zero never-stable
episodes, median latency 0-3 decisions (dodgeball's 0 is the default's
gift, as before; every transit world locks within ~0.25 s). The named
residual risk (classic ↔ sealed opening door) did not materialize.
Merging the confusable family did not dilute it — it dissolved it.
Phase 2 (the union exam) launches per the frozen gate.

## v2 phase 2 — REFUTED, with the mechanism caught red-handed (2026-07-06)

| cell | dispatch | solo record | bar |
|---|---|---|---|
| gap@1.0 | **0 %** (crash 10) | 0.90+ | ✗ |
| mgap@1.0 | 10 % (crash 70) | 0.85-0.93 | ✗ |
| door@1.0 | **0 % (crash 0)** | 0.93 | ✗ |
| odoor@1.0 | 36.7 % | ~0.70 | ✗ |
| slalom3@1.0 | 60 % | 0.967 | ✗ |
| dodge@v1.8 | 60 % ✓ | 0.60 | ✓ |
| cluttered | crash 0 ✓ (success 0 — vacuous) | | ✓ |
| sweep@2.0 | crash 26.7 | 0-5 | ✗ |

Multiple home cells collapse far beyond 20 points → the refuted clause
fires. The trace diagnostic confirms the mechanism exactly:
door/gap episodes read `dodgeball × 90/90, first_escape = None` —
**the dispatcher never leaves the hover-biased default.** The loop is
self-confirming: the default expert hovers → a stationary,
motion-free observation stream is precisely what the dodgeball
class's training streams look like → the classifier keeps answering
"dodgeball" → the hysteresis never sees 3/5 of anything else. The
scene-distinctive arenas partially escape by pure appearance (slalom's
three rows: 60 %; odoor rewards waiting anyway: 36.7 %); everything
else starves. door@1.0's 0 %-success/0 %-crash row is the signature in
one line: it never went anywhere at all.

**The exported law — the same one, measured one level up.** Phase-1's
meters were perfect (1.00 everywhere) because they metered the OPEN
loop: streams generated by correct experts flying. The exam runs the
CLOSED loop: streams generated by the dispatcher's own behavior. BC
paid this exact tax at the policy level this morning (val 0.908 →
58.5 % closed); the dispatcher pays it at the meta-decision level
this evening (identification 1.00 open → ~0 closed on transit
worlds). **Any learned component whose inputs are shaped by its own
outputs must be trained — and metered — in its own closed loop.**

v3 seed (one delta, fresh pre-registration): collect classifier
streams under the RUNTIME distribution — every training episode
starts with the default expert flying the first ~6 decisions before
the designated expert takes over (hover-start prefixes), so
"gap world seen from a hover" is a training class, not a trap. The
phase-1 meter must then replay the same closed-loop start.

## dispatch-v3 pre-registration (2026-07-06, before any v3 number exists)

One delta, dictated by v2's caught mechanism: **close the loop on both
sides.** Collection — every training episode's first PREFIX=6 decisions
are flown by the DEFAULT (hover-biased) expert before the designated
expert takes over, so "this world seen from a hover-start" is a
training view, not a trap; labels stay the world's true class
throughout. Meter — phase 1 no longer grades expert-generated streams:
**DispatchPolicy itself flies the validation episodes and its own
trace is judged** (final class == truth, floor 0.85 on every world;
escape latency and never-stable reported). Roster, hysteresis, default,
union exam, crown/support/refuted all inherited frozen from v2. New
seed series (80000+), versioned artifact (dispatch_classifier_v3.pth).

# dodge-crown — the dial's second cash-out (four ball speeds + the guard wall)

## Pre-registration (2026-07-07, before any number exists)

The dodgeball throne is split two ways (RL-K3 holds v1.0 at 0.60,
the clone holds v1.8 at 0.60; v0.6 and v1.4 unheld) and every past
contender failed the guard wall structurally (pure-diet specialists).
The slalom crown just proved the recipe that beats exactly this
shape of problem: **BC shape + mass-weighted anchored repair +
slice-aware diet.** This campaign points it at dodge.

**Stage 1 — the crown pot (frozen shares, seeds verbatim from the
frozen recipe codes; slalom deliberately EXCLUDED — the dodge gate
does not grade it, and un-graded shapes spend fidelity):**

| world | episodes | teacher (record) | seed0 |
|---|---|---|---|
| gap | 100+100 | weave (0.97) | 42000/46000 |
| moving_gap | 200+200 | track (0.90) | 43000/47000 |
| classic | 150 | champion | 44000 |
| solo @2.0 | 120 | champion | 45000 |
| dodgeball_v06 | 200 | dodge06 (ceiling 0.90) | 51000 |
| dodgeball_v10 | 200 | dodge10 (0.80) | 52000 |
| dodgeball_v14 | 200 | dodge14 (0.80) | 53000 |
| dodgeball_v18 | 200 | dodge18 (0.80) | 54000 |

**BC floors (obs-sufficiency gates; FT does not fly unless both):**
pooled val ≥ 0.80; the fast-ball manipulation meter (non-hover
dodge-decision accuracy, the dodge_distill instrument) ≥ 0.85 — the
undiluted clone read 0.898; a meaningful dilution shave below 0.85
stops the campaign at the pot (verdict: rebalance is the next knob,
not flown here).

**Stage 2 — the crown shot (ONE arm, the slalom-crown recipe
verbatim):** 450k anchored-schedule FT (kl 1.0 → 0.1), diet =
dodgeball_v06,v10,v14,v18,gap,moving_gap,classic,solo (8 worlds,
round-robin — every graded surface carries rollout mass; the fifth
clause, applied at design time), station_tick 0.6 (fires on ball
worlds only, by meta), edge_bias 0.5 (the sweep slice's mass).
Priced risks, stated now: (i) slalom (in no diet) will corrode —
expected, ungraded, recorded measured-only if at all; (ii) 8-way
round-robin halves per-world mass vs the slalom crown's 5-way — the
chain-free gate should tolerate it; (iii) v0.6's bar (0.65) is the
steepest climb from the clone's 0.333 — the drift-repair leg
(surpass_teacher: FT repairs drift almost fully) is the bet.

**The gate (crown rule, frozen — ALL eight):** dodge@v0.6 ≥ 0.65,
dodge@v1.0 ≥ 0.55, dodge@v1.4 ≥ 0.55, dodge@v1.8 ≥ 0.55 (n=60,
seed0 23000), gap ≥ 0.75 (n=60, 9000), mgap ≥ 0.70 (n=60, 9500),
cluttered crash ≤ 0.05 (n=60, 1000), sweep@2.0 crash ≤ 0.10 (n=60,
3000). Borderline ±0.08 → ONE fresh block, POOLED, never re-rolled.
Any failure = no crown, verdict recorded, no deviation slot.

Cost: ~1670 collection episodes + one BC + one 450k FT + ~480 exam
episodes ≈ 4-6 h, background queue with markers.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01GGt7SZ3GgNrbrXFrC5UWcn

## Verdict: REFUTED — and the anchor's limit is named (2026-07-07)

**Floors passed, gate failed 5/8.** Pot pooled val 0.9218; fast-ball
manipulation meter 0.9573 (n=5400/world — the mixed pot did NOT
dilute fast-ball fidelity; it may have helped). The crown shot:

| bar | read | verdict |
|---|---|---|
| dodge@v0.6 ≥ 0.65 | **0.000** (crash 0.167) | ✗ |
| dodge@v1.0 ≥ 0.55 | **0.000** (crash 0.217) | ✗ |
| dodge@v1.4 ≥ 0.55 | **0.000** (crash 0.533) | ✗ |
| dodge@v1.8 ≥ 0.55 | **0.000** (crash 0.550) | ✗ |
| gap ≥ 0.75 | 0.833 | ✓ |
| mgap ≥ 0.70 | 0.550 | ✗ |
| cluttered ≤ 0.05 | 0.133 | ✗ |
| sweep@2.0 ≤ 0.10 | 0.083 | ✓ |

Zero success with sub-bar crash rates = the artifact dodges and
survives but never holds the box — the station economy is GONE.

**The autopsy convicts the fine-tune, not the pot** (BC prior flown
on the same cells, measured-only): 0.267 / 0.400 / 0.467 / 0.700.
The clone holds station at every speed — v1.8 at 0.700, ABOVE the
pure dodge clone's 0.60 record (n=30, observation not title). The
anchored FT took a station-holding prior and erased station-keeping
to 0.000 at all four speeds, with station_tick=0.6 PAYING for the
box the whole time and the prior's demos holding it.

**The FT-safety law's sixth clause (measured):** the anchor defends
against DRIFT, not against REWARD. Five of eight diet worlds pay
forward progress; their gradient majority actively opposes staying
in a box, and the schedule's late freedom (kl → 0.1) ratifies the
vote precisely when it consolidates. Contrast the chain, which the
same recipe carried to a crown: nothing in the five-world reward
OPPOSED weaving — mass-weighted anchoring protects what reward is
neutral about; **nothing in this design protects what reward
opposes.** (K2-dodgeball measured the naked version of this wash-out;
this campaign measured that the anchor does not change it.)

Secondary findings, both priced in the pre-registration: the 8-way
round-robin thinned per-world mass and broke mgap (0.550) and
cluttered (0.133) — risk (ii) fired; edge_bias held sweep green for
the third consecutive campaign (0.083, clearance 0.60 m).

**Successor (named, not scheduled): per-world anchor coefficients**
— the dial's third axis, present in the original ledger entry. Pin
kl high on ball worlds (defend station against the transit majority)
while the schedule relaxes transit worlds for repair. Alternative
named: reward surgery (progress term masked on ball worlds — but
that is a reward change, a different knob family). Ball-only diets
are NOT a road: the fifth clause prices zero-mass guards as naked.

Artifacts kept (best-so-far, no titles): ppo_dodge_crown_BC.zip
(the pot clone — v1.8 0.700 observation), ppo_dodge_crown_FT.zip
(the refuted shot). Throne state unchanged: split two ways, v0.6 and
v1.4 vacant. Cost: ~1670 collection + 450k FT + 600 exam episodes.

## K2 pre-registration: per-world (per-GROUP) anchor coefficients (2026-07-07, before any number)

The sixth clause's named successor, played as two arms. Machinery on
the record first: the anchor term now supports per-GROUP coefficients
(ball vs transit, read off the env's episode meta) — a collection-time
callback keeps a tag list positionally aligned to rollout-buffer rows,
and the vendored train() samples that buffer with per-sample
coefficients. Wiring smoke: 8192 steps on a 2-world diet landed
{ball: 1.0, transit: 0.325} with both groups tagged (1113/935) — the
0.325 is the exact frac-0.75 schedule value. One flatten-layout bug
caught by the smoke (SB3's .get() flattens the buffer in place; the
branch now handles both layouts).

**Both arms reuse the SAME frozen pot prior (ppo_dodge_crown_BC.zip),
diet, tick, edge_bias, 450k — the only delta per arm is the ball
group's schedule:**
- **K2a — ball PINNED (1.0 → 1.0), transit scheduled (1.0 → 0.1).**
  The mechanism arm: if station survives here, per-group anchoring
  defends reward-opposed behavior; dodge repair is expected to be
  LIMITED (the kl=1.0 record repaired +10 inside a tight ball) — v1.8
  (prior 0.700) may hold while v0.6 (needs +38) likely cannot.
- **K2b — ball FLOOR (1.0 → 0.5), transit scheduled (1.0 → 0.1).**
  The crown bet: half-freedom on ball states — enough late movement
  for the on-policy repair the slow cells need, enough floor (above
  K1-dial's leaky 0.3) to out-vote the transit majority.

**Exam:** the crown gate verbatim (all eight bars, n=60, borderline
±0.08 → one fresh block pooled). **Verdict grid (frozen):** any arm
passes all 8 → the throne is taken. Station survives (>0 success
with in-box behavior at every speed) in both arms but bars fail →
"the ball-floor dial" is real and named; station dies even PINNED →
per-group anchoring cannot defend reward-opposed behavior at all —
the road forks to reward surgery / DAgger, recorded.

Cost: 2 x 450k FT + 2 x 480-episode gates ≈ 4-5 h, background.

## K2 verdict: the defense WORKS, the crown stays out of reach — and the wall has a name (2026-07-07)

| cell (bar) | global sched (K1-era) | K2b floor 0.5 | K2a PIN 1.0 | BC prior |
|---|---|---|---|---|
| dodge@v0.6 (≥0.65) | 0.000 | 0.317 | **0.350** | 0.267 |
| dodge@v1.0 (≥0.55) | 0.000 | 0.200 | **0.333** | 0.400 |
| dodge@v1.4 (≥0.55) | 0.000 | 0.383 | **0.550** | 0.467 |
| dodge@v1.8 (≥0.55) | 0.000 | 0.400 | **0.500** | 0.700 |
| gap (≥0.75) | 0.833 | 0.933 ✓ | 0.850 ✓ | — |
| mgap (≥0.70) | 0.550 | 0.583 ✗ | 0.600 ✗ | — |
| cluttered (≤0.05) | 0.133 | 0.050 ✓ | 0.100 ✗ | — |
| sweep@2.0 (≤0.10) | 0.083 | 0.300 ✗ | 0.200 ✗ | — |

**The pre-registered middle branch fires** (station survives in both
arms, bars fail): no crown. No borderline rechecks flown — the gate
is dead through TWO non-borderline failures in each arm (mgap and
sweep), so no recheck could flip the verdict; rechecks exist to
settle verdicts, not to decorate them.

**Finding 1 — the sixth clause has a working countermeasure.** Ball
success is MONOTONE in the ball-group anchor: global schedule 0.000
everywhere → floor 0.5 lands 0.20-0.40 → pin 1.0 lands 0.33-0.55.
Per-group anchoring defends reward-opposed behavior in direct
proportion to its coefficient. The pin arm even repairs a little
inside the ball (v0.6 0.267→0.350, v1.4 0.467→0.550 — the +10-ish
in-ball repair the kl=1.0 record predicted).

**Finding 2 — the wall: station and slow-ball repair live on the
SAME states.** The floor hypothesis (half-freedom buys ball repair)
is refuted in the cleanest possible way: the floor is worse than the
pin on ALL FOUR ball cells — freedom on ball states buys erosion,
not repair, because the reward opposition dominates whatever
on-policy improvement was hoped for. Per-group anchoring separates
ball from transit; **nothing in this design separates
station-keeping from dodge-improvement within the ball group.**
v0.6's bar (0.65) needs true learning the pin forbids and the floor
squanders.

**Named roads (recorded, not scheduled):**
- **The fidelity road (cheapest):** the BC prior's v0.6 = 0.267
  against a 0.90 teacher ceiling is a FIDELITY gap at the pot level —
  slow-ball episodes are long, drift compounds, the big-pot lesson
  applies verbatim: raise the v06/v10 demo shares (data volume, not
  architecture), then PIN. If BC-level v0.6 reaches ~0.6+, the pin
  preserves it.
- **The teacher-re-anchor road (DAgger's seventh datapoint):**
  re-anchor to a TEACHER (station-holding AND stronger than the
  prior) instead of the prior itself — the anchor then defends the
  right target rather than the imperfect starting point.
- Guards mgap/sweep remain the 8-way-diet thinning problem in every
  arm — any future attempt inherits it (mass budgeting, not new law).

Cost: 2 x 450k FT + 960 exam episodes, ~3.2 h. Artifacts kept
(best-so-far): ppo_dodge_K2a_pin.zip — the strongest station-holding
generalist measured (0.850 gap + nonzero station at every speed).

## K3 pre-registration: the fidelity road — feed the slow ball, then pin (2026-07-07, before any number)

K2 named the wall (station and repair share ball states) and the
cheapest road around it: the prior's slow-ball fidelity. The teacher
holds v0.6 at 0.90; the pot clone converts it to 0.267 closed-loop —
slow-ball episodes run ~90 decisions, drift compounds, and the
big-pot lesson (data volume closed exactly such a gap for the slalom
chain: val 0.928 → 0.963 ended an identical stall) applies verbatim.

**Single delta vs K2a — the POT's slow-ball shares:**
v06 200 → 600 episodes (+400, fresh seed series 57000; the 55-56k
audit series stays untouched), v10 200 → 400 (+200, seed0 58000).
Everything else in the pot byte-identical (same recipes, same seeds).
Collection is saved to npz this time (pot reuse, future rebalances).

**Checkpoint gates (frozen, in order):**
1. BC floors as before: pooled val ≥ 0.80, fast-ball meter ≥ 0.85.
2. **The road's own checkpoint:** BC closed-loop dodge@v0.6 ≥ 0.50
   at n=30 (prior read 0.267). Below 0.50 = the fidelity road is
   REFUTED at the pot level (volume does not buy slow-ball
   closed-loop the way it bought the chain) — stop before FT,
   verdict recorded, no FT flown.
3. FT arm (only if 1-2 pass): the K2a PIN recipe verbatim
   (ball 1.0→1.0, transit 1.0→0.1, tick 0.6, edge_bias, 8-world
   diet, 450k) on the new BC.

**Exam:** the crown gate verbatim (all 8, n=60, borderline pooled).
Honest expectation set now: mgap/sweep carry K2's standing 8-way
thinning deficit — a dodge-side success with guard failures is the
EXPECTED shape, and it would fork a K4 (mass budgeting) rather than
deny the fidelity finding. The gate flies regardless (cheap, and the
guard reads feed K4's design).

Cost: ~2270 collection episodes (~1.5-2 h, npz saved) + BC + probe
+ 450k FT + 480-episode gate ≈ 4-4.5 h, background queue.

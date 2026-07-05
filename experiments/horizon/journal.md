# horizon — the chaining bottleneck, attacked at the architecture

## Pre-registration (2026-07-06, frozen before any number exists)

**Hypothesis (inherited from the slalom arc).** Chaining fails because
the policy's observation cannot represent the NEXT gate: at dx=0.70 and
cruise the gate period is 0.875 s, the longest collision-head horizon
is k=32 ≈ 0.67 s, and the observation carries head outputs only — the
camera sees gate k+1, the bottleneck discards it. H1 extends the
horizon ladder to k=48 (1.0 s > 0.875 s): the whole stack — labels,
predictor heads, collision heads, and therefore the policy observation
(10 probabilities per candidate instead of 8) — retrains under
`WM_HORIZONS=4,8,16,32,48`. One coupled system-level knob: the stack's
horizon. Everything else (hard data diet, 96×120 seed 0, 80 epochs,
v2-combination policy diet + slalom3_fixed, 900 k, the slalom-v2 exam
cells and bars) is inherited unchanged.

Honest data note: H_MAX drives the intervention hold lengths, so the
H1 dataset is necessarily a different draw (longer holds, fewer long
windows at L=120) — recorded, not hidden; the exam is closed-loop
flight, where the draw lesson says the verdict belongs anyway.

**The pre-stated falsifiable signature (from the slalom-v2 close):**

- Baseline (k=32 stacks): slalom3@1.0 success 0 %, chain_break_at
  1.33-2.10 across four trained attempts.
- **Support:** chain_break_at moves first — ≥ 2.5 mean — whether or not
  success clears the bar. Full support: success ≥ 0.70 (the inherited
  target on the 0.97-ceiling arena).
- **Refuted:** success ≈ 0 AND chain_break_at unmoved (< 2.5) with the
  manipulation checks green — then the bottleneck is not observability
  (credit assignment / exploration become the live suspects) and the
  campaign closes honestly.

**Bars (inherited verbatim from slalom-v2):** target slalom3@1.0 ≥
0.70; guards gap ≥ 0.75, mgap ≥ 0.70, cluttered ≤ 0.05, sweep@2.0 ≤
0.10 (all on the NEW stack; n and seeds per `exam_cells.json`, judged
with the skill's own predicates via `eval_policy_cells --skill`).
Manipulation checks (harness, not science): WM48 trains to completion,
val AUC@48 > 0.60, deploy budget prints and fits; the classic-stack
regression probe already reproduced 0.8389/0.7511/0.8390 bit-for-bit
after the layout surgery.

**H2 (reserve, played only if chain_break moves but success
undershoots):** k=64 (1.33 s — two gate periods). No other reserves; a
refuted H1 closes the campaign.

**Protocol:** every step of the H1 queue runs under the env switch and
is listed here verbatim; the G1 champion is restored to
`output/world_model.pth` after the exam (the horizon stack lives in
`experiments/horizon/artifacts/`).

## Gates

(appended when the queue lands)

## H1 gate — the signature fires REFUTED; campaign closes (2026-07-06)

Queue ran clean end to end (`h1_results.json`; every step under
`WM_HORIZONS=4,8,16,32,48`; G1 restored after the exam).

**Manipulation checks: green.** WM48 trained to completion; val
AUC@4/8/16/32/48 = 0.88/0.88/0.86/0.86/**0.75** (the new head clears
the 0.60 floor); deploy 89.5 KB (+8.2 for the extra predictor+collision
heads, still ≪512); the expected data cost recorded (2682 train seqs vs
3677 — longer holds, fewer long windows at L=120). Per-world val AUC
printed classic/dense = 1.00/1.00 on this draw — flagged and ignored
per the instrument lesson (dense-slice model AUC is weather).

**The exam, against the frozen signature:**

| cell | baseline (k=32 stacks) | H1 (k=48 stack) |
|---|---|---|
| slalom3@1.0 success | 0 % | **3 %** |
| slalom3@1.0 chain_break_at | 1.33–2.10 | **1.47** |
| slalom3@1.0 weave_frac | 0.72–0.85 | **0.62** |

`chain_break_at` 1.47 < 2.5 and success ≈ 0 → **the pre-stated
refutation clause fires.** Observability was not the wall: giving the
policy an observation that *can* represent gate k+1 (1.0 s > the
0.875 s gate period) moved nothing — the break point sits inside the
baseline band and per-gate competence actually dropped. H2 (k=64) stays
unplayed: its precondition (chain_break moved) never occurred.

**Honest caveat, recorded (a future hypothesis, not a license to keep
digging now):** the k=48 head is the stack's weakest (AUC 0.75 vs 0.86
at k=32) — 1-second extrapolation is genuinely harder and L=120
rollouts feed it fewer windows. The extension gave the policy a
long-distance lens that exists but is blurry; a sharper lens (longer
rollouts, more data) is a distinct, unpriced knob. It would need its
own pre-registration and a reason to believe blur — not absence — was
binding, which today's chain_break stasis does not supply.

## Campaign verdict: CLOSED — the slalom arc's suspect list, updated

Across the whole arc: the arena is flyable (oracle 0.97), per-gate
competence is learnable (frac up to 0.85), and the chain survives
**diet** (v1/v2), **budget** (1350 k), **fixed rhythm** (v2 K1), and
now **observability** (k=48). Live suspects, for whoever picks this up:
credit assignment across the chain (success is distal — nothing rewards
threading gate k *in a way that sets up* gate k+1), exploration (the
joint maneuver may never be sampled), and reward structure
(progress+crash shaping is indifferent to setup positioning). All three
are RL-algorithm-side, not model-side — a genuinely new axis for this
repo, and priced as such: the first capability that survived every
model-side and diet-side knob the catalog owns.

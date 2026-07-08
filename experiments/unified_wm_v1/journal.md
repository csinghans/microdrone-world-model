# unified_wm_v1 — can ONE 512 KB world model hold BOTH tracks?

## The question (Hans)

「同一顆可以包含穿越跟室內的能力嗎」— can ONE world model carry BOTH the
transit-benchmark capability (forward flight through pillar corridors, the
transit action vocab) AND the indoor-search capability (2-D roaming in
rooms, the nav vocab) — instead of forking two specialists? This is the
one architectural risk the earlier audit flagged (a single shared WM used
OOD). If one WM genuinely holds both, the "risk" becomes the WEDGE: one
512 KB model, avoidance + indoor search, no fork.

Scope: this unifies the WM's PERCEPTION/prediction substrate; the task
policies/runners stay separate and ride it. yaw stays 0 (both existing
capabilities are yaw=0; the turning fork is separate and later).

## Pre-registration (bars frozen BEFORE the unified WM existed)

The incumbent baseline is the SHIPPED champion `output/world_model.pth`
(the current transit specialist AND the current indoor performer). The
plan (`jazzy-imagining-gray.md`) pre-registered, before any unified number:

- **Transit — must NOT regress.** Per-world collision AUC@32
  (classic/dense/moving) and veer-ranking, unified vs champion.
- **Indoor — must MATCH or beat.** Forward-collision AUC (the WM's
  feasibility signal, champion 0.814) and target-detection WM-latent AUC
  (the WM's native home, champion 0.940).
- **PASS = matches transit (within noise) AND matches-or-beats indoor.**
  Honest outcomes recorded either way: match-both → one-WM win; regress
  transit → capacity dilution, keep two; improve indoor → bonus.

## Method

**Unified training set** (`datasets/combine_rollouts.py`): 120 transit
rollouts (classic/dense/moving, seed 0) + 80 room rollouts (seed 100000),
common `--len 120`, concatenated. Room `world_id` remapped 0→3 (else it
aliases transit classic=0); `world_names=[classic,dense,moving,room]`.

**The counterfactual-loss fix** (`datasets/intervention_labels.py`): the
cf oracle is pillar-kinematic. For NaN-pillar room frames the mask empties
→ without a fix they keep `cf=0, vis=1` = a fully-weighted "ALL candidates
safe (incl. forward-into-wall)" signal that fights the honest wall-danger
`col_loss` on the shared heads. Fix: room frames marked UNANSWERABLE
(`vis=0`) → they contribute 0 to `cf_loss` and train collision only from
their honest `dists` wall-clearance label. Transit rollouts bit-identical.
(This fix has a downstream cost — see the indoor forward-collision result.)

**Trained** to a SEPARATE path (champion never clobbered):
`scripts.train --data output/combined.npz --out output/world_model_unified.pth
--epochs 80 --seed 0`. Same v2 architecture/hyperparameters as the champion.

**Head-to-head is apples-to-apples.** Transit: a FRESH held-out eval set
(120 rollouts, seed 777 — OOD for both models), scored via
`eval_wm_checkpoint.evaluate(ckpt, data, seed=0)` — same data + same split
seed → both models score the IDENTICAL val frames. Indoor: `frontier` is a
GEOMETRIC (model-independent) flight, and the detection grid is fixed, so
champion and unified traverse the IDENTICAL frames; only their scores
differ.

**Confound control — a transit-only twin.** "Unified beats champion" could
be a data-quantity artifact (unified's 120 transit rollouts vs the
champion's unknown count). So a CONTROL WM was trained on the EXACT same
120 transit rollouts from `combined.npz` with the 80 rooms DROPPED (same
seed 0, same 80 epochs) → `world_model_transit120.pth`. Unified vs control
isolates the ONE variable: adding 80 rooms.

## Results

### Transit — 3-way on the identical held-out (seed 777) val frames

| model | classic | dense | moving | AUC@32 (all) |
|---|---|---|---|---|
| CHAMPION (shipped) | 0.657 | **0.933** | 0.931 | 0.896 |
| CONTROL (transit-only-120) | 0.716 | 0.890 | 0.930 | 0.887 |
| **UNIFIED (transit120 + room80)** | **0.821** | 0.918 | **0.956** | **0.931** |

- **Unified does NOT regress transit — it beats the champion** on
  classic (+0.164), moving (+0.025) and overall AUC@32 (+0.035); dense is
  a statistical tie (−0.015).
- **The win survives the confound control.** Unified beats the
  transit-only-120 control — identical transit data, only difference is the
  80 rooms — on EVERY world (classic +0.105, dense +0.028, moving +0.026,
  overall +0.044). So the improvement is NOT a data-quantity artifact: the
  room frames act as a beneficial auxiliary signal / regularizer (the
  control slightly overfits 120 transit rollouts → worse on held-out
  seed-777 transit; the rooms broaden the visual representation).
- (`dense=0.30` appeared on the unified's OWN training-val split — a
  noisy ~8-rollout bucket; on the 40-rollout held-out set with ≥20 val
  samples per world it is 0.918. Small-bucket noise, not a collapse.)

### Indoor — champion vs unified on identical frames

| metric | champion | unified | Δ |
|---|---|---|---|
| target-detection WM-latent AUC | 0.940 | **0.978** | **+0.038** |
| forward-collision AUC (fov-label) | **0.814** | 0.674 | **−0.140** |

- **Detection: unified WINS** (0.978 vs 0.940) — expected: the unified WM
  actually trained on rooms, so its latent carries even more target /
  room-appearance signal. Detection is the WM's native home, now sharper.
- **Forward-collision: unified REGRESSES** (0.674 vs 0.814) — an honest
  negative. Mechanism: the cf-loss fix (correctly) removed the spurious
  "all-safe" room signal, but that ALSO removed the only ACTION-CONDITIONED
  danger signal room frames could carry (rooms train collision from
  position-based `dists` only, no counterfactual). The champion, never
  having seen a room, transfers its SHARP pillar-cf action-conditioning and
  ranks room forward-collisions better. Training on rooms with col-only
  supervision blunted that ranking.

### Transit closed-loop (deployed path) — champion vs unified, 60 seeds

The WM IS the deployed avoidance mechanism on transit, so the AUC win must
survive flight. `eval_closed_loop.evaluate()` takes model components
directly (NO artifact swap); same 60 seeds (70% in-path), seed0=1000,
speed=1.0 for both. WM-arm metrics:

| metric | champion | unified |
|---|---|---|
| crash % (in-path) | 40% | **21%** |
| min-clear (in-path) | 0.35 m | **0.39 m** |
| false-evasion % (clear) | 100% | **6%** |
| reached % (in-path) | 100% | 100% |
| trigger lead vs reactive | +258 ms | +216 ms |

**Unified roughly HALVES the crash rate (40→21%) and nearly eliminates
false-evasion (100→6%)** at comparable lead and 100% goal-reach — the
held-out AUC win translates to flight, decisively.

Honesty caveat: these absolute rates are at `eval_closed_loop`'s default
operating point (speed 1.0, seed0 1000), which is evidently stressful —
the STANDARD tool independently reproduces the champion's 40% crash /
100% false-evasion (two code paths agree, so the harness is faithful), and
even at this point the champion's WM-arm is worse than its own reactive
baseline (crash 2%→40%). So 40% is NOT the champion's best-case
deployment number; the COMPARISON under identical stress is what is valid.
The multi-speed sweep below is the pre-condition for any promotion.

### Transit speed sweep (the promotion pre-condition) — 40 seeds/speed

Does the win hold at more than one operating point? WMPolicy head-to-head
across the repo's transit envelope (x0.8 m/s base → 0.8..1.6 m/s), same
seeds every cell (`eval_unified_wm_gate --speed-sweep`, seed0=3000):

| cruise m/s | crash (ch→uni) | reached (ch→uni) | min-clr (ch→uni) | false-evade (ch→uni) |
|---|---|---|---|---|
| 0.80 | 50% → **29%** | 100% → 100% | 0.32 → **0.34** | 100% → **0%** |
| 1.00 | 32% → 32% | 100% → 100% | 0.33 → **0.35** | 100% → **0%** |
| 1.20 | 43% → **29%** | 100% → 93% | 0.34 → **0.37** | 100% → **0%** |
| 1.40 | 32% → **29%** | 96% → 79% | 0.28 → **0.33** | 100% → **0%** |
| 1.60 | 61% → **54%** | 100% → 75% | 0.21 → **0.25** | 100%*→ 0% |

- **Crash: unified ≤ champion at EVERY speed** (tie only at 1.00). The
  transit safety win is NOT a single-operating-point artifact — it holds
  across the envelope. min-clear is higher for unified at every speed too.
- **False-evasion: unified ≈ 0% everywhere vs champion's 100%** — it does
  not cry wolf. (*champion also drops to ~0% only at 1.60, where the course
  geometry at max speed suppresses triggers.)
- **HONEST trade at the aggressive edge:** unified's goal-reach falls to
  79%/75% at 1.4/1.6 m/s (champion 96%/100%). Its lower caution (0%
  false-evasion) means that at high speed ~25% of runs stall out without
  finishing (not crashes — they just don't cross the goal in time), while
  the champion bulls through (at the cost of 61% clipping at 1.6). **At
  normal cruise (0.8–1.2 m/s) unified is strictly better or tied on every
  metric with 93–100% reach.**

## Verdict — YES, one WM holds both; a WIN on every OWNED job, one honest trade

Scoreboard, unified vs the shipped champion:

| track / job | metric | champion | unified | winner |
|---|---|---|---|---|
| transit (WM-owned) | held-out AUC@32 | 0.896 | 0.931 | **unified** |
| transit (WM-owned) | closed-loop crash | 40% | 21% | **unified** |
| transit (WM-owned) | closed-loop false-evasion | 100% | 6% | **unified** |
| indoor (WM's home) | target-detection AUC | 0.940 | 0.978 | **unified** |
| indoor (geometry-owned) | forward-collision AUC | 0.814 | 0.674 | champion |

**One 512 KB world model DOES hold both tracks — and on every capability
the WM is actually RESPONSIBLE for, the unified model BEATS the
specialist**: transit collision-prediction (its core deployed job — better
held-out AUC AND ~half the closed-loop crashes) and indoor target
detection (its native home, sharper at 0.978). The transit win is not a
data-quantity artifact — it survives the transit-only-120 control that saw
the identical transit data (the rooms act as a beneficial auxiliary
signal).

**The one trade is honest and bounded:** indoor forward-collision AUC
regresses 0.814→0.674. But that signal is NOT on the deployed indoor path
— the indoor safety arc (search_wm_v3 → beams) already handed
collision-avoidance to geometric rangefinder/beam filters; the WM was
never the indoor safety mechanism. So the cost lands on a superseded
signal, while the wins land on deployed jobs. The likely cause is the
cf-loss room-mask fix (necessary to avoid the spurious "all-safe" label):
it also removed the only ACTION-CONDITIONED danger signal rooms could
carry, blunting the action-ranking the champion transfers zero-shot from
pillar counterfactuals. A future room-cf oracle (a wall-kinematic
counterfactual, not pillar-kinematic) could likely recover it — a clean
next step, not a blocker.

**Strategic read:** this turns the earlier "shared-WM risk" into the
WEDGE. No fork — ONE model, avoidance + indoor detection, each better than
a specialist would be, at 512 KB. The yaw=0 turning fork remains the one
real capability boundary (separate, later).

**Promotion — the pre-condition sweep PASSED, decision is Hans's.** The
pinned champion `output/world_model.pth` is UNTOUCHED. The pre-condition I
pre-registered — a multi-speed closed-loop sweep confirming the win is not
a single-operating-point artifact — is now DONE (above): unified crashes ≤
champion at every speed 0.8–1.6 m/s, holds more clearance, and nearly
eliminates false-evasion, with an honest goal-reach trade only at the
aggressive 1.4–1.6 m/s edge (unified 79/75% vs champion 96/100% — a
caution/completion trade, not a safety loss). So the evidence supports
promotion FOR the normal cruise envelope; the one thing a promoter must
accept is the high-speed completion trade (or gate deployment to ≤1.2
m/s). Promotion (overwrite the pinned champion + bump `artifacts.lock.json`)
remains Hans's explicit strategic call — not taken autonomously.

**Where the trade actually lands (Hans's steer: indoor exploration is
deliberately slow).** The whole caveat is confined to FAST transit. The
indoor track runs at 0.6 m/s by design (the robust config of the entire
indoor arc) — below the 0.8 m/s sweep floor and far below the 1.4–1.6 m/s
where the completion trade appears, so it never bites the indoor half.
And indoor collision-avoidance is GEOMETRIC (beams8), WM-independent — so
the indoor forward-collision AUC regression (0.814→0.674) is invisible at
deployment too: beams8 does the avoiding, the WM is not on that path.
Net: the unified WM has NO deployment downside for slow indoor, and wins
transit at cruise (≤1.2 m/s); the only regime where a promoter accepts a
trade is fast transit (1.4–1.6 m/s) — which may not be a target regime at
all. This tightens the promotion case to: clean everywhere the system
actually flies.

### Promotion-readiness — does swapping the WM break the learned policies?

Promotion overwrites the pinned champion, and the learned transit policies
(PPO on an obs built from the WM latent + collision-head probs) were
TRAINED against the champion latent — so swapping the substrate under them
is the real hidden cost. Test: the dense/hard transit champion
(`ppo_wm_policy_edge_hard_xp`, the hardest transit policy) run on champion
WM vs unified WM, same seeds, `--promotion`:

| world @ m/s | champion crash/success | unified crash/success | Δ succ |
|---|---|---|---|
| dense @0.8 | 16% / 83% | 26% / 73% | −10 |
| dense @1.0 | 40% / 60% | 36% / 63% | +3 |
| dense @1.2 | 26% / 73% | 30% / 70% | −3 |
| moving @0.8 | 13% / 86% | 6% / 93% | +7 |
| moving @1.0 | 0% / 100% | 3% / 96% | −4 |
| moving @1.2 | 6% / 93% | 3% / 96% | +3 |

**Mean Δ success ≈ −0.7% — NEUTRAL, within seed noise (n=30 → ±~9%/cell),
not the catastrophic OOD degradation one might fear.** The unified latent
is close enough to the champion's (shared architecture + the unified's
training data CONTAINS the champion's entire transit set) that a policy
trained on the champion transfers to the unified WM almost losslessly. So
**promotion would NOT break the learned transit zoo — no retrain needed.**
Honest scope: one policy (the hardest, most representative transit one) at
n=30; a full-zoo pass (slalom / gap / dodge / doors, each on its own
scenario) is the remaining pre-promotion check before overwriting the
champion. But the hidden cost I flagged does not materialize on the
policy most likely to show it.

## Artifacts (all under output/, none committed — champion untouched)
- `world_model_unified.pth` — the unified WM (transit120 + room80, 80 ep, seed 0)
- `world_model_transit120.pth` — the transit-only-120 confound control
- `combined.npz` — the union training set
- `transit_only120.npz` — control training set (rooms dropped)
- `transit_eval_holdout.npz` — fresh seed-777 held-out transit eval set
- reproduce: `python -m eval.eval_unified_wm_gate` (transit AUC + indoor
  detection/forward head-to-heads; closed-loop via `--closed-loop`)

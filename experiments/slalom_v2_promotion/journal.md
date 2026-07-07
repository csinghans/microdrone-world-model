# slalom-v2 promotion — the tenth sitting (anchor-schedule artifact)

## Pre-registration (2026-07-07, before any number exists)

anchor_dial K2 (`ppo_anchor_sched.zip`, BC2 + 450k five-world FT,
kl 1.0→0.1) passed the three index bars (0.833 / 1.000 / 0.800 —
same cells, same seeds as the corridor-slalom-v2 gate). The throne is
vacant after nine sittings; a crown is permanent catalog state, so
this sitting is judged STRICTER than the letter of the old gate,
per the standing pooled-graduation protocol (the n=30 friendly-block
lesson, integration era):

**Exam (frozen):**
- The three already-read criteria get one FRESH disjoint block each
  (n=30: slalom3 seed0 22030, gap 9030, mgap 9530) and are judged on
  the POOLED n=60 read (fresh + the anchor_dial block).
- guard:cluttered (n=60, seed0 1000, in_path) and guard:sweep@2.0
  (n=60) fly at their gate spec, first time for this artifact.
- diag:slalom2@1.0 and diag:slalom3@1.25 fly measured-only (no bars,
  unpriced ceilings — recorded for the map).

**Crown rule (frozen):** ALL five criteria pass — slalom3 pooled
≥ 0.70, gap pooled ≥ 0.75, mgap pooled ≥ 0.70, cluttered crash
≤ 0.05, sweep@2.0 crash ≤ 0.10. Any failure = throne stays vacant,
verdict recorded, no deviation slot (the artifact is what it is;
fixing it is a new campaign).

Honest exposure: mgap's index margin is +0.10 at n=30 — the pooled
demand can honestly kill this crown. That is the point of pooling.

Cost: ~240 episodes, ~45-70 min, zero training.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01GGt7SZ3GgNrbrXFrC5UWcn

## Tenth-sitting verdict: the throne stays VACANT — killed by the guard nobody had measured (2026-07-07)

Pooled and fresh reads, all frozen bars:

| criterion (bar) | block A (dial) | block B (fresh) | POOLED n=60 | verdict |
|---|---|---|---|---|
| slalom3@1.0 ≥ 0.70 | 0.833 | 0.767 | **0.800** | ✓ |
| gap ≥ 0.75 | 0.933 | 1.000 | **0.967** | ✓ |
| mgap ≥ 0.70 | 0.800 | 0.867 | **0.833** | ✓ |
| cluttered crash ≤ 0.05 | — | — | 0.033 (n=60) | ✓ |
| **sweep@2.0 crash ≤ 0.10** | — | — | **0.317 (n=60)** | **✗** |

Diagnostics (measured-only): slalom2 0.233, slalom3@1.25 0.000 —
consistent with their unpriced/0.07 ceilings.

**The crown rule fires: throne stays vacant.** The pooling demand did
not kill it (every pooled read is comfortably green — mgap's fresh
block came in HIGHER); the kill is the guard the dial campaign never
measured. The BC2 prior flies sweep@2.0 at **3 % crash (n=120)**; its
schedule-anchored fine-tune flies it at **31.7 %** — a 10x corrosion
the anchor was supposed to prevent.

**The mechanism, and the FT-safety law's fifth clause.** The KL
anchor acts on ROLLOUT states, and WMPolicyEnv samples speed
uniformly per episode — so the fast-solo slice IS visited, at roughly
4 % of rollout mass (1/5 of solo episodes above ~1.75x, solo = 1/5 of
the diet). Protection proportional to visitation is no protection:
**anchor pressure is mass-weighted — thin slices corrode almost as if
the fine-tune were naked.** bcft K1's untouched-world collapse was
the zero-mass limit of the same clause; this is the first measurement
of the thin-mass regime, caught only because a promotion gate audits
guards the training exam did not.

**Successor (single delta, pre-registered below): raise the slice's
rollout mass** with the champion's own recipe knob — `edge_bias`
(EDGE_P = 0.5: half the FT episodes drawn from the 1.5-2.0 envelope
edge). Priced risk, stated now: halving cruise mass may tax the chain
(0.800 pooled has 6 points of headroom).

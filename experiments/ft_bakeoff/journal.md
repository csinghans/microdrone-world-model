# ft-bakeoff — the best fine-tune method, measured head to head

## Pre-registration (2026-07-07, before any number exists)

The repo has priced a family of fine-tune methods against catastrophic
forgetting (the six-clause safety law). The reigning method is the KL
**schedule anchor** (1.0 -> 0.1): it crowned slalom-v2, passing all
three index bars at **0.833 / 1.000 / 0.800** (chain / gap / mgap).
But it leaves a residual: the chain bleeds 10 points off the prior
(BC2 0.933 -> 0.833). This campaign asks the direct question the
catalog has not: **is there a fine-tune method that DOMINATES the
schedule anchor** — passes all three bars with LESS forgetting?

Every method starts from the SAME prior
(`ppo_distill_generalist_BC2.zip`), SAME 450k steps, SAME five-world
diet (`slalom3_fixed,gap,moving_gap,classic,solo`), x_progress, **NO
edge_bias** (held off so the only variable is the anchoring METHOD),
SAME index cells (`experiments/conservative_ft/index_cells.json`,
n=30, seeds 22000/9000/9500). Borderline +/-0.08 -> one fresh block
POOLED, never re-rolled.

**Reference row (measured, NOT re-run):** KL schedule 1.0 -> 0.1 =
chain 0.833 / gap 1.000 / mgap 0.800 (`experiments/anchor_dial/`).

**Method arms (single knob = the anchoring mechanism):**

- **Arm E — EWC (Fisher-weighted parameter anchor).** The
  continual-learning textbook answer, never tried here. Instead of a
  per-STATE KL to the prior's *outputs*, penalize per-PARAMETER
  drift weighted by each weight's importance to the prior's skills:
  loss += lambda_ewc * sum_i F_i (theta_i - theta*_i)^2, where F is
  the diagonal Fisher of the prior policy (E[(grad log pi)^2] over
  prior-visited states, computed once at FT start, frozen). Machinery
  vendored into AnchoredPPO alongside the KL term. **Hypothesis:** the
  chain lives in a small, identifiable set of high-Fisher weights;
  EWC freezes those and frees the rest, so chain stays >= 0.90 (no
  bleed) WHILE gap/mgap still reach their bars. lambda_ewc calibrated
  in a smoke so the start-of-run penalty magnitude ~ the KL anchor's.

- **Arm F — floor schedule 1.0 -> 0.3.** The "unopened dial question"
  the anchor_dial verdict named (does a higher floor remove the chain
  bleed?). Zero new machinery (existing --anchor-end). **Hypothesis:**
  chain lands closer to 0.933; repair (gap/mgap) may cost a little.

- **Arm L — layer-freeze, head-only FT.** Freeze the shared feature
  extractor, FT only the policy+value heads (constant kl=1.0 anchor
  on the trainable head, for a fair "anchored" baseline). Cheap
  control. **Hypothesis:** if forgetting lives in the shared trunk,
  freezing it preserves the chain; if it lives in the head, this
  buys nothing — either way, it LOCALIZES where FT does its damage.

**Frozen verdict grid:**
- The **best method** = the arm that passes all three bars
  (chain >= 0.70, gap >= 0.75, mgap >= 0.70) with the HIGHEST chain
  (least forgetting). Ties on bars broken by chain, then by the
  gap+mgap mean.
- If an arm passes all bars AND chain > 0.833 (beats the schedule's
  chain) -> it DOMINATES; the recommended method changes, and a
  fresh slalom-v2-style promotion shot with +edge_bias is the named
  successor.
- If no arm beats the schedule -> the schedule anchor is CONFIRMED
  the repo's best fine-tune method, and this campaign's export is the
  head-to-head table + whatever the arms teach about WHERE forgetting
  lives (Arm L localizes trunk vs head; Arm E tests importance-based
  vs distributional anchoring).
- Honest negatives count: an arm that fails a bar is a finding about
  that method, not a retry.

Cost: 3 x 450k FT (Arm E adds a one-time Fisher pass) + 3 x 90 exam
episodes ~ 4-5 h, &&-chained background (K3's queue-gotcha applies:
conditional stops must halt the chain).

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01GGt7SZ3GgNrbrXFrC5UWcn

## Launch note — machinery + lambda calibration (2026-07-07, pre-number)

Machinery shipped and smoked: `--ewc LAMBDA` (diagonal Fisher of the
prior computed once at FT start over 512 rollout states, frozen;
penalty lambda * sum_i F_i (theta_i - theta*_i)^2 added per minibatch)
and `--freeze-trunk` (freezes mlp_extractor.policy_net = 4 trunk
tensors, action_net + value path train). Smoke: Fisher sum ~1.5e2,
freeze froze 4 tensors, both save clean.

**lambda_ewc = 10 (first shot, rationale frozen):** with Fisher sum
~150 and a target parameter RMS drift ~0.05 (Delta-theta^2 ~ 2.5e-3),
the start penalty magnitude is ~150 * 10 * 2.5e-3 ~ 3.8 — a firm
anchor comparable in scale to the kl=1.0 term at mid-drift. If the
EWC arm lands degenerate (chain fully preserved AND no repair =
lambda too high; or chain dead = too low), ONE resumed shot at the
bracketing lambda is sanctioned (lambda is EWC's single knob, the
analogue of the anchor coefficient the schedule arm tuned). Any other
change = fresh pre-registration.

Arms launched (all from BC2, 450k, five-world diet, no edge_bias):
Arm E `--ewc 10`, Arm F `--anchor 1.0 --anchor-end 0.3`, Arm L
`--anchor 1.0 --freeze-trunk`.

## Verdict: the FLOOR SCHEDULE wins; EWC did not beat it; freeze-trunk is the mechanism gem (2026-07-07)

Reference (measured, anchor_dial): schedule 1.0→0.1 = 0.833 / 1.000 / 0.800.

| arm | chain slalom3 | gap | mgap | all bars? | chain vs 0.833 |
|---|---|---|---|---|---|
| **F — floor 1.0→0.3** | **0.867** (pooled 52/60) | **0.983** (59/60) | **0.833** (50/60) | **✓✓✓** | **+0.034** |
| E — EWC λ=10 | 0.533 | 0.833 ✓ | 0.567 ✗ | ✗ | −0.30 |
| L — freeze-trunk | 0.933 | 0.800 ✓ | 0.500 ✗ | ✗ | +0.10 (but mgap dead) |

**Arm F borderline recheck (mgap was 0.767 at n=30, inside ±0.08):** fresh
block 0.900 → pooled 50/60 = 0.833, comfortably green; chain block B
0.867 == block A, pooled 0.867. By the frozen grid F PASSES all bars
with chain > 0.833 → it dominates the 1.0→0.1 schedule *by the letter*.
Honesty on the margin: 0.867 vs 0.833 is ~2 pts, inside n=60 binomial
noise — so the true statement is **the floor schedule is the
equal-or-better default and forgets no more than the tighter one**. The
anchor_dial "unopened dial question" (does a higher floor remove the
chain bleed?) resolves toward the floor: **1.0→0.3 keeps more chain
headroom while still repairing mgap.**

**EWC (per-parameter Fisher importance) did NOT beat the schedule.** At
λ=10 both the chain (0.533) and mgap (0.567) fell — the penalty was too
weak to hold the chain yet still distorted the repair. Its high-λ limit
is BRACKETED by freeze-trunk (hard-locking the important weights = the
trunk): chain preserved, mgap dead. So per-parameter importance
anchoring does not dominate distributional-KL scheduling on this
problem. The pre-registered single bracketing shot (EWC-high) is
sanctioned but LOW-INFORMATION — freeze-trunk already shows the high-λ
regime — and is deferred, not run.

**Freeze-trunk is the finding, not a contender.** Freezing
`mlp_extractor.policy_net` preserves the chain at **0.933 = the BC2
prior EXACTLY (zero forgetting)** — so the chain LIVES IN the shared
trunk, not the action head. But the same frozen trunk cannot repair
mgap (0.500). **The skill to keep and the skill to repair compete for
the same trunk weights** — a parameter-level echo of the dodge-crown
wall ("station and repair live on the same states"). Forgetting is
localized (trunk), and so is the repair capacity: you cannot freeze one
without freezing the other.

**The best fine-tune method, stated plainly:** a KL anchor on a
tight→loose SCHEDULE, floored around 0.3 — a better-tuned version of the
reigning method, not a new mechanism. EWC and layer-freezing each fail
the repair while over-protecting; the schedule's graded distributional
pressure remains the winner. Artifacts kept: ppo_floor.zip (the
dominating-by-letter arm), ppo_freeze.zip (the zero-forgetting probe).
Cost: 3×450k FT + exams + one pooled recheck.

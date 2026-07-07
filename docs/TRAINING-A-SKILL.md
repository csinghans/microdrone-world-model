# Training a new skill — what goes wrong, and how to strengthen it

The plain-language playbook, distilled from every campaign in
`experiments/`. Read [ONBOARDING](ONBOARDING.md) first for the tools;
this doc is the *why* behind the recipe. Every lesson here was paid
for by a real campaign — the journal is cited so you can check the
receipt.

The one-sentence version: **imitation buys a skill's shape for cheap,
fine-tuning buys its timing and robustness — and the entire art of
fine-tuning is repairing the new skill without eroding the old ones.**

---

## Part 1 — what goes wrong (the failure taxonomy)

### Problem 1: some skills reinforcement learning simply cannot find
Reward-and-try-again (RL) can leave a policy stuck forever — not
because the task is impossible, but because the reward signal is too
sparse to stumble onto the answer. The 3-gate slalom sat at 0–7 %
across **five** knob families (diet, budget, rhythm, horizon, reward).
The observation was sufficient and the body could do it; the *learning
method* was the wall.
→ `experiments/chain_learning/`, `experiments/corridor_slalom_v2/`

### Problem 2: sometimes the arena is physically unflyable
Before blaming the policy, check the ceiling. On the high-speed
slalom cell, even a privileged scripted pilot (reads true coordinates,
can't lose to perception) only cleared 7 %. A bar set above the
physical ceiling just punishes the drone for the impossible.
→ `experiments/slalom_v2_promotion/` (feasibility-first), the
`eval_*_ceiling` probes

### Problem 3: units pass, the composite collapses (the seam tax)
Every skill can pass its own exam and still fail when chained. A relay
of the strongest per-stage experts scored **0.13** where independence
predicted 0.73 — because entering stage two mid-flight (carrying
stage one's leftover velocity and lateral offset) is a state no
single-skill practice ever produced. Roughly half of all failures
live in these seams.
→ `experiments/integration_v1/`, [TDD-FLIGHT.md](TDD-FLIGHT.md)

### Problem 4: small errors compound (fidelity is multiplicative)
A 40-decision course succeeds at roughly *per-decision-fidelity to the
40th power*. 0.93 vs 0.96 per step sounds like 3 points; over 40
decisions it is the difference between stuck and passed. Long tasks
are brutally sensitive to per-step accuracy.
→ `experiments/integration_ft/` (the big-pot fidelity lesson)

### Problem 5 (the big one): fine-tuning breaks the skills you already have
This is catastrophic forgetting, and it earned the repo's
**six-clause fine-tune safety law** (full text in
[GLOSSARY.md](GLOSSARY.md)). Try to repair a weak skill with PPO and
the strong ones rot — and rot *faster than the repair completes* (the
slalom chain died inside 25 000 steps, before early stopping could
help). Measured shape:
1. fine-tuning repairs skills **inside** its training diet;
2. it corrodes skills **outside** the diet;
3. it erases RL-unlearnable skills **even inside** the diet;
4. a strong-but-imperfect starting point can land a *worse* basin than
   training from scratch;
5. protection is **mass-weighted** — a skill that is only 4 % of the
   training episodes corrodes almost as if unprotected;
6. anchors defend against **drift, not against reward** — behavior the
   diet's reward actively opposes gets voted out no matter what.
→ `experiments/conservative_ft/`, `experiments/bcft_generalist/`,
`experiments/dodge_crown/`

---

## Part 2 — how to strengthen the training (the playbook)

### 1. If RL can't learn it, imitate instead
Rather than reward-and-retry, clone a privileged scripted teacher
(behavior cloning). The slalom wall that beat RL 25 times fell to
imitation in one shot (0.967). "Can't learn it" is usually a
statement about the *method*, not the skill.
→ `experiments/chain_distill/`, `scripts/distill.py`

### 2. Walk on two legs: imitation for shape, fine-tune for timing
Clone first (the student learns what the motion looks like), then a
short on-policy fine-tune buys *when to act* and *how to stay stable
in real flight*. Opening-door went 0.37 → 0.96 this way — and **beat
its own teacher**.
→ `experiments/surpass_teacher/`, `experiments/odoor_v2/`

### 3. Anchor the fine-tune — and schedule the anchor tight-then-loose
Tie a KL "rubber band" to the starting policy so fine-tuning can't
wander far. But a *constant* band only trades (pick a coefficient,
pick which skill you lose). A **schedule — tight early, loose late**
buys both: early tightness carries the fragile skill through the
period when re-optimization pressure is fiercest, late freedom
finishes the repair a tight band can't reach. This crowned slalom-v2.
→ `experiments/anchor_dial/`, `scripts/distill.py` (`--anchor-end`)

### 4. Cover the whole diet, and up-weight the thin slices
The training menu must contain **every** skill you care about —
anything off the menu will rot (clause 2). And anything *thinly*
represented rots too (clause 5): a rare cell at ~4 % of episodes
corroded 3 % → 32 %; raising its share ~6× (`--ft-edge-bias`) repaired
it back to 5 %.
→ `experiments/slalom_v2_promotion/` (the eleventh sitting)

### 5. When the anchor can't save it, fix the reward — not the anchor
The rubber band stops accidental drift; it can't stop a reward that
*points the other way*. The dodgeball station ("hover and hold")
collapsed because the other diet worlds all reward forward progress,
and the majority gradient voted the station out. No anchor setting
rescued it (five methods tried, including per-group pinning and
teacher-anchored DAgger). That is a reward-design problem.
→ `experiments/dodge_crown/`

### 6. Measurement discipline is what makes a "win" real
Freeze the pass bar and the old-skill guard bars **before** any number
exists. Record honest negatives (a failed method is a finding, not a
retry). When a read lands within ±0.08 of a bar, pool a fresh block —
never re-roll until it passes. This is how you know a win is signal,
not luck.
→ `CLAUDE.md` (house rules), [GLOSSARY.md](GLOSSARY.md)

---

## Part 3 — the standard order of operations

When a new skill arrives, this is the sequence:

1. **Probe the ceiling.** Fly a privileged scripted oracle; confirm the
   arena is flyable *before* setting a bar (Problem 2).
2. **Freeze the rules.** Pass bar + guard bars for every old skill,
   committed before any number (Playbook 6).
3. **Imitate if you can.** Clone a teacher rather than grinding sparse
   RL (Playbook 1).
4. **Fine-tune with a scheduled anchor** to buy timing/robustness
   without erasing the prior (Playbook 2 + 3).
5. **Cover the diet, up-weight thin slices** (Playbook 4).
6. **If a behavior the reward opposes keeps dying, change the reward**
   (Playbook 5).
7. **Pool borderline rechecks; record every negative** (Playbook 6).

---

## The open frontier (measured, not settled)

Playbook step 3's rubber band still leaves a residue: the crowned
schedule anchor preserved the slalom chain at 0.833, down 10 points
from the prior's 0.933 — it passed, but it *did* forget a little. The
`ft_bakeoff` campaign is measuring whether a fine-tune method exists
that forgets **less**: EWC (lock only the parameters that matter to the
old skills) vs a higher anchor floor vs freezing the shared trunk.
"The best fine-tune method" is an open, actively-measured question —
this doc will gain a line when it resolves.
→ `experiments/ft_bakeoff/`

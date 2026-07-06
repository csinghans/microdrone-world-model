"""chain-distill: imitate the pilot that CAN chain — the sixth cut at the wall.

Pre-registration (written before any number exists). The slalom chain
has survived five eliminations (diet, budget, rhythm, horizon,
reward/credit) — every one of them reinforcement-side. Imitation is a
genuinely different mechanism: OracleWeave chains at **97 %** with the
SAME action set, and behavior cloning sidesteps exploration and credit
assignment entirely — no discovery, no distal reward; just "output what
the successful pilot outputs, given the vision observation".

Machinery: `scripts/distill.py` (selftested, CI). Collection flies the
oracle on `slalom3_fixed` (seeds 40000+ — disjoint from the exam's
22000 courses) while an ObsBuilder computes the exam-exact observation
stream (push-then-decide ordering, x_progress on, G1 model). BC then
supervises a standard PPO policy saved as a runner-ready zip.

**BC validation accuracy is the pre-registered obs-sufficiency meter**
(floor 0.80): the teacher reads privileged geometry, the student reads
collision probabilities — if supervised fitting cannot clear the floor,
the observation provably cannot represent the teacher's decision
function and the campaign closes WITHOUT flying (that verdict would
sharpen the horizon campaign's refutation: not even the teacher's
mapping fits, let alone RL's). Above the floor, the exam decides.

Knobs:

- K1 — zero_shot: the BC zip (400 collection episodes, 40 epochs,
  frozen before any exam number). Hypothesis: if the observation
  carries what chaining needs, the clone chains — chain_break_at moves
  first, exactly like every signature in this arc.
- K2 — zero_shot RESERVE (arbitrated with `research step`, never
  `run`): PPO fine-tune (450k) on the BC init. Played ONLY if K1 moves
  chain_break_at above the five-elimination band (> 2.10) while
  success undershoots 0.70 — closed-loop drift is then the live
  suspect, and on-policy fine-tuning from a chaining prior is the
  cheapest drift fix (DAgger stays the named escalation, fresh
  pre-registration).

Frozen campaign signature (thresholds shared with horizon and
chain-learning for arc comparability): **support** = slalom3@1.0
chain_break_at ≥ 2.5 (mean, n=30); **full support** = success ≥ 0.70
(the probe-priced bar, unchanged); **refuted** = BC val ≥ 0.80 yet
chain_break_at < 2.5 with success ≈ 0 — open-loop imitation of a
chaining teacher does not survive the closed loop; compounding drift
(DAgger-class) or execution-level mismatch become the final suspects,
and the arc records its SIXTH elimination.

Baseline band (five gated attempts): chain_break_at 1.33-2.10, success
0-6.7 %, weave_frac 0.62-0.85. Guards: structural failures expected
(the clone has only ever seen slalom corridors) — promotion out of
scope; the science cell is slalom3@1.0.
"""

from skills.base import Knob, Skill
from skills.corridor_slalom_v2.skill import SKILL as V2

_BC = "experiments/chain_distill/artifacts/ppo_chain_distill_BC.zip"
_FT = "experiments/chain_distill/artifacts/ppo_chain_distill_FT.zip"

SKILL = Skill(
    name="chain-distill",
    version="1",
    scenarios=dict(V2.scenarios),
    cells=V2.cells,  # the slalom-v2 exam, verbatim — seventh sitting
    criteria=V2.criteria,
    knobs=(
        Knob(
            "K0",
            "zero_shot",
            "the BC clone of OracleWeave (97 % teacher), exam-naive seeds",
            "if the observation carries what chaining needs, the clone "
            "chains — chain_break_at moves first; BC val >= 0.80 is the "
            "pre-registered obs-sufficiency gate before this knob flies",
            policy_path=_BC,
        ),
        Knob(
            "K1",
            "zero_shot",
            "RESERVE: PPO fine-tune (450k) on the BC init",
            "played ONLY if the clone moves chain_break_at above the "
            "five-elimination band (> 2.10) but undershoots success 0.70 — "
            "then closed-loop drift is live and on-policy polish from a "
            "chaining prior is the cheapest fix (step-arbitrated)",
            policy_path=_FT,
        ),
    ),
    max_knobs=3,  # one deviation slot, charter rationale required
    success=V2.success,
    episode_metrics=V2.episode_metrics,
)


def selftest() -> None:
    from skills.base import load_skill
    from skills.corridor_slalom_v2 import skill as v2mod

    s = load_skill("chain-distill")
    assert s.cells == V2.cells and s.criteria == V2.criteria
    assert s.success is v2mod.SKILL.success
    assert s.episode_metrics is v2mod.SKILL.episode_metrics
    targets = [c for c in s.criteria if c.kind == "target"]
    assert len(targets) == 1 and targets[0].cell == "slalom3@1.0"
    assert all(k.kind == "zero_shot" for k in s.knobs), "artifacts are hand-built"
    assert s.knobs[0].policy_path == _BC and s.knobs[1].policy_path == _FT
    print(
        "CHAIN-DISTILL OK: slalom-v2 exam verbatim (seventh sitting), both "
        "knobs are hand-built zero-shot artifacts, reserve is step-gated"
    )


if __name__ == "__main__":
    selftest()

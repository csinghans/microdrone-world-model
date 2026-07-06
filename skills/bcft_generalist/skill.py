"""bcft-generalist: the two-leg recipe at five-world scale — the crown shot.

Pre-registration (written before any number exists). The measured
pieces, assembled: the generalist BC2 pot holds the chain (93.3 %,
twice) but drifts in the single-fence worlds (gap 70 %, mgap 43 % —
share measured NOT to be the lever), and surpass-the-teacher then
measured that SB3-default PPO fine-tuning repairs exactly that drift
class (+29.5 points on mgap, crash 41→11.5 %, prior not destroyed).
**K0 composes them: PPO 450k on the BC2 init, uniform five-world
transit diet** (slalom3_fixed, gap, moving_gap, classic, solo — one
economy, no reward war; the measured dose, no tuning).

The headline risk IS the experiment: the whole slalom arc measured
that on-policy RL cannot DISCOVER the chain — K0 asks whether it can
at least KEEP a chain it was handed. A chaining policy is
return-optimal when it works (crash 6.7 %, fast goal), so PPO should
preserve it; if 450k of progress-reward experience erodes the clone
back toward RL's own local optima, that is a finding about fine-tune
safety that no smaller experiment would have caught.

Exam: corridor-slalom-v2 cells/criteria VERBATIM — the ninth sitting,
bars frozen since the probe. **Full pass crowns the catalog's first
distilled champion** (the corridor-slalom-v2 crown, vacant through
five RL attempts and two distillation campaigns).

Knobs:

- K0 — zero_shot: the FT zip (BC2 + 450k uniform five-world PPO).
- K1 — zero_shot RESERVE (step-arbitrated): FT on the two broken
  worlds only ("gap,moving_gap"), protecting the chain by not
  touching slalom. Played ONLY if K0 loses the chain (slalom3 < 0.70)
  while repairing >= 1 broken guard — the forgetting-vs-repair
  trade-off knob. If K0 holds the chain, K1 stays sheathed
  regardless of guards.

Frozen campaign signature. **Crown** = the full gate (chain +/ all
four guards) — the first distilled champion. **Support** = chain held
(>= 0.70) AND >= 1 of the two broken guards repaired to its bar — the
two-leg recipe composes at scale even if the crown waits. **Refuted**
= the chain erodes below 0.70 at K0 AND K1's condition path also
fails to produce a chain-holding guard repair — fine-tune safety at
multi-world scale is the recorded casualty.

Baselines (all gated): BC2 = 93.3 / gap 70 / mgap 43 / cluttered 93.3
/ sweep 93.3. The chain-distill specialist = 96.7 on the chain. The
teacher lines: OracleWeave 0.97, OracleTrack 0.885 (n=200).
"""

from skills.base import Knob, Skill
from skills.corridor_slalom_v2.skill import SKILL as V2

_FT = "experiments/bcft_generalist/artifacts/ppo_bcft_generalist_FT.zip"
_FT2 = "experiments/bcft_generalist/artifacts/ppo_bcft_generalist_FT2.zip"

SKILL = Skill(
    name="bcft-generalist",
    version="1",
    scenarios=dict(V2.scenarios),
    cells=V2.cells,  # the slalom-v2 exam, verbatim — ninth sitting
    criteria=V2.criteria,
    knobs=(
        Knob(
            "K0",
            "zero_shot",
            "BC2 + PPO 450k on the uniform five-world diet (the crown shot)",
            "the measured two-leg recipe composed: imitation bought five "
            "skills, on-policy RL now repairs the closed-loop drift that "
            "share could not — while hopefully KEEPING the chain RL could "
            "never discover",
            policy_path=_FT,
        ),
        Knob(
            "K1",
            "zero_shot",
            "RESERVE: FT on the broken worlds only (gap,moving_gap)",
            "played ONLY if K0 loses the chain (< 0.70) while repairing a "
            "broken guard — the forgetting/repair trade-off, step-arbitrated; "
            "sheathed if K0 holds the chain",
            policy_path=_FT2,
        ),
    ),
    max_knobs=3,  # one deviation slot, charter rationale required
    success=V2.success,
    episode_metrics=V2.episode_metrics,
)


def selftest() -> None:
    from skills.base import load_skill
    from skills.corridor_slalom_v2 import skill as v2mod

    s = load_skill("bcft-generalist")
    assert s.cells == V2.cells and s.criteria == V2.criteria
    assert s.success is v2mod.SKILL.success
    assert s.episode_metrics is v2mod.SKILL.episode_metrics
    assert all(k.kind == "zero_shot" for k in s.knobs), "artifacts are hand-built"
    assert s.knobs[0].policy_path == _FT and s.knobs[1].policy_path == _FT2
    targets = [c for c in s.criteria if c.kind == "target"]
    assert len(targets) == 1 and targets[0].bar == 0.70, "bars frozen since the probe"
    print(
        "BCFT-GENERALIST OK: slalom-v2 exam verbatim (ninth sitting), both "
        "knobs hand-built zero-shot, reserve step-gated on the "
        "forgetting/repair condition"
    )


if __name__ == "__main__":
    selftest()

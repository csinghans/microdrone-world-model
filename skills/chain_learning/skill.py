"""chain-learning: the slalom wall, attacked on the RL side.

Pre-registration (written before any number exists). The horizon
campaign closed the model axis (`experiments/horizon/journal.md`): the
chain now survives diet (v1/v2), budget (1350k), fixed rhythm (v2 K1)
and observation horizon (k=48 > the gate period) — while the arena is
flyable (oracle 0.97) and per-gate competence is learnable (frac up to
0.85). The live suspects are the learning algorithm's: **credit
assignment** (success is distal — nothing rewards threading gate k *in
a way that sets up* gate k+1), **exploration** (chains are sampled at
0-3 %, too rare to reinforce), **reward structure** (progress+crash is
indifferent to setup positioning). This campaign plays the two cheapest
RL-side knobs as a 2x2 factorial on the shared 900k chassis, pinned
against corridor-slalom-v2's K1 (same diet, same budget, same exam
seeds — the "neither" cell of the factorial, already gated):

- K1 — per-gate task reward (`gate_bonus=8.0`), single delta vs v2 K1.
  Hypothesis: if distal credit is the wall, paying each threaded gate
  proximally concentrates advantage on the rare successful chains and
  `chain_break_at` moves first.
- K2 — graded diet (+`slalom2_fixed`), single delta vs v2 K1.
  Hypothesis: 2-gate chains succeed at 10-20 % — common enough to
  reinforce — and the learned reversal transfers to gate 3. Confound,
  stated honestly: this also raises total slalom share (2/9 vs 1/8);
  v1's share-doubling knob got *worse* and broke a guard, so a K2 win
  reads as gradation-not-share only weakly — the diag:slalom2 cell and
  K3 help separate.
- K3 — both (the interaction cell, played unconditionally: the
  factorial is only complete with it).

Reward-shaping legality: the no-hand-tuned-danger-weights rule bans
tuning the policy's *perception of danger* (the hand-MPC failure
mode). The gate bonus is task-structure reward — the same category as
the existing +50 goal / -30 crash / 25x progress constants — computed
from privileged sim geometry at training time only; nothing of it is
readable by the policy at inference. Magnitude frozen at **8.0**: about
half the inter-gate progress payout (25 x 0.70 m = 17.5), three gates
total 24 < the goal's 50 (finishing still dominates), one-shot per
fence (no farming), and paid by the exam's own predicate —
`gate_bonus_hits` mirrors `slalom_metrics` inequality-for-inequality,
so the reward cannot teach a different "through the gap" than the one
judged. One value, no sweep: if 8.0 fails, the knob fails.

Campaign signature (frozen): **support** = any knob moves slalom3@1.0
`chain_break_at` to >= 2.5 (mean, n=30); **full support** = success
>= 0.70 (the priced bar, unchanged from the probe). **Refuted** = all
three knobs land chain_break_at < 2.5 with success < 0.10 and the
trainings completing — then reward-altitude and diet-altitude RL fixes
are eliminated too, and the remaining suspects escalate to
algorithm-class surgery (policy memory, n_steps/GAE, algorithm swap),
a separate future campaign.

Exam: corridor-slalom-v2's cells, criteria and predicates VERBATIM
(same seed0 22000 — every reading is comparable to the whole baseline
band: chain_break_at 1.33-2.10, success 0-3 %, weave_frac 0.62-0.85
across v2 K0/K1/K2 and the h48 stack). Guards: the dilution
expectation is on the record — 8-world diets have broken guard:mgap
three times (v2 K1/K2, h48); a recurrence blocks promotion as always
but does not touch the science signature.
"""

import numpy as np

from skills.base import Knob, Skill
from skills.corridor_slalom.skill import slalom_metrics
from skills.corridor_slalom_v2.skill import SKILL as V2
from skills.corridor_slalom_v2.skill import _spawn_slalom3_fixed

_V2_DIET = ("classic", "classic", "dense", "moving", "gap", "moving_gap", "solo")
_CHASSIS = dict(x_progress=True, edge_bias=True, timesteps=900_000)
_BONUS = 8.0

SKILL = Skill(
    name="chain-learning",
    version="1",
    scenarios=dict(V2.scenarios),  # same five worlds, re-registered idempotently
    cells=V2.cells,  # the exam, verbatim (bars were priced by the probe)
    criteria=V2.criteria,
    knobs=(
        Knob(
            "K1",
            "policy",
            "per-gate task reward (gate_bonus=8.0) on the v2-K1 recipe",
            "if distal credit is the wall, proximal gate pay concentrates "
            "advantage on rare chains and chain_break_at moves first",
            train_kwargs=dict(
                worlds=_V2_DIET + ("slalom3_fixed",), gate_bonus=_BONUS, **_CHASSIS
            ),
        ),
        Knob(
            "K2",
            "policy",
            "graded diet: slalom2_fixed added to the v2-K1 recipe",
            "2-gate chains succeed often enough to reinforce; the reversal "
            "should transfer (share confound stated in the pre-registration)",
            train_kwargs=dict(
                worlds=_V2_DIET + ("slalom2_fixed", "slalom3_fixed"), **_CHASSIS
            ),
        ),
        Knob(
            "K3",
            "policy",
            "both: gate reward + graded diet (the interaction cell)",
            "played unconditionally — the factorial is only complete with it; "
            "a K3-only win means the axes help jointly, not alone",
            train_kwargs=dict(
                worlds=_V2_DIET + ("slalom2_fixed", "slalom3_fixed"),
                gate_bonus=_BONUS,
                **_CHASSIS,
            ),
        ),
    ),
    max_knobs=4,  # one deviation slot, charter rationale required
    success=V2.success,
    episode_metrics=V2.episode_metrics,
)


def selftest() -> None:
    from skills.base import load_skill

    s = load_skill("chain-learning")
    # the exam is v2's, verbatim — bars, seeds, predicates all shared
    assert s.cells == V2.cells and s.criteria == V2.criteria
    assert s.success is V2.success and s.episode_metrics is V2.episode_metrics

    # the factorial is exact: K1 = v2K1 + bonus; K2 = v2K1 + slalom2; K3 = both
    v2k1 = dict(V2.knobs[1].train_kwargs)
    k1, k2, k3 = (dict(k.train_kwargs) for k in s.knobs)
    assert k1.pop("gate_bonus") == _BONUS and k1 == v2k1
    assert "gate_bonus" not in k2
    assert set(k2["worlds"]) - set(v2k1["worlds"]) == {"slalom2_fixed"}
    assert k3.pop("gate_bonus") == _BONUS and k3 == k2

    # soul-assert: the training bonus and the exam metric judge the SAME
    # crossing — thread pays once per fence, a detour spends the fence
    # unpaid and cannot circle back for the money
    from planner.learned_policy import gate_bonus_hits
    from skills.gap_flight.skill import PILLAR_R

    fences = _spawn_slalom3_fixed(None, np.random.default_rng(5)).meta["fences"]
    (x0, yc0, w0), (x1, yc1, _), (x2, yc2, _) = fences
    weave = [
        (0.4, 0.0),
        (x0 + 0.05, yc0),
        (x1 + 0.05, yc1),
        (x2 + 0.05, yc2),
        (3.6, 0.0),
    ]
    spent, paid = set(), []
    for a, b in zip(weave, weave[1:]):
        paid += gate_bonus_hits(a, b, fences, spent, PILLAR_R)
    m = slalom_metrics(
        {
            "scenario_meta": {"fences": fences},
            "path": np.array(weave),
            "reached": True,
            "crashed": False,
        }
    )
    assert paid == [0, 1, 2] and m["weave_frac"] == 1.0 and m["chain_break_at"] == 3.0
    y_out = yc0 + (w0 + 2 * PILLAR_R) / 2.0 + 0.3  # outside the crash-legal band
    detour = [
        (x0 - 0.05, y_out),
        (x0 + 0.05, y_out),
        (x0 - 0.05, yc0),
        (x0 + 0.05, yc0),
    ]
    spent, paid = set(), []
    for a, b in zip(detour, detour[1:]):
        paid += gate_bonus_hits(a, b, fences, spent, PILLAR_R)
    md = slalom_metrics(
        {
            "scenario_meta": {"fences": fences},
            "path": np.array(detour + [(3.6, 0.0)]),
            "reached": True,
            "crashed": False,
        }
    )
    assert paid == [] and 0 in spent, "detour must spend fence 0 unpaid"
    assert md["chain_break_at"] == 0.0, "exam agrees: first fence not threaded"
    print(
        f"CHAIN-LEARNING OK: exam inherited verbatim from v2, exact 2x2 "
        f"factorial vs the v2-K1 control (bonus={_BONUS}, +slalom2), reward "
        f"predicate mirrors the exam metric (thread pays, detour spends)"
    )


if __name__ == "__main__":
    selftest()

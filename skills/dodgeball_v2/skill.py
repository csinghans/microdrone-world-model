"""dodgeball v2: the guard-clean defender — the union cell of the 2x2.

Pre-registration (written before any number exists). The v1 campaign
closed SUPPORT with the crown vacant and left a factorial one cell
short: (diet: pure/mixed) x (station pay: distal/dense) has been
measured at pure x distal (v1 K1: dodges by yielding ground), mixed x
distal (v1 K2: transit majority erases the station entirely), and
pure x dense (v1 K3: holds the station, dodge@v1.0 60 % over its bar,
but transit guards structurally fail). **This campaign plays the
missing cell: mixed x dense** — can one zip transit AND defend?

Exam: v1's cells, criteria and predicates VERBATIM (bars stay frozen
per the v1 close; same seed0 23000 — every reading comparable to the
whole v1 gate history). Baselines, already gated in
`experiments/dodgeball/`: K2 (mixed, no tick) dodge success 0 %
everywhere with disp_x 3.01 (flees to goal) and sweep@2.0 broken at
37 %; K3 (tick, pure) v0.6/v1.0/v1.4/v1.8 = 47/60/20/13 % with all
transit guards structurally failed.

Knobs (single-delta chains, frozen):

- K1 — v1-K2's exact 7-world diet + station_tick=0.6 (single delta vs
  K2: the tick; single delta vs K3: the mixing). Hypothesis: the tick
  gave the pure specialist a reason to hold ground; transit worlds pay
  progress, ball worlds pay the station, and the per-world reward
  dispatch (meta-carried) lets one policy learn both economies.
- K2 — CONDITIONAL, arbitrated with `research step` per the CLAUDE.md
  lesson (never `run` with conditional knobs): played only if K1
  passes >= 1 dodge bar AND breaks guard:sweep@2.0 or guard:cluttered
  — the dilution signature (v1-K2 broke sweep at 37 %; classic share
  is 1/7 here). Then K2 = K1's diet + classic x2 (the moving-gap-v2
  share-healing pattern, one delta). If K1 instead fails every dodge
  bar (mixing erodes the station even WITH the tick), K2 stays
  sheathed and the campaign closes: the union does not hold at this
  training altitude.

Frozen campaign signature. **Support (the ledger's claim):** one zip
passes >= 1 dodge target bar AND all four guards — the guard-clean
defender exists. **Crown:** the full gate (all four dodge bars +
guards); stated openly: v1.4/v1.8 sit behind the k=32 warning-range
arithmetic (0.7 + v*0.67 m) that v1 measured twice, so a crown likely
needs the WM48 crutch and is NOT expected here. **Refuted:** every
played knob either fails all dodge bars or breaks guards — the
transit/defense trade is structural at 900k and the campaign closes
honestly; escalations (WM48 warning time, share surgery beyond one
delta) belong to a fresh pre-registration.
"""

from skills.base import Knob, Skill
from skills.dodgeball.skill import SKILL as V1

_CHASSIS = dict(x_progress=True, edge_bias=True, timesteps=900_000)
_MIXED = ("classic", "gap", "moving_gap") + (
    "dodgeball_v06",
    "dodgeball_v10",
    "dodgeball_v14",
    "dodgeball_v18",
)

SKILL = Skill(
    name="dodgeball-v2",
    version="2",
    scenarios=dict(V1.scenarios),  # same worlds, re-registered idempotently
    cells=V1.cells,  # the exam verbatim — bars frozen at the v1 close
    criteria=V1.criteria,
    knobs=(
        Knob(
            "K1",
            "policy",
            "the union cell: v1-K2's mixed diet + station_tick=0.6",
            "single delta vs K2 (the tick) and vs K3 (the mixing): per-world "
            "reward dispatch lets one policy learn both economies — transit "
            "pays progress, ball worlds pay the station",
            train_kwargs=dict(worlds=_MIXED, station_tick=0.6, **_CHASSIS),
        ),
        Knob(
            "K2",
            "policy",
            "share healing: K1's recipe + classic x2",
            "CONDITIONAL (research step only): played iff K1 passes >= 1 "
            "dodge bar AND breaks sweep/cluttered — the dilution signature; "
            "classic share 1/7 -> 2/8 per the moving-gap-v2 pattern",
            train_kwargs=dict(
                worlds=("classic",) + _MIXED, station_tick=0.6, **_CHASSIS
            ),
        ),
    ),
    max_knobs=3,  # one deviation slot, charter rationale required
    success=V1.success,
    episode_metrics=V1.episode_metrics,
)


def selftest() -> None:
    from skills.base import load_skill
    from skills.dodgeball import skill as v1mod

    s = load_skill("dodgeball-v2")
    # the exam is v1's, verbatim — bars, seeds, predicates all shared
    assert s.cells == V1.cells and s.criteria == V1.criteria
    assert s.success is v1mod.dodge_success
    assert s.episode_metrics is v1mod.dodge_metrics
    # single-delta chains: K1 = v1K2 diet + tick; = v1K3 kwargs + mixing
    v1k2, v1k3 = dict(V1.knobs[2].train_kwargs), dict(V1.knobs[3].train_kwargs)
    k1, k2 = (dict(k.train_kwargs) for k in s.knobs)
    assert k1.pop("station_tick") == 0.6 and k1 == v1k2, "one delta vs v1 K2"
    k1b = dict(s.knobs[0].train_kwargs)
    assert k1b["station_tick"] == v1k3["station_tick"], "same tick as K3"
    assert set(k1b["worlds"]) > set(v1k3["worlds"]), "K3 + mixing"
    # K2 is K1 + classic x2 (share healing), nothing else
    assert k2["worlds"].count("classic") == 2
    assert (
        k2.pop("worlds") and k1b.pop("worlds") and k2 == {k: v for k, v in k1b.items()}
    )
    print(
        "DODGEBALL-V2 OK: exam inherited verbatim (bars frozen), the union "
        "cell is an exact single delta vs both v1 arms, share-healing "
        "reserve is one further delta"
    )


if __name__ == "__main__":
    selftest()

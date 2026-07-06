"""wm48-defense: same body, same reward, longer eyes — attack the warning wall.

Pre-registration (written before any number exists). The dodgeball arc
measured the fast-cell wall twice and priced its mechanism: the heads
answer "inside 0.7 m within k<=32 steps (0.67 s)", so a ball enters the
observation at range 0.7 + v*0.67 — a 1.06 s warning at 1.8 m/s against
a ~1.1 s dodge. v1-K3's crash gradient (0/27/43/77 %) tracks that
arithmetic. The horizon campaign left a trained k=48 stack in
`experiments/horizon/artifacts/wm_h48.pth` (horizons 4/8/16/32/48,
val AUC@48 = 0.75): under it a ball is visible at 0.7 + v*1.0 — 1.4 s
of warning at 1.8 m/s. Its transit refutation says nothing about
defense; this campaign asks the defense question.

**The knob is the MODEL, nothing else.** K1's train_kwargs are v1-K3's
verbatim (pure ball diet, station_tick=0.6, the standard chassis) —
asserted identical in the selftest — and the single delta lives
outside the kwargs: `output/world_model.pth` is SWAPPED to the WM48
checkpoint for the whole knob (train + exam), then restored to G1 and
verified against its artifacts.lock.json sha256. ObsBuilder sizes the
observation from the loaded model's meta (10 probs/candidate instead
of 8), so the policy zip pairs EXCLUSIVELY with wm_h48.pth — the
provenance pairing is recorded in the journal, M2-style.

Exam: dodgeball v1 cells/criteria VERBATIM (bars frozen: 0.65 /
0.55 x3; same seed0 23000 — comparable to the whole v1/v2 gate
history). Baseline: v1-K3 = 47/60/20/13 % with crash 0/27/43/77 %.

Frozen signature. **Support:** >= 1 of the two fast cells (v1.4, v1.8)
clears its 0.55 bar. **Mechanism check** (reported either way): crash
at v1.8 materially below K3's 77 % — the longer lens must show up in
the crash column first. **Refuted:** both fast cells at K3-level with
training completed — then the blur is the live suspect (the k=48 head
is the stack's weakest, AUC 0.75 vs 0.86; a longer lens that cannot
rank actions buys nothing) or the dodge kinematics bind earlier than
warning time; either way the warning-time hypothesis dies honestly.
Secondary read, recorded not judged: v0.6/v1.0 retention under the
swap (the 4/8/16/32 heads rode along — they should hold).

Transit guards are expected structural failures (pure diet, as v1-K3):
promotion impossible by design, the fast cells are the point.
"""

from skills.base import Knob, Skill
from skills.dodgeball.skill import SKILL as V1

_K3_RECIPE = dict(V1.knobs[3].train_kwargs)  # verbatim — the model is the knob

SKILL = Skill(
    name="wm48-defense",
    version="1",
    scenarios=dict(V1.scenarios),
    cells=V1.cells,  # the exam verbatim — bars frozen at the v1 close
    criteria=V1.criteria,
    knobs=(
        Knob(
            "K1",
            "policy",
            "v1-K3's recipe verbatim, trained and examined under WM48",
            "the single delta is the swapped model (1.0 s horizon): warning "
            "1.06 -> 1.4 s at v1.8. Swap protocol + provenance pairing in "
            "the journal; zip flies ONLY with wm_h48.pth",
            train_kwargs=dict(_K3_RECIPE),
        ),
    ),
    max_knobs=2,  # one deviation slot, charter rationale required
    success=V1.success,
    episode_metrics=V1.episode_metrics,
)


def selftest() -> None:
    from skills.base import load_skill
    from skills.dodgeball import skill as v1mod

    s = load_skill("wm48-defense")
    assert s.cells == V1.cells and s.criteria == V1.criteria
    assert s.success is v1mod.dodge_success
    assert s.episode_metrics is v1mod.dodge_metrics
    # the model is the ONLY knob: kwargs are v1-K3's, byte for byte
    assert dict(s.knobs[0].train_kwargs) == dict(V1.knobs[3].train_kwargs)
    print(
        "WM48-DEFENSE OK: exam inherited verbatim, K1 kwargs identical to "
        "v1-K3 — the swapped model is the single delta, enforced"
    )


if __name__ == "__main__":
    selftest()

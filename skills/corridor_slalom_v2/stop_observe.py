"""Stop-and-observe slalom: a wrapper that HOVERS after each threaded gate
to settle and re-plan from a clean frame, then resumes to the next gate.

Why: slalom is the longest, tightest chain (~40 decisions); a per-decision
latent shift COMPOUNDS over the chain (0.99^40 ~= 0.67), which is why the
continuous slalom champion collapsed 80%->0% when run on the unified WM
(the encoder swap). Stopping between gates RESETS the accumulation — each
gate becomes an independent short-horizon decision — so it should (a) be a
robust cautious behaviour and (b) let slalom survive the WM swap. Both are
measured in eval/eval_slalom_stopobserve.py.

Design (no retrain, no scenario change): wrap an existing slalom
`LearnedPolicy`. Detect "just threaded gate k" with the SAME predicate the
exam uses (`planner/learned_policy.py:gate_bonus_hits`, mirrors the scoring
exactly, spends each fence once). On a hit, return the HOVER action (id 5,
already in the champion's trained menu) for `hover` decisions — VelCommander
turns a zero command into a true position hold — then delegate back to the
champion, which re-encodes a settled latent and picks the next-gate action.
"Observe = re-plan from a clean frame": the hover itself is the observation
(a stable frame + re-anchored reference); no extra perception is added.
"""

import argparse
import sys

from planner.action_set import ACTION_NAMES
from planner.learned_policy import gate_bonus_hits

HOVER = ACTION_NAMES.index("hover")  # id 5 — in the champion's trained menu
PILLAR_R = 0.18  # == skills/gap_flight/skill.py PILLAR_R (the exam's half-band)


class StopObserveSlalom:
    """Wraps `inner` (a slalom policy: begin(pillars)/decide(frame,state)->int).
    `fences` = the scenario's meta["fences"] list of (x, yc, w). After the
    drone threads a gate, hover `hover` decisions before resuming."""

    def __init__(self, inner, fences, hover: int = 8, pillar_r: float = PILLAR_R):
        self.inner = inner
        self.fences = list(fences)
        self.hover = int(hover)
        self.pillar_r = float(pillar_r)

    def begin(self, pillars) -> None:
        self.prev = None
        self.spent: set = set()
        self.hover_left = 0
        self.gates_hit = 0  # diagnostic: how many gates triggered a hover
        self.inner.begin(pillars)

    def decide(self, frame, state) -> int:
        cur = (float(state[0]), float(state[1]))
        if self.hover_left == 0:  # only look for a new gate when not hovering
            prev = self.prev if self.prev is not None else cur
            if gate_bonus_hits(prev, cur, self.fences, self.spent, self.pillar_r):
                self.hover_left = self.hover  # open a fresh hover window
                self.gates_hit += 1
        self.prev = cur
        if self.hover_left > 0:
            self.hover_left -= 1
            self.inner.decide(frame, state)  # keep the champion's history warm
            return HOVER
        return self.inner.decide(frame, state)


class _StubInner:
    """Env-free stand-in: always FORWARD, records call count."""

    def __init__(self):
        self.calls = 0

    def begin(self, pillars) -> None:
        self.began = True

    def decide(self, frame, state) -> int:
        self.calls += 1
        return 0  # FORWARD


def selftest() -> None:
    # two gates on x-planes 1.0 and 2.0, gaps centred at y=0, width 0.6
    fences = [(1.0, 0.0, 0.6), (2.0, 0.0, 0.6)]
    inner = _StubInner()
    pol = StopObserveSlalom(inner, fences, hover=3)
    pol.begin(pillars=[])
    assert inner.began

    def step(x):  # fly straight through the gaps (y stays 0)
        return pol.decide(frame=None, state=[x, 0.0, 1.0])

    # approach gate 1: no crossing yet -> delegate (FORWARD)
    assert step(0.5) == 0 and step(0.9) == 0, "pre-gate should delegate"
    # cross gate-1 plane (0.9 -> 1.1): trigger hover, then hover=3 total
    assert step(1.1) == HOVER, "crossing gate 1 must start a hover"
    assert step(1.1) == HOVER and step(1.1) == HOVER, "hover window = 3 decisions"
    assert pol.hover_left == 0, "hover window exhausted"
    # resume: delegate again until gate 2
    assert step(1.5) == 0, "after hover, resume delegating"
    # cross gate-2 plane (1.9 -> 2.1)
    assert step(1.9) == 0
    assert step(2.1) == HOVER, "crossing gate 2 must start a hover"
    assert pol.gates_hit == 2, "exactly two gates triggered hovers"
    assert pol.spent == {0, 1}, "both fences spent once"
    # a fence is never double-counted
    n_before = pol.gates_hit
    for _ in range(4):
        step(2.1)
    assert pol.gates_hit == n_before, "no gate re-triggers after it is spent"
    print(
        f"STOP-OBSERVE OK: hover id {HOVER}, gate-once trigger, "
        f"{pol.gates_hit} gates hovered (window 3), spent {sorted(pol.spent)}"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.parse_args()
    selftest()


if __name__ == "__main__":
    sys.exit(main())

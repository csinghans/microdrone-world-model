"""The synthetic pilot family — a seeded, imperfect human stand-in.

Privileged vision, imperfect execution: the competence core is the dense
probe's gap tracker (`eval.eval_dense_probe.OracleField`, the measured
arena-ceiling instrument — geometry constants imported, not re-derived),
and the humanity is a fixed four-stage pipeline wrapped around it:

    intent -> distraction (eyes off: hold the stale command)
           -> noise       (fat thumb: a random menu action)
           -> delay       (reaction-latency FIFO, decision ticks)
           -> emitted

The pipeline order is frozen and load-bearing: "didn't look" gates
"mis-executed" gates "was late". Personas are INSTRUMENT CONSTANTS (the
OracleField convention — frozen with the tool): they may be tuned once
during bring-up if the probe's usable-band rule fires, and never after the
pre-registration commit. Reaction-latency design note (not a claim): human
visual RT of 150-300 ms maps to 2-4 ticks at 12 Hz.

The pilot is honestly privileged (a human sees the whole scene; the
embedded guardian sees one 64x64 frame) — the constraint under study is
the assistant's, which is this repo's wedge spent on someone else's intent.

Run:
  python -m assist.pilot   # env-free selftest
"""

from collections import deque
from dataclasses import dataclass

import numpy as np

from eval.eval_dense_probe import (
    CAP,
    EDGE,
    LOOK2,
    PROX_W,
    RECENTER,
    STICKY,
    VEER_L,
    VEER_R,
)
from planner.action_set import FORWARD, menu

MENU = tuple(menu())


@dataclass(frozen=True)
class PilotParams:
    """One persona. delay: reaction latency in decision ticks (1 = 83 ms);
    noise_p: P(fat-thumb random menu action) per decision; distract_p /
    distract_len: P(a distraction window opens) and its length in decisions
    (the stale command is held, eyes off); deadband: |target_y - y| the
    pilot is content to call centred (sloppiness)."""

    name: str
    delay: int
    noise_p: float
    distract_p: float
    distract_len: int
    deadband: float


PERSONAS = {
    "expert": PilotParams("expert", 1, 0.00, 0.005, 4, 0.12),
    "average": PilotParams("average", 2, 0.03, 0.020, 6, 0.18),
    "novice": PilotParams("novice", 4, 0.08, 0.040, 10, 0.25),
}
# the oracle-guardian arm's takeover stand-in: perfect eyes, near-zero flaws
# (an instrument, not a persona — never a probe cell)
PERFECT = PilotParams("perfect", 1, 0.00, 0.000, 1, 0.12)
_SALT = {"expert": 101, "average": 211, "novice": 331, "perfect": 431}


class SyntheticPilot:
    """Speaks the standard policy contract (`begin`/`decide`), emits menu
    action ids, and is deterministic per (params, seed): the same seed gives
    the same imperfection stream, which is what makes the paired protocol
    (same pilot flown with and without the guardian) attributable."""

    def __init__(self, params, seed: int):
        self.params = PERSONAS[params] if isinstance(params, str) else params
        self.seed = int(seed)
        self.pillars: list = []  # runner/guardian-refreshed (movers stay live)
        self.target = None

    def begin(self, pillars) -> None:
        self.pillars = list(pillars) if pillars is not None else []
        self.rng = np.random.default_rng(
            (self.seed << 8) ^ _SALT.get(self.params.name, 997)
        )
        self._fifo = deque([FORWARD] * max(self.params.delay, 1))
        self._distract_left, self._held = 0, FORWARD
        self.target = None

    def _intent(self, state) -> int:
        """The OracleField gap tracker with the persona's deadband: sort the
        window's pillars into a virtual y-ladder, score gaps by capped width
        minus distance-to-reach plus stickiness, error-steer to the winner."""
        x, y = float(state[0]), float(state[1])
        win = [float(q[1]) for q in self.pillars if x < float(q[0]) <= x + LOOK2]
        if not win:
            self.target = None
            if y > RECENTER:
                return VEER_R
            if y < -RECENTER:
                return VEER_L
            return FORWARD
        ys = [-EDGE] + sorted(win) + [EDGE]
        best, tgt = None, 0.0
        for lo, hi in zip(ys, ys[1:]):
            width, mid = hi - lo, (hi + lo) / 2.0
            score = min(width, CAP) - PROX_W * abs(mid - y)
            if self.target is not None and abs(mid - self.target) < 0.2:
                score += STICKY
            if best is None or score > best:
                best, tgt = score, mid
        self.target = tgt
        err = tgt - y
        if abs(err) < self.params.deadband:
            return FORWARD
        return VEER_L if err > 0 else VEER_R

    def decide(self, frame, state) -> int:
        del frame  # privileged pilot: honestly not a vision contender
        intent = self._intent(state)
        if self._distract_left > 0:  # eyes off: the stale command persists
            self._distract_left -= 1
            intent = self._held
        elif self.rng.random() < self.params.distract_p:
            self._distract_left = self.params.distract_len - 1
            intent = self._held
        if self.rng.random() < self.params.noise_p:  # fat thumb
            intent = int(self.rng.choice(MENU))
        self._fifo.append(intent)  # reaction latency: emit the stale intent
        emitted = int(self._fifo.popleft())
        self._held = emitted
        return emitted


def selftest() -> None:
    course = [(1.2, 0.3), (2.0, -0.5), (2.6, 0.1)]

    def fly(pilot, n=200, seed=5):
        rng = np.random.default_rng(seed)
        pilot.begin(course)
        out = []
        for i in range(n):
            state = np.zeros(20)
            state[0], state[1] = 3.0 * i / n, float(rng.uniform(-0.6, 0.6))
            out.append(pilot.decide(None, state))
        return out

    # determinism: same (persona, seed) -> identical stream; new seed differs
    a = fly(SyntheticPilot("novice", 42))
    b = fly(SyntheticPilot("novice", 42))
    c = fly(SyntheticPilot("novice", 43))
    assert a == b, "same persona+seed must replay identically"
    assert a != c, "a fresh seed must draw fresh imperfections"
    assert set(a) <= set(MENU), "the pilot must stay on the planner menu"

    # delay: with flaws zeroed, emitted == intent shifted by exactly `delay`
    class _Scripted(SyntheticPilot):
        def _intent(self, state):
            self._i = getattr(self, "_i", -1) + 1
            return MENU[self._i % len(MENU)]

    p = _Scripted(PilotParams("x", 3, 0.0, 0.0, 1, 0.12), 7)
    p.begin([])
    got = [p.decide(None, np.zeros(20)) for _ in range(20)]
    want = [FORWARD] * 3 + [MENU[i % len(MENU)] for i in range(17)]
    assert got == want, "delay FIFO must shift the intent stream exactly"

    # noise: empirical fat-thumb rate within 3 sigma of noise_p
    p = SyntheticPilot(PilotParams("x", 1, 0.30, 0.0, 1, 0.12), 11)
    p.begin([])
    n = 4000
    flips = 0
    for _ in range(n):
        state = np.zeros(20)  # no pillars, centred -> clean intent is FORWARD
        flips += int(p.decide(None, state) != FORWARD)
    rate = flips / n
    # a random menu draw returns FORWARD 1/5 of the time -> observable 0.24
    want_rate = 0.30 * (1 - 1 / len(MENU))
    sigma = (want_rate * (1 - want_rate) / n) ** 0.5
    assert abs(rate - want_rate) < 3 * sigma, (rate, want_rate)

    # distraction: the window holds the stale command exactly distract_len
    p = SyntheticPilot(PilotParams("x", 1, 0.0, 1.0, 5, 0.12), 3)
    p.begin([])
    state = np.zeros(20)
    p.decide(None, state)  # opens a window on the first draw
    held = p._held
    for _ in range(4):  # the remaining window decisions replay it
        assert p.decide(None, state) == held

    # persona table: monotone degradation, keys consistent, frozen values
    for k in ("expert", "average", "novice"):
        assert PERSONAS[k].name == k
    e, a_, n_ = PERSONAS["expert"], PERSONAS["average"], PERSONAS["novice"]
    assert e.delay <= a_.delay <= n_.delay
    assert e.noise_p <= a_.noise_p <= n_.noise_p
    assert e.distract_p <= a_.distract_p <= n_.distract_p
    assert e.deadband <= a_.deadband <= n_.deadband
    assert PERFECT.noise_p == 0.0 and PERFECT.distract_p == 0.0
    print(
        f"PILOT OK: {len(PERSONAS)} personas frozen, deterministic per seed, "
        f"pipeline distraction->noise->delay verified, menu-closed"
    )


if __name__ == "__main__":
    selftest()

"""The safety envelope around any policy — scripted, MPC, or learned.

v0.1 codifies the two guards the planners already rely on, behind one
interface, so every policy can be wrapped identically:

  * **Imminent-critical backstop** — when "straight ahead hits within
    ~170 ms" saturates, force an evasion regardless of what the policy says.
    (The relative-margin trigger goes blind exactly when every candidate
    saturates together — measured; this is the absolute floor under it.)
  * **Geofence** — a soft box in the drone's own odometry frame; outside it,
    command hover. Never sees pillar positions.

The full hardware failsafe list (manual override, emergency land,
low-battery behaviour, log replay, field-test checklist) is specified in
docs/safety.md and lands with the v0.4 hardware bridge.
"""

import numpy as np

IMMINENT_P = 0.5  # P(critical within <=170 ms straight ahead) that forces evasion
FENCE_Y = 2.4  # |y| beyond this -> hover (matches the training envelope)


class SafetyFilter:
    """Wraps a policy decision with the imminent backstop + geofence."""

    def __init__(self, i_fwd: int, i_veers, i_hover: int):
        self.i_fwd, self.i_veers, self.i_hover = int(i_fwd), list(i_veers), int(i_hover)

    def imminent(self, p: np.ndarray) -> bool:
        """p: (n_cands, n_horizons, 2) sigmoid probs. True when straight
        ahead is about to hit within the two shortest horizons."""
        return float(p[self.i_fwd, :2, 1].max()) > IMMINENT_P

    def filter(self, action: int, p: np.ndarray, state: np.ndarray) -> int:
        if abs(float(state[1])) > FENCE_Y:
            return self.i_hover
        if action == self.i_fwd and self.imminent(p):
            crit = p[:, :2, 1].max(axis=1)  # near-term crit per candidate
            return self.i_veers[int(np.argmin([crit[i] for i in self.i_veers]))]
        return action


def selftest() -> None:
    sf = SafetyFilter(i_fwd=0, i_veers=[2, 3], i_hover=4)
    p = np.zeros((5, 4, 2), dtype=np.float32)
    state = np.zeros(20)
    assert sf.filter(0, p, state) == 0, "clear ahead must pass through"
    p[0, 0, 1] = 0.9  # straight ahead about to hit
    p[2, :2, 1] = 0.8  # left veer also bad; right veer clean
    assert sf.filter(0, p, state) == 3, "backstop must pick the safer veer"
    state[1] = 3.0
    assert sf.filter(0, p, state) == 4, "outside the fence -> hover"
    print("SAFETY-FILTER OK: imminent backstop + geofence override assert")


if __name__ == "__main__":
    selftest()

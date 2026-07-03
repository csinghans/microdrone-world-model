"""The hand-crafted planners: a latent MPC and its reactive baseline.

**WMPolicy** is a tiny latent MPC from vision alone: an anticipatory
*trigger* plus a safest-veer *chooser*, at ~12 Hz (an on-board-honest
decision rate). Each decision encodes the frame once, then asks the
predictor "and if I held *this* command?" for every candidate — the
expensive encoder is shared, so on a GAP8 the whole deliberation is nearly
free. The trigger is *relative*: evade when going straight is predicted
meaningfully more warn-dangerous than the better veer (an absolute threshold
inherits the heads' course-dependent probability floor and false-triggers —
measured), with an absolute near-term *crit* backstop for the moment
everything saturates together. On trigger it commits ~0.5 s to the veer with
the cheapest predicted future:

    cost = 6*(0.25*warn + 0.75*crit) + heading + 1.5*|y_after| - 1.2*progress

The *critical* ring keeps that choice sighted inside the warn ring (where
every moving action correctly "warns"), and the |y_after| term is a
corridor-centering prior from the drone's own odometry — because the camera
cannot see 60 degrees to the side, the planner prefers not to wander there.

**ReactivePolicy** is the honest baseline: same encoder, but only the
danger-*now* head — no look-ahead. Generous handicap: when it does trigger,
we hand it the correct evasion direction from privileged pillar positions (a
real reactive stack would need a depth net for that). It can only lose on
*timing*, so the comparison isolates anticipation.

Historical note, measured across eight hand-tuned planner configurations:
every constant below fixed one failure mode and exposed the next. That
whack-a-mole is why the learned policy (`planner.learned_policy`) exists —
and why it beat this planner everywhere. This MPC stays as the transparent,
inspectable middle rung of the ladder.
"""

import numpy as np
import torch

from planner.action_set import ACTION_NAMES, FORWARD
from sim.envs import CTRL_HZ

DECIDE_EVERY = 4  # decide at 12 Hz — an honest on-board rate; PID stays 48 Hz
THETA_NOW = 0.5  # reactive trigger on P(too close now)
EVADE_HOLD = 24  # hold a chosen evasion ~0.5 s before re-checking
W_DANGER, W_HEAD, W_SWITCH, W_PROG = 6.0, 1.0, 0.5, 1.2  # MPC cost weights
W_CENTER = 1.5  # corridor-centering prior (own odometry only)
# Urgency weights over the horizons (83/167/333/667 ms). Imminent danger
# counts fully; distant danger is an early warning. A flat max-over-horizons
# would treat "will cross 0.7 m within 667 ms" as a veto — but passing a
# pillar at a safe 0.5 m *is* such a crossing, so far horizons must warn,
# not forbid.
W_HORIZON = (1.0, 0.6, 0.35, 0.2)
MARGIN_WM = 0.4  # relative trigger margin (immune to the probability floor)


def _frame_tensor(frame: np.ndarray) -> torch.Tensor:
    x = torch.tensor(frame, dtype=torch.float32).permute(2, 0, 1) / 255.0
    return x.unsqueeze(0)  # (1, 3, 64, 64)


class WMPolicy:
    """Latent MPC from vision alone. Never sees the pillar positions."""

    def __init__(self, enc, pred, cheads, meta, speed: float = 1.0):
        self.enc, self.pred, self.cheads = enc, pred, cheads
        names = list(meta["action_names"])
        vecs = float(speed) * np.array(meta["action_vecs"], dtype=np.float32)
        # The planner's menu. The corridor task is planar and `climb` games the
        # planar danger label (a slower planar approach scores "safer" without
        # ever engaging the visual task — traced: the MPC climbed over the
        # course), so the planner leaves it off the menu; the model itself
        # still knows the full six-command vocabulary.
        self.ids = [i for i, n in enumerate(names) if n != "climb"]
        self.i_fwd = self.ids.index(FORWARD)
        self.i_veers = [
            self.ids.index(names.index(n)) for n in ("veer_left", "veer_right")
        ]
        sub = vecs[self.ids]
        self.cands = torch.tensor(sub / np.array(meta["a_norm"], dtype=np.float32))
        # per-candidate cost terms that never change: heading error vs the +x
        # goal direction, and forward progress normalised to the menu's fastest
        # candidate — so the cost trade-offs are identical at every cruise speed
        xy = sub[:, :2]
        spd = np.linalg.norm(xy, axis=1)
        self.heading = torch.tensor(
            np.where(spd > 1e-6, 1.0 - xy[:, 0] / np.maximum(spd, 1e-6), 1.0),
            dtype=torch.float32,
        )
        self.progress = torch.tensor(sub[:, 0] / max(float(sub[:, 0].max()), 1e-6))
        self.vy = sub[:, 1]  # for the centering prior (own odometry only)
        h_w = list(W_HORIZON)[: len(meta["horizons"])]
        self.h_w = torch.tensor(h_w, dtype=torch.float32)
        self.hold, self.evade = 0, FORWARD
        self.h = None  # model-side memory state (v3 checkpoints)

    def begin(self, pillars) -> None:
        del pillars  # vision only — the whole point
        self.hold, self.evade = 0, FORWARD
        self.h = None

    def _state(self, frame: np.ndarray):
        """Encoder (+ one GRU step when the model carries memory). Runs every
        decision — including during holds — so the memory never skips frames.
        Returns (conditioning, frame latent): the forecast is conditioned on
        the memory but its residual starts from the current frame."""
        z = self.enc(_frame_tensor(frame))
        tem = getattr(self.enc, "temporal", None)
        if tem is None:
            return z, z
        h, self.h = tem.step(z, self.h)
        return h, z

    def decide(self, frame: np.ndarray, state: np.ndarray) -> int:
        # `state` supplies the drone's OWN odometry (y, for the centering
        # prior) — its knowledge of itself, never of the pillars
        with torch.no_grad():
            cond, z0 = self._state(frame)  # encoder runs ONCE per frame
            if self.hold > 0:  # fly the chosen maneuver through
                self.hold -= DECIDE_EVERY
                return self.evade
            z_hat = self.pred(
                cond.expand(len(self.cands), -1),
                self.cands,
                base=z0.expand(len(self.cands), -1),
            )
            p = torch.sigmoid(self.cheads(z_hat))  # (n_cands, horizons, 2 rings)
        warn = p[:, :, 0] @ self.h_w  # urgency-weighted "close soon"
        crit = p[:, :, 1] @ self.h_w  # urgency-weighted "about to hit"
        edge = float(warn[self.i_fwd]) - min(float(warn[i]) for i in self.i_veers)
        # the relative margin has a blind spot: when the drone is already deep
        # in trouble every candidate saturates together and the difference
        # *collapses* — so an absolute near-term backstop ("straight ahead hits
        # within ~170 ms") forces the evasion the margin can no longer see
        imminent = float(p[self.i_fwd, :2, 1].max())
        if edge < MARGIN_WM and imminent < 0.5:
            self.evade = FORWARD  # ahead is no worse than aside — keep flying
            return FORWARD
        danger = 0.25 * warn + 0.75 * crit  # crit carries the in-ring gradient
        y_after = float(state[1]) + self.vy * (EVADE_HOLD / CTRL_HZ)
        cost = (
            W_DANGER * danger
            + W_HEAD * self.heading
            + W_CENTER * torch.tensor(np.abs(y_after), dtype=torch.float32)
            - W_PROG * self.progress
        )
        j = min(self.i_veers, key=lambda i: float(cost[i]))
        self.evade = self.ids[j]
        self.hold = EVADE_HOLD
        return self.evade


class ReactivePolicy:
    """Danger-now trigger + privileged evasion direction (see module note)."""

    def __init__(self, enc, nhead):
        self.enc, self.nhead = enc, nhead
        self.pillars = []
        self.hold = 0
        self.evade = FORWARD

    def begin(self, pillars) -> None:
        self.pillars = [np.array(q) for q in pillars]
        self.hold, self.evade = 0, FORWARD

    def decide(self, frame: np.ndarray, state: np.ndarray) -> int:
        # deliberately memory-free: danger-now on the current frame is the
        # honest reactive baseline, even when the checkpoint carries a GRU
        if self.hold > 0:
            self.hold -= DECIDE_EVERY
            return self.evade
        with torch.no_grad():
            p_now = float(torch.sigmoid(self.nhead(self.enc(_frame_tensor(frame)))))
        if p_now > THETA_NOW:
            q = min(self.pillars, key=lambda q: np.linalg.norm(state[0:2] - q))
            away_left = state[1] > q[1]  # privileged direction (see class note)
            self.evade = ACTION_NAMES.index("veer_left" if away_left else "veer_right")
            self.hold = EVADE_HOLD
            return self.evade
        return FORWARD


def selftest() -> None:
    from datasets.intervention_labels import HORIZONS
    from planner.action_set import A_NORM, ACTION_VECS
    from sim.scenarios import DANGER_R, RADII
    from world_model.collision_head import CollisionHeads, DangerNowHead
    from world_model.encoder import Encoder
    from world_model.predictor import MultiPredictor

    meta = {
        "action_names": ACTION_NAMES,
        "action_vecs": ACTION_VECS.tolist(),
        "a_norm": A_NORM.tolist(),
        "horizons": list(HORIZONS),
        "radii": list(RADII),
        "danger_r": DANGER_R,
    }
    pol = WMPolicy(Encoder(), MultiPredictor(), CollisionHeads(), meta)
    pol.begin(None)
    frame = np.zeros((64, 64, 3), dtype=np.uint8)
    a = pol.decide(frame, np.zeros(20))
    assert a in range(len(ACTION_NAMES)) and ACTION_NAMES[a] != "climb"
    rea = ReactivePolicy(Encoder(), DangerNowHead())
    rea.begin([(1.0, 0.0)])
    assert rea.decide(frame, np.zeros(20)) in range(len(ACTION_NAMES))
    print(f"LATENT-MPC OK: menu {len(pol.ids)}, margin {MARGIN_WM}, 12 Hz decisions")


if __name__ == "__main__":
    selftest()

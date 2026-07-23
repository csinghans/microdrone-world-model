"""The Level-3 authority layer: the pilot proposes, the envelope disposes.

Transit and indoor search fly Level-4 — the AI holds the stick end to end.
This module opens the assisted chapter: a PILOT (a human at a keyboard, or a
scripted stand-in) flies the drone while the world model watches every
command and answers the repo's one question per decision — "and if *this*
command is held?" — spent, for the first time, on someone else's intent.
Authority moves along a ladder, never a cliff:

  PILOT     the pilot's command executes; the guardian only watches.
  OVERRIDE  momentary force-intervention: the pilot's command is about to
            hit within ~170 ms (or breached the geofence) — the guardian
            substitutes the safest menu action for ~0.5 s, then hands back.
  AUTO      the autopilot flies. Entered instantly when the pilot asks
            (toggle — handing the stick TO the AI is always granted), or by
            ESCALATION when danger persists (3-of-5 recent decisions — the
            dispatch Hysteresis vote); left only through a GATED HANDBACK:
            the pilot asks AND the last 12 decisions were clear.

Trigger philosophy follows the measured house idiom (planner/latent_mpc):
the ABSOLUTE imminent-crit backstop fires the momentary override — it is
the only trigger sharp enough to grab a human's stick on a single decision.
The RELATIVE margin (known to carry a course-dependent probability floor;
the temperature recalibration campaign failed on it) never forces an
instant substitution — it only accumulates escalation evidence.
docs/safety.md's rule that the imminent backstop "cannot be overridden by
the policy" extends here to the pilot: a handback request during danger is
latched, not granted — the AEB that will not release the brake mid-event.
The hardware RC kill-switch stays ABOVE this whole machine (hardware
column); in sim, the demo's kill key flies the emergency-land choreography.

Run:
  python -m planner.authority   # env-free selftest
"""

from collections import Counter, deque

import numpy as np
import torch

from planner.action_set import HOVER
from planner.latent_mpc import (
    DECIDE_EVERY,
    EVADE_HOLD,
    MARGIN_WM,
    W_HORIZON,
    _frame_tensor,
)
from planner.safety_filter import FENCE_Y, IMMINENT_P

PILOT, OVERRIDE, AUTO = "pilot", "override", "auto"
OVERRIDE_HOLD = EVADE_HOLD // DECIDE_EVERY  # 6 decisions ~0.5 s — the MPC's commit
ESCALATE_WINDOW, ESCALATE_NEED = 5, 3  # the dispatch Hysteresis vote, reused
HANDBACK_CLEAR = 12  # consecutive clear decisions (~1 s) before a handback
REFRACTORY = 12  # decisions after a handback before escalation may re-fire
MOVING = ("forward", "veer_left", "veer_right")  # the relative-edge comparison set


class AuthorityMachine:
    """The pure authority ladder — no torch, no env, selftested exhaustively.

    `step()` is called once per 12 Hz decision with three booleans and
    returns (authority, event): who flies THIS decision, and the transition
    event (None in steady state). `escalate=False` disables the
    sustained-danger takeover (the veto-only arm campaigns measure against).
    Safety is never refractory — only the authority transfer is."""

    def __init__(
        self,
        window: int = ESCALATE_WINDOW,
        need: int = ESCALATE_NEED,
        hold: int = OVERRIDE_HOLD,
        clear: int = HANDBACK_CLEAR,
        refractory: int = REFRACTORY,
        escalate: bool = True,
    ):
        self.window, self.need = int(window), int(need)
        self.hold, self.clear = int(hold), int(clear)
        self.refractory, self.escalate = int(refractory), bool(escalate)
        self.reset()

    def reset(self) -> None:
        self.authority = PILOT
        self.danger_win: deque = deque(maxlen=self.window)
        self.clear_run = 0
        self.hold_left = 0
        self.refr_left = 0
        self.pending = False  # latched handback request

    def _escalation_due(self) -> bool:
        return (
            self.escalate and self.refr_left == 0 and sum(self.danger_win) >= self.need
        )

    def step(self, danger: bool, hard: bool, toggle: bool):
        danger = bool(danger) or bool(hard)
        self.danger_win.append(danger)
        self.clear_run = 0 if danger else self.clear_run + 1
        if self.refr_left > 0:
            self.refr_left -= 1

        if self.authority == AUTO:
            event = None
            if toggle:
                if self.pending:
                    self.pending = False
                    event = "handback_cancel"
                else:
                    self.pending = True
                    event = "handback_deferred"
            if self.pending and self.clear_run >= self.clear:
                self.authority = PILOT
                self.pending = False
                self.refr_left = self.refractory
                self.danger_win.clear()  # stale danger must not re-escalate
                event = "handback"
            return self.authority, event

        # PILOT / OVERRIDE
        if toggle:  # handing the stick TO the AI: always granted, this decision
            self.authority, self.hold_left = AUTO, 0
            return AUTO, "toggle_auto"
        if self._escalation_due():  # persistence converts chatter into one AUTO
            self.authority, self.hold_left = AUTO, 0
            return AUTO, "escalate"
        if self.authority == OVERRIDE:
            self.hold_left -= 1
            if self.hold_left > 0:  # committed maneuver flies through
                return OVERRIDE, None
            if hard:  # still hot at expiry: recompute + re-arm
                self.hold_left = self.hold
                return OVERRIDE, "override_fire"
            self.authority = PILOT
            return PILOT, "override_clear"
        if hard:  # PILOT -> momentary force-intervention
            self.authority, self.hold_left = OVERRIDE, self.hold
            return OVERRIDE, "override_fire"
        return PILOT, None


class Guardian:
    """Wraps (pilot, autopilot) behind the standard policy contract, so one
    assisted flight is just `run_scenario_episode(env, Guardian(...), ...)`.

    Each decision: encode the frame ONCE (Rule 3), one predictor+heads sweep
    over the 5-menu -> p (n_menu, horizons, 2 rings); score the pilot's
    command (imminent = its own near-term crit; edge = its urgency-weighted
    warn vs the best other MOVING command — slow/hover are excluded from the
    comparison, braking always "looks safer"); step the machine; execute per
    authority. The autopilot's decide() runs EVERY tick so its state never
    cold-starts at a takeover (the dispatch warm-stack law). `scorer`, if
    given, replaces the WM sweep (callable(frame, state) -> (n_menu, H, 2));
    that is the CI seam and the privileged-oracle-ceiling seam in one."""

    def __init__(
        self,
        pilot,
        autopilot,
        enc,
        pred,
        cheads,
        meta,
        speed: float = 1.0,
        machine: AuthorityMachine = None,
        scorer=None,
        margin: float = None,
        imm_thr: float = None,
        trace=None,
    ):
        assert scorer is not None or None not in (enc, pred, cheads)
        self.pilot, self.autopilot = pilot, autopilot
        self.enc, self.pred, self.cheads = enc, pred, cheads
        self.machine = machine if machine is not None else AuthorityMachine()
        self.scorer = scorer
        self.margin = MARGIN_WM if margin is None else float(margin)
        self.imm_thr = IMMINENT_P if imm_thr is None else float(imm_thr)
        self.trace = trace
        names = list(meta["action_names"])
        vecs = float(speed) * np.array(meta["action_vecs"], dtype=np.float32)
        self.ids = [i for i, n in enumerate(names) if n != "climb"]
        self.j_moving = [self.ids.index(names.index(n)) for n in MOVING]
        sub = vecs[self.ids]
        self.cands = torch.tensor(sub / np.array(meta["a_norm"], dtype=np.float32))
        self.h_w = np.array(list(W_HORIZON)[: len(meta["horizons"])], dtype=np.float32)
        self.pillars: list = []  # runner-refreshed; forwarded to whoever needs it
        self.log: list = []
        self._sub, self.h, self.d = HOVER, None, 0

    def begin(self, pillars) -> None:
        self.pilot.begin(pillars)
        self.autopilot.begin(pillars)
        self.machine.reset()
        self.log = []
        self._sub, self.h, self.d = HOVER, None, 0

    def _score(self, frame, state) -> np.ndarray:
        if self.scorer is not None:
            return np.asarray(self.scorer(frame, state), dtype=np.float32)
        with torch.no_grad():
            z = self.enc(_frame_tensor(frame))
            tem = getattr(self.enc, "temporal", None)
            cond = z
            if tem is not None:  # v3 checkpoints: memory steps every decision
                cond, self.h = tem.step(z, self.h)
            zh = self.pred(
                cond.expand(len(self.cands), -1),
                self.cands,
                base=z.expand(len(self.cands), -1),
            )
            return torch.sigmoid(self.cheads(zh)).numpy()

    def _substitute(self, p: np.ndarray, j: int, fence: bool) -> int:
        if fence:
            return HOVER  # the deployed geofence answer (planner/safety_filter)
        crit_near = p[:, :2, 1].max(axis=1)  # brake or dodge — the heads decide
        ks = [k for k in range(len(self.ids)) if k != j]
        return self.ids[min(ks, key=lambda k: float(crit_near[k]))]

    def decide(self, frame: np.ndarray, state: np.ndarray) -> int:
        for pol in (self.pilot, self.autopilot, self.scorer):
            if pol is not None and hasattr(pol, "pillars"):
                pol.pillars = self.pillars  # forward the privileged refresh
        p = self._score(frame, state)
        a_pilot = int(self.pilot.decide(frame, state))
        a_auto = int(self.autopilot.decide(frame, state))  # warm every tick
        ev = self.pilot.events() if hasattr(self.pilot, "events") else {}
        try:
            j = self.ids.index(a_pilot)
        except ValueError:
            raise SystemExit(f"pilot left the menu: action {a_pilot}") from None
        fence = abs(float(state[1])) > FENCE_Y
        imminent = float(p[j, :2, 1].max())
        hard = fence or imminent > self.imm_thr
        edge = 0.0
        if j in self.j_moving:  # relative danger is defined between movers
            warn_u = p[:, :, 0] @ self.h_w
            others = [k for k in self.j_moving if k != j]
            edge = float(warn_u[j] - min(warn_u[k] for k in others))
        danger = hard or edge >= self.margin
        authority, event = self.machine.step(
            danger, hard, bool(ev.get("toggle", False))
        )
        if event == "override_fire":
            self._sub = self._substitute(p, j, fence)
        a_exec = {PILOT: a_pilot, OVERRIDE: self._sub, AUTO: a_auto}[authority]
        if self.trace is not None:
            self.trace.append((edge, imminent))
        self.log.append(
            {
                "d": self.d,
                "authority": authority,
                "event": event,
                "pilot": a_pilot,
                "auto": a_auto,
                "exec": int(a_exec),
                "edge": round(edge, 3),
                "imminent": round(imminent, 3),
                "fence": fence,
                "danger": danger,
                "hard": hard,
            }
        )
        self.d += 1
        return int(a_exec)


def summarize_log(log: list) -> dict:
    """Per-episode authority scorecard from the Guardian's decision log."""
    n = len(log)
    events = Counter(r["event"] for r in log if r["event"])
    n_over = sum(1 for r in log if r["exec"] != r["pilot"])
    first = next((r["d"] for r in log if r["exec"] != r["pilot"]), -1)
    lat, pend = [], None
    for r in log:
        if r["event"] == "handback_deferred":
            pend = r["d"]
        elif r["event"] == "handback_cancel":
            pend = None
        elif r["event"] == "handback":
            lat.append(r["d"] - (pend if pend is not None else r["d"]))
            pend = None
    return {
        "n_decisions": n,
        "n_overridden": n_over,
        "n_override_fires": events.get("override_fire", 0),
        "n_escalations": events.get("escalate", 0),
        "n_toggles": events.get("toggle_auto", 0),
        "n_handbacks": events.get("handback", 0),
        "handback_latencies": lat,
        "frac_auto": round(
            sum(1 for r in log if r["authority"] == AUTO) / max(n, 1), 4
        ),
        "first_override_d": first,
    }


# --- selftest ----------------------------------------------------------------
class _Insist:
    """Selftest pilot: insists on one action; optional scripted toggles."""

    def __init__(self, action: int, toggles=()):
        self.action, self.toggles, self.d = int(action), set(toggles), 0
        self.pillars: list = []

    def begin(self, pillars) -> None:
        self.d = 0

    def decide(self, frame, state) -> int:
        self.d += 1
        return self.action

    def events(self) -> dict:
        return {"toggle": (self.d - 1) in self.toggles}


def _machine_asserts() -> None:
    m = AuthorityMachine()
    for _ in range(20):  # steady PILOT on all-clear
        assert m.step(False, False, False) == (PILOT, None)
    # one hard decision -> OVERRIDE for exactly OVERRIDE_HOLD decisions
    a, e = m.step(True, True, False)
    assert (a, e) == (OVERRIDE, "override_fire")
    for _ in range(OVERRIDE_HOLD - 1):
        a, e = m.step(False, False, False)
        assert (a, e) == (OVERRIDE, None)
    assert m.step(False, False, False) == (PILOT, "override_clear")
    # persistent hard danger escalates (chatter converts to one clean AUTO)
    m = AuthorityMachine()
    seen = []
    for _ in range(ESCALATE_WINDOW):
        seen.append(m.step(True, True, False))
    assert any(e == "escalate" for _, e in seen), seen
    assert m.authority == AUTO
    # handback during danger is latched, granted only after HANDBACK_CLEAR
    a, e = m.step(True, False, True)
    assert (a, e) == (AUTO, "handback_deferred")
    for i in range(HANDBACK_CLEAR):
        a, e = m.step(False, False, False)
        assert a == AUTO or i == HANDBACK_CLEAR - 1, (i, a)
    assert (a, e) == (PILOT, "handback")
    # refractory: danger burst right after a handback must not re-escalate...
    for _ in range(ESCALATE_NEED):
        a, e = m.step(True, False, False)
        assert a == PILOT and e is None, (a, e)
    # ...but hard STILL fires the momentary override (safety is not refractory)
    a, e = m.step(True, True, False)
    assert (a, e) == (OVERRIDE, "override_fire")
    # toggle to AUTO is granted on the SAME decision, from any pilot state
    m = AuthorityMachine()
    assert m.step(False, False, True) == (AUTO, "toggle_auto")
    # a second toggle mid-danger latches, a third cancels the latch
    m.step(True, False, False)
    assert m.step(True, False, True)[1] == "handback_deferred"
    assert m.step(True, False, True)[1] == "handback_cancel"
    # escalate=False: veto works, sustained danger never takes the stick
    m = AuthorityMachine(escalate=False)
    for _ in range(3 * ESCALATE_WINDOW):
        a, _e = m.step(True, True, False)
        assert a == OVERRIDE
    # clean immediate handback: toggle while already clear -> latency 0
    m = AuthorityMachine()
    m.step(False, False, True)
    for _ in range(HANDBACK_CLEAR):
        m.step(False, False, False)
    assert m.step(False, False, True) == (PILOT, "handback")


def _guardian_asserts() -> None:
    from datasets.intervention_labels import HORIZONS
    from planner.action_set import (
        A_NORM,
        ACTION_NAMES,
        ACTION_VECS,
        FORWARD,
    )

    meta = {
        "action_names": ACTION_NAMES,
        "action_vecs": ACTION_VECS.tolist(),
        "a_norm": A_NORM.tolist(),
        "horizons": list(HORIZONS),
    }
    n_menu, n_h = len(ACTION_NAMES) - 1, len(HORIZONS)
    veer_l = ACTION_NAMES.index("veer_left")

    class _Sched:
        """Scripted scorer: a p tensor per decision index, zeros elsewhere."""

        def __init__(self, p_by_d=()):
            self.p_by_d, self.d = dict(p_by_d), 0

        def __call__(self, frame, state):
            p = self.p_by_d.get(self.d, np.zeros((n_menu, n_h, 2), np.float32))
            self.d += 1
            return p

    frame, state = np.zeros((64, 64, 3), dtype=np.uint8), np.zeros(20)

    # clear scene: the pilot's command passes through untouched
    auto = _Insist(HOVER)
    g = Guardian(_Insist(FORWARD), auto, None, None, None, meta, scorer=_Sched())
    g.begin([])
    for _ in range(8):
        assert g.decide(frame, state) == FORWARD
    assert summarize_log(g.log)["n_overridden"] == 0
    assert auto.d == 8, "autopilot must stay warm every tick (dispatch law)"

    # imminent on the pilot's chosen VEER (not forward) triggers substitution
    hot = np.zeros((n_menu, n_h, 2))
    j_veer = g.ids.index(veer_l)
    hot[j_veer, :2, 1] = 0.9  # the veer is about to hit
    hot[g.ids.index(FORWARD), :2, 1] = 0.2
    g = Guardian(
        _Insist(veer_l),
        _Insist(HOVER),
        None,
        None,
        None,
        meta,
        scorer=_Sched({0: hot, 1: hot}),
        machine=AuthorityMachine(escalate=False),
    )
    g.begin([])
    a = g.decide(frame, state)
    assert a != veer_l and g.log[0]["event"] == "override_fire"
    crit_near = hot[:, :2, 1].max(axis=1)
    assert crit_near[g.ids.index(a)] == crit_near.min(), "substitute the safest"

    # geofence: |y| beyond the fence forces hover regardless of the probs
    g = Guardian(
        _Insist(veer_l),
        _Insist(FORWARD),
        None,
        None,
        None,
        meta,
        scorer=_Sched(),
    )
    g.begin([])
    state_out = np.zeros(20)
    state_out[1] = FENCE_Y + 0.5
    assert g.decide(frame, state_out) == HOVER

    # escalation on sustained soft danger -> AUTO executes the autopilot
    soft = np.zeros((n_menu, n_h, 2))
    soft[g.ids.index(FORWARD), :, 0] = 0.95  # forward warns, veers clear
    g = Guardian(
        _Insist(FORWARD),
        _Insist(HOVER),
        None,
        None,
        None,
        meta,
        scorer=_Sched({d: soft for d in range(12)}),
    )
    g.begin([])
    acts = [g.decide(frame, state) for _ in range(8)]
    s = summarize_log(g.log)
    assert s["n_escalations"] == 1 and HOVER in acts, (s, acts)
    assert all(
        r["event"] != "override_fire" for r in g.log
    ), "soft danger must never fire a momentary override"


def selftest() -> None:
    _machine_asserts()
    _guardian_asserts()
    print(
        f"AUTHORITY OK: ladder pilot->override->auto, hold {OVERRIDE_HOLD} "
        f"decisions, escalate {ESCALATE_NEED}-of-{ESCALATE_WINDOW}, handback "
        f"after {HANDBACK_CLEAR} clear, toggle<=1 decision, "
        "soft-danger never grabs the stick"
    )


if __name__ == "__main__":
    selftest()

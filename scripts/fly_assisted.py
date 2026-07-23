"""Interactive assisted flight — YOU are the pilot, the WM is the guardian.

Demo-only: the measured campaign (eval/eval_assist_gate) imports nothing
from here; interactivity is quarantined in this script. The stack is the
real deployed one — unified WM guardian + WMPolicy takeover on the same
latent (`planner.authority`, the `assisted` flight mode's brain).

Keys (click the pybullet window first — macOS delivers keys only to the
focused window):

  W / UP     forward          A / LEFT   veer left
  S / DOWN   slow             D / RIGHT  veer right
  (nothing)  hover            SPACE      hover
  T          toggle PILOT <-> AUTO (handing TO the AI is instant; asking it
             back mid-danger is latched — the guardian grants it clear)
  K          kill: emergency land (capped rate), then exit. Models the
             hardware RC kill row — ABOVE the authority machine.

The HUD over the drone shows who is flying and what the guardian sees:
green PILOT, red OVERRIDE, blue AUTO, with the live (edge, imminent)
trigger values. Held keys read at 48 Hz, latched at 12 Hz decisions; the
sim paces to wall clock so a human can actually fly it.

Run:
  python -m scripts.fly_assisted --gui                    # fly it yourself
  python -m scripts.fly_assisted --script "6:toggle,30:toggle" --gif out.gif
  python -m scripts.fly_assisted --selftest
"""

import argparse
import sys
import time

import numpy as np

HUD_RGB = {
    "pilot": (0.1, 0.8, 0.1),
    "override": (1.0, 0.2, 0.0),
    "auto": (0.2, 0.4, 1.0),
}
LAND_Z = 0.08  # touchdown height for the kill choreography
KILL_V = (-0.35, 0.0)  # capped descent (vz, anything) — mirrors emergency_land


def _keymap():
    import pybullet as p

    from planner.action_set import ACTION_NAMES

    a = {n: ACTION_NAMES.index(n) for n in ACTION_NAMES}
    return {
        ord("w"): a["forward"],
        p.B3G_UP_ARROW: a["forward"],
        ord("s"): a["slow"],
        p.B3G_DOWN_ARROW: a["slow"],
        ord("a"): a["veer_left"],
        p.B3G_LEFT_ARROW: a["veer_left"],
        ord("d"): a["veer_right"],
        p.B3G_RIGHT_ARROW: a["veer_right"],
        ord(" "): a["hover"],
    }


class KeyboardPilot:
    """Polls the pybullet keyboard at 48 Hz (`poll`), speaks the standard
    policy contract at 12 Hz. No key held -> hover (re-centering stick)."""

    def __init__(self, client: int):
        self.client = client
        self.keymap = _keymap()
        from planner.action_set import HOVER

        self._held = HOVER
        self._toggle, self._kill = False, False

    def poll(self) -> None:
        import pybullet as p

        keys = p.getKeyboardEvents(physicsClientId=self.client)
        held = [a for k, a in self.keymap.items() if keys.get(k, 0) & p.KEY_IS_DOWN]
        from planner.action_set import HOVER

        self._held = held[0] if held else HOVER
        if keys.get(ord("t"), 0) & p.KEY_WAS_TRIGGERED:
            self._toggle = True
        if keys.get(ord("k"), 0) & p.KEY_WAS_TRIGGERED:
            self._kill = True

    def begin(self, pillars) -> None:
        del pillars

    def decide(self, frame, state) -> int:
        del frame, state
        return self._held

    def events(self) -> dict:
        ev = {"toggle": self._toggle, "kill": self._kill}
        self._toggle = False
        return ev


class ScriptPilot:
    """Replay pilot for deterministic demos/GIFs: a SyntheticPilot flying
    the course with toggle/kill events at scripted decision indices."""

    def __init__(self, schedule: dict, persona: str = "average", seed: int = 800000):
        from assist.pilot import SyntheticPilot

        self.inner = SyntheticPilot(persona, seed)
        self.schedule = dict(schedule)
        self.d = -1
        self._kill = False

    @property
    def pillars(self):
        return self.inner.pillars

    @pillars.setter
    def pillars(self, v):
        self.inner.pillars = v

    def begin(self, pillars) -> None:
        self.inner.begin(pillars)
        self.d = -1

    def decide(self, frame, state) -> int:
        self.d += 1
        return self.inner.decide(frame, state)

    def events(self) -> dict:
        ev = self.schedule.get(self.d, "")  # fires on ITS decision index
        self._kill = self._kill or ev == "kill"
        return {"toggle": ev == "toggle", "kill": self._kill}


def parse_script(spec: str) -> dict:
    """'6:toggle,30:toggle,50:kill' -> {6: 'toggle', 30: 'toggle', 50: 'kill'}."""
    out = {}
    for part in filter(None, (spec or "").split(",")):
        d, _, ev = part.partition(":")
        assert ev in ("toggle", "kill"), f"unknown scripted event {ev!r}"
        out[int(d)] = ev
    return out


def fly(
    world: str = "dense",
    seed: int = 800000,
    speed: float = 1.0,
    gui: bool = True,
    script: str = "",
    gif: str = None,
    tmax: int = 1440,
    stack=None,
) -> dict:
    """One interactive (or scripted) assisted flight; returns the scorecard.
    `stack` = (enc, pred, cheads, meta) override — the selftest injects a
    `load_or_train` stand-in so this stays CI-safe; None rides the deployed
    unified WM."""
    import pybullet as p

    from planner.action_set import ACTION_VECS
    from planner.authority import Guardian, summarize_log
    from planner.latent_mpc import DECIDE_EVERY, WMPolicy
    from sim.envs import VelCommander, grab_frame, make_ctrl, make_env
    from sim.scenario_registry import get as get_scenario
    from sim.scenarios import COLLISION_R, GOAL_X, nearest_planar

    env = make_env(gui=gui)
    rng = np.random.default_rng(seed)
    obs, _ = env.reset(seed=int(seed))
    cmd = VelCommander(make_ctrl(), env.CTRL_TIMESTEP)
    cmd.reset(obs[0][0:3])
    scenario = get_scenario(world).spawn(env, rng, speed=speed)
    if stack is None:
        from planner.flight_mode import UNIFIED_WM, load_wm_cached

        enc, pred, cheads, _n, meta = load_wm_cached(UNIFIED_WM)
    else:
        enc, pred, cheads, meta = stack
    pilot = (
        ScriptPilot(parse_script(script), seed=seed)
        if script
        else KeyboardPilot(env.CLIENT)
    )
    guardian = Guardian(
        pilot,
        WMPolicy(enc, pred, cheads, meta, speed=speed),
        enc,
        pred,
        cheads,
        meta,
        speed=speed,
    )
    guardian.begin(scenario.positions())
    vecs = float(speed) * ACTION_VECS
    if not script:
        print(
            "[fly-assisted] click the pybullet window, then fly: WASD/arrows,"
            " T toggle AUTO, K kill"
        )

    state, a_id, txt_id, frames = obs[0], None, -1, []
    min_clear, killed, start = 9.0, False, time.time()
    for t in range(tmax):
        if hasattr(pilot, "poll"):
            pilot.poll()
        if t % DECIDE_EVERY == 0:
            guardian.pillars = [np.array(q) for q in scenario.positions()]
            a_id = guardian.decide(grab_frame(env), state)
            rec = guardian.log[-1]
            if getattr(pilot, "_kill", False):  # sticky; set by K / a script
                killed = True
                break
            if gui:
                hud = (
                    f"{rec['authority'].upper()}  edge={rec['edge']:+.2f} "
                    f"imm={rec['imminent']:.2f}"
                )
                txt_id = p.addUserDebugText(
                    hud,
                    [float(state[0]), float(state[1]), float(state[2]) + 0.35],
                    textColorRGB=HUD_RGB[rec["authority"]],
                    textSize=1.2,
                    replaceItemUniqueId=txt_id,
                    physicsClientId=env.CLIENT,
                )
            sys.stdout.write(
                f"\r[{rec['authority']:>8s}] d={rec['d']:4d} "
                f"edge={rec['edge']:+.2f} imm={rec['imminent']:.2f} "
                f"x={state[0]:+.2f} y={state[1]:+.2f}   "
            )
            sys.stdout.flush()
            if gif:
                from eval.eval_integration import _god_frame

                frames.append(_god_frame(env, GOAL_X))
        obs, *_ = env.step(cmd.rpm(state, vecs[a_id]).reshape(1, 4))
        state = obs[0]
        scenario.step()
        min_clear = min(min_clear, nearest_planar(state[0:2], scenario.positions()))
        if gui:
            _wall_pace(t, start, env.CTRL_TIMESTEP)
        if state[0] >= GOAL_X:
            break
    if killed:  # the kill choreography: capped-rate descent, no AI in the loop
        print("\n[fly-assisted] KILL — emergency land")
        down = np.array([0.0, 0.0, KILL_V[0], 0.0])
        for _ in range(600):
            if float(state[2]) <= LAND_Z:
                break
            obs, *_ = env.step(cmd.rpm(state, down).reshape(1, 4))
            state = obs[0]
            if gui:
                time.sleep(env.CTRL_TIMESTEP)
    if gif and frames:
        from eval.eval_integration import _gif

        _gif(frames, gif, fps=12)
        print(f"\n[fly-assisted] wrote {gif} ({len(frames)} frames)")
    env.close()
    au = summarize_log(guardian.log)
    out = {
        "reached": bool(state[0] >= GOAL_X),
        "crashed": bool(min_clear < COLLISION_R),
        "killed": killed,
        "min_clear": round(float(min_clear), 3),
        "authority": au,
    }
    print(
        f"\n[fly-assisted] reached={out['reached']} crashed={out['crashed']} "
        f"killed={killed} min_clear={out['min_clear']}m | overrides="
        f"{au['n_overridden']}/{au['n_decisions']} escalations="
        f"{au['n_escalations']} toggles={au['n_toggles']} "
        f"handbacks={au['n_handbacks']} frac_auto={au['frac_auto']}"
    )
    return out


def _wall_pace(t: int, start: float, dt: float) -> None:
    """Pace the loop to wall clock so a human can fly (BaseAviary.step never
    sleeps). The sync helper from gym_pybullet_drones, inlined to stay
    dependency-light."""
    elapsed = time.time() - start
    target = t * dt
    if target > elapsed:
        time.sleep(target - elapsed)


def selftest() -> None:
    # keymap + script parsing are pure; then one short HEADLESS scripted
    # flight proves the loop end to end (no keyboard, no GUI, no GIF)
    assert parse_script("6:toggle,30:kill") == {6: "toggle", 30: "kill"}
    assert parse_script("") == {}
    try:
        parse_script("3:bogus")
        raise AssertionError("bogus scripted event must be refused")
    except AssertionError as e:
        if "bogus" not in str(e):
            raise
    sp = ScriptPilot({2: "toggle"}, seed=7)
    sp.begin([])
    sp.decide(None, np.zeros(20))  # d=0
    assert sp.events() == {"toggle": False, "kill": False}
    sp.decide(None, np.zeros(20))  # d=1
    assert sp.events()["toggle"] is False
    sp.decide(None, np.zeros(20))  # d=2: the scheduled decision
    assert sp.events()["toggle"] is True
    from eval.eval_closed_loop import load_or_train

    enc, pred, cheads, _n, meta = load_or_train(device="cpu")
    r = fly(
        world="classic",
        seed=800000,
        gui=False,
        script="3:toggle",
        tmax=192,
        stack=(enc, pred, cheads, meta),
    )
    assert r["authority"]["n_toggles"] == 1, r
    assert r["authority"]["frac_auto"] > 0, "the toggle must hand over"
    print(
        "FLY-ASSISTED OK: keymap+script parsing, scripted headless flight "
        f"toggled to AUTO (frac_auto={r['authority']['frac_auto']})"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", default="dense")
    ap.add_argument("--seed", type=int, default=800000)
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--gui", action="store_true")
    ap.add_argument("--script", default="", help="e.g. '6:toggle,30:kill'")
    ap.add_argument("--gif", default=None, help="write a god-view GIF here")
    ap.add_argument("--tmax", type=int, default=1440, help="48 Hz steps (~30 s)")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    if not args.gui and not args.script:
        raise SystemExit("--gui to fly it yourself, or --script to replay")
    fly(
        world=args.world,
        seed=args.seed,
        speed=args.speed,
        gui=args.gui,
        script=args.script,
        gif=args.gif,
        tmax=args.tmax,
    )


if __name__ == "__main__":
    sys.exit(main())

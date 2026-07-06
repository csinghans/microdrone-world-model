"""The integration suite — random composite courses, a deployment gate,
and the flight video of record.

Flight TDD's integration layer (`docs/TDD-FLIGHT.md`): n randomly
composed 3-stage courses (`sim/composite.py`), one policy entry flying
each end to end. The verdict is composite-level (reach the final goal,
never crash) with stage-resolution diagnostics; the pre-registered
**deployment gate** is success >= 0.70 at n = 100 — the standing
precondition for any real-hardware deployment (the hardware itself
stays parked until separately unfrozen).

`--video` re-flies one PASSING course with recording on and writes the
repo's videos of record to docs/media/: the drone's own 64x64 camera
(upscaled) and a simulator god view (top-down getCameraImage on the
same DIRECT client, ER_TINY_RENDERER), both as GIFs via Pillow — zero
new dependencies — plus a provenance stamp json. "The latest passing
integration flight" is regenerated on every passing suite run.

Contenders plug in as factories; `PerStageExperts` is the PRIVILEGED
ceiling probe (it reads the course composition and flies each stage
with its solo-holder artifact — pricing course flyability with the
identification problem removed; honestly labelled, never a contender).

Run:
  python -m eval.eval_integration --suite 30 --contender ceiling
  python -m eval.eval_integration --suite 100 --zip <policy.zip>
  python -m eval.eval_integration --video-seed 110007 --contender ceiling
  python -m eval.eval_integration --selftest
"""

import argparse
import json
import os
import sys

import numpy as np

from sim.composite import (
    STAGE_LEN,
    StageLocal,
    course_for_seed,
    integration_metrics,
    integration_success,
    register_course,
)

THRESHOLD = 0.70  # the deployment gate (pre-registered; n=100)
SEED0 = 110000
K_STAGES = 3
MEDIA = "docs/media"

# the solo holder for each stage type (gated records in each journal)
STAGE_EXPERT = {
    "gap": "experiments/gap_flight/artifacts/ppo_gap_flight_KD1.zip",
    "moving_gap": "experiments/moving_gap_v2/artifacts/ppo_moving_gap_v2_K3.zip",
    "door": "experiments/moving_gap_v2/artifacts/ppo_moving_gap_v2_K3.zip",
    "opening_door": "experiments/odoor_v2/artifacts_local/ppo_odoor_v3_FT.zip",
    "slalom3_fixed": "experiments/chain_distill/artifacts/ppo_chain_distill_BC.zip",
}


def _expert(zip_path: str, speed: float):
    from planner.dispatch import _model, _stack
    from planner.learned_policy import LearnedPolicy

    enc, pred, cheads, meta = _stack()
    return LearnedPolicy(_model(zip_path), enc, pred, cheads, meta, speed=speed)


# the flight-plan hybrid (deployment-legal per the 2026-07-07 ruling:
# course composition = legitimate mission information, like waypoints):
# the course-FT generalist flies everything except slalom stages, which
# the chain-distill clone flies
HYBRID = {
    "gap": "experiments/integration_ft/artifacts_local/ppo_integration_ft_v3.zip",
    "moving_gap": "experiments/integration_ft/artifacts_local/ppo_integration_ft_v3.zip",
    "door": "experiments/integration_ft/artifacts_local/ppo_integration_ft_v3.zip",
    "opening_door": "experiments/integration_ft/artifacts_local/ppo_integration_ft_v3.zip",
    "slalom3_fixed": (
        "experiments/integration_ft/artifacts_local/ppo_slalom_hot_BC.zip"
    ),
}


class PerStageExperts:
    """Per-stage experts keyed on the course composition. As the CEILING
    probe (solo-holder map) it is a privileged instrument; as the HYBRID
    (flight-plan map) it is a deployment-legal contender per the ruling
    that mission plans know their waypoints."""

    SETTLE_K = 5  # entry brake: hover decisions at a slalom-stage entry
    # (flight-plan-legal: the plan knows the boundary; braking recreates
    # the specialist's native near-still start and kills the seam)

    def __init__(
        self, names, speed: float = 1.0, stage_len: float = STAGE_LEN, experts=None
    ):
        table = experts or STAGE_EXPERT
        self.names = tuple(names)
        self.pilots = [_expert(table[n], speed) for n in names]
        self._settle = 0
        self.L = float(stage_len)
        self._stage = 0

    def begin(self, pillars) -> None:
        self._stage = 0
        self._settle = 0
        self.pilots[0].begin(pillars)

    def decide(self, frame, state) -> int:
        from planner.action_set import ACTION_NAMES

        k = int(np.clip(float(state[0]) // self.L, 0, len(self.pilots) - 1))
        if k != self._stage:
            self._stage = k
            self.pilots[k].begin([])
            # entry brake removed: measured exactly null on the slalom
            # conditional (v3, 0.645 == v2) — the failure is per-decision
            # fidelity compounding over the chain, not the entry state
        s = np.array(state, dtype=float, copy=True)
        s[0] -= k * self.L
        a = self.pilots[k].decide(frame, s)  # keep the stack warm
        if self._settle > 0:
            self._settle -= 1
            return ACTION_NAMES.index("hover")
        return a


class Cruise:
    """FORWARD-only stand-in for artifact-less selftests."""

    def begin(self, pillars) -> None:
        pass

    def decide(self, frame, state) -> int:
        return 0


def _god_frame(env, span: float, res: int = 400) -> np.ndarray:
    import pybullet as p

    vm = p.computeViewMatrix(
        cameraEyePosition=[span / 2.0, 0.0, span * 1.05],
        cameraTargetPosition=[span / 2.0, 0.0, 0.5],
        cameraUpVector=[1, 0, 0],
    )
    pm = p.computeProjectionMatrixFOV(fov=55.0, aspect=1.0, nearVal=0.1, farVal=60.0)
    _w, _h, rgb, _d, _s = p.getCameraImage(
        res,
        res,
        viewMatrix=vm,
        projectionMatrix=pm,
        renderer=p.ER_TINY_RENDERER,
        physicsClientId=env.CLIENT,
    )
    return np.reshape(rgb, (res, res, 4))[:, :, :3].astype(np.uint8)


def run_composite_episode(env, policy, seed, world, k=K_STAGES, speed=1.0, record=None):
    """The episode runner, composite-scaled (goal k*L, tmax k*360), with
    min-clear step tracking (crash localization) and optional recording.
    Mirrors eval/episode.py's loop shape."""
    from planner.action_set import ACTION_VECS
    from planner.latent_mpc import DECIDE_EVERY
    from sim.envs import VelCommander, grab_frame, make_ctrl
    from sim.scenario_registry import get as get_scenario
    from sim.scenarios import TMAX, nearest_planar

    goal_x, tmax = k * STAGE_LEN, k * TMAX
    obs0, _ = env.reset(seed=seed)
    cmd = VelCommander(make_ctrl(), env.CTRL_TIMESTEP)
    state = obs0[0]
    cmd.reset(state[0:3])
    scenario = get_scenario(world).spawn(env, np.random.default_rng(seed), speed=speed)
    pillars0 = scenario.positions()
    policy.begin(pillars0)
    a = 0
    path, min_clear, min_step = [state[0:3].copy()], 9.0, 0
    for t in range(tmax):
        if t % DECIDE_EVERY == 0:
            frame = grab_frame(env)
            if hasattr(policy, "pillars"):
                policy.pillars = [np.array(q) for q in scenario.positions()]
            a = policy.decide(frame, state)
            if record is not None:
                record["fpv"].append(frame.copy())
                record["god"].append(_god_frame(env, goal_x))
        rpm = cmd.rpm(state, float(speed) * ACTION_VECS[a])
        obs, _r, _te, _tr, _i = env.step(rpm.reshape(1, 4))
        state = obs[0]
        scenario.step()
        d = nearest_planar(state[0:2], scenario.positions())
        if d < min_clear:
            min_clear, min_step = d, len(path)
        path.append(state[0:3].copy())
        if state[0] >= goal_x:
            break
    from sim.scenarios import COLLISION_R

    return {
        "path": np.array(path),
        "scenario_meta": dict(getattr(scenario, "meta", {}) or {}),
        "min_clear": min_clear,
        "min_clear_step": min_step,
        "crashed": min_clear < COLLISION_R,
        "steps": len(path) - 1,
        "reached": bool(state[0] >= goal_x),
    }


def _gif(frames, out: str, scale: int = 1, fps: int = 12) -> None:
    from PIL import Image

    if scale > 1:
        frames = [
            np.kron(f, np.ones((scale, scale, 1), dtype=np.uint8)) for f in frames
        ]
    imgs = [Image.fromarray(f) for f in frames]
    imgs[0].save(
        out,
        save_all=True,
        append_images=imgs[1:],
        duration=int(1000 / fps),
        loop=0,
    )


def record_video(
    make_policy, seed: int, out_dir: str = MEDIA, extra: dict | None = None
):
    """Re-fly one course with recording; write the videos of record."""
    from sim.envs import make_env

    os.makedirs(out_dir, exist_ok=True)
    names = course_for_seed(seed)
    world = register_course(seed)
    env = make_env()
    rec = {"fpv": [], "god": []}
    ep = run_composite_episode(env, make_policy(names), seed, world, record=rec)
    env.close()
    _gif(rec["fpv"], os.path.join(out_dir, "integration_fpv.gif"), scale=4)
    _gif(rec["god"], os.path.join(out_dir, "integration_god.gif"))
    stamp = {
        "seed": seed,
        "course": list(names),
        "success": bool(integration_success(ep)),
        **integration_metrics(ep),
        **(extra or {}),
    }
    with open(os.path.join(out_dir, "integration_stamp.json"), "w") as f:
        json.dump(stamp, f, indent=1)
    print(f"[video] {out_dir}/integration_{{fpv,god}}.gif  stamp={stamp}")
    return ep, stamp


def suite(make_policy, n: int, seed0: int = SEED0, out: str | None = None):
    from sim.envs import make_env

    env = make_env()
    records, wins = [], 0
    for i in range(n):
        seed = seed0 + i
        names = course_for_seed(seed)
        world = register_course(seed)
        ep = run_composite_episode(env, make_policy(names), seed, world)
        ok = integration_success(ep)
        wins += int(ok)
        records.append(
            {
                "seed": seed,
                "course": list(names),
                "success": bool(ok),
                **{k: v for k, v in integration_metrics(ep).items()},
            }
        )
        print(
            f"  [{i + 1}/{n}] seed={seed} {'PASS' if ok else 'fail'} "
            f"{records[-1].get('stages_cleared', 0):.0f}/3 {list(names)}"
        )
    env.close()
    rate = wins / n
    hist: dict = {}
    for r in records:
        if not r["success"]:
            hist[r.get("stage_break_at", -1)] = (
                hist.get(r.get("stage_break_at", -1), 0) + 1
            )
    report = {
        "n": n,
        "seed0": seed0,
        "success_rate": round(rate, 4),
        "deployment_threshold": THRESHOLD,
        "deployment_gate": "PASS" if rate >= THRESHOLD else "FAIL",
        "break_histogram": {str(k): v for k, v in sorted(hist.items())},
        "records": records,
    }
    print(
        f"[suite] success {wins}/{n} = {rate:.3f}  gate({THRESHOLD:.2f}): "
        f"{report['deployment_gate']}  breaks={report['break_histogram']}"
    )
    if out:
        with open(out, "w") as f:
            json.dump(report, f, indent=1)
        print(f"[suite] saved {out}")
    return report


def _load_all_skills() -> None:
    from skills.base import load_skill

    for s in (
        "gap-flight",
        "corridor-slalom-v2",
        "moving-gap",
        "closing-door",
        "opening-door",
    ):
        load_skill(s)


def make_factory(args):
    if args.zip:
        return lambda names: StageLocal(_expert(args.zip, 1.0), n_stages=K_STAGES)
    if args.contender == "ceiling":
        return lambda names: PerStageExperts(names, 1.0)
    if args.contender == "hybrid":
        return lambda names: PerStageExperts(names, 1.0, experts=HYBRID)
    raise SystemExit(f"unknown contender {args.contender!r} and no --zip given")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", type=int, default=0)
    ap.add_argument("--seed0", type=int, default=SEED0)
    ap.add_argument("--contender", default=None, choices=(None, "ceiling", "hybrid"))
    ap.add_argument("--zip", default=None)
    ap.add_argument("--video-seed", type=int, default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        # artifact-less end-to-end: a 2-stage course flown by the FORWARD
        # cruiser, 8 recorded frames, tiny GIFs, metrics keys present
        import tempfile

        _load_all_skills()
        from sim.composite import CompositeCourse  # noqa: F401 (registration path)
        from sim.envs import make_env
        from sim.scenario_registry import register

        register(
            "_it_selftest",
            lambda env, rng, speed=1.0, randomize=False, in_path=True: __import__(
                "sim.composite", fromlist=["CompositeCourse"]
            ).CompositeCourse(env, rng, stages=("gap", "gap"), speed=speed),
        )
        env = make_env()
        rec = {"fpv": [], "god": []}
        ep = run_composite_episode(env, Cruise(), 5, "_it_selftest", k=2, record=rec)
        env.close()
        assert ep["path"].shape[1] == 3 and "min_clear_step" in ep
        m = integration_metrics(ep)
        assert "stages_cleared" in m and "stage_break_at" in m
        assert len(rec["fpv"]) >= 8 and rec["god"][0].shape == (400, 400, 3)
        with tempfile.TemporaryDirectory() as td:
            _gif(rec["fpv"][:8], os.path.join(td, "a.gif"), scale=4)
            _gif(rec["god"][:8], os.path.join(td, "b.gif"))
            assert os.path.getsize(os.path.join(td, "a.gif")) > 5_000
            assert os.path.getsize(os.path.join(td, "b.gif")) > 5_000
        print(
            "INTEGRATION OK: 2-stage composite flies end-to-end, crash "
            "localization recorded, FPV+god frames render, GIFs write"
        )
        return

    _load_all_skills()
    factory = make_factory(args)
    if args.video_seed is not None:
        record_video(factory, args.video_seed)
        return
    if args.suite:
        suite(factory, args.suite, args.seed0, args.out)


if __name__ == "__main__":
    main()
    sys.exit(0)

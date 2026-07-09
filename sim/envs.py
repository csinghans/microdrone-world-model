"""The simulated micro-drone: a Crazyflie-class quad at 48 Hz with a 64x64
on-board camera, flown through a PID flight controller.

The two-layer split is load-bearing everywhere in this project: the AI layer
only ever emits a velocity command (vx, vy, vz, yaw-rate); `VelCommander`
integrates it into a reference position and the PID controller keeps the
aircraft alive at 48 Hz. That is how real autonomy stacks are built, and it
means every policy in this repo — scripted, hand MPC, or learned — speaks the
same narrow interface.
"""

import numpy as np

IMG_RES = 64  # camera + network input resolution
CTRL_HZ = 48  # control steps per second (the AI decides at CTRL_HZ / 4)
START = np.array([0.0, 0.0, 1.0])  # every rollout starts here, 1 m up


def make_env(gui: bool = False):
    """CtrlAviary at 48 Hz with the 64x64 on-board camera (shared by the
    dataset generator, the planners and every eval)."""
    from gym_pybullet_drones.envs.CtrlAviary import CtrlAviary
    from gym_pybullet_drones.utils.enums import DroneModel, Physics

    env = CtrlAviary(
        drone_model=DroneModel.CF2X,
        num_drones=1,
        initial_xyzs=np.array([START]),
        physics=Physics.PYB,
        pyb_freq=240,
        ctrl_freq=CTRL_HZ,
        gui=gui,
    )
    env.IMG_RES = np.array([IMG_RES, IMG_RES])
    return env


def make_ctrl():
    from gym_pybullet_drones.control.DSLPIDControl import DSLPIDControl
    from gym_pybullet_drones.utils.enums import DroneModel

    return DSLPIDControl(drone_model=DroneModel.CF2X)


class VelCommander:
    """Track a held velocity command with the two-layer split intact: we
    integrate a reference position (re-anchored whenever the command changes)
    and let the PID flight controller chase it. The command is
    (vx, vy, vz, yaw_rate); the 48 Hz attitude loop stays the controller's job.

    yaw: `yaw_ref` integrates the commanded yaw-rate from 0, giving an
    absolute heading setpoint fed to the PID as `target_rpy=[0,0,yaw_ref]`.
    When yaw_rate is 0 for the whole flight (every transit/indoor recipe
    today), yaw_ref stays 0 and target_rpy=[0,0,0], which is exactly the
    controller's default — so the yaw=0 behaviour is BIT-IDENTICAL. Note the
    translational (vx,vy) are integrated in the WORLD frame here; that is
    correct for yaw-in-place (the hover-yaw-scan), while translate-WHILE-yawed
    (body-frame vx,vy) + collision under yaw is the deferred WM-retrain step."""

    def __init__(self, ctrl, dt: float):
        self.ctrl, self.dt = ctrl, dt
        self.ref = None
        self.last = None
        self.yaw_ref = 0.0

    def reset(self, pos) -> None:
        self.ctrl.reset()
        self.ref = np.array(pos, dtype=float)
        self.last = None
        self.yaw_ref = 0.0

    def rpm(self, state, v_cmd):
        v = np.asarray(v_cmd[:3], dtype=float)
        yaw_rate = float(v_cmd[3]) if len(v_cmd) > 3 else 0.0
        if self.last is None or not np.allclose(v_cmd, self.last):
            self.ref = state[0:3].copy()  # re-anchor so a switch never jumps
            self.last = np.array(v_cmd, dtype=float)
        self.ref = self.ref + v * self.dt
        self.yaw_ref += yaw_rate * self.dt  # absolute heading; stays 0 if never yawed
        rpm, _, _ = self.ctrl.computeControlFromState(
            control_timestep=self.dt,
            state=state,
            target_pos=self.ref,
            target_vel=v,
            target_rpy=np.array([0.0, 0.0, self.yaw_ref]),
        )
        return rpm


def grab_frame(env) -> np.ndarray:
    """One 64x64x3 uint8 frame from the on-board camera."""
    rgb, _dep, _seg = env._getDroneImages(0, segmentation=False)
    return rgb[:IMG_RES, :IMG_RES, :3].astype(np.uint8)


def selftest() -> None:
    env = make_env()
    cmd = VelCommander(make_ctrl(), env.CTRL_TIMESTEP)
    obs, _ = env.reset(seed=7)
    cmd.reset(START)
    state = obs[0]
    for _ in range(24):  # half a second of forward flight
        rpm = cmd.rpm(state, np.array([0.8, 0.0, 0.0, 0.0]))
        obs, _, _, _, _ = env.step(rpm.reshape(1, 4))
        state = obs[0]
    frame = grab_frame(env)
    env.close()
    assert frame.shape == (IMG_RES, IMG_RES, 3) and frame.dtype == np.uint8
    assert state[0] > 0.05, "commanded forward flight did not move forward"
    print(f"SIM-ENV OK: 48 Hz CtrlAviary + PID VelCommander, frame {frame.shape}")


if __name__ == "__main__":
    selftest()

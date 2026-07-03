# Hardware bridge — v0.4 (design placeholder)

Nothing here runs yet, on purpose. The simulation stack must reproduce its
benchmarks in this repo (v0.1) and survive harder worlds (v0.2) before any
airframe pays for our bugs. This note pins the design so the code that lands
here has a shape to land into.

## Two stages, honestly labelled

**Stage 1 — Tello (off-board AI).** A DJI/Ryze Tello flown over Wi-Fi with
the world model running on a laptop. Cheap, fast to stand up, and *not*
on-board autonomy — the point is to measure the sim-to-real perception gap
(real camera, real latency) with the same evals this repo already has, and
to say so plainly.

`tello_adapter.py` (planned): the `VelCommander` velocity-setpoint interface
implemented over DJITelloPy `send_rc_control`, with unit conversion and the
safety filter wrapped around every command.

**Stage 2 — Crazyflie 2.1+ + AI-deck (on-board, the point).** The GAP8 is
the target this whole stack is sized for: int8 weights + activations +
workspace ≤ 512 KB, ~12 Hz decisions. Deployment path: NNTool quantization →
Autotiler codegen → encoder/predictor/heads on GAP8; the flight loop stays
on the STM32 through cflib setpoints.

`crazyflie_adapter.py` (planned): cflib velocity setpoints + the same safety
filter; the AI-deck streams camera frames during bring-up so on-board and
off-board inference can be A/B-measured on the same flight.

## Non-negotiables (from docs/safety.md)

Geofence, manual override, emergency land, low-battery behaviour, log
replay, and a field-test checklist — all present before the first
free flight, both stages.

# metric_grounding — the v0.5 campaign journal

## Hypothesis (pre-registered 2026-07-03, before any gate ran)

4D-GS-style **metric grounding** — supervising the latent with "where is
stuff, and how far" — makes the world model carry metric structure that the
collision heads and the learned policy can exploit, attacking the dense
floor (17–27 % at v0.3).

**Honest framing.** The real-world version of this supervision is an
offline 4D-Gaussian-Splatting reconstruction: Orin-class compute, hours per
scene, never on the drone. In sim we skip the reconstruction and read the
privileged pillar layout directly (`datasets/metric_labels.py`, a 5×3
FOV-honest polar grid to 2.1 m). That makes every number in this campaign
the **perfect-reconstruction upper bound** of the 4D-GS pipeline:

- if perfect metric supervision buys nothing here, the
  offline-reconstruction road is dead at this model scale;
- if it buys X, X is the *ceiling* — a real 4D-GS pass reconstructs with
  error and can only buy less.

Deploy-time cost is zero by construction: the grounding head is a
train-only auxiliary, dropped from the flight stack; the 512 KB line does
not move (`int8_kb` reports deploy weights; `aux_kb` prices the head
separately).

## The knob schedule (bars frozen at pre-registration; guards are sacred)

**M1 — model axis.** One knob on the G1 recipe: `--ground` (grounding aux,
λ = 0.5, 5×3 grid — λ and the grid geometry are part of the knob's
identity). Both arms train on the **same fresh draw**
(`python -m datasets.generate_rollouts --worlds hard --rollouts 96
--len 120 --seed 0`), 80 epochs, seed 0:

- grounded arm → `artifacts/wm_m1_ground.pth`
- same-draw control (identical minus the head) → `artifacts/wm_m1_control.pth`

| kind | bar |
|---|---|
| target | dense AUC@32 ≥ control + 0.05, **or** moving AUC@32 ≥ control + 0.05 |
| guard | every world-slice AUC@32 ≥ control − 0.03 |
| guard | veer-ranking ≥ 0.95 (n ≥ 20) |
| guard | now-AUC ≥ control − 0.03 |
| guard | deploy `int8_kb` identical to control (aux priced separately) |

Manipulation checks (harness, not science):

- grounded `gnd-AUC` ≥ 0.80 — below that the knob wasn't installed and the
  run is a harness error, not a measurement;
- control arm shows `mean(val MSE) < mean(no-op)` at scale — re-verifying
  the G2 at-scale finding (MSE@32 1.31 vs no-op 1.94). Context: the
  20-rollout smoke fails this claim deterministically on shipped v0.4.0
  (val Δ overfits at smoke scale), so the smoke asserts were recalibrated
  2026-07-03 and the claim now lives here, at the scale where it is
  measurable. A control-arm failure escalates to a code bisect — it does
  not judge grounding.

Borderline rule: if the winning delta lands within ±0.02 of its bar,
repeat the grounded arm at seed 1 against the same control and judge on
the mean of the two grounded runs.

Sanity anchors (context, **not** bars — cross-draw comparisons don't
gate): G1 recorded classic/dense/moving AUC@32 = 0.86/0.82/0.88.

**M1b — reserve knob**, may be played only on an M1 failure with a
convergence signature (latent MSE still falling at epoch 80 / MSE@32 not
beating no-op while gnd-AUC is high): both arms retrained at 160 epochs,
same draw, same bars. Rationale must be written before launch.

**M2 — policy axis**, runs **only if M1 passes.** One knob: the grounded
model replaces G1 under the unchanged v0.3 champion recipe
(`--policy --worlds hard --x-progress --edge-bias`, 300 k, seed 0).
n = 30 seeds/cell; any cell within ±0.08 of its bar is rechecked at n = 60
on fresh seeds (house rule).

| kind | bar |
|---|---|
| target | dense@0.8 crash ≤ 12 % (champion 17 %), **or** dense@1.2 ≤ 20 % (champion 27 %) |
| guard | moving@0.8 ≤ 18 %, moving@1.2 ≤ 12 % |
| guard | cluttered ≤ 5 % |
| guard | sweep ≤ 5/5/5/10/10 % (0.8/1.0/1.2/1.4/1.6 m/s) |
| guard | fast single-pillar ≤ 10 % |

Budget: at most these three knobs (M1, reserve M1b, M2). Anything else is
a deviation and needs a written rationale before it runs. Honest negatives
get recorded, not retried into passing.

---

## Gates

(appended per gate; numbers only from rerunnable commands)

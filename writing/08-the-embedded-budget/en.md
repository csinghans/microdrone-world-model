# From Sim Toward Crazyflie: The Embedded Budget

*Article 8 of a series on building a latent world model that fits in
512 KB. Article 7 was about keeping skills alive while you improve
them; this one is about the number that shaped every design decision —
and what happened when we finally ran the stack the way the chip
would run it: quantized. Everything reruns from
[microdrone-world-model](https://github.com/csinghans/microdrone-world-model).*

---

> **The simple version.** A 7 kg carry-on limit doesn't just constrain your packing — it decides what you own. Our chip's 512 KB decided the model's entire shape the same way. And "it fits on paper" is not "it flies": when we finally ran the stack the way the chip would — squeezed to int8 — the models survived, but the tripwire that decides "dodge NOW" did not. Weighing your luggage is not the same as boarding the plane.


## The budget as constitution

A Crazyflie's AI-deck offers one GAP8-class chip: about **512 KB** of
fast memory for weights *and* activations *and* working buffers, and a
compute rate we book at 0.5 GMAC/s — a figure we state explicitly so it
can be challenged. Our control loop decides at 12 Hz, so a decision may
spend ~83 ms; we budget **~8 ms** of it on inference and leave the rest
to margins we will be glad of later.

That budget was never a deployment detail to be handled at the end. It
is the reason the model looks the way it does: a 64-d latent instead of
pixels (a planner needs "which option gets close to something", not a
picture), four horizontal strips instead of global pooling (16k extra
int8 weights buy left-vs-right, which dodging *is*), one shared trunk
with per-horizon residual heads (anticipation at four time scales for a
few KB), collision heads instead of decoders. The bill, printed and
asserted by a selftest on every run: **137.3 KB** — 81.3 KB of int8
weights + 28 KB peak activations + 28 KB double-buffered workspace —
at ~3.9 M MACs per decision, ~8 ms at the stated rate.

Since v0.8 there are two world models resident — the pinned transit
champion and the unified transit+indoor WM — together **~163 KB int8,
32 % of the budget**, one running per flight mode. Everything below is
about the day we stopped trusting that arithmetic and measured it.

## The first embedded lesson needed no quantizer

Before any int8 question, the unified WM taught us an embedded-systems
lesson the hard way. It beats the champion on every job a WM owns —
held-out transit AUC@32 0.896→0.931, closed-loop crash 40 %→21 %,
false-evasion 100 %→6 %, indoor detection 0.940→0.978. The obvious move
was to overwrite the champion. The full-zoo pass said no: every
distilled skill policy was trained against the champion's latent, and
swapping encoders under them broke the zoo — the 40-decision slalom
chain fell **80 %→0 %**, the others lost 5–30 points.

**A latent is an ABI.** Policies are compiled against it; change the
encoder and you must re-link (re-distill) or keep both resident. We
ship both — the flight-mode selector binds each mission to its own WM
at takeoff — and 163 KB of 512 makes "both" affordable. That is a
luxury the budget granted; the next section is about the bill it
deferred.

## Accounting is not measurement

Until this month, every int8 claim in the project was arithmetic:
`n_params / 1024`. No quantized forward pass had ever produced a gate
number. So we built a fake-quant harness shaped like the GAP8 NNTool
SQ8 flow — int8 symmetric weights, per-channel for convs and per-tensor
for linears; uint8 asymmetric activations calibrated on the WM's own
two-track training union — froze parity bars *before* any number
existed, and re-ran the exact shipped gates on identical frames, seeds
and device.

The models pass. The unified WM's worst per-world transit AUC moves
**−0.007** (bar −0.010); the indoor detection probe moves **−0.004**
(bar −0.015). One honest exception: the older champion loses **−0.016**
on the moving world, and the loss is calibration-insensitive — a
percentile calibration made it *worse* (the activation tails carry
signal), and doubling the calibration sample reproduced it to the third
decimal. Real cost, one world, third argument this month that the
unified WM is the embedded-path artifact.

Then we flew it.

## A rank-preserving detector is not the same aircraft

The closed-loop WM arm, quantized naively, crashed 21 %→36 % — and
evaded on **100 %** of clear runs (float: 6 %). Remember the AUC barely
moved: the *ordering* of dangers survived quantization. What died was
everything downstream of ordering, and the campaign pinned it in three
one-knob moves:

- **Not miscalibration.** Fitting temperatures on the quantized logits
  returned T ≈ 1.0 across every horizon and ring: the probabilities are
  not globally inflated. The re-flown gate did not move.
- **The killer was four action dims sharing a 64-dim latent's scale.**
  The predictor's input is `z ‖ action` under one activation scale, so
  the actions kept ~25 effective levels — the *differences between
  candidate actions*, which the policy's relative-margin trigger
  actually reads, were quantization-randomized. Splitting the seam into
  two quant nodes (SQ8-legal, zero weights) returned false-evasion to
  the float value exactly — while the layer's SNR barely moved, because
  SNR measures absolute error and the trigger reads differential error.
  Our best diagnostic was blind to the failure mode that mattered.
- **And still the crash bar would not close.** 16-bit predictor
  activations landed crash at bit-exact float parity — and flipped
  false-evasion back to 100 %. A false evasion is an ANY-over-the-run
  statistic: one spurious margin among ~300 decisions flips a whole
  flight. Max-statistics amplify exactly the noise PTQ leaves behind;
  every point fix reshuffled which clause failed.

**Verdict: post-training quantization alone does not buy closed-loop
flight parity for a margin-triggered policy.** The transit WMPolicy
stays float until a freshly pre-registered re-tune of its margins on
the quantized landscape — or quantization-aware training. We publish
the FAIL with its mechanism chain: rank ✓ → probabilities ✓ →
per-candidate differentials ✗ (fixed by the split) → threshold-adjacent
margin mass ✗ (open).

## The symmetric law — and the recipe that ships

The indoor stack failed differently, and the difference is the finding.
Quantized as shipped, the three detection heads all missed their parity
bars (they were trained on float latents — a distribution the quantized
encoder no longer produces), and the yaw-scan flight gate failed at
correct-find 0.40 — **by missing (0.55), not false-alarming: FA 0.05,
better than the float gate's 0.10.** The indoor trigger is a confirm-2
temporal filter, and consensus statistics are the mirror image of max
statistics: they suppress noise-induced false positives and amplify
recall loss instead.

Recall loss is the failure mode you can repair in seconds. Refit each
head *on the quantized latents* — same recipe, same train block — and
two of three come back **above** their float scores (yaw +0.001,
person +0.025; the near-floor head stays down −0.114, the campaign's
honest residual: grazing views are genuinely quantization-hostile).
Re-fly the gate with the refit yaw head:

**correct 0.75 / false-alarm 0.10 / collision 0.00 / return 1.00 —
the fully quantized indoor stack matches or beats the float gate of
record (0.70 / 0.10 / 0.00 / 1.00).**

So the embedded recipe, measured end to end: **int8 per-channel
weights + activation calibration on both tracks + one extra quant node
at the z‖action seam + refit every detection head on the quantized
latents.** Heads cost seconds and a new lock entry each; the WM itself
never retrains.

## What the sim cannot settle — and one thing it just did

One gap stopped being speculation this month. The AI-deck's stock
camera is monochrome; our stack trains on RGB. A luminance-only arm
prices it: **transit collision prediction collapses** (unified AUC@32
0.931→0.715, with the dense world falling below chance) while
**indoor detection barely moves** (0.978→0.953). If the bridge is ever
unfrozen, the transit WM needs a color sensor or a gray-trained
retrain; the seeing-instrument story survives the stock camera. The
sim's palette may overstate color reliance — stated so the number is
read with its caveat.

Still honestly open, and only hardware can close them: PULP-NN's exact
rounding and saturation, Autotiler's tiling and the real latency behind
our 0.5 GMAC/s assumption, real optics, and the near-surface
aerodynamics our floor-hugging experiments already flagged as the
sim-to-real gap. The bridge itself stays parked by standing
instruction. What changed is what waits on the other side: the gates it
must pass are green in float — and for the indoor mission, now green
in int8.

## Rerun the numbers

```bash
python -m eval.eval_latency_budget --selftest        # the 137.3 KB / ~8 ms bill
python -m eval.eval_unified_wm_gate --zoo            # why we ship two WMs (slalom 80->0)
python -m eval.eval_int8_parity --k0                 # B1/B2 parity + SNR + monochrome arms
python -m eval.eval_int8_parity --closed-loop --cl-arms float,int8pc+split
python -m eval.eval_int8_parity --b3 --b5 --retrain-heads   # the recipe, in flight
```

Bars, decision rules and every verdict:
`experiments/int8_parity_v1/journal.md` — committed before the numbers
existed, as always.

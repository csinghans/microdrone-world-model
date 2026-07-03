# The embedded budget

The target class is a GAP8 (8+1 RISC-V cores, ~512 KB L2, ultra-low power —
the Crazyflie AI-deck's chip). The budget arithmetic is the project's
foundation: if it does not fit here, it does not ship, however well it
scores.

## The memory bill (measured by `eval.eval_latency_budget`)

Weights are not the whole story. Three tenants share the same SRAM:

| Tenant | What it is | Measured (v0.1 stack) |
|---|---|---|
| int8 weights | encoder + predictor + collision heads + danger-now | **81.3 KB** |
| Peak activations | the largest live input+output tensor pair (ReLU fused) | **28.0 KB** |
| Workspace | double-buffered DMA staging for the same pair | **28.0 KB** |
| **Total** | | **137.3 KB < 512 KB** |

Headroom ≈ 375 KB — deliberately large, because the v0.2+ roadmap (memory
over latents, harder scenes) will spend some of it, and because real
deployments carry a flight stack beside the model.

## The compute bill

Per decision (~12 Hz): encode the frame once (the expensive part), then run
the tiny MLPs once per candidate command — the MPC's whole deliberation
re-uses one encoding.

- ~**3.9 M MACs** per decision (analytic count, encoder shared across 6
  candidates)
- at an assumed **0.5 GMAC/s** effective int8 throughput (PULP-NN-class
  kernels — an order-of-magnitude figure, stated so it can be challenged):
  ~**8 ms** per decision, comfortably inside the 83 ms budget of a 12 Hz
  loop.

## Rules this imposes upstream

1. **No pixel generation.** A decoder would blow both bills at once.
2. **Latent width is a budget line.** 64-d today; growing it must be paid
   for in the table above, not just in AUC.
3. **Per-candidate cost must stay MLP-cheap.** Anything that re-runs the
   encoder per candidate breaks the 12 Hz loop.
4. **Quantization is assumed from day one.** All sizes are int8; a design
   that only works in fp32 is over budget by 4x before it starts.

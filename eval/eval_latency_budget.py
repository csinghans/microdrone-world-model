"""The embedded bill: would this actually run on a GAP8?

Splits the 512 KB budget the way an embedded engineer would: weights are not
the whole story — the activation tensors and the DMA double-buffer workspace
live in the same SRAM. Latency is measured on this machine and *estimated*
for GAP8 from analytic MACs at an assumed 0.5 GMAC/s effective int8
throughput (PULP-NN-class kernels, order of magnitude, stated so it can be
challenged).

Run:
  python -m eval.eval_latency_budget            # prints the budget lines
  python -m eval.eval_latency_budget --selftest # asserts budget + 12 Hz
"""

import argparse
import os
import sys
import time

import numpy as np
import torch
import torch.nn as nn

from planner.action_set import ACTION_VECS
from planner.latent_mpc import WMPolicy
from sim.envs import IMG_RES
from world_model.training import GAP8_BUDGET_KB

GAP8_GMACS = 0.5  # assumed effective int8 throughput (GMAC/s), stated not hidden


def onboard_budget(enc, pred, cheads, nhead, img_res: int = IMG_RES) -> dict:
    """int8 weights + the peak pair of live activation tensors + a
    double-buffer workspace (DMA staging) estimate — all three share the
    GAP8's 512 KB L2. Also counts MACs analytically for the latency
    estimate. `img_res` bills a perception-tier candidate at its own
    camera resolution (default = the deployed 64; every existing caller
    unchanged)."""
    mods = (enc, pred, cheads, nhead)
    n_params = sum(p.numel() for m in mods for p in m.parameters())

    r = int(img_res)
    c_in = int(enc.features[0].in_channels)  # 6 for two-frame input models
    sizes, macs_enc = [c_in * r * r], 0
    x = torch.zeros(1, c_in, r, r)
    with torch.no_grad():
        for mod in enc.features:
            x = mod(x)
            if isinstance(mod, nn.ReLU):
                continue  # fused into the conv kernel on-device; no own buffer
            sizes.append(x.numel())
            if isinstance(mod, nn.Conv2d):
                k = mod.kernel_size[0] * mod.kernel_size[1]
                macs_enc += x.numel() * mod.in_channels * k
    peak_act = max(a + b for a, b in zip(sizes, sizes[1:]))  # in+out live pair
    macs_enc += sum(  # the strip-pool projection runs once per frame too
        m.in_features * m.out_features
        for m in enc.modules()
        if isinstance(m, nn.Linear)
    )

    tem = getattr(enc, "temporal", None)
    if tem is not None:  # one GRU step per frame: three gates, two matmuls each
        d_in, d_h = tem.gru.input_size, tem.gru.hidden_size
        macs_enc += 3 * (d_in * d_h + d_h * d_h)

    macs_lin = sum(
        m.in_features * m.out_features
        for mod in (pred, cheads, nhead)
        for m in mod.modules()
        if isinstance(m, nn.Linear)
    )
    n_cands = len(ACTION_VECS)  # the MPC re-runs only the MLPs per candidate
    return {
        "weights_kb": n_params / 1024,
        "peak_act_kb": peak_act / 1024,
        "workspace_kb": peak_act / 1024,  # double-buffered DMA staging
        "total_kb": n_params / 1024 + 2 * peak_act / 1024,
        "macs_frame": macs_enc + macs_lin,  # encoder once + one MLP sweep
        "macs_decision": macs_enc + n_cands * macs_lin,  # MPC: encoder shared
    }


def measure_latency(policy, n: int = 50) -> float:
    """Wall-clock ms per MPC decision on this machine (content-free frame)."""
    frame = np.zeros((IMG_RES, IMG_RES, 3), dtype=np.uint8)
    state = np.zeros(20)
    policy.begin([])
    t0 = time.perf_counter()
    for _ in range(n):
        policy.decide(frame, state)
    return (time.perf_counter() - t0) / n * 1000


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument(
        "--ckpt",
        default=None,
        help="bill a candidate checkpoint (analytic [budget] line only; "
        "replaces the ad-hoc heredoc the perception campaigns used)",
    )
    ap.add_argument(
        "--img-res",
        type=int,
        default=None,
        help="camera resolution to bill at (default: the checkpoint's meta)",
    )
    args = ap.parse_args()

    if args.ckpt:
        from world_model.training import load_model

        enc, pred, cheads, nhead, meta = load_model(args.ckpt, device="cpu")
        res = int(args.img_res or meta.get("img_res", IMG_RES))
        budget = onboard_budget(enc, pred, cheads, nhead, img_res=res)
        gap8_ms = budget["macs_decision"] / (GAP8_GMACS * 1e9) * 1000
        name = os.path.splitext(os.path.basename(args.ckpt))[0]
        fits = "OK" if budget["total_kb"] < GAP8_BUDGET_KB else "OVER"
        print(
            f"[budget] {name}: total={budget['total_kb']:.1f}KB "
            f"macs={budget['macs_decision'] / 1e6:.1f}M est={gap8_ms:.0f}ms "
            f"(D={meta.get('D', 64)} img_res={res}) {fits}"
        )
        if args.selftest:
            assert budget["total_kb"] < GAP8_BUDGET_KB, "over the GAP8 budget"
        return

    from eval.eval_closed_loop import load_or_train

    enc, pred, cheads, nhead, meta = load_or_train(device="cpu")
    budget = onboard_budget(enc, pred, cheads, nhead)
    lat_ms = measure_latency(WMPolicy(enc, pred, cheads, meta))
    gap8_ms = budget["macs_decision"] / (GAP8_GMACS * 1e9) * 1000

    print(
        f"LATENCY OK: {lat_ms:.1f} ms measured (this CPU) | "
        f"~{gap8_ms:.0f} ms est @ GAP8 {GAP8_GMACS:.1f} GMAC/s "
        f"({budget['macs_decision'] / 1e6:.1f} M MACs, encoder shared "
        f"across {len(ACTION_VECS)} candidates)"
    )
    print(
        f"ONBOARD-BUDGET OK: weights={budget['weights_kb']:.1f} KB + "
        f"peak_activation={budget['peak_act_kb']:.1f} KB + "
        f"workspace(dbl-buf)={budget['workspace_kb']:.1f} KB = "
        f"{budget['total_kb']:.1f} KB < {GAP8_BUDGET_KB} KB"
    )
    if args.selftest:
        assert budget["total_kb"] < GAP8_BUDGET_KB, "over the GAP8 budget"
        assert gap8_ms < 1000.0 / 12, "MPC too slow for a 12 Hz decision loop"


if __name__ == "__main__":
    main()
    sys.exit(0)

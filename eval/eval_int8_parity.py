"""int8 fake-quant parity — the embedded story's missing measurement.

Every budget number in this repo is int8 ACCOUNTING (`n_params/1024`,
`eval_latency_budget`); no quantized forward pass has ever produced a
gate number. This tool fake-quantizes the shipped WMs the way the GAP8
NNTool SQ8 flow would — weights int8 symmetric (per-channel for convs,
per-tensor for linears), activations uint8 asymmetric calibrated by
min/max at every Conv2d/Linear input — then re-runs the EXACT shipped
reads on identical data/seeds/device:

  B1  transit per-world AUC@32 on the held-out set
      (`eval_wm_checkpoint.evaluate_components`, split seed 0)
  B2  indoor detection linear-probe AUC on the fixed grid
      (`eval_target_probe.collect_target_frames`, identical frames)
  B4  transit closed-loop WM-arm, n=60 (`eval_closed_loop.evaluate`
      components seam)  [--closed-loop; sim-heavy]

plus a per-layer SNR diagnostic (quantize ONE leaf at a time — names the
hostile layer before anyone guesses) and grayscale-input arms (the
AI-deck's stock camera is monochrome; the stack trains RGB).

Pre-registered bars + decision rules: experiments/int8_parity_v1/journal.md
(committed before any number). Honesty — what this does NOT model:
PULP-NN rounding/saturation exactness, Autotiler tiling/DMA + real
latency, NNTool's actual per-layer choices; ReLU/pool/flatten run float
between quantized leaves; bias stays float; terminal logits are not
output-quantized (rank metrics are monotone-invariant — threshold
effects land in the closed-loop arm).

Run:
  python -m eval.eval_int8_parity --k0            # B1 + B2 + SNR + gray
  python -m eval.eval_int8_parity --closed-loop   # B4 (n=60, slow)
  python -m eval.eval_int8_parity --selftest
"""

import argparse
import copy
import json
import os
import sys

import numpy as np
import torch
import torch.nn.functional as F
from torch import nn

from world_model.training import MODEL, load_model

UNIFIED = os.path.join(os.path.dirname(MODEL), "world_model_unified.pth")
HOLDOUT = os.path.join(os.path.dirname(MODEL), "transit_eval_holdout.npz")
COMBINED = os.path.join(os.path.dirname(MODEL), "combined.npz")
CALIB_N = 1024
CALIB_SEED = 20260711
DEVICE = "cpu"  # both arms on one deterministic device — parity is a Δ


class FQLeaf(nn.Module):
    """Fake-quant one Conv2d/Linear: int8 symmetric weights (per-channel
    for convs when enabled), uint8 asymmetric input activations with a
    running min/max calibration. In `calibrating` mode the float leaf runs
    and ranges are recorded; afterwards inputs are fake-quantized and the
    quantized weights are used."""

    def __init__(self, leaf, per_channel=True, pct=None):
        super().__init__()
        self.leaf = leaf
        self.per_channel = bool(per_channel) and isinstance(leaf, nn.Conv2d)
        w = leaf.weight.detach().clone()
        if self.per_channel:
            s = (w.abs().flatten(1).amax(1).clamp(min=1e-12) / 127.0).view(
                (-1,) + (1,) * (w.dim() - 1)
            )
        else:
            s = w.abs().amax().clamp(min=1e-12) / 127.0
        self.register_buffer("qw", (w / s).round().clamp(-127, 127) * s)
        self.calibrating = False
        self.pct = pct  # None -> min/max ranges; else e.g. 0.999 percentile
        self.lo, self.hi = None, None

    def _fq_act(self, x):
        if self.lo is None:  # never calibrated: honest float passthrough
            return x
        lo, hi = self.lo, max(self.hi, self.lo + 1e-9)
        s = (hi - lo) / 255.0
        return ((x - lo) / s).round().clamp(0, 255) * s + lo

    def forward(self, x):
        if self.calibrating:
            if self.pct is None:
                xmin, xmax = float(x.min()), float(x.max())
            else:  # K1a rule: per-batch percentiles, lo/hi run over batches
                xf = x.detach().reshape(-1).float()
                xmin = float(torch.quantile(xf, 1.0 - self.pct))
                xmax = float(torch.quantile(xf, self.pct))
            self.lo = min(self.lo, xmin) if self.lo is not None else xmin
            self.hi = max(self.hi, xmax) if self.hi is not None else xmax
            return self.leaf(x)
        x = self._fq_act(x)
        if isinstance(self.leaf, nn.Conv2d):
            c = self.leaf
            return F.conv2d(
                x, self.qw, c.bias, c.stride, c.padding, c.dilation, c.groups
            )
        return F.linear(x, self.qw, self.leaf.bias)


def _swap_leaves(mod, per_channel, only, prefix, out, pct=None):
    for name, child in mod.named_children():
        full = f"{prefix}.{name}" if prefix else name
        if isinstance(child, (nn.Conv2d, nn.Linear)):
            if only is None or full in only:
                fq = FQLeaf(child, per_channel, pct=pct)
                setattr(mod, name, fq)
                out.append((full, fq))
        else:
            _swap_leaves(child, per_channel, only, full, out, pct)


def quantize(module, per_channel=True, only=None, pct=None):
    """Deep-copy `module`, replacing every Conv2d/Linear leaf (or exactly
    the ones named in `only`) with an FQLeaf. Returns (copy, leaves)."""
    m = copy.deepcopy(module)
    leaves = []
    _swap_leaves(m, per_channel, only, "", leaves, pct)
    return m, leaves


def _strip(only, prefix):
    if only is None:
        return None
    return {n[len(prefix) :] for n in only if n.startswith(prefix)}


class QWM:
    """A quantized copy of one WM checkpoint's four modules. The shipped
    artifact is loaded read-only and deep-copied — sacred paths untouched."""

    def __init__(self, ck, per_channel=True, only=None, pct=None):
        enc, pred, cheads, nhead, meta = load_model(ck, device=DEVICE)
        self.meta = meta
        self.leaves = []
        for prefix, mod in (
            ("enc.", enc),
            ("pred.", pred),
            ("cheads.", cheads),
            ("nhead.", nhead),
        ):
            q, ls = quantize(mod, per_channel, _strip(only, prefix), pct)
            setattr(self, prefix[:-1], q)
            self.leaves += [(prefix + n, f) for n, f in ls]

    def set_calibrating(self, flag: bool):
        for _, f in self.leaves:
            f.calibrating = flag

    def components(self):
        return self.enc, self.pred, self.cheads, self.nhead


def _calib_batch(n=CALIB_N, seed=CALIB_SEED):
    """Frames + paired actions sampled seed-fixed from the two-track
    training union (combined.npz) — the deployment-realistic calibration
    set (no rendered-target imagery; journal names that as a K1 knob)."""
    blob = np.load(COMBINED, allow_pickle=True)
    frames, actions = blob["frames"], blob["actions"]
    R, L = frames.shape[:2]
    rng = np.random.default_rng(seed)
    r, t = rng.integers(0, R, n), rng.integers(0, L, n)
    x = (
        torch.tensor(
            np.stack([frames[i, j] for i, j in zip(r, t)]), dtype=torch.float32
        ).permute(0, 3, 1, 2)
        / 255.0
    )
    a = torch.tensor(
        np.stack([actions[i, j] for i, j in zip(r, t)]), dtype=torch.float32
    )
    return x, a


def calibrate(q: QWM, x, a, batch=256):
    """One pass of the real compute graph in calibration mode, so every
    leaf sees its true input distribution from BOTH tracks."""
    from planner.action_set import A_NORM

    q.set_calibrating(True)
    with torch.no_grad():
        for i in range(0, len(x), batch):
            z = q.enc(x[i : i + batch])
            zh = q.pred(z, a[i : i + batch] / A_NORM, base=z)
            q.cheads(zh)
            q.nhead(z)
    q.set_calibrating(False)


def _gray(x):
    """Luminance-only input (Y replicated x3): the AI-deck monochrome arm."""
    y = 0.299 * x[:, 0] + 0.587 * x[:, 1] + 0.114 * x[:, 2]
    return y.unsqueeze(1).expand(-1, 3, -1, -1).contiguous()


class GrayInput(nn.Module):
    def __init__(self, enc):
        super().__init__()
        self.enc = enc

    def forward(self, x):
        return self.enc(_gray(x))


def _arm_components(ck, arm, calib, pct=None):
    """Build one arm's (enc, pred, cheads, nhead). `calib` = (x, a)."""
    if arm == "float":
        enc, pred, cheads, nhead, _m = load_model(ck, device=DEVICE)
    elif arm == "gray":
        enc, pred, cheads, nhead, _m = load_model(ck, device=DEVICE)
        enc = GrayInput(enc)
    elif arm in ("int8pc", "int8pt", "gray+int8pc"):
        q = QWM(ck, per_channel=("pt" not in arm), pct=pct)
        x, a = calib
        calibrate(q, _gray(x) if arm.startswith("gray") else x, a)
        enc, pred, cheads, nhead = q.components()
        if arm.startswith("gray"):
            enc = GrayInput(enc)
    else:
        raise SystemExit(f"unknown arm {arm!r}")
    return enc, pred, cheads, nhead


class TempScale(nn.Module):
    """Divide collision logits by a fitted per-(horizon, ring) temperature —
    algebraically identical to calibrate_heads.bake (w/T, b/T), kept as a
    wrapper so it composes with FQLeaf-quantized heads. On GAP8 the division
    folds into the output dequant scale: zero extra compute."""

    def __init__(self, cheads, T):
        super().__init__()
        self.cheads = cheads
        self.register_buffer("T", T)

    def forward(self, zh):
        return self.cheads(zh) / self.T


# --- B1: transit per-world AUC@32, identical held-out split ------------------
def b1_transit(arms, wms=None, data_path=HOLDOUT, seed=0, pct=None):
    from eval.eval_wm_checkpoint import evaluate_components

    wms = wms or {"champion": MODEL, "unified": UNIFIED}
    data = dict(np.load(data_path, allow_pickle=True))
    calib = _calib_batch()
    out = {}
    for wname, ck in wms.items():
        out[wname] = {}
        for arm in arms:
            enc, pred, cheads, nhead = _arm_components(ck, arm, calib, pct=pct)
            r = evaluate_components(enc, pred, cheads, nhead, data, seed, DEVICE)
            out[wname][arm] = {
                **{k: float(v) for k, v in r["auc_by_world"].items()},
                "auc32": float(r["auc_h"][-1]),
                "now_auc": float(r["now_auc"]),
            }
            print(f"  [B1] {wname:9s} {arm:11s} " + _fmt(out[wname][arm]))
    return out


# --- B2: indoor detection linear-probe AUC, identical frames -----------------
def b2_detection(arms, ck=UNIFIED, n_rooms=6, seed0=600000):
    from eval.eval_target_probe import _linear_probe_auc, collect_target_frames

    d = collect_target_frames(n_rooms, seed0, ckpt=ck, return_frames=True)
    frames, y = d["frames"], d["label"]
    calib = _calib_batch()
    out = {"n_frames": int(len(y)), "positive_rate": float(y.mean())}
    for arm in arms:
        enc, *_ = _arm_components(ck, arm, calib)
        lat = _encode(enc, frames)
        if arm == "float":  # instrument check: batched path == collector path
            drift = float(np.abs(lat - d["lat"]).max())
            assert drift < 1e-4, f"batched encode drifted from collector ({drift})"
        out[arm] = float(_linear_probe_auc(lat, y))
        print(f"  [B2] unified   {arm:11s} detection_auc={out[arm]:.4f}")
    return out


def _encode(enc, frames_u8, batch=256):
    zs = []
    with torch.no_grad():
        for i in range(0, len(frames_u8), batch):
            x = (
                torch.tensor(frames_u8[i : i + batch], dtype=torch.float32).permute(
                    0, 3, 1, 2
                )
                / 255.0
            )
            zs.append(enc(x).numpy())
    return np.concatenate(zs).astype(np.float32)


# --- SNR: quantize ONE leaf at a time, name the hostile layer ----------------
def snr_diag(ck=UNIFIED, n=256):
    from planner.action_set import A_NORM

    x, a = _calib_batch(n=n)
    enc, pred, cheads, nhead, _m = load_model(ck, device=DEVICE)
    with torch.no_grad():
        z = enc(x)
        ref = cheads(pred(z, a / A_NORM, base=z))
    names = [n_ for n_, _ in QWM(ck).leaves]
    out = {}
    for name in names:
        q = QWM(ck, per_channel=True, only={name})
        calibrate(q, x, a)
        with torch.no_grad():
            zq = q.enc(x)
            got = q.cheads(q.pred(zq, a / A_NORM, base=zq))
        err = float(((ref - got) ** 2).sum())
        sig = float((ref**2).sum())
        out[name] = 10.0 * float(np.log10(sig / max(err, 1e-12)))
        print(f"  [SNR] {name:24s} {out[name]:7.1f} dB")
    return out


# --- B4: transit closed-loop WM-arm via the components seam ------------------
def b4_closed_loop(arms=("float", "int8pc"), ck=UNIFIED, n=60, seed0=1000):
    from eval.eval_closed_loop import evaluate as cl_eval
    from eval.eval_unified_wm_gate import wm_arm

    calib = _calib_batch()
    out = {}
    for arm in arms:
        enc, pred, cheads, nhead = _arm_components(ck, arm, calib)
        meta = load_model(ck, device=DEVICE)[4]
        out[arm] = wm_arm(cl_eval(n, seed0, enc, pred, cheads, nhead, meta))
        print(f"  [B4] unified   {arm:11s} " + _fmt(out[arm]))
    if {"float", "int8pc"} <= set(out):
        n_ip = sum(1 for i in range(n) if (i % 10) < 7)
        p = out["float"]["crash"]
        half = 1.96 * float(np.sqrt(max(p * (1 - p), 1e-9) / n_ip))
        dq = out["int8pc"]["crash"] - p
        out["bar_B4"] = {
            "delta_crash": float(dq),
            "float_ci95_half": float(half),
            "pass": bool(dq <= 0.03 + 1e-9 and abs(dq) <= half + 1e-9),
        }
        print(
            f"  [B4] Δcrash={dq:+.3f} (bar ≤ +0.030, float CI ±{half:.3f}) "
            f"-> {'PASS' if out['bar_B4']['pass'] else 'FAIL'}"
        )
    return out


def _fmt(d):
    return "  ".join(
        f"{k}={v:.4f}" for k, v in d.items() if isinstance(v, (int, float))
    )


# --- K1 knobs (pre-registered in the journal before these runs) --------------
def _q_logit_stack(q, data, rolls, cf, vis):
    """calibrate_heads._logit_stack through QUANTIZED components: candidate
    logits (F, n_a, H, R), cf-oracle labels and vis mask over `rolls`
    (rooms auto-drop — their vis mask is all-zero by the cf-loss fix)."""
    from planner.action_set import A_NORM, ACTION_VECS

    n_a, L = len(ACTION_VECS), data["frames"].shape[1]
    outs, lbls, msks = [], [], []
    with torch.no_grad():
        for r in rolls:
            x = (
                torch.tensor(data["frames"][r], dtype=torch.float32).permute(0, 3, 1, 2)
                / 255.0
            )
            z = q.enc(x)
            cands = torch.tensor(
                float(data["speed"][r]) * ACTION_VECS / A_NORM, dtype=torch.float32
            )
            zz = z.repeat_interleave(n_a, dim=0)
            lg = q.cheads(q.pred(zz, cands.repeat(L, 1), base=zz))
            outs.append(lg.reshape(L, n_a, *lg.shape[1:]).cpu())
            lbls.append(torch.tensor(cf[r], dtype=torch.float32))
            msks.append(torch.tensor(vis[r], dtype=torch.bool))
    return torch.cat(outs), torch.cat(lbls), torch.cat(msks)


def k1a_champion_pct(pct=0.999):
    """K1a: champion B1 re-read with percentile activation calibration
    (single knob vs K0's min/max; bar unchanged)."""
    return b1_transit(("float", "int8pc"), wms={"champion": MODEL}, pct=pct)


def k1b_rebake(ck=UNIFIED, n=60, seed0=1000, fit_rolls_cap=40):
    """K1b: fit T per (horizon, ring) on the QUANTIZED graph's candidate
    logits (cf-oracle labels, combined-union TRAIN rollouts), TempScale
    the quantized cheads, re-fly B4 on identical seeds. The float
    reference is the recorded same-tool arm (b4_results.json)."""
    from datasets.intervention_labels import counterfactual_labels
    from eval.calibrate_heads import fit_temperatures
    from eval.eval_closed_loop import evaluate as cl_eval
    from eval.eval_unified_wm_gate import wm_arm
    from world_model.training import _split_rollouts

    data = dict(np.load(COMBINED, allow_pickle=True))
    tr_rolls, _va = _split_rollouts(data, np.random.default_rng(0))
    cf, vis = counterfactual_labels(data)
    rolls = [r for r in tr_rolls if bool(vis[r].any())][:fit_rolls_cap]
    q = QWM(ck, per_channel=True)
    calibrate(q, *_calib_batch())
    lg, y, m = _q_logit_stack(q, data, rolls, cf, vis)
    assert bool(m.any()), "no labelled frames in the fit set"
    T = fit_temperatures(lg, y, m)
    t_str = " ".join(f"{float(t):.2f}" for t in T.flatten())
    print(f"  [K1b] fitted T (warn/crit x horizons): {t_str}  (fit rolls {len(rolls)})")
    q.cheads = TempScale(q.cheads, T)
    meta = load_model(ck, device=DEVICE)[4]
    arm = wm_arm(cl_eval(n, seed0, q.enc, q.pred, q.cheads, q.nhead, meta))
    print("  [K1b] int8pc+T  " + _fmt(arm))
    return {
        "T": [float(t) for t in T.flatten()],
        "fit_rollouts": len(rolls),
        "int8pc_T": arm,
    }


def selftest() -> None:
    torch.manual_seed(0)
    from world_model.collision_head import CollisionHeads, DangerNowHead
    from world_model.encoder import Encoder
    from world_model.predictor import ACTION_D, MultiPredictor

    # 1) per-tensor weight-quant error is bounded by half a step
    lin = nn.Linear(8, 4)
    fq = FQLeaf(lin, per_channel=False)
    s = float(lin.weight.detach().abs().amax()) / 127.0
    assert float((fq.qw - lin.weight.detach()).abs().max()) <= s / 2 + 1e-7

    # 2) per-channel beats per-tensor when channel scales differ wildly
    conv = nn.Conv2d(3, 4, 3)
    with torch.no_grad():
        conv.weight[0] *= 100.0  # one loud channel starves the others' scale
    e_pc = float((FQLeaf(conv, True).qw - conv.weight.detach()).abs().max())
    e_pt = float((FQLeaf(conv, False).qw - conv.weight.detach()).abs().max())
    assert e_pc <= e_pt + 1e-9, "per-channel must not be worse"

    # 3) calibration mode runs the FLOAT leaf exactly; calibrated quantized
    #    forward stays close on in-range data and clamps out-of-range
    x = torch.rand(16, 8)
    fq.calibrating = True
    assert torch.allclose(fq(x), lin(x)), "calibration must run the float leaf"
    fq.calibrating = False
    q_in = fq._fq_act(torch.tensor([[-99.0] + [0.5] * 7]))
    assert float(q_in.min()) >= fq.lo - 1e-6, "out-of-range must clamp to lo"
    snr = float(
        10
        * torch.log10(
            (lin(x) ** 2).sum() / ((lin(x) - fq(x)) ** 2).sum().clamp(min=1e-12)
        )
    )
    assert snr > 25.0, f"calibrated linear too lossy ({snr:.1f} dB)"

    # 4) leaf accounting: Encoder has exactly 4 leaves; `only` wraps 1
    enc = Encoder()
    _, all_leaves = quantize(enc)
    assert len(all_leaves) == 4, [n for n, _ in all_leaves]
    _, one = quantize(enc, only={all_leaves[0][0]})
    assert len(one) == 1

    # 5) the composed graph runs quantized end to end, shapes intact
    pred, cheads, nhead = MultiPredictor(), CollisionHeads(), DangerNowHead()
    qe, le = quantize(enc)
    qp, lp = quantize(pred)
    qc, lc = quantize(cheads)
    qn, ln_ = quantize(nhead)
    for _, f in le + lp + lc + ln_:
        f.calibrating = True
    xi, ai = torch.rand(4, 3, 64, 64), torch.rand(4, ACTION_D)
    z = qe(xi)
    _ = qc(qp(z, ai, base=z)), qn(z)
    for _, f in le + lp + lc + ln_:
        f.calibrating = False
    z = qe(xi)
    logits = qc(qp(z, ai, base=z))
    assert logits.shape[0] == 4 and qn(z).shape == (4,)

    # 6) grayscale of a gray image is itself
    g = torch.rand(2, 1, 64, 64).expand(-1, 3, -1, -1).contiguous()
    assert torch.allclose(_gray(g), g, atol=1e-6)

    # 7) percentile calibration shrugs off a lone outlier; min/max is hostage
    fq_mm = FQLeaf(nn.Linear(8, 4), per_channel=False)
    fq_p = FQLeaf(nn.Linear(8, 4), per_channel=False, pct=0.99)
    xo = torch.rand(1000, 8)
    xo[0, 0] = 1e3
    for f in (fq_mm, fq_p):
        f.calibrating = True
        f(xo)
        f.calibrating = False
    assert fq_mm.hi >= 999.0 and fq_p.hi < 10.0, (fq_mm.hi, fq_p.hi)

    # 8) TempScale: T=1 is identity; T=2 halves the logits (AUC-invariant
    #    by monotonicity — the calibrate_heads selftest owns that proof)
    zh_t = torch.rand(2, len(cheads.heads), 64)
    t1 = torch.ones(len(cheads.heads), 2)
    assert torch.allclose(TempScale(cheads, t1)(zh_t), cheads(zh_t))
    assert torch.allclose(TempScale(cheads, 2 * t1)(zh_t), cheads(zh_t) / 2.0)

    print(
        "INT8-PARITY OK: weight-quant bounds, per-channel<=per-tensor, "
        "calibration exactness + clamp, leaf accounting, quantized "
        "end-to-end graph, gray idempotence, percentile-vs-outlier, "
        "TempScale algebra"
    )


ARMS_K0 = ("float", "int8pc", "int8pt", "gray", "gray+int8pc")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k0", action="store_true", help="B1 + B2 + SNR (+gray arms)")
    ap.add_argument("--closed-loop", action="store_true", help="B4, n=60 (slow)")
    ap.add_argument(
        "--k1a", action="store_true", help="champion B1 @ percentile calibration"
    )
    ap.add_argument("--pct", type=float, default=0.999)
    ap.add_argument(
        "--rebake",
        action="store_true",
        help="K1b: TempScale the quantized cheads, re-fly B4 (slow)",
    )
    ap.add_argument("--cl-seeds", type=int, default=60)
    ap.add_argument("--out", default=None, help="write results json here")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    if not (args.k0 or args.closed_loop or args.k1a or args.rebake):
        raise SystemExit("pick --k0 / --closed-loop / --k1a / --rebake (or --selftest)")
    res = {"device": DEVICE, "calib_n": CALIB_N, "calib_seed": CALIB_SEED}
    if args.k0:
        print("=== B1 transit per-world AUC@32 (held-out, split seed 0) ===")
        res["B1"] = b1_transit(ARMS_K0)
        print("=== B2 indoor detection linear-probe AUC (identical frames) ===")
        res["B2"] = b2_detection(ARMS_K0)
        print("=== per-layer SNR (quantize one leaf at a time, unified) ===")
        res["snr_db"] = snr_diag()
    if args.closed_loop:
        print(f"=== B4 transit closed-loop WM-arm (n={args.cl_seeds}) ===")
        res["B4"] = b4_closed_loop(n=args.cl_seeds)
    if args.k1a:
        print(f"=== K1a champion B1 @ percentile {args.pct} calibration ===")
        res["K1a"] = {"pct": args.pct, **k1a_champion_pct(args.pct)}
    if args.rebake:
        print(
            f"=== K1b TempScale(quantized cheads) -> B4 re-fly (n={args.cl_seeds}) ==="
        )
        res["K1b"] = k1b_rebake(n=args.cl_seeds)
    if args.out:
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        with open(args.out, "w") as f:
            json.dump(res, f, indent=1)
        print(f"[int8-parity] wrote {args.out}")


if __name__ == "__main__":
    sys.exit(main())

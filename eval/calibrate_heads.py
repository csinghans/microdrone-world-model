"""Temperature-recalibrate a checkpoint's collision heads — the C0 knob.

D0 measured the v0.5 flight loss's mechanism candidate: grounding left
the heads' *ranking* intact and inflated their warn-ring *numbers*
(dense warn ECE 1.75x, mean P up on every world). The cheapest possible
fix costs zero retraining: fit one temperature per (horizon, ring) on
the training rollouts' counterfactual-oracle labels (FOV-masked, the
same currency D0's ECE used), then **bake T into the head weights**
(w/T, b/T — algebraically identical to dividing the logits) so every
consumer — ObsBuilder, the policies, the probes — rides the calibrated
surface with no code change anywhere.

Temperature is monotonic, so per-world AUC is invariant *by
construction* — this knob can only move what D0 said was broken (the
numbers-as-probabilities), never what M1 said was won (the ordering).
The selftest asserts both properties on a synthetic miscalibration.

Run:
  python -m eval.calibrate_heads --ckpt <in.pth> --out <calibrated.pth>
  python -m eval.calibrate_heads --selftest
"""

import argparse
import copy
import sys

import numpy as np
import torch

from datasets.generate_rollouts import OUT as DATA
from datasets.intervention_labels import HORIZONS, counterfactual_labels
from planner.action_set import A_NORM, ACTION_VECS
from sim.scenarios import RADII
from world_model.losses import roc_auc
from world_model.training import _split_rollouts, load_model


def _logit_stack(ckpt_path: str, data: dict, rolls, device):
    """Head logits + oracle labels + FOV mask on the given rollouts:
    logits (F, n_a, H, R), labels (F, n_a, H, R), mask (F, n_a).
    Candidates speed-scaled per rollout (the ObsBuilder convention)."""
    enc, pred, cheads, _nhead, _meta = load_model(ckpt_path, device)
    if getattr(enc, "temporal", None) is not None:
        raise SystemExit("temporal checkpoints need a windowed probe")
    cf, vis = counterfactual_labels(data)
    n_a, L = len(ACTION_VECS), data["frames"].shape[1]
    outs, lbls, msks = [], [], []
    with torch.no_grad():
        for r in rolls:
            x = (
                torch.tensor(
                    data["frames"][r], dtype=torch.float32, device=device
                ).permute(0, 3, 1, 2)
                / 255.0
            )
            z = enc(x)
            cands = torch.tensor(
                float(data["speed"][r]) * ACTION_VECS / A_NORM,
                dtype=torch.float32,
                device=device,
            )
            lg = cheads(
                pred(
                    z.repeat_interleave(n_a, dim=0),
                    cands.repeat(L, 1),
                    base=z.repeat_interleave(n_a, dim=0),
                )
            )  # (L*n_a, H, R)
            outs.append(lg.reshape(L, n_a, *lg.shape[1:]).cpu())
            lbls.append(torch.tensor(cf[r, :, :, :, :], dtype=torch.float32))
            msks.append(torch.tensor(vis[r], dtype=torch.bool))
    return torch.cat(outs), torch.cat(lbls), torch.cat(msks)


def fit_temperatures(logits, labels, mask) -> torch.Tensor:
    """One T per (horizon, ring), fitted by masked BCE on the natural frame
    distribution (no oversampling — this is exactly the distribution the
    flying policy observes). Returns T (H, R), all > 0."""
    H, R = logits.shape[2], logits.shape[3]
    T = torch.ones(H, R)
    bce = torch.nn.BCEWithLogitsLoss()
    for h in range(H):
        for q in range(R):
            lg = logits[:, :, h, q][mask]
            y = labels[:, :, h, q][mask]
            p = torch.nn.Parameter(torch.zeros(()))  # log T
            opt = torch.optim.Adam([p], lr=0.05)
            for _ in range(300):
                opt.zero_grad()
                bce(lg / p.exp(), y).backward()
                opt.step()
            T[h, q] = float(p.detach().exp())
    return T


def bake(ckpt: dict, T: torch.Tensor) -> dict:
    """Divide each head row's weight+bias by its temperature — identical to
    logits/T for every input, so downstream code needs no change."""
    out = copy.deepcopy(ckpt)
    sd = out["collision_heads"]
    for h in range(T.shape[0]):
        for q in range(T.shape[1]):
            sd[f"heads.{h}.weight"][q] /= float(T[h, q])
            sd[f"heads.{h}.bias"][q] /= float(T[h, q])
    out["meta"] = dict(out["meta"])
    out["meta"]["calibration_T"] = [[float(v) for v in row] for row in T]
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt")
    ap.add_argument("--out")
    ap.add_argument("--data", default=DATA)
    ap.add_argument("--seed", type=int, default=0, help="split seed (fit=train)")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        torch.manual_seed(0)
        rng = np.random.default_rng(0)
        # synthetic: true logits are well-calibrated; the "model" reports
        # them 2.5x too hot. The fit must recover T ~= 2.5 and leave the
        # ranking untouched.
        true_lg = torch.tensor(rng.normal(0, 1.5, size=(400, 6, 4, 2))).float()
        y = torch.bernoulli(torch.sigmoid(true_lg))
        hot = true_lg * 2.5
        mask = torch.ones(400, 6, dtype=torch.bool)
        T = fit_temperatures(hot, y, mask)
        assert ((T > 1.8) & (T < 3.4)).all(), f"T off target: {T}"
        a0 = roc_auc(
            torch.sigmoid(hot[:, :, -1, 0]).ravel().numpy(),
            y[:, :, -1, 0].ravel().numpy(),
        )
        a1 = roc_auc(
            torch.sigmoid(hot[:, :, -1, 0] / T[-1, 0]).ravel().numpy(),
            y[:, :, -1, 0].ravel().numpy(),
        )
        assert abs(a0 - a1) < 1e-9, "temperature must not move AUC"
        # bake() must equal logits/T through a real head
        from world_model.collision_head import CollisionHeads
        from world_model.encoder import LATENT_D

        heads = CollisionHeads()
        z = torch.rand(5, len(HORIZONS), LATENT_D)
        ck = {"collision_heads": heads.state_dict(), "meta": {}}
        Tb = torch.full((len(HORIZONS), len(RADII)), 2.0)
        heads2 = CollisionHeads()
        heads2.load_state_dict(bake(ck, Tb)["collision_heads"])
        assert torch.allclose(heads(z) / 2.0, heads2(z), atol=1e-6)
        print(
            f"CALIBRATE OK: recovered T~2.5 (got {T.mean():.2f} mean), "
            f"AUC invariant to 1e-9, baked weights == logits/T"
        )
        return

    if not (args.ckpt and args.out):
        raise SystemExit("--ckpt and --out required (or --selftest)")
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    blob = np.load(args.data)
    data = {k: blob[k] for k in blob.files}
    rng = np.random.default_rng(args.seed)
    tr_rolls, _va = _split_rollouts(data, rng)
    lg, y, m = _logit_stack(args.ckpt, data, tr_rolls, device)
    T = fit_temperatures(lg, y, m)
    ckpt = torch.load(args.ckpt, map_location="cpu", weights_only=True)
    torch.save(bake(ckpt, T), args.out)
    t_str = " ".join(
        f"k{k}:{T[i, 0]:.2f}/{T[i, 1]:.2f}" for i, k in enumerate(HORIZONS)
    )
    print(f"CALIBRATE OK: fitted T (warn/crit per horizon) {t_str}")
    print(f"  fit on {len(tr_rolls)} train rollouts; saved {args.out}")
    print("  (verify ECE/AUC with eval_head_calibration + eval_wm_checkpoint)")


if __name__ == "__main__":
    main()
    sys.exit(0)

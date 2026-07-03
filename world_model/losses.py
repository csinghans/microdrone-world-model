"""The tricks that make latent prediction learnable without a pixel loss.

  * **EMA target encoder** (JEPA/BYOL): the prediction target is produced by
    a slow-moving copy of the encoder, stop-gradient by construction — so the
    latent space cannot chase itself.
  * **Variance guard** (VICReg-style): a hinge on the batch std of z keeps
    the space from collapsing to a constant (the other classic failure).
  * **Train-time appearance jitter** (torch port of the numpy DR): applied to
    the frames the ONLINE encoder sees — never to the EMA target's frames, so
    the JEPA targets stay stable while the encoder learns to shrug off
    appearance.

Plus `roc_auc`, the rank metric every collision claim in this repo is
validated with (0.5 = chance).
"""

import numpy as np
import torch
import torch.nn as nn

EMA_M = 0.99  # target-encoder momentum


@torch.no_grad()
def ema_update(target: nn.Module, online: nn.Module, m: float = EMA_M) -> None:
    """target = m*target + (1-m)*online (stop-gradient by construction)."""
    for pt, po in zip(target.parameters(), online.parameters()):
        pt.mul_(m).add_(po.detach(), alpha=1.0 - m)


def variance_guard(z: torch.Tensor) -> torch.Tensor:
    """Hinge on per-dim batch std: pushes back when the space starts to collapse."""
    return torch.relu(1.0 - z.std(dim=0)).mean()


def augment_torch(x: torch.Tensor) -> torch.Tensor:
    """Brightness 0.5-1.5 + noise sigma<=0.18 + random 3x3 blur, on-device."""
    b = torch.empty(len(x), 1, 1, 1, device=x.device).uniform_(0.5, 1.5)
    s = torch.empty(len(x), 1, 1, 1, device=x.device).uniform_(0.0, 0.18)
    x = x * b + torch.randn_like(x) * s
    blur = torch.rand(len(x), device=x.device) < 0.5
    if bool(blur.any()):
        xb = torch.nn.functional.avg_pool2d(x[blur], 3, stride=1, padding=1)
        x = x.clone()
        x[blur] = xb
    return x.clamp(0.0, 1.0)


def roc_auc(scores: np.ndarray, labels: np.ndarray) -> float:
    """Rank-based AUC (Mann-Whitney U); 0.5 = chance."""
    pos, neg = scores[labels > 0.5], scores[labels < 0.5]
    if len(pos) == 0 or len(neg) == 0:
        return 0.5
    order = np.concatenate([pos, neg]).argsort()
    ranks = np.empty(len(order), dtype=np.float64)
    ranks[order] = np.arange(1, len(order) + 1)
    r_pos = ranks[: len(pos)].sum()
    return float((r_pos - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def selftest() -> None:
    a, b = nn.Linear(4, 4), nn.Linear(4, 4)
    w0 = a.weight.detach().clone()
    ema_update(a, b, m=0.5)
    assert torch.allclose(a.weight, 0.5 * w0 + 0.5 * b.weight), "EMA math off"
    z_flat = torch.zeros(8, 4)
    assert float(variance_guard(z_flat)) == 1.0, "collapse must cost the full hinge"
    x = augment_torch(torch.full((4, 3, 8, 8), 0.5))
    assert x.shape == (4, 3, 8, 8) and 0.0 <= float(x.min()) <= float(x.max()) <= 1.0
    auc = roc_auc(np.array([0.9, 0.8, 0.2, 0.1]), np.array([1, 1, 0, 0]))
    assert auc == 1.0, "AUC of a perfect ranking must be 1.0"
    print("LOSSES OK: EMA, variance hinge, torch jitter, rank AUC assert")


if __name__ == "__main__":
    selftest()

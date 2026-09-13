"""The tricks that make latent prediction learnable without a pixel loss.

  * **EMA target encoder** (JEPA/BYOL): the prediction target is produced by
    a slow-moving copy of the encoder, stop-gradient by construction — so the
    latent space cannot chase itself.
  * **Variance guard** (VICReg-style, two-sided since stability_v1): hinges
    on the batch std of z keep the space from collapsing to a constant (the
    classic failure) AND from inflating without bound (the failure
    perception_v3's 160-epoch run measured: the EMA target chases an
    inflating online encoder, latent scale x13). The band [VAR_LO, VAR_HI]
    is dead — zero loss, zero gradient — at every shipped champion's
    operating point (measured per-dim std <= 2.53 on 2026-08-31).
  * **Train-time appearance jitter** (torch port of the numpy DR): applied to
    the frames the ONLINE encoder sees — never to the EMA target's frames, so
    the JEPA targets stay stable while the encoder learns to shrug off
    appearance.

Plus `roc_auc`, the rank metric every collision claim in this repo is
validated with (0.5 = chance).
"""

import torch
import torch.nn as nn

from world_model.metrics import roc_auc as roc_auc  # preserve the public import
from world_model.metrics import selftest as metrics_selftest

EMA_M = 0.99  # target-encoder momentum


@torch.no_grad()
def ema_update(target: nn.Module, online: nn.Module, m: float = EMA_M) -> None:
    """target = m*target + (1-m)*online (stop-gradient by construction)."""
    for pt, po in zip(target.parameters(), online.parameters()):
        pt.mul_(m).add_(po.detach(), alpha=1.0 - m)


VAR_LO = 1.0  # collapse hinge: per-dim std must not fall below this
VAR_HI = 8.0  # inflation hinge. stability_v1 measured the design rule the
# hard way: a ceiling must clear the RECIPE'S OWN healthy operating point
# (96d128 @ 80 ep: std max 6.44), not just other recipes' (64-res champions
# <= 2.53) — at 4.0 the whole space re-equilibrated onto the lower hinge and
# moving ranking paid 0.054. 8.0 sits above 6.44 and below the measured
# explosion (12.05). Revision pre-registered as stability_v2.


def variance_guard(z: torch.Tensor) -> torch.Tensor:
    """Two-sided hinge on per-dim batch std: pushes back when the space starts
    to collapse (std < VAR_LO) or to inflate (std > VAR_HI)."""
    std = z.std(dim=0)
    return torch.relu(VAR_LO - std).mean() + torch.relu(std - VAR_HI).mean()


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


def selftest() -> None:
    a, b = nn.Linear(4, 4), nn.Linear(4, 4)
    w0 = a.weight.detach().clone()
    ema_update(a, b, m=0.5)
    assert torch.allclose(a.weight, 0.5 * w0 + 0.5 * b.weight), "EMA math off"
    z_flat = torch.zeros(8, 4)
    assert float(variance_guard(z_flat)) == 1.0, "collapse must cost the full hinge"
    torch.manual_seed(0)
    z_ok = torch.randn(64, 4) * 2.0  # inside the [VAR_LO, VAR_HI] band
    assert float(variance_guard(z_ok)) == 0.0, "healthy band must be free"
    z_big = torch.randn(64, 4) * 50.0  # the x13-style explosion
    assert float(variance_guard(z_big)) > 0.0, "inflation must cost too"
    x = augment_torch(torch.full((4, 3, 8, 8), 0.5))
    assert x.shape == (4, 3, 8, 8) and 0.0 <= float(x.min()) <= float(x.max()) <= 1.0
    metrics_selftest()
    print("LOSSES OK: EMA, two-sided variance hinge, torch jitter, tie-aware rank AUC")


if __name__ == "__main__":
    selftest()

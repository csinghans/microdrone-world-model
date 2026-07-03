"""Action-conditioned latent forecaster at every horizon.

z_hat_{t+k} = z_t + delta_k(z_t, a_t) for k in HORIZONS. One shared trunk
reads (z, a); one tiny linear head per horizon emits that horizon's
*residual*. Predicting residuals bakes in the right inductive bias — with a
zero residual it reproduces "the future looks like the present", so any
learned motion can only improve on that baseline.

Why multiple horizons? Because "proactive" is a claim about *time*: to buy
back even a few hundred milliseconds of reaction, the model has to see all
the way out to ~667 ms, not one fixed 167 ms hop. Sharing the trunk means
anticipation at four time scales costs a few extra KB, not a new network.
"""

import torch
import torch.nn as nn

from datasets.intervention_labels import HORIZONS
from world_model.encoder import LATENT_D

ACTION_D = 4  # (vx, vy, vz, yaw-rate), normalised per-dim to ~[-1, 1]


class MultiPredictor(nn.Module):
    def __init__(self, d=LATENT_D, a=ACTION_D, h=128, horizons=HORIZONS):
        super().__init__()
        self.trunk = nn.Sequential(nn.Linear(d + a, h), nn.ReLU())
        self.heads = nn.ModuleList(nn.Linear(h, d) for _ in horizons)

    def forward(self, z, a):  # z: (B,D)  a: (B,A)
        feat = self.trunk(torch.cat([z, a], dim=1))
        return torch.stack([z + head(feat) for head in self.heads], dim=1)  # (B,H,D)


def selftest() -> None:
    pred = MultiPredictor()
    z, a = torch.rand(3, LATENT_D), torch.rand(3, ACTION_D)
    zh = pred(z, a)
    assert zh.shape == (3, len(HORIZONS), LATENT_D)
    # zero every residual head: the forecast must collapse to "future == present"
    for head in pred.heads:
        nn.init.zeros_(head.weight), nn.init.zeros_(head.bias)
    assert torch.allclose(pred(z, a), z.unsqueeze(1).expand(-1, len(HORIZONS), -1))
    print(
        f"PREDICTOR OK: (B,{LATENT_D})x(B,{ACTION_D}) -> "
        f"(B,{len(HORIZONS)},{LATENT_D}), residual baseline holds"
    )


if __name__ == "__main__":
    selftest()

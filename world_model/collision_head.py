"""Latents -> danger logits: the signals a planner actually reads.

`CollisionHeads` reads the *predicted future* latents: one linear layer per
horizon, two logits each — "within 0.7 m within k steps" (the warning) and
"within 0.35 m within k steps" (the about-to-hit). Two rings because one ring
is a region test, not a risk gradient: inside the warn ring every action's
warn label is 1 — including the one that leaves — and the critical ring is
what keeps a planner sighted there.

`DangerNowHead` reads the *current* latent: "dangerously close right now".
That is the reactive signal — same encoder, no look-ahead — kept as the
honest baseline that anticipation must beat in the closed-loop evals.
"""

import torch
import torch.nn as nn

from datasets.intervention_labels import HORIZONS
from sim.scenarios import RADII
from world_model.encoder import LATENT_D


class CollisionHeads(nn.Module):
    def __init__(self, d=LATENT_D, horizons=HORIZONS, radii=RADII):
        super().__init__()
        self.heads = nn.ModuleList(nn.Linear(d, len(radii)) for _ in horizons)

    def forward(self, zh):  # zh: (B, H, D)
        return torch.stack([h(zh[:, i]) for i, h in enumerate(self.heads)], dim=1)


class DangerNowHead(nn.Module):
    def __init__(self, d=LATENT_D):
        super().__init__()
        self.lin = nn.Linear(d, 1)

    def forward(self, z):  # z: (B, D)
        return self.lin(z).squeeze(-1)  # (B,)


def selftest() -> None:
    zh = torch.rand(3, len(HORIZONS), LATENT_D)
    logits = CollisionHeads()(zh)
    assert logits.shape == (3, len(HORIZONS), len(RADII))
    now = DangerNowHead()(torch.rand(3, LATENT_D))
    assert now.shape == (3,)
    print(f"HEADS OK: {len(HORIZONS)} horizons x {len(RADII)} rings + danger-now")


if __name__ == "__main__":
    selftest()

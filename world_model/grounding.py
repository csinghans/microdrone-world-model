"""The metric grounding head: latent -> polar occupancy logits (train-only).

One linear layer from the frame latent to the N_BEAR x N_RANGE grid of
`datasets.metric_labels`. It exists to *pull metric structure into the
latent* during training — at deploy time it is dropped, so it never costs
the 512 KB budget a byte. Whether that pull is worth anything is exactly
what the v0.5 M-gates measure; the head itself takes no position.

Run:
  python -m world_model.grounding      # selftest, asserts
"""

import torch
import torch.nn as nn

from datasets.metric_labels import N_BEAR, N_CELLS, N_RANGE
from world_model.encoder import LATENT_D


class GroundingHead(nn.Module):
    def __init__(self, d=LATENT_D, n_cells=N_CELLS):
        super().__init__()
        self.lin = nn.Linear(d, n_cells)

    def forward(self, z):  # z: (B, D) -> flat cell logits (B, N_CELLS)
        return self.lin(z)


def selftest() -> None:
    head = GroundingHead()
    out = head(torch.rand(3, LATENT_D))
    assert out.shape == (3, N_CELLS)
    kb = sum(p.numel() for p in head.parameters()) / 1024
    print(
        f"GROUNDING OK: {LATENT_D}-d latent -> {N_BEAR}x{N_RANGE} polar cells, "
        f"train-only aux (+{kb:.1f} KB int8, dropped at deploy)"
    )


if __name__ == "__main__":
    selftest()

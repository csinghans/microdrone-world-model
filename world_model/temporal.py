"""Model-side memory: a GRU over per-frame latents.

The FOV limit and the moving world share one root cause: a single frame
cannot carry *where things were* or *how they move*. Policy-side stacks
(12 x 47 numbers) patched this for the policy; this module puts the memory
where the information dies — inside the world model. h_t = GRU(z_1..z_t)
is what the predictor and heads read, so a pillar that slid out of view
stays in the state, and two frames of a crosser reveal its velocity.

Deployment is stateful and cheap: one GRU step per frame (~25 k MACs,
negligible next to the encoder), with the hidden state reset at episode
start — exactly like the policy-side LSTM, but shared by every consumer of
the model.
"""

import torch
import torch.nn as nn

from world_model.encoder import LATENT_D

K_WIN = 8  # training window (~0.67 s @ 12 Hz decisions on 48 Hz frames)


class TemporalEncoder(nn.Module):
    """GRU over frame latents: (B, K, D) -> (B, D) at train time;
    step-by-step with an explicit hidden state at flight time."""

    def __init__(self, d=LATENT_D, hidden=LATENT_D):
        super().__init__()
        self.gru = nn.GRU(d, hidden, batch_first=True)

    def forward(self, z_seq):  # (B, K, D) -> (B, D)
        out, _ = self.gru(z_seq)
        return out[:, -1]

    def step(self, z, h=None):  # (B, D), h -> (B, D), h'
        out, h2 = self.gru(z.unsqueeze(1), h)
        return out[:, -1], h2


def selftest() -> None:
    tenc = TemporalEncoder()
    z_seq = torch.rand(3, K_WIN, LATENT_D)
    h_all = tenc(z_seq)
    assert h_all.shape == (3, LATENT_D)
    # stepping one frame at a time must equal the batched pass
    h, state = None, None
    for k in range(K_WIN):
        h, state = tenc.step(z_seq[:, k], state)
    assert torch.allclose(h, h_all, atol=1e-5), "step() diverges from forward()"
    n = sum(p.numel() for p in tenc.parameters())
    assert n < 40_000, f"GRU ballooned ({n} params)"
    print(f"TEMPORAL OK: GRU({LATENT_D}) {n} params, step==forward, K={K_WIN}")


if __name__ == "__main__":
    selftest()

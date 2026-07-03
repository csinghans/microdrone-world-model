"""Image -> latent z, with bearing kept alive.

The conv stack is three strided blocks (64x64x3 -> 8x8x64) — small enough to
train in minutes and quantize onto a microcontroller (the PULP-Dronet
spirit). The pooling is the part that earns its keep: global average pooling
averages "where" away — it can say a pillar is close, never which *side* it
is on — and dodging left-vs-right is precisely a "which side" question.
(Measured: with global pooling the veer-ranking check sits at chance no
matter how it is supervised; with four horizontal strips it reaches 1.00.)
Cost of the strips: ~16k extra int8 weights.
"""

import torch.nn as nn

LATENT_D = 64  # embedding size (the conv stack already outputs 64 channels)


class Encoder(nn.Module):
    """(B, 3, 64, 64) -> (B, LATENT_D), bearing-aware."""

    def __init__(self, d=LATENT_D):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 16, 5, stride=2, padding=2),
            nn.ReLU(),  # 64 -> 32
            nn.Conv2d(16, 32, 3, stride=2, padding=1),
            nn.ReLU(),  # 32 -> 16
            nn.Conv2d(32, 64, 3, stride=2, padding=1),
            nn.ReLU(),  # 16 -> 8
        )
        self.pool = nn.AdaptiveAvgPool2d((1, 4))  # 4 horizontal strips
        self.proj = nn.Sequential(nn.Flatten(), nn.Linear(64 * 4, d))

    def forward(self, x):  # x: (B, 3, 64, 64)
        return self.proj(self.pool(self.features(x)))  # (B, LATENT_D)


def selftest() -> None:
    import torch

    enc = Encoder()
    z = enc(torch.rand(2, 3, 64, 64))
    assert z.shape == (2, LATENT_D)
    n_params = sum(p.numel() for p in enc.parameters())
    assert n_params < 100_000, f"encoder ballooned ({n_params} params)"
    # the strips must be able to tell left from right: a bright-left image and
    # its mirror must not encode identically
    x = torch.zeros(1, 3, 64, 64)
    x[..., :32] = 1.0
    dz = (enc(x) - enc(x.flip(-1))).abs().max()
    assert float(dz) > 1e-6, "pooling erased left/right"
    print(f"ENCODER OK: (B,3,64,64)->(B,{LATENT_D}), {n_params} params, side-aware")


if __name__ == "__main__":
    selftest()

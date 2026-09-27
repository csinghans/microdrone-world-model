"""Verify shared probe selection and image/action wiring without fitting.

python -m scripts.veer_probe_selftest
"""

import numpy as np
import torch

from planner.action_set import A_NORM, ACTION_VECS
from world_model.temporal import K_WIN
from world_model.training import veer_ranking
from world_model.veer_probe import fixture, select


def selftest():
    data = fixture()
    data["frames"] = np.arange(45, dtype=np.uint8).reshape(5, 3, 1, 1, 3)
    # Input fixture values identify both rollout and time, including t=0
    # clamping; geometry has independently asserted pairs/safer-side truth.
    pairs = [(0, 0), (0, 1), (1, 0), (1, 1)]
    expected = select(data)
    rng_before = torch.get_rng_state().clone()
    for mode in ("single", "two", "memory"):
        captured = []

        def encoder(x):
            captured.append(x.clone())
            return x.mean(dim=(1, 2, 3))[:, None]

        def memory(z):
            captured.append(z.clone())
            return z.sum(dim=1) + 10

        def predictor(z, action, base):
            captured.append((z.clone(), action.clone(), base.clone()))
            # Fixed toy prediction: the right veer is always safer.
            return action[:, 1, None, None].expand(-1, 4, 2)

        sample = {}
        score, count = veer_ranking(
            data,
            range(5),
            encoder,
            predictor,
            lambda z: z,
            "cpu",
            tgru=memory if mode == "memory" else None,
            in_frames=2 if mode == "two" else 1,
            frame_stride=1,
            sample_output=sample,
        )
        assert count == 4 and score == 0.5
        for key in ("veer_pairs", "veer_gt_left", "veer_world_id"):
            assert np.array_equal(sample[key], expected[key])
        assert sample["veer_correct"].tolist() == [True, True, False, False]
        expected_left = torch.sigmoid(torch.full((4,), 0.5)).numpy()
        expected_right = torch.sigmoid(torch.full((4,), -0.5)).numpy()
        assert np.array_equal(sample["veer_score_left"], expected_left)
        assert np.array_equal(sample["veer_score_right"], expected_right)
        if mode == "memory":
            frames = [
                data["frames"][r, max(t - K_WIN + 1 + j, 0)]
                for r, t in pairs
                for j in range(K_WIN)
            ]
        else:
            frames = [
                (
                    np.concatenate(
                        [data["frames"][r, t], data["frames"][r, max(t - 1, 0)]], -1
                    )
                    if mode == "two"
                    else data["frames"][r, t]
                )
                for r, t in pairs
            ]
        x = (
            torch.tensor(np.array(frames), dtype=torch.float32).permute(0, 3, 1, 2)
            / 255
        )
        assert torch.equal(captured[0], x)
        for (z, action, base), aid in zip(captured[-2:], (2, 3)):
            want = torch.tensor(np.tile(ACTION_VECS[aid] / A_NORM, (4, 1)))
            assert torch.equal(action, want)
            if mode == "memory":
                zseq = x.mean(dim=(1, 2, 3)).reshape(4, K_WIN, 1)
                assert torch.equal(base, zseq[:, -1])
                assert torch.equal(z, zseq.sum(dim=1) + 10)
            else:
                assert torch.equal(z, base)
        # Equal danger scores are never silently credited as a correct rank.
        tied = {}
        score, _ = veer_ranking(
            data,
            range(5),
            encoder,
            predictor,
            lambda z: z * 0,
            "cpu",
            sample_output=tied,
        )
        assert score == 0
        assert (tied["veer_score_left"] == 0.5).all()
        assert np.array_equal(tied["veer_score_left"], tied["veer_score_right"])
        assert not tied["veer_correct"].any()

    try:
        veer_ranking(
            data,
            range(5),
            encoder,
            predictor,
            lambda z: z * float("nan"),
            "cpu",
            sample_output={},
        )
    except ValueError as exc:
        assert "nonfinite" in str(exc)
    else:
        raise AssertionError("nonfinite probe probabilities exported")

    def forbidden(*args, **kwargs):
        raise AssertionError("empty probe called a model")

    sample = {}
    score, count = veer_ranking(
        data, [4], forbidden, forbidden, forbidden, "cpu", sample_output=sample
    )
    assert np.isnan(score) and count == 0
    assert sample["veer_pairs"].shape == (0, 2)
    assert sample["veer_correct"].shape == (0,)
    assert sample["veer_score_left"].shape == sample["veer_score_right"].shape == (0,)
    assert torch.equal(torch.get_rng_state(), rng_before)
    print("VEER-PROBE-WIRING OK: one/two/memory frames, actions, ties, empty, no RNG")


if __name__ == "__main__":
    selftest()

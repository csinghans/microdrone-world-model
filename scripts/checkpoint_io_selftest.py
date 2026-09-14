"""Check training entry-point and artifactless-eval persistence without fitting.

python -m scripts.checkpoint_io_selftest
"""

import contextlib
import io
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import torch

from eval import eval_closed_loop
from scripts.dataset_identity_selftest import train_fixture
from scripts.train import train_world_model, world_model_output


def selftest():
    with tempfile.TemporaryDirectory(prefix="checkpoint_entry_selftest_") as tmp:
        root = Path(tmp).resolve()
        champion = root / "world_model.pth"
        (root / "artifacts.lock.json").write_text(
            json.dumps(
                {
                    "artifacts": [
                        {"dest": "world_model.pth"},
                        {"dest": "world_model_unified.pth"},
                    ]
                }
            )
        )
        champion.write_bytes(b"synthetic champion sentinel")
        args = SimpleNamespace(
            temporal=False,
            ground=False,
            two_frame=False,
            selftest=False,
            epochs=1,
            data=None,
            strips=None,
            latent_d=None,
            batch=2,
            seed=0,
            robust=False,
            ground_lambda=0.5,
            cf_hard_pool="legacy_masked",
            executed_moving_weight=1.0,
            out=None,
        )
        data = {"frames": np.zeros((1, 1, 2, 2, 3), dtype=np.uint8)}
        with (
            patch("world_model.checkpoint_io.ROOT", root),
            patch("scripts.train.MODEL", str(champion)),
            patch("scripts.train._load_or_make", return_value=data) as load,
            patch("scripts.train.train", side_effect=train_fixture) as fit,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            output = root / "world_model_candidate.pth"
            assert world_model_output(args) == output
            train_world_model(args)
            assert (
                output.exists()
                and champion.read_bytes() == b"synthetic champion sentinel"
            )
            load.reset_mock()
            fit.reset_mock()
            for target in (None, str(champion), str(root / "world_model_unified.pth")):
                args.out = target
                try:
                    train_world_model(args)
                except (ValueError, FileExistsError):
                    pass
                else:
                    raise AssertionError("existing/locked path reached fitting")
                load.assert_not_called()
                fit.assert_not_called()
            args.out = str(root / "new_candidate.pth")
            train_world_model(args)
            assert Path(args.out).exists()
            # Selftest paths ignore --out, remain replaceable and never reserve
            # the user's explicitly named champion path for writing.
            args.selftest, args.out = True, str(champion)
            assert world_model_output(args).name == "world_model_selftest.pth"

        # Artifactless evals retain a reusable, labelled tiny model, while the
        # real champion path stays absent. Scoped dry gates still get the
        # exact *_selftest* file they hash in their provenance.
        champion.unlink()

        def fake_load(path, device):
            return (None,) * 4 + (torch.load(path, weights_only=True)["meta"],)

        with (
            patch("world_model.checkpoint_io.ROOT", root),
            patch.object(eval_closed_loop, "MODEL", str(champion)),
            patch.object(
                eval_closed_loop, "train", return_value=({"meta": {}}, {})
            ) as fit,
            patch.object(eval_closed_loop, "load_model", side_effect=fake_load),
            patch("datasets.generate_rollouts.gen", return_value={}) as gen,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            for _ in range(2):
                assert eval_closed_loop.load_or_train()[-1]["autotrained_tiny"]
                assert not champion.exists()
            assert fit.call_count == gen.call_count == 1
            standin = root / "world_model_autotrained_selftest.pth"
            assert standin.exists()
            dry_path = root / "dry/world_model_selftest.pth"
            with patch.object(eval_closed_loop, "MODEL", str(dry_path)):
                assert eval_closed_loop.load_or_train()[-1]["autotrained_tiny"]
                assert dry_path.exists()
            assert fit.call_count == 2
            from scripts import research

            experiment = root / "experiments/dry_selftest"
            with patch.object(research, "ROOT", str(root)):
                with research._world_model_scope(str(experiment), True) as receipt:
                    assert "_selftest" in receipt["path"]
                    assert (root / receipt["path"]).exists()
                    assert len(receipt["sha256"]) == 64
            assert not (root / "output/world_model.pth").exists()
            assert fit.call_count == 3
    print(
        "CHECKPOINT-ENTRY OK: early rejection, candidate save, "
        "reusable/scoped stand-ins"
    )


if __name__ == "__main__":
    selftest()

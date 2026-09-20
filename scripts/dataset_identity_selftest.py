"""Exercise dataset identity across training, probe API/CLI and comparison.

    python -m scripts.dataset_identity_selftest

Synthetic fixtures replace fitting/scoring; no real checkpoint is touched.
"""

import contextlib
import io
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import torch

from datasets.provenance import file_identity
from eval.eval_wm_checkpoint import evaluate
from eval.eval_wm_checkpoint import main as probe_main
from scripts.train import _load_or_make, train_world_model


def train_fixture(data, **kwargs):
    return {"meta": {"seed": kwargs["seed"]}}, {
        "n_train": 1,
        "mse": [0.1],
        "noop": [0.2],
        "zstd_med": 1,
        "zstd_max": 1,
        "zabs": 1,
        "auc": [0.5],
        "now_auc": 0.5,
        "side": 0.5,
        "n_side": 1,
        "int8_kb": 1,
    }


def selftest():
    with tempfile.TemporaryDirectory(prefix="dataset_identity_selftest_") as tmp:
        directory = Path(tmp)
        source = directory / "training_selftest.npz"
        values = np.arange(12, dtype=np.uint8).reshape(1, 1, 2, 2, 3)
        np.savez(source, frames=values)
        identity = file_identity(source)
        args = SimpleNamespace(
            temporal=False,
            ground=False,
            two_frame=False,
            selftest=False,
            epochs=1,
            data=str(source),
            strips=None,
            latent_d=None,
            batch=2,
            seed=0,
            robust=False,
            ground_lambda=0.5,
            cf_hard_pool="legacy_masked",
            executed_moving_weight=1.0,
            out=str(directory / "world_model_identity_selftest.pth"),
        )
        with patch("scripts.train.train", side_effect=train_fixture) as fit:
            with contextlib.redirect_stdout(io.StringIO()):
                train_world_model(args)
            assert np.array_equal(fit.call_args.args[0]["frames"], values)
        saved = torch.load(args.out, weights_only=True)
        assert saved["meta"]["training_dataset_sha256"] == identity["sha256"]

        # A source file changed during fitting must never get a false hash
        # attached to a published checkpoint.
        args.out = str(directory / "changed_source_selftest.pth")

        def change_source(data, **kwargs):
            np.savez(source, frames=values + 1)
            return train_fixture(data, **kwargs)

        with patch("scripts.train.train", side_effect=change_source):
            try:
                train_world_model(args)
            except ValueError as exc:
                assert "changed during fitting" in str(exc)
            else:
                raise AssertionError("changed source published a checkpoint")
        assert not Path(args.out).exists()
        # Detect source replacement during the load itself, before fitting.
        with patch(
            "scripts.train.file_identity",
            side_effect=[identity, {**identity, "sha256": "changed"}],
        ):
            try:
                _load_or_make(False, str(source), {})
            except ValueError as exc:
                assert "while loading" in str(exc)
            else:
                raise AssertionError("dataset changed during load was accepted")

        current = file_identity(source)
        meta = {"seed": 0, "training_dataset_sha256": current["sha256"]}
        model = directory / "probe_identity_selftest.pth"
        model.write_bytes(b"mock checkpoint; no model inference in this selftest")
        with (
            patch(
                "eval.eval_wm_checkpoint.load_model", return_value=(None,) * 4 + (meta,)
            ),
            patch(
                "eval.eval_wm_checkpoint.evaluate_components", return_value={}
            ) as score,
        ):
            try:
                evaluate(
                    str(model),
                    {},
                    independent_holdout=True,
                    dataset_sha256=current["sha256"],
                    device="cpu",
                )
            except ValueError as exc:
                assert "identical SHA-256" in str(exc)
            else:
                raise AssertionError("API scored a known training corpus as holdout")
            score.assert_not_called()

            out, samples = directory / "scores.json", directory / "scores.npz"
            with patch(
                "sys.argv",
                [
                    "eval.eval_wm_checkpoint",
                    "--ckpt",
                    str(model),
                    "--data",
                    str(source),
                    "--independent-holdout",
                    "--out",
                    str(out),
                    "--scores-out",
                    str(samples),
                ],
            ):
                try:
                    probe_main()
                except SystemExit as exc:
                    assert "identical SHA-256" in str(exc)
                else:
                    raise AssertionError("CLI forgot to pass the dataset identity")
            score.assert_not_called()
            assert not out.exists() and not samples.exists()

            # A known different file must also fail in original-validation
            # mode. Even the same numerical seed does not establish the same
            # split after a corpus is reordered. Recompression likewise lacks
            # exact-file identity; it is not an independently generated exam.
            repacked = directory / "repacked_training_selftest.npz"
            np.savez_compressed(repacked, frames=values + 1)
            repacked_sha = file_identity(repacked)["sha256"]
            assert repacked_sha != current["sha256"]
            try:
                evaluate(
                    str(model),
                    {},
                    dataset_sha256=repacked_sha,
                    device="cpu",
                )
            except ValueError as exc:
                assert "SHA-256 mismatch" in str(exc)
            else:
                raise AssertionError("different file scored as original validation")
            with patch(
                "sys.argv",
                [
                    "eval.eval_wm_checkpoint",
                    "--ckpt",
                    str(model),
                    "--data",
                    str(repacked),
                    "--out",
                    str(out),
                    "--scores-out",
                    str(samples),
                ],
            ):
                try:
                    probe_main()
                except SystemExit as exc:
                    assert "SHA-256 mismatch" in str(exc)
                else:
                    raise AssertionError("CLI accepted wrong original-validation file")
            score.assert_not_called()
            assert not out.exists() and not samples.exists()

            result = evaluate(
                str(model), {}, dataset_sha256=current["sha256"], device="cpu"
            )
            assert result["dataset_file_relation"] == "same_as_training"
            assert (
                score.call_count == 1
            ), "ordinary training-validation must remain valid"
            result = evaluate(
                str(model),
                {},
                independent_holdout=True,
                dataset_sha256="a" * 64,
                device="cpu",
            )
            assert score.call_count == 2
            assert result["dataset_file_relation"] == "different_from_training"
            # The in-memory API does not acquire identity merely because its
            # checkpoint has one. Legacy callers remain supported and visible.
            warning = io.StringIO()
            with contextlib.redirect_stderr(warning):
                result = evaluate(str(model), {}, device="cpu")
            assert result["dataset_file_relation"] == "unverified"
            assert "file identity unverified" in warning.getvalue()
            assert score.call_count == 3
            meta.pop("training_dataset_sha256")
            warning = io.StringIO()
            with contextlib.redirect_stderr(warning):
                result = evaluate(
                    str(model), {}, dataset_sha256=current["sha256"], device="cpu"
                )
            assert result["dataset_file_relation"] == "unverified"
            assert "file identity unverified" in warning.getvalue()
            result = evaluate(
                str(model),
                {},
                independent_holdout=True,
                dataset_sha256=current["sha256"],
                device="cpu",
            )
            assert (
                score.call_count == 5
            ), "legacy caller assertion must remain supported"
            assert result["dataset_file_relation"] == "unverified"
    # Same index split on reordered data selects different physical courses.
    # This is a split-only fixture: no training, pixels or scoring.
    from world_model.training import _split_rollouts

    rolls = {
        "frames": np.zeros((12, 1, 0, 0, 3), dtype=np.uint8),
        "world_id": np.zeros(12, dtype=np.int16),
        "in_path": np.ones(12, dtype=bool),
        "seg": np.zeros((12, 1), dtype=np.int16),
    }
    original = np.arange(12)
    order = np.roll(original, 1)
    _, val = _split_rollouts(rolls, np.random.default_rng(7))
    _, val_reordered = _split_rollouts(
        {key: value[order] for key, value in rolls.items()}, np.random.default_rng(7)
    )
    assert val == val_reordered
    assert set(original[val]) != set(order[val_reordered])
    print(
        "DATASET-IDENTITY OK: training provenance, source mutation, API/CLI "
        "reject holdout reuse and validation mismatch before scoring/writing, "
        "known/unknown file relation, reordered-course split, legacy compatibility"
    )


if __name__ == "__main__":
    selftest()

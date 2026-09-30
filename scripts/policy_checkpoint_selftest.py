"""Policy output/CLI regressions and real SB3 serialization, without learning.

python -m scripts.policy_checkpoint_selftest
"""

import contextlib
import io
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import gymnasium as gym
import torch

from planner import learned_policy as policy
from scripts.train import train_policy
from world_model.checkpoint_io import publish_checkpoint


def selftest():
    with tempfile.TemporaryDirectory(prefix="policy_checkpoint_selftest_") as tmp:
        root = Path(tmp).resolve()
        champion = root / "output/ppo_wm_policy_edge_hard_xp.zip"
        champion.parent.mkdir()
        champion.write_bytes(b"synthetic champion")
        (root / "artifacts.lock.json").write_text(
            json.dumps(
                {"artifacts": [{"dest": "output/ppo_wm_policy_edge_hard_xp.zip"}]}
            )
        )
        with (
            patch("world_model.checkpoint_io.ROOT", root),
            patch.object(policy, "_ROOT", str(root)),
            patch("stable_baselines3.common.env_util.make_vec_env") as factory,
            patch("stable_baselines3.PPO") as ppo,
            patch("sb3_contrib.RecurrentPPO") as rppo,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            default = policy.training_path(edge_bias=True, hard=True, x_progress=True)
            assert Path(default).name == "ppo_wm_policy_edge_hard_xp_candidate.zip"
            assert policy.zip_path(edge=True, hard=True, xp=True) == str(champion)
            existing = root / "existing.zip"
            existing.write_bytes(b"previous research result")
            for out, recurrent in (
                (champion, False),
                (existing, False),
                (root / "missing_suffix", False),
                (root / "rnn.zip", True),
                (root / "unexpected_recurrent.zip", False),
            ):
                try:
                    policy.train(1, out=str(out), recurrent=recurrent)
                except (ValueError, FileExistsError):
                    pass
                else:
                    raise AssertionError("invalid output reached training")
            factory.assert_not_called()
            ppo.assert_not_called()
            rppo.assert_not_called()
            recurrent_existing = root / "existing_recurrent.zip"
            recurrent_existing.write_bytes(b"previous recurrent result")
            try:
                policy.train_curriculum(7, out=str(recurrent_existing))
            except FileExistsError:
                pass
            else:
                raise AssertionError("curriculum overwrote existing output")
            factory.assert_not_called()

            # Exact recipe arguments and all three curriculum chunks survive
            # the persistence refactor. Models/environments are test doubles.
            def archive(stream):
                stream.write(b"synthetic policy archive")

            ppo.return_value.save.side_effect = archive
            policy.train(7, seed0=13, edge_bias=True, hard=True, x_progress=True)
            assert Path(default).read_bytes() == b"synthetic policy archive"
            ppo.assert_called_once_with(
                "MlpPolicy", factory.return_value, ent_coef=0.01, seed=13, verbose=0
            )
            ppo.return_value.learn.assert_called_once_with(total_timesteps=7)
            factory.return_value.close.assert_called_once()
            factory.reset_mock()
            rppo.return_value.save.side_effect = archive
            policy.train(
                5,
                seed0=13,
                recurrent=True,
                out=str(root / "train_recurrent.zip"),
                n_steps=32,
                lstm_size=16,
            )
            rppo.assert_called_once_with(
                "MlpLstmPolicy",
                factory.return_value,
                ent_coef=0.01,
                n_steps=32,
                policy_kwargs={"lstm_hidden_size": 16},
                seed=13,
                verbose=0,
            )
            rppo.return_value.learn.assert_called_once_with(total_timesteps=5)
            factory.return_value.close.assert_called_once()
            factory.reset_mock()
            rppo.reset_mock()
            recurrent = root / "new_recurrent.zip"
            policy.train_curriculum(
                7, seed0=13, out=str(recurrent), n_steps=32, lstm_size=16
            )
            rppo.assert_called_once_with(
                "MlpLstmPolicy",
                factory.return_value,
                ent_coef=0.01,
                n_steps=32,
                policy_kwargs={"lstm_hidden_size": 16},
                seed=13,
                verbose=0,
            )
            assert [c.kwargs for c in rppo.return_value.learn.call_args_list] == [
                {"total_timesteps": 2, "reset_num_timesteps": False},
                {"total_timesteps": 2, "reset_num_timesteps": False},
                {"total_timesteps": 3, "reset_num_timesteps": False},
            ]
            assert [c.args for c in factory.return_value.env_method.call_args_list] == [
                ("set_edge_p", 0.0),
                ("set_edge_p", 0.5),
                ("set_edge_p", 0.25),
            ]
            factory.return_value.close.assert_called_once()

            for failure in ("learn", "save"):
                factory.reset_mock()
                ppo.return_value.learn.side_effect = None
                ppo.return_value.save.side_effect = archive
                getattr(ppo.return_value, failure).side_effect = RuntimeError(
                    "synthetic"
                )
                failed = root / f"failed_{failure}.zip"
                try:
                    policy.train(1, out=str(failed))
                except RuntimeError:
                    pass
                else:
                    raise AssertionError("failure swallowed")
                factory.return_value.close.assert_called_once()
                assert not failed.exists()
            assert not list(root.glob(".*.tmp"))
            factory.reset_mock()
            ppo.side_effect = RuntimeError("synthetic constructor failure")
            try:
                policy.train(1, out=str(root / "failed_constructor.zip"))
            except RuntimeError:
                pass
            else:
                raise AssertionError("constructor failure swallowed")
            factory.return_value.close.assert_called_once()
            ppo.side_effect = None

            args = SimpleNamespace(
                selftest=False,
                curriculum=False,
                out=str(root / "cli.zip"),
                timesteps=9,
                seed=0,
                recurrent=False,
                randomize=False,
                edge_bias=True,
                worlds="hard",
                x_progress=True,
                n_steps=32,
                lstm_size=16,
            )
            with patch.object(policy, "train") as train:
                train_policy(args)
                assert train.call_args.kwargs["out"] == args.out
            args.curriculum, args.out = True, str(root / "cli_recurrent.zip")
            args.worlds, args.edge_bias, args.x_progress = "classic", False, False
            with patch.object(policy, "train_curriculum") as curriculum:
                train_policy(args)
                assert curriculum.call_args.kwargs["out"] == args.out
            args.selftest = True
            with patch.object(policy, "selftest") as smoke:
                train_policy(args)
                smoke.assert_called_once_with()
            assert champion.read_bytes() == b"synthetic champion"
            assert existing.read_bytes() == b"previous research result"

        # Real library contract: save/load both architectures through the
        # binary stream (no PPO learn call and no drone environment).
        from sb3_contrib import RecurrentPPO
        from stable_baselines3 import PPO

        with gym.make("CartPole-v1") as env:
            for cls, name, extra in (
                (PPO, "MlpPolicy", {}),
                (
                    RecurrentPPO,
                    "MlpLstmPolicy",
                    {"policy_kwargs": {"lstm_hidden_size": 8}},
                ),
            ):
                model = cls(name, env, n_steps=8, batch_size=8, device="cpu", **extra)
                suffix = "_recurrent" if cls is RecurrentPPO else ""
                path = root / f"roundtrip{suffix}_selftest.zip"
                publish_checkpoint(path, model.save)
                loaded = policy.load_policy(str(path))
                assert type(loaded) is cls
                assert all(
                    torch.equal(value, loaded.policy.state_dict()[key])
                    for key, value in model.policy.state_dict().items()
                )
    print("POLICY-CHECKPOINT OK: preflight, CLI, recipes, cleanup, PPO/LSTM roundtrips")


if __name__ == "__main__":
    selftest()

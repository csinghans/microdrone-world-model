"""Check policy CLI seeds/worlds through parsing and constructors, without fitting.

python -m scripts.policy_recipe_selftest
"""

import contextlib
import io
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from planner import learned_policy as policy
from scripts.train import main
from sim import scenario_registry


def invoke(*flags):
    output = io.StringIO()
    with (
        patch("sys.argv", ["scripts.train", "--policy", *flags]),
        contextlib.redirect_stdout(output),
    ):
        main()
    return output.getvalue()


def selftest():
    with tempfile.TemporaryDirectory(prefix="policy_recipe_selftest_") as tmp:
        root = Path(tmp).resolve()
        (root / "artifacts.lock.json").write_text(json.dumps({"artifacts": []}))
        probe = scenario_registry.ScenarioSpec("recipe_probe", 99, Mock())
        with (
            patch("world_model.checkpoint_io.ROOT", root),
            patch.object(policy, "_ROOT", str(root)),
            patch.dict(scenario_registry._REGISTRY, {probe.name: probe}),
        ):
            # Invoke the real parser, preserving default/preset filenames while
            # retaining the order and multiplicity of explicit world lists.
            cases = (
                ([], 0, False, None, "ppo_wm_policy_candidate.zip"),
                (["--seed", "17"], 17, False, None, "ppo_wm_policy_candidate.zip"),
                (
                    ["--worlds", "hard"],
                    0,
                    True,
                    None,
                    "ppo_wm_policy_hard_candidate.zip",
                ),
                (
                    ["--seed", "17", "--worlds", "moving, dense,moving"],
                    17,
                    False,
                    ("moving", "dense", "moving"),
                    "weighted.zip",
                ),
                (["--worlds", "moving"], 0, False, ("moving",), "moving.zip"),
                (
                    ["--worlds", "classic,recipe_probe"],
                    0,
                    False,
                    ("classic", "recipe_probe"),
                    "registered.zip",
                ),
            )
            for flags, seed, hard, worlds, filename in cases:
                if worlds is not None:
                    flags = [*flags, "--out", str(root / filename)]
                with (
                    patch.object(policy, "train") as train,
                    patch.object(policy, "train_curriculum") as curriculum,
                ):
                    log = invoke(*flags)
                train.assert_called_once()
                curriculum.assert_not_called()
                kw = train.call_args.kwargs
                assert (kw["seed0"], kw["hard"], kw["worlds"]) == (seed, hard, worlds)
                assert Path(kw["out"]).name == filename
                actual = worlds or (
                    ("classic", "dense", "moving") if hard else ("classic",)
                )
                assert f"seed={seed}, worlds={','.join(actual)}" in log

            for flags, seed in (([], 0), (["--seed", "17", "--recurrent"], 17)):
                with (
                    patch.object(policy, "train") as train,
                    patch.object(policy, "train_curriculum") as curriculum,
                ):
                    log = invoke("--curriculum", *flags)
                train.assert_not_called()
                curriculum.assert_called_once()
                assert curriculum.call_args.kwargs["seed0"] == seed
                assert f"seed={seed}, worlds=classic" in log

            # Invalid recipes must fail before even choosing a destination.
            invalid = (
                (["--worlds", "unknown_world"], "unknown world"),
                (["--worlds", " , "], "at least one"),
                (["--worlds", "moving,dense"], "requires --out"),
                (["--curriculum", "--worlds", "hard"], "curriculum requires classic"),
                (["--curriculum", "--randomize"], "--randomize"),
                (["--curriculum", "--edge-bias"], "--edge-bias"),
                (["--curriculum", "--x-progress"], "--x-progress"),
            )
            for flags, message in invalid:
                with (
                    patch.object(policy, "training_path") as destination,
                    patch.object(policy, "train") as train,
                    patch.object(policy, "train_curriculum") as curriculum,
                ):
                    try:
                        invoke(*flags)
                    except (ValueError, KeyError) as exc:
                        assert message in str(exc)
                    else:
                        raise AssertionError(f"invalid recipe accepted: {flags}")
                destination.assert_not_called()
                train.assert_not_called()
                curriculum.assert_not_called()

            # Follow all three routes through the real training functions to
            # the environment and PPO constructors. Only the library objects
            # and drone environment are doubles; no optimizer or simulator runs.
            routes = (
                ([], False, ("classic",)),
                (
                    ["--recurrent", "--worlds", "moving,dense,moving"],
                    True,
                    ("moving", "dense", "moving"),
                ),
                (["--curriculum"], True, ("classic",)),
            )
            for index, (flags, recurrent, worlds) in enumerate(routes):
                vector = Mock()

                def make_vector(creator, **kwargs):
                    assert kwargs == {"n_envs": 1}
                    creator()
                    return vector

                def save(stream):
                    stream.write(b"synthetic archive; no optimizer")

                suffix = "_recurrent" if recurrent else ""
                path = root / f"route{index}{suffix}_selftest.zip"
                with (
                    patch.object(policy, "WMPolicyEnv") as env,
                    patch(
                        "stable_baselines3.common.env_util.make_vec_env",
                        side_effect=make_vector,
                    ),
                    patch("stable_baselines3.PPO") as ppo,
                    patch("sb3_contrib.RecurrentPPO") as rppo,
                ):
                    ppo.return_value.save.side_effect = save
                    rppo.return_value.save.side_effect = save
                    invoke(
                        "--seed", "17", "--timesteps", "7", "--out", str(path), *flags
                    )
                model = rppo if recurrent else ppo
                unused = ppo if recurrent else rppo
                model.assert_called_once()
                unused.assert_not_called()
                assert model.call_args.kwargs["seed"] == 17
                env.assert_called_once()
                assert env.call_args.kwargs["seed0"] == 17
                assert env.call_args.kwargs.get("worlds", ("classic",)) == worlds
                assert env.call_args.kwargs["history"] == (
                    1 if recurrent else policy.HISTORY
                )
                vector.close.assert_called_once()
                assert path.read_bytes() == b"synthetic archive; no optimizer"
            probe.spawn.assert_not_called()
    print("POLICY-RECIPE OK: CLI seeds/worlds, curriculum refusal, constructor routing")


if __name__ == "__main__":
    selftest()

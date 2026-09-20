"""Policy-cell identity/publication tests using synthetic inputs, without flights.

python -m scripts.policy_eval_selftest
"""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from datasets.provenance import file_identity
from eval import eval_policy_cells as probe
from scripts import research


class PolicyEvalIntegrity(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="policy_eval_selftest_")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.wm, self.zip = self.root / "wm.pth", self.root / "policy.zip"
        self.spec, self.out = self.root / "cells.json", self.root / "results.json"
        self.wm.write_bytes(b"synthetic WM")
        self.zip.write_bytes(b"synthetic policy")
        (self.root / "artifacts.lock.json").write_text(
            json.dumps({"artifacts": [{"dest": "wm.pth"}]})
        )
        self.rows = [
            dict(id="dense", world="dense", speed=1.0, n=2, seed0=7),
            dict(
                id="guard",
                world=None,
                speed=2.0,
                n=3,
                seed0=11,
                kwargs={"solo": True, "in_path": True},
                role="guard",
            ),
        ]
        self.spec.write_text(json.dumps(self.rows))
        self.env = Mock()
        self.factory = self.start(patch("scripts.research._policy_factory"))
        self.fly = self.start(
            patch("scripts.research.run_cell", side_effect=self.result)
        )
        self.make_env = self.start(patch("sim.envs.make_env", return_value=self.env))
        self.start(patch("world_model.checkpoint_io.ROOT", self.root))

    def start(self, patcher):
        value = patcher.start()
        self.addCleanup(patcher.stop)
        return value

    @staticmethod
    def result(factory, cell, judge, env, n=None, seed0=None):
        return dict(
            n=cell.n_seeds if n is None else n,
            seed0=cell.seed0 if seed0 is None else seed0,
            crash=0.0,
            success=1.0,
            reached=1.0,
            clearance_mean=1.25,
            custom={},
        )

    def cli(self, *extra, default_wm=False):
        argv = [
            "eval.eval_policy_cells",
            "--zip",
            str(self.zip),
            "--cells",
            str(self.spec),
            "--out",
            str(self.out),
            *extra,
        ]
        if not default_wm:
            argv.extend(["--wm", str(self.wm)])
        with patch("sys.argv", argv), contextlib.redirect_stdout(io.StringIO()):
            probe.main()

    def test_record_keeps_metrics_and_identifies_all_inputs(self):
        self.cli()
        record = json.loads(self.out.read_text())
        self.assertEqual(record["schema_version"], 2)
        self.assertEqual(record["zip"], str(self.zip))
        for name, path in (
            ("world_model", self.wm),
            ("policy", self.zip),
            ("cell_spec", self.spec),
        ):
            self.assertEqual(record["provenance"][name], file_identity(path))
        self.assertEqual(set(record["cells"]), {"dense", "guard"})
        self.assertEqual(record["cells"]["guard"]["n"], 3)
        self.assertEqual(record["cells"]["guard"]["seed0"], 11)
        selected = record["evaluation"]["cells"]
        self.assertEqual(selected[1]["kwargs"], {"solo": True, "in_path": True})
        self.assertEqual(selected[1]["role"], "guard")
        self.assertEqual(record["judge"], {"kind": "reached_and_clean_shim"})
        self.assertTrue(record["runtime"]["torch"])
        self.factory.assert_called_once_with(str(self.zip), wm_path=str(self.wm))
        self.env.close.assert_called_once()
        self.assertTrue(probe.SHIM.success({"reached": True, "crashed": False}))
        self.assertFalse(probe.SHIM.success({"reached": True, "crashed": True}))

    def test_overrides_and_skill_judge_are_explicit(self):
        judge = SimpleNamespace(name="synthetic", version="v1")
        with patch("skills.base.load_skill", return_value=judge):
            self.cli(
                "--only",
                "guard",
                "--n",
                "60",
                "--seed0",
                "1000",
                "--skill",
                "synthetic",
            )
        record = json.loads(self.out.read_text())
        self.assertEqual(
            record["judge"], {"kind": "skill", "name": "synthetic", "version": "v1"}
        )
        self.assertEqual(list(record["cells"]), ["guard"])
        self.assertEqual(record["cells"]["guard"]["n"], 60)
        self.assertEqual(record["cells"]["guard"]["seed0"], 1000)
        self.assertEqual(record["evaluation"]["cells"][0]["n"], 60)
        self.assertEqual(record["evaluation"]["cells"][0]["seed0"], 1000)
        self.assertIs(self.fly.call_args.args[2], judge)

    def test_named_baseline_needs_no_zip(self):
        self.zip.unlink()
        self.cli("--zip", "builtin:reactive")
        record = json.loads(self.out.read_text())
        self.assertEqual(record["zip"], "builtin:reactive")
        self.assertNotIn("policy", record["provenance"])

    def test_existing_and_locked_outputs_rejected_before_loading(self):
        self.out.write_bytes(b"previous result")
        with self.assertRaises(FileExistsError):
            self.cli()
        self.assertEqual(self.out.read_bytes(), b"previous result")
        with self.assertRaisesRegex(ValueError, "locked artifact"):
            self.cli("--out", str(self.wm))
        self.factory.assert_not_called()
        self.make_env.assert_not_called()

    def test_bad_specs_and_overrides_fail_before_loading(self):
        changes = [
            dict(id=""),
            dict(n=0),
            dict(n=1.5),
            dict(seed0=-1),
            dict(seed0=True),
            dict(speed=0),
            dict(speed=float("nan")),
            dict(role="oops"),
            dict(world="unknown"),
            dict(kwargs=[]),
            dict(kwargs={"randomize": True}),
            dict(world=None, kwargs={"unsupported": True}),
            dict(world=None, kwargs={"solo": "false"}),
            dict(world=None, kwargs={"tmax": 0}),
        ]
        specs = [[], {}, [self.rows[0], self.rows[0]]]
        specs += [[{**self.rows[0], **change}] for change in changes]
        for spec in specs:
            with self.subTest(spec=spec):
                self.spec.write_text(json.dumps(spec))
                with self.assertRaises((ValueError, KeyError)):
                    self.cli()
        self.spec.write_text(json.dumps(self.rows))
        for flags in (
            ("--n", "0"),
            ("--seed0", "-1"),
            ("--only", "unknown"),
            ("--zip", "builtin:unknown"),
        ):
            with self.subTest(flags=flags), self.assertRaises((ValueError, SystemExit)):
                self.cli(*flags)
        self.factory.assert_not_called()
        self.make_env.assert_not_called()
        self.assertFalse(self.out.exists())

    def test_missing_world_model_does_not_reach_fallback(self):
        with patch("world_model.training.MODEL", str(self.wm)):
            self.cli(default_wm=True)
        self.factory.assert_called_once_with(str(self.zip), wm_path=str(self.wm))
        self.out.unlink()
        self.factory.reset_mock()
        self.make_env.reset_mock()
        self.wm.unlink()
        for default_wm in (False, True):
            with (
                patch("world_model.training.MODEL", str(self.wm)),
                self.assertRaises(FileNotFoundError),
            ):
                self.cli(default_wm=default_wm)
        self.factory.assert_not_called()
        self.make_env.assert_not_called()

    def test_input_change_during_load_stops_before_flying(self):
        def changed(*args, **kwargs):
            self.wm.write_bytes(b"changed while loading")
            return Mock()

        self.factory.side_effect = changed
        with self.assertRaisesRegex(ValueError, "inputs changed"):
            self.cli()
        self.make_env.assert_not_called()
        self.assertFalse(self.out.exists())

    def test_each_changed_input_blocks_publication(self):
        for path in (self.wm, self.zip, self.spec):
            original = path.read_bytes()

            def changed(*args, **kwargs):
                path.write_bytes(b"changed during evaluation")
                return self.result(*args, **kwargs)

            self.fly.side_effect = changed
            self.env.close.reset_mock()
            with (
                self.subTest(path=path),
                self.assertRaisesRegex(ValueError, "inputs changed"),
            ):
                self.cli()
            self.env.close.assert_called_once()
            self.assertFalse(self.out.exists())
            path.write_bytes(original)

    def test_failed_or_nonfinite_flight_closes_without_record(self):
        self.fly.side_effect = RuntimeError("synthetic flight failure")
        with self.assertRaisesRegex(RuntimeError, "synthetic"):
            self.cli()
        self.env.close.assert_called_once()
        self.assertFalse(self.out.exists())
        self.env.close.reset_mock()

        def nonfinite(*args, **kwargs):
            return {**self.result(*args, **kwargs), "custom": {"bad": float("nan")}}

        self.fly.side_effect = nonfinite
        with self.assertRaises(ValueError):
            self.cli()
        self.env.close.assert_called_once()
        self.assertFalse(self.out.exists())

    def test_concurrent_result_is_never_replaced(self):
        def competing(*args, **kwargs):
            self.out.write_bytes(b"concurrent result")
            return self.result(*args, **kwargs)

        self.fly.side_effect = competing
        with self.assertRaises(FileExistsError):
            self.cli()
        self.assertEqual(self.out.read_bytes(), b"concurrent result")
        self.assertFalse(list(self.root.glob(".*.tmp")))
        self.env.close.assert_called_once()


class ExplicitWorldModel(unittest.TestCase):
    def test_factory_routes_loaded_components_and_preserves_legacy_default(self):
        components = (object(), object(), object(), object(), {})
        enc, pred, heads, now, meta = components
        with (
            patch("world_model.training.load_model", return_value=components) as load,
            patch(
                "eval.eval_closed_loop.load_or_train", return_value=components
            ) as fallback,
            patch("planner.learned_policy.load_policy") as policy,
            patch("planner.learned_policy.LearnedPolicy") as learned,
            patch("planner.latent_mpc.ReactivePolicy") as reactive,
            patch("planner.latent_mpc.WMPolicy") as mpc,
        ):
            for name in ("candidate.zip", "builtin:reactive", "builtin:wm_mpc"):
                factory = research._policy_factory(name, wm_path="candidate.pth")
                factory(0.6)
            self.assertEqual(load.call_count, 3)
            load.assert_called_with("candidate.pth", device="cpu")
            fallback.assert_not_called()
            policy.assert_called_once_with("candidate.zip")
            learned.assert_called_once_with(
                policy.return_value, enc, pred, heads, meta, speed=0.6
            )
            reactive.assert_called_once_with(enc, now)
            mpc.assert_called_once_with(enc, pred, heads, meta, speed=0.6)
            research._policy_factory("candidate.zip")
            fallback.assert_called_once_with(device="cpu")
            self.assertEqual(load.call_count, 3)

    def test_explicit_tiny_model_rejected_without_policy_or_fallback(self):
        with (
            patch(
                "world_model.training.load_model",
                return_value=(None, None, None, None, {"autotrained_tiny": True}),
            ),
            patch("eval.eval_closed_loop.load_or_train") as fallback,
            patch("planner.learned_policy.load_policy") as policy,
        ):
            with self.assertRaisesRegex(ValueError, "tiny selftest"):
                research._policy_factory("candidate.zip", wm_path="tiny.pth")
            policy.assert_not_called()
            fallback.assert_not_called()


def selftest():
    suite = unittest.TestSuite(
        unittest.defaultTestLoader.loadTestsFromTestCase(cls)
        for cls in (PolicyEvalIntegrity, ExplicitWorldModel)
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    assert result.wasSuccessful(), "policy evaluation integrity selftest failed"
    print(f"PCELLS OK: {result.testsRun} isolated identity/publication regressions")


if __name__ == "__main__":
    selftest()

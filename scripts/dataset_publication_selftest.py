"""Exercise all dataset CLI publication paths without flying or training.

python -m scripts.dataset_publication_selftest
"""

import contextlib
import importlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from datasets.combine_rollouts import _synth
from datasets.provenance import dataset_destination, save_dataset

CLIS = (
    ("datasets.generate_rollouts", "gen", ["--rollouts", "1", "--len", "40"]),
    ("datasets.search_rollouts", "gen", ["--rollouts", "1", "--len", "40"]),
    (
        "datasets.combine_rollouts",
        "build",
        ["--n-transit", "1", "--n-indoor", "1", "--len", "40"],
    ),
)


class DatasetPublicationTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="dataset_publication_selftest_")
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / "artifacts.lock.json").write_text(
            json.dumps({"artifacts": [{"dest": "reserved.npz"}]})
        )
        self.data = _synth([0], length=40)

    def invoke(self, cli, output, factory, extra=()):
        name, attr, flags = cli
        module = importlib.import_module(name)
        with (
            patch("sys.argv", [name, *flags, "--out", str(output), *extra]),
            patch.object(module, attr, factory),
            patch("world_model.checkpoint_io.ROOT", self.root),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            module.main()

    def test_all_clis_reject_existing_before_generation(self):
        from unittest.mock import Mock

        output = self.root / "historical.npz"
        output.write_bytes(b"immutable historical dataset")
        for cli in CLIS:
            factory = Mock(return_value=self.data)
            with self.subTest(cli=cli[0]), self.assertRaises(FileExistsError):
                self.invoke(cli, output, factory)
            factory.assert_not_called()
            self.assertEqual(output.read_bytes(), b"immutable historical dataset")

    def test_all_clis_reject_locked_alias_and_suffix_before_generation(self):
        from unittest.mock import Mock

        alias = self.root / "alias.npz"
        alias.symlink_to(self.root / "unwritten.npz")
        for cli in CLIS:
            for output in (self.root / "reserved.npz", alias, self.root / "no_suffix"):
                factory = Mock(return_value=self.data)
                with (
                    self.subTest(cli=cli[0], output=output),
                    self.assertRaises(ValueError),
                ):
                    self.invoke(cli, output, factory)
                factory.assert_not_called()
        self.assertFalse((self.root / "reserved.npz").exists())
        self.assertFalse((self.root / "unwritten.npz").exists())

    def test_all_clis_save_exact_arrays_and_forward_recipe(self):
        from unittest.mock import Mock

        for cli in CLIS:
            output = self.root / cli[1] / (cli[0] + ".npz")
            factory = Mock(return_value=self.data)
            extra = ["--seed", "17"]
            if cli[0] != "datasets.search_rollouts":
                extra += [
                    "--worlds",
                    "moving,dense,moving",
                    "--schedule-layout",
                    "legacy",
                ]
            else:
                extra += ["--fov-honest"]
            self.invoke(cli, output, factory, extra)
            self.assertEqual(factory.call_count, 1)
            args, kwargs = factory.call_args
            if cli[0] == "datasets.generate_rollouts":
                self.assertEqual(args, (1, 40))
                self.assertEqual(kwargs["seed"], 17)
            elif cli[0] == "datasets.search_rollouts":
                self.assertEqual(args, (1, 40, 17))
                self.assertTrue(kwargs["fov_honest"])
            else:
                self.assertEqual(args, (1, 1, 40, 17))
            if cli[0] != "datasets.search_rollouts":
                self.assertEqual(kwargs["worlds"], ("moving", "dense", "moving"))
                self.assertEqual(kwargs["schedule_layout"], "legacy")
            with np.load(output, allow_pickle=False) as blob:
                self.assertEqual(set(blob.files), set(self.data))
                for key, value in self.data.items():
                    np.testing.assert_array_equal(blob[key], value)

    def test_filename_only_output_works_for_all_clis(self):
        from unittest.mock import Mock

        with contextlib.chdir(self.root):
            for i, cli in enumerate(CLIS):
                output = Path(f"local_{i}.npz")
                self.invoke(cli, output, Mock(return_value=self.data))
                self.assertTrue(output.exists())

    def test_combined_cli_keeps_custom_worlds_and_reports_room_by_name(self):
        module = importlib.import_module("datasets.combine_rollouts")
        transit = _synth([0, 3], length=40)
        transit["world_names"] = np.array(["classic", "dense", "moving", "gap"])
        indoor = _synth([0], length=40, nan_pillars=True)
        indoor["world_names"] = np.array(["room"])
        output = self.root / "custom_combined.npz"
        stdout = io.StringIO()
        with (
            patch("datasets.generate_rollouts.gen", return_value=transit) as generated,
            patch("datasets.search_rollouts.gen", return_value=indoor),
            patch(
                "sys.argv",
                [
                    "datasets.combine_rollouts",
                    "--n-transit",
                    "2",
                    "--n-indoor",
                    "1",
                    "--len",
                    "40",
                    "--worlds",
                    "classic,gap",
                    "--out",
                    str(output),
                ],
            ),
            patch("world_model.checkpoint_io.ROOT", self.root),
            contextlib.redirect_stdout(stdout),
        ):
            module.main()
        self.assertEqual(generated.call_args.kwargs["worlds"], ("classic", "gap"))
        self.assertIn("transit 2, room 1", stdout.getvalue())
        with np.load(output, allow_pickle=False) as data:
            self.assertEqual(
                data["world_names"][data["world_id"]].tolist(),
                ["classic", "gap", "room"],
            )
            self.assertEqual(data["world_id"].tolist(), [0, 3, 4])

    def test_serializer_failure_leaves_no_partial_output(self):
        from unittest.mock import Mock

        def broken(stream, **kwargs):
            stream.write(b"partial NPZ")
            raise OSError("synthetic disk failure")

        output = self.root / "failed.npz"
        for cli in CLIS:
            with patch("numpy.savez_compressed", side_effect=broken):
                with self.assertRaisesRegex(OSError, "disk failure"):
                    self.invoke(cli, output, Mock(return_value=self.data))
            self.assertFalse(output.exists())
            self.assertEqual(list(self.root.rglob("*.tmp")), [])

    def test_competing_output_created_during_generation_is_preserved(self):
        output = self.root / "contender.npz"
        for cli in CLIS:

            def competing(*args, **kwargs):
                output.write_bytes(b"other writer completed during simulation")
                return self.data

            with self.assertRaises(FileExistsError):
                self.invoke(cli, output, competing)
            self.assertEqual(
                output.read_bytes(), b"other writer completed during simulation"
            )
            output.unlink()  # only the synthetic fixture between distinct CLI checks

    def test_only_named_selftest_can_replace_and_failure_keeps_old_bytes(self):
        output = self.root / "corpus_selftest.npz"
        save_dataset({"value": np.array([1])}, output, selftest=True)
        before = output.read_bytes()
        with self.assertRaises(FileExistsError):
            save_dataset({}, output)
        with self.assertRaisesRegex(ValueError, "_selftest"):
            dataset_destination(self.root / "ordinary.npz", selftest=True)
        with patch("numpy.savez_compressed", side_effect=OSError("synthetic failure")):
            with self.assertRaises(OSError):
                save_dataset({}, output, selftest=True)
        self.assertEqual(output.read_bytes(), before)
        save_dataset({"value": np.array([2])}, output, selftest=True)
        with np.load(output, allow_pickle=False) as blob:
            np.testing.assert_array_equal(blob["value"], [2])

    def test_transit_selftest_never_uses_explicit_out(self):
        from unittest.mock import Mock

        module = importlib.import_module("datasets.generate_rollouts")
        explicit = self.root / "user_dataset.npz"
        explicit.write_bytes(b"user corpus")
        expected = self.root / "default_selftest.npz"
        seen = []

        def preflight(path, *, selftest=False):
            seen.append((Path(path), selftest))
            raise RuntimeError("stop before actual selftest simulation")

        factory = Mock()
        with (
            patch.object(module, "OUT", str(self.root / "default.npz")),
            patch.object(module, "dataset_destination", side_effect=preflight),
            self.assertRaisesRegex(RuntimeError, "stop before"),
        ):
            self.invoke(CLIS[0], explicit, factory, ["--selftest"])
        self.assertEqual(seen, [(expected, True)])
        factory.assert_not_called()
        self.assertEqual(explicit.read_bytes(), b"user corpus")

    def test_failed_transit_selftest_keeps_previous_selftest_corpus(self):
        from unittest.mock import Mock

        module = importlib.import_module("datasets.generate_rollouts")
        output = self.root / "default_selftest.npz"
        output.write_bytes(b"previous successful selftest corpus")
        # This fixture has 4px frames, so the real CLI's image-shape assertion
        # must fail before publishing. No real environment is constructed.
        factory = Mock(return_value=_synth([0] * 12, length=100))
        with (
            patch.object(module, "OUT", str(self.root / "default.npz")),
            self.assertRaisesRegex(AssertionError, "bad frame shape"),
        ):
            self.invoke(CLIS[0], self.root / "ignored.npz", factory, ["--selftest"])
        self.assertEqual(output.read_bytes(), b"previous successful selftest corpus")
        self.assertEqual(list(self.root.rglob("*.tmp")), [])


def selftest():
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(DatasetPublicationTests)
    )
    assert result.wasSuccessful()
    print(f"DATASET-PUBLICATION OK: {result.testsRun} artifactless CLI/IO regressions")


if __name__ == "__main__":
    selftest()

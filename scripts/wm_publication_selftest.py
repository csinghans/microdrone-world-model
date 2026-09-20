"""Fault-inject WM export publication without fitting or scoring a model.

python -m scripts.wm_publication_selftest
"""

import contextlib
import copy
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np

from eval import eval_wm_checkpoint as probe
from world_model.checkpoint_io import publish_checkpoint


class PublicationTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="wm_publication_selftest_")
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.model, self.data = self.root / "mock.pth", self.root / "data.npz"
        self.out, self.scores = self.root / "metrics.json", self.root / "scores.npz"
        self.model.write_bytes(b"synthetic checkpoint; model load mocked")
        np.savez(self.data, frames=np.zeros((1, 1, 1, 1, 3), dtype=np.uint8))
        (self.root / "artifacts.lock.json").write_text(
            json.dumps({"artifacts": [{"dest": "locked.pth"}]})
        )
        self.result = {
            "auc_h": [0.5] * 4,
            "auc_by_world": {},
            "veer_val": (float("nan"), 0),
            "veer_all": (float("nan"), 0),
            "n_val_samples": 1,
            "va_rolls": [0],
            "now_auc": 0.5,
            "dataset_file_relation": "unverified",
        }
        self.sample = np.array([[0.1, 0.2, 0.3, 0.4]], dtype=np.float32)
        self.scorer = Mock(side_effect=self.fake_evaluate)
        self.stdout = io.StringIO()

    def fake_evaluate(self, *args, sample_output=None, **kwargs):
        if sample_output is not None:
            sample_output["scores"] = self.sample.copy()
        return copy.deepcopy(self.result)

    def invoke(self, *flags):
        argv = ["probe", "--ckpt", str(self.model), "--data", str(self.data), *flags]
        with (
            patch("sys.argv", argv),
            patch.object(probe, "evaluate", self.scorer),
            patch("world_model.checkpoint_io.ROOT", self.root),
            contextlib.redirect_stdout(self.stdout),
        ):
            probe.main()

    def assert_no_partial_files(self):
        self.assertFalse(self.out.exists())
        self.assertFalse(self.scores.exists())
        self.assertEqual(list(self.root.rglob("*.tmp")), [])

    def test_successful_outputs_share_metadata_and_scores(self):
        self.invoke("--out", str(self.out), "--scores-out", str(self.scores))
        record = json.loads(self.out.read_text())
        with np.load(self.scores, allow_pickle=False) as blob:
            self.assertEqual(json.loads(str(blob["metadata"])), record)
            np.testing.assert_array_equal(blob["scores"], self.sample)
        self.assertEqual(record["veer_val"], [None, 0])
        self.assertEqual(
            record["provenance"]["dataset"]["path"], str(self.data.resolve())
        )
        self.assertEqual(self.scorer.call_count, 1)
        self.assertIn("WM-PROBE OK", self.stdout.getvalue())
        self.assertEqual(list(self.root.rglob("*.tmp")), [])

    def test_failed_npz_serialization_leaves_no_final_prefix(self):
        def failure(stream, **kwargs):
            stream.write(b"partial NPZ")
            raise RuntimeError("synthetic serializer failure")

        with patch.object(probe.np, "savez_compressed", side_effect=failure):
            with self.assertRaisesRegex(RuntimeError, "serializer failure"):
                self.invoke("--out", str(self.out), "--scores-out", str(self.scores))
        self.assert_no_partial_files()
        self.assertNotIn("WM-PROBE OK", self.stdout.getvalue())

    def test_bad_json_is_rejected_before_either_publication(self):
        self.result["unserializable"] = object()
        with self.assertRaises(TypeError):
            self.invoke("--out", str(self.out), "--scores-out", str(self.scores))
        self.assert_no_partial_files()

    def test_json_write_error_removes_temporary_prefix(self):
        def failure(path, writer):
            def broken(stream):
                stream.write(b'{"partial":')
                raise OSError("synthetic disk error")

            return publish_checkpoint(path, broken)

        with patch.object(probe, "publish_checkpoint", side_effect=failure):
            with self.assertRaisesRegex(OSError, "disk error"):
                self.invoke("--out", str(self.out))
        self.assert_no_partial_files()

    def test_second_publication_failure_retains_complete_first_file(self):
        def second_fails(path, writer):
            if Path(path) == self.out:
                raise OSError("synthetic second publication failure")
            return publish_checkpoint(path, writer)

        with patch.object(probe, "publish_checkpoint", side_effect=second_fails):
            with self.assertRaisesRegex(OSError, "second publication failure"):
                self.invoke("--out", str(self.out), "--scores-out", str(self.scores))
        self.assertFalse(self.out.exists())
        with np.load(self.scores, allow_pickle=False) as blob:
            np.testing.assert_array_equal(blob["scores"], self.sample)
            self.assertEqual(json.loads(str(blob["metadata"]))["n_val_samples"], 1)
        self.assertNotIn("WM-PROBE OK", self.stdout.getvalue())
        self.assertEqual(list(self.root.rglob("*.tmp")), [])

    def test_existing_outputs_and_aliases_fail_before_loading(self):
        self.out.write_bytes(b"previous immutable result")
        alias = self.root / "alias.json"
        alias.symlink_to(self.root / "absent_target.json")
        cases = [
            ["--out", str(self.out)],
            ["--out", str(alias)],
            ["--out", str(self.root / "locked.pth")],
            ["--scores-out", str(self.root / "locked.pth")],
            ["--out", str(self.scores), "--scores-out", str(self.scores)],
        ]
        for flags in cases:
            with self.subTest(flags=flags), patch.object(probe.np, "load") as load:
                with self.assertRaises(SystemExit):
                    self.invoke(*flags)
                load.assert_not_called()
        self.scorer.assert_not_called()
        self.assertEqual(self.out.read_bytes(), b"previous immutable result")
        self.assertFalse((self.root / "absent_target.json").exists())
        self.assertFalse((self.root / "locked.pth").exists())

    def test_concurrent_writer_is_preserved(self):
        link = os.link

        def competing_link(source, dest):
            Path(dest).write_bytes(b"concurrent writer owns this path")
            return link(source, dest)

        with patch("world_model.checkpoint_io.os.link", side_effect=competing_link):
            with self.assertRaises(FileExistsError):
                self.invoke("--scores-out", str(self.scores))
        self.assertEqual(self.scores.read_bytes(), b"concurrent writer owns this path")
        self.assertEqual(list(self.root.rglob("*.tmp")), [])
        self.assertNotIn("WM-PROBE OK", self.stdout.getvalue())

    def test_input_change_prevents_publication(self):
        def changing(*args, **kwargs):
            result = self.fake_evaluate(*args, **kwargs)
            self.model.write_bytes(b"changed during scoring")
            return result

        self.scorer.side_effect = changing
        with self.assertRaisesRegex(SystemExit, "changed during evaluation"):
            self.invoke("--out", str(self.out), "--scores-out", str(self.scores))
        self.assert_no_partial_files()


def selftest():
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(PublicationTests)
    )
    assert result.wasSuccessful()
    print(f"WM-PUBLICATION OK: {result.testsRun} artifactless publication regressions")


if __name__ == "__main__":
    selftest()

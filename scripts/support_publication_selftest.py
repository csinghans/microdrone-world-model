"""Fault-inject metadata report publication, without model or pixel access.

python -m scripts.support_publication_selftest
"""

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from datasets.combine_rollouts import _synth
from datasets.provenance import file_identity
from eval import eval_dataset_support as dataset
from eval import eval_veer_support as veer
from planner.action_set import ACTION_VECS
from world_model.checkpoint_io import publish_checkpoint

MODULES = (dataset, veer)


class PublicationTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="support_publication_selftest_")
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.data = self.root / "data.npz"
        data = _synth([0] * 12, length=40)
        data["actions"][:] = ACTION_VECS[0]
        data["dists"][:6] = 0.1
        # Loading this member would fail with allow_pickle=False.
        data["frames"] = np.array([object()], dtype=object)
        np.savez(self.data, **data)
        self.original = self.data.read_bytes()
        (self.root / "artifacts.lock.json").write_text(
            json.dumps(
                {
                    "artifacts": [{"dest": "reserved.pth"}, {"dest": "missing.pth"}],
                }
            )
        )
        self.stdout = io.StringIO()

    def invoke(self, module, output, extra=()):
        self.stdout = io.StringIO()
        with (
            patch(
                "sys.argv",
                [
                    module.__name__,
                    "--data",
                    str(self.data),
                    "--out",
                    str(output),
                    *extra,
                ],
            ),
            patch("world_model.checkpoint_io.ROOT", self.root),
            contextlib.redirect_stdout(self.stdout),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            module.main()

    def absent(self, output):
        self.assertFalse(output.exists())
        self.assertEqual(list(self.root.rglob("*.tmp")), [])
        self.assertNotIn("SUPPORT OK:", self.stdout.getvalue())

    def test_success_preserves_analysis_and_never_reads_pixels(self):
        for module in MODULES:
            with self.subTest(module=module.__name__):
                expected = module.analyze(module.load_metadata(self.data))
                expected = expected[0] if module is veer else expected
                output = self.root / module.__name__ / "report.json"
                self.invoke(module, output)
                actual = json.loads(output.read_text())
                provenance = actual.pop("provenance")
                self.assertEqual(actual, expected)
                self.assertEqual(provenance["dataset"], file_identity(self.data))
                self.assertTrue(output.read_bytes().endswith(b"\n"))
                self.assertIn("SUPPORT OK:", self.stdout.getvalue())
        self.assertEqual(list(self.root.rglob("*.tmp")), [])

    def test_filename_only_output(self):
        with contextlib.chdir(self.root):
            for module in MODULES:
                output = Path(module.__name__ + ".json")
                self.invoke(module, output)
                self.assertIn("provenance", json.loads(output.read_text()))

    def test_existing_locked_and_alias_paths_reject_before_loading(self):
        existing, locked = self.root / "old.json", self.root / "reserved.pth"
        existing.write_bytes(b"old report")
        locked.write_bytes(b"synthetic protected model")
        alias, hard = self.root / "alias.json", self.root / "hard.json"
        dangling = self.root / "dangling.json"
        alias.symlink_to(locked)
        os.link(locked, hard)
        dangling.symlink_to(self.root / "absent.json")
        for module in MODULES:
            for output in (
                existing,
                locked,
                alias,
                hard,
                dangling,
                self.root / "missing.pth",
            ):
                with self.subTest(module=module.__name__, output=output):
                    with patch.object(module, "load_metadata") as load:
                        with self.assertRaises(SystemExit) as error:
                            self.invoke(module, output)
                        self.assertEqual(error.exception.code, 2)
                        load.assert_not_called()
        self.assertEqual(existing.read_bytes(), b"old report")
        self.assertEqual(locked.read_bytes(), b"synthetic protected model")
        self.assertFalse((self.root / "missing.pth").exists())

    def test_bad_json_leaves_no_final_and_valid_attempt_can_follow(self):
        for module in MODULES:
            original = module.analyze
            for bad in (object(), float("nan")):
                output = self.root / (module.__name__ + str(type(bad)) + ".json")

                def invalid(*args, **kwargs):
                    result = original(*args, **kwargs)
                    record = result[0] if module is veer else result
                    record["invalid"] = bad
                    return result

                with patch.object(module, "analyze", side_effect=invalid):
                    with self.assertRaises((TypeError, ValueError)):
                        self.invoke(module, output)
                self.absent(output)
                self.invoke(module, output)
                self.assertNotIn("invalid", json.loads(output.read_text()))

    def test_disk_failure_cleans_partial_temporary(self):
        def failed(path, writer):
            def broken(stream):
                stream.write(b'{"partial":')
                raise OSError("synthetic disk failure")

            return publish_checkpoint(path, broken)

        for module in MODULES:
            output = self.root / (module.__name__ + ".json")
            with patch.object(module, "publish_checkpoint", side_effect=failed):
                with self.assertRaisesRegex(OSError, "disk failure"):
                    self.invoke(module, output)
            self.absent(output)

    def test_competing_writer_is_preserved(self):
        link = os.link

        def race(source, destination):
            Path(destination).write_bytes(b"concurrent winner")
            return link(source, destination)

        for module in MODULES:
            output = self.root / (module.__name__ + ".json")
            with patch("os.link", side_effect=race):
                with self.assertRaises(FileExistsError):
                    self.invoke(module, output)
            self.assertEqual(output.read_bytes(), b"concurrent winner")
            self.assertEqual(list(self.root.rglob("*.tmp")), [])
            self.assertNotIn("SUPPORT OK:", self.stdout.getvalue())

    def test_abrupt_writer_exit_keeps_final_invisible(self):
        script = """
import importlib
import os
import sys
from pathlib import Path
from unittest.mock import patch
from world_model.checkpoint_io import publish_checkpoint

module = importlib.import_module(sys.argv[1])
data, output, root = sys.argv[2:]
def interrupted(path, writer):
    def stop(stream):
        stream.write(b'partial temporary payload')
        stream.flush()
        os._exit(37)  # bypass finally, like an abrupt worker termination
    return publish_checkpoint(path, stop)
with patch('world_model.checkpoint_io.ROOT', Path(root)), \\
     patch.object(module, 'publish_checkpoint', side_effect=interrupted), \\
     patch('sys.argv', [module.__name__, '--data', data, '--out', output]):
    module.main()
"""
        for module in MODULES:
            output = self.root / (module.__name__ + ".json")
            process = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    script,
                    module.__name__,
                    str(self.data),
                    str(output),
                    str(self.root),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(process.returncode, 37, process.stderr)
            self.assertFalse(output.exists())
            self.assertNotIn("SUPPORT OK:", process.stdout)
        # Abrupt termination cannot run cleanup; only hidden temporaries remain.
        partials = list(self.root.rglob("*.tmp"))
        self.assertEqual(len(partials), 2)
        self.assertTrue(
            all(p.read_bytes() == b"partial temporary payload" for p in partials)
        )

    def test_dataset_change_during_analysis_prevents_publication(self):
        for module in MODULES:
            self.data.write_bytes(self.original)
            original = module.analyze

            def changed(*args, **kwargs):
                result = original(*args, **kwargs)
                self.data.write_bytes(self.original + b"changed")
                return result

            output = self.root / (module.__name__ + ".json")
            with patch.object(module, "analyze", side_effect=changed):
                with self.assertRaisesRegex(
                    (RuntimeError, ValueError), "dataset changed"
                ):
                    self.invoke(module, output)
            self.absent(output)

    def test_source_change_during_analysis_prevents_publication(self):
        for module in MODULES:
            state = {"changed": False}
            analyze = module.analyze
            name = "digest" if module is dataset else "file_identity"
            digest = getattr(module, name)

            def measured(path):
                value = digest(path)
                if (
                    Path(path).resolve() == Path(module.__file__).resolve()
                    and state["changed"]
                ):
                    return (
                        "0" * 64 if module is dataset else {**value, "sha256": "0" * 64}
                    )
                return value

            def changed(*args, **kwargs):
                result = analyze(*args, **kwargs)
                state["changed"] = True
                return result

            output = self.root / (module.__name__ + ".json")
            with (
                patch.object(module, name, side_effect=measured),
                patch.object(module, "analyze", side_effect=changed),
            ):
                with self.assertRaisesRegex(
                    (RuntimeError, ValueError), "source changed"
                ):
                    self.invoke(module, output)
            self.absent(output)

    def test_input_change_during_serialization_is_rechecked(self):
        dumps = json.dumps

        def changed(value, *args, **kwargs):
            payload = dumps(value, *args, **kwargs)
            if isinstance(value, dict) and "provenance" in value:
                self.data.write_bytes(self.original + b"changed during JSON encoding")
            return payload

        for module in MODULES:
            self.data.write_bytes(self.original)
            output = self.root / (module.__name__ + ".json")
            with patch("json.dumps", side_effect=changed):
                with self.assertRaisesRegex(
                    (RuntimeError, ValueError), "dataset changed"
                ):
                    self.invoke(module, output)
            self.absent(output)

    def test_earlier_export_change_is_rechecked_after_all_exports(self):
        data = veer.load_metadata(self.data)
        _, sample = veer.analyze(data)
        exports = [self.root / f"export{i}.npz" for i in range(2)]
        for export in exports:
            np.savez(
                export,
                **sample,
                world_names=data["world_names"],
                metadata=np.array(
                    json.dumps(
                        {
                            "split": "independent_holdout_all",
                            "provenance": {"dataset": file_identity(self.data)},
                        }
                    )
                ),
            )
        original = veer.check_export

        def changed(path, *args):
            result = original(path, *args)
            if Path(path) == exports[1]:
                exports[0].write_bytes(b"changed after its own check")
            return result

        output = self.root / "probe.json"
        with patch.object(veer, "check_export", side_effect=changed):
            with self.assertRaisesRegex(ValueError, "checked export changed"):
                self.invoke(
                    veer,
                    output,
                    [
                        "--check-export",
                        str(exports[0]),
                        "--check-export",
                        str(exports[1]),
                    ],
                )
        self.absent(output)


def selftest():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PublicationTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    assert result.wasSuccessful(), "support publication regression"
    print(
        f"SUPPORT-PUBLICATION OK: {result.testsRun} "
        "artifactless CLI/failure regressions"
    )


if __name__ == "__main__":
    selftest()

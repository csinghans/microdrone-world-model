"""Artifactless regression tests for prospective action-support requirements.

    python -m scripts.support_requirements_selftest

Uses count fixtures and a synthetic metadata-only producer check; no model,
real exam, rendered-vision claim or scientific pass threshold is involved.
"""

import contextlib
import copy
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from eval import eval_support_requirements as checker


def fixture():
    """Two classes may share course IDs; absent actions are truly omitted."""
    labels = {
        "positive": 6,
        "negative": 4,
        "positive_rollouts": 2,
        "negative_rollouts": 2,
        "auc_defined": True,
    }
    partition = {
        "rollouts": 3,
        "valid_windows": 10,
        "worlds": {
            "moving": {
                "rollout_ids": [0, 1, 2],
                "rollouts": 3,
                "valid_windows": 10,
                "labels_at_32": dict(labels),
                "actions": {"forward": {"windows": 10, **labels}},
            }
        },
    }
    report = {
        "schema_version": 1,
        "target": checker.TARGET,
        "horizons": [4, 8, 16, 32],
        "all": partition,
        "splits": {"7": {"train": copy.deepcopy(partition)}},
    }
    requirements = {
        "schema_version": 1,
        "target": checker.TARGET,
        "checks": [
            {
                "partition": "all",
                "world": "moving",
                "actions": ["forward"],
                "minimum": {k: labels[k] for k in checker.COUNTS},
            }
        ],
    }
    return report, requirements


class SupportTests(unittest.TestCase):
    def setUp(self):
        self.report, self.requirements = fixture()

    def test_exact_boundary_and_no_mutation(self):
        before = copy.deepcopy((self.report, self.requirements))
        result = checker.check_support(self.report, self.requirements)
        self.assertEqual(result["status"], "satisfied")
        self.assertEqual(result["checks"][0]["deficits"], {})
        self.assertEqual(before, (self.report, self.requirements))

    def test_each_minimum_and_course_window_distinction(self):
        for key in checker.COUNTS:
            with self.subTest(key=key):
                spec = copy.deepcopy(self.requirements)
                spec["checks"][0]["minimum"][key] += 1
                result = checker.check_support(self.report, spec)
                self.assertEqual(result["status"], "insufficient")
                self.assertEqual(result["checks"][0]["deficits"], {key: 1})
        # A course lower bound greater than a window lower bound is legal:
        # it implies a stronger effective window bound, not contradictory data.
        spec["checks"][0]["minimum"] = dict.fromkeys(checker.COUNTS, 1)
        spec["checks"][0]["minimum"]["positive_rollouts"] = 2
        self.assertEqual(
            checker.check_support(self.report, spec)["status"], "satisfied"
        )

    def test_all_checks_retained_and_absence_is_insufficient(self):
        checks = self.requirements["checks"]
        checks[0]["actions"].append("veer_left")
        checks.append({**copy.deepcopy(checks[0]), "world": "dense"})
        result = checker.check_support(self.report, self.requirements)
        self.assertEqual(len(result["checks"]), 4)
        self.assertEqual(result["status"], "insufficient")
        self.assertEqual(
            [row["missing"] for row in result["checks"]],
            [None, "action_absent", "world_absent", "world_absent"],
        )
        self.assertEqual(
            result["checks"][1]["observed"], dict.fromkeys(checker.COUNTS, 0)
        )

    def test_classless_support_does_not_become_half_auc(self):
        row = self.report["all"]["worlds"]["moving"]
        for counts in (row["actions"]["forward"], row["labels_at_32"]):
            counts.update(
                positive=10, negative=0, negative_rollouts=0, auc_defined=False
            )
        result = checker.check_support(self.report, self.requirements)
        self.assertEqual(result["status"], "insufficient")
        self.assertEqual(
            result["checks"][0]["deficits"], {"negative": 4, "negative_rollouts": 2}
        )

    def test_partition_is_explicit_no_fallback(self):
        self.requirements["checks"][0]["partition"] = "splits/7/train"
        self.report["all"] = {}  # only selected partitions are inspected
        self.assertEqual(
            checker.check_support(self.report, self.requirements)["status"], "satisfied"
        )
        self.requirements["checks"][0]["partition"] = "splits/7/val"
        with self.assertRaisesRegex(ValueError, "partition.*absent"):
            checker.check_support(self.report, self.requirements)

    def test_room_catalog_and_typos(self):
        row = self.report["all"]["worlds"].pop("moving")
        row["actions"]["reverse"] = row["actions"].pop("forward")
        self.report["all"]["worlds"]["room"] = row
        check = self.requirements["checks"][0]
        check.update(world="room", actions=["reverse"])
        self.assertEqual(
            checker.check_support(self.report, self.requirements)["status"], "satisfied"
        )
        for world, action in (
            ("moving", "reverse"),
            ("room", "veer_left"),
            ("rom", "forward"),
        ):
            check.update(world=world, actions=[action])
            with (
                self.subTest(world=world, action=action),
                self.assertRaises(ValueError),
            ):
                checker.check_support(self.report, self.requirements)

    def test_invalid_requirements_rejected(self):
        invalid = []
        for key, value in (
            ("checks", []),
            ("schema_version", True),
            ("target", "now"),
            ("typo", 1),
        ):
            invalid.append({**copy.deepcopy(self.requirements), key: value})
        for key, value in (
            ("actions", []),
            ("actions", ["forward", "forward"]),
            ("partition", "splits/07/train"),
            ("partition", "val"),
            ("minimum", {"positive": 1}),
            ("minimun", {}),
        ):
            spec = copy.deepcopy(self.requirements)
            spec["checks"][0][key] = value
            invalid.append(spec)
        for value in (0, -1, True, 1.5, "2", None):
            spec = copy.deepcopy(self.requirements)
            spec["checks"][0]["minimum"]["positive"] = value
            invalid.append(spec)
        for spec in invalid:
            with self.subTest(spec=spec), self.assertRaises(ValueError):
                checker.check_support(self.report, spec)

    def test_malformed_counts_are_errors_not_insufficiency(self):
        for key, value in (
            ("positive", 5),
            ("positive", True),
            ("negative", -1),
            ("positive_rollouts", 7),
            ("positive_rollouts", 0),
            ("negative_rollouts", 1.5),
            ("auc_defined", False),
            ("windows", 9),
        ):
            report = copy.deepcopy(self.report)
            report["all"]["worlds"]["moving"]["actions"]["forward"][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                checker.check_support(report, self.requirements)
        for key, value in (
            ("rollout_ids", [0, 0, 1]),
            ("rollouts", 1),
            ("valid_windows", 9),
        ):
            report = copy.deepcopy(self.report)
            report["all"]["worlds"]["moving"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                checker.check_support(report, self.requirements)

    def test_unknown_report_contract_not_silently_upgraded(self):
        for key, value in (
            ("schema_version", None),
            ("target", "now"),
            ("horizons", [4, 8]),
        ):
            report = {**self.report, key: value}
            with self.subTest(key=key), self.assertRaises(ValueError):
                checker.check_support(report, self.requirements)

    def test_producer_cli_to_checker_with_unreadable_pixels(self):
        import numpy as np

        from datasets.combine_rollouts import _synth
        from planner.action_set import ACTION_VECS

        data = _synth([0] * 6, length=40)
        data["actions"][:] = ACTION_VECS[0]
        data["dists"][:3] = 0.1
        # Any attempted pixel load with allow_pickle=False must fail.
        data["frames"] = np.array([object()], dtype=object)
        with tempfile.TemporaryDirectory(prefix="support_producer_selftest_") as tmp:
            root = Path(tmp)
            source, report_path = root / "data.npz", root / "report.json"
            np.savez(source, **data)
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "eval.eval_dataset_support",
                    "--data",
                    str(source),
                    "--out",
                    str(report_path),
                    "--independent-holdout",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.requirements["checks"][0].update(
                world="classic", minimum=dict.fromkeys(checker.COUNTS, 1)
            )
            spec = root / "requirements.json"
            spec.write_text(json.dumps(self.requirements))
            result = checker.run(report_path, spec, source, root / "receipt.json")
            self.assertEqual(result["status"], "satisfied")
            self.assertEqual(
                result["checks"][0]["observed"],
                {
                    "positive": 24,
                    "negative": 24,
                    "positive_rollouts": 3,
                    "negative_rollouts": 3,
                },
            )

    def test_real_producer_contract_without_artifacts(self):
        from datasets.combine_rollouts import _synth
        from eval.eval_dataset_support import analyze
        from planner.action_set import ACTION_VECS

        data = _synth([0] * 6, length=40)
        data["actions"][:] = ACTION_VECS[0]
        data["dists"][:3] = 0.1
        report = analyze(data, seeds=(7,))
        check = self.requirements["checks"][0]
        check.update(world="classic", minimum=dict.fromkeys(checker.COUNTS, 1))
        self.assertEqual(
            checker.check_support(report, self.requirements)["status"], "satisfied"
        )
        self.assertEqual(
            report["all"]["worlds"]["classic"]["actions"]["forward"]["positive"], 24
        )


class FileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="support_requirements_selftest_")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.data = self.root / "synthetic_data.npz"
        self.data.write_bytes(b"synthetic identity only; never loaded as a corpus")
        self.report, self.spec = fixture()
        self.report["provenance"] = {
            "dataset": {
                "path": "/original/synthetic.npz",
                "sha256": checker._digest(self.data),
            }
        }
        self.report_path, self.spec_path = (
            self.root / "report.json",
            self.root / "spec.json",
        )
        self.out = self.root / "receipt.json"
        self.save()

    def save(self):
        self.report_path.write_text(json.dumps(self.report))
        self.spec_path.write_text(json.dumps(self.spec))

    def run_check(self):
        return checker.run(self.report_path, self.spec_path, self.data, self.out)

    def test_receipt_pins_sources_and_does_not_overwrite(self):
        result = self.run_check()
        self.assertEqual(json.loads(self.out.read_text()), result)
        for key, path in (
            ("report", self.report_path),
            ("requirements", self.spec_path),
            ("dataset", self.data),
        ):
            self.assertEqual(result["provenance"][key]["sha256"], checker._digest(path))
        self.assertEqual(len(result["provenance"]["sources"]), 4)
        before = self.out.read_bytes()
        with self.assertRaises(FileExistsError):
            self.run_check()
        self.assertEqual(self.out.read_bytes(), before)

    def test_wrong_dataset_and_input_changes_prevent_publication(self):
        self.data.write_bytes(b"different dataset")
        with self.assertRaisesRegex(ValueError, "SHA does not match"):
            self.run_check()
        self.assertFalse(self.out.exists())
        self.report["provenance"]["dataset"]["sha256"] = checker._digest(self.data)
        self.save()
        original = checker.check_support
        for path in (self.data, self.report_path, self.spec_path):
            before = path.read_bytes()

            def changing(report, spec):
                result = original(report, spec)
                path.write_bytes(before + b" ")
                return result

            with patch.object(checker, "check_support", side_effect=changing):
                with self.assertRaisesRegex(ValueError, "changed during"):
                    self.run_check()
            self.assertFalse(self.out.exists())
            path.write_bytes(before)

    def test_duplicate_keys_and_nonfinite_json(self):
        for text in ('{"schema_version": 1, "schema_version": 1}', '{"x": NaN}'):
            self.spec_path.write_text(text)
            with self.assertRaises(ValueError):
                self.run_check()
            self.assertFalse(self.out.exists())

    def test_cli_exit_codes_and_negative_receipt(self):
        argv = [sys.executable, "-m", "eval.eval_support_requirements"]
        for name, path in (
            ("report", self.report_path),
            ("requirements", self.spec_path),
            ("data", self.data),
        ):
            argv.extend(["--" + name, str(path)])
        for code in (0, 10, 2):
            self.spec["checks"][0]["minimum"]["positive_rollouts"] = (
                2 if code == 0 else 3
            )
            if code == 2:
                self.spec["checks"][0]["world"] = "typo"
            self.save()
            out = self.root / f"exit_{code}.json"
            proc = subprocess.run(
                argv + ["--out", str(out)], capture_output=True, text=True
            )
            self.assertEqual(proc.returncode, code, proc.stdout + proc.stderr)
            self.assertEqual(out.exists(), code != 2)
            if code == 10:
                result = json.loads(out.read_text())
                self.assertEqual(result["status"], "insufficient")
                self.assertEqual(
                    result["checks"][0]["deficits"], {"positive_rollouts": 1}
                )
        with (
            contextlib.redirect_stderr(io.StringIO()),
            self.assertRaises(SystemExit) as err,
        ):
            checker.main([])
        self.assertEqual(err.exception.code, 2)


def selftest():
    suite = unittest.TestSuite(
        unittest.defaultTestLoader.loadTestsFromTestCase(cls)
        for cls in (SupportTests, FileTests)
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    assert result.wasSuccessful()
    print(f"SUPPORT-REQUIREMENTS OK: {result.testsRun} artifactless regressions")


if __name__ == "__main__":
    selftest()

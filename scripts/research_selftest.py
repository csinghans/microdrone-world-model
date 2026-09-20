"""Research integrity regressions; numpy + stdlib only, no training/artifacts.

    python -m scripts.research_selftest

Real git commits are tested exclusively inside disposable repositories.
Numerical examples below are synthetic harness fixtures, not flight results.
"""

import copy
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import nullcontext, redirect_stdout
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts import research
from skills.base import Criterion, EvalCell, Knob, Skill


def _skill():
    return Skill(
        name="integrity_selftest",
        version="1",
        scenarios={},
        cells=(EvalCell("a", None),),
        criteria=(
            Criterion("a", "success", ">=", 0.7, "target"),
            Criterion("a", "reached", ">=", 0.9, "guard"),
        ),
        knobs=tuple(
            Knob(f"K{i}", "zero_shot", "fixture", "fixture", policy_path="builtin:x")
            for i in range(2)
        ),
        max_knobs=2,
        success=lambda ep: True,
    )


def _stats(n=30, success=1.0, reached=0.9):
    return {
        "n": n,
        "seed0": 9000,
        "crash": 0.0,
        "success": success,
        "reached": reached,
        "clearance_mean": 1.0,
        "custom": {"margin": 0.3},
    }


def _block(knob_id="K0", verdict="continue"):
    return {
        "id": knob_id,
        "gate": {"verdict": verdict, "criteria": []},
        "cells": {"a": _stats()},
    }


def _args(cmd="run", knob=None, from_knob=0):
    return SimpleNamespace(
        cmd=cmd,
        knob=knob,
        knob_json=None,
        dry=False,
        no_commit=True,
        from_knob=from_knob,
    )


class GateIntegrity(unittest.TestCase):
    def test_recheck_verdict_uses_pooled_values_for_every_criterion(self):
        for reverse in (False, True):
            skill = _skill()
            if reverse:
                skill = replace(skill, criteria=skill.criteria[::-1])
            cells = {"a": _stats()}
            with patch.object(
                research, "run_cell", return_value=_stats(60, success=0.1)
            ) as fly:
                gate = research.evaluate_gate(skill, cells, None, None, False)
            fly.assert_called_once()
            self.assertEqual(gate["verdict"], "continue")
            self.assertEqual(cells["a"]["n"], 90)
            self.assertAlmostEqual(cells["a"]["success"], 0.4)
            self.assertEqual(cells["a"]["initial"]["success"], 1.0)
            for criterion in gate["criteria"]:
                self.assertTrue(criterion["rechecked"])
                if criterion["kind"] == "target":
                    self.assertAlmostEqual(criterion["measured"], 0.4)
                    self.assertFalse(criterion["pass"])

    def test_recheck_seeds_do_not_overlap_large_initial_block(self):
        cells = {"a": _stats(n=1200)}
        with patch.object(research, "run_cell", return_value=_stats(60)) as fly:
            research.evaluate_gate(_skill(), cells, None, None, False)
        self.assertEqual(fly.call_args.kwargs["seed0"], 10200)

    def test_recheck_rejects_changed_custom_metric_schema(self):
        recheck = _stats(60)
        recheck["custom"] = {}
        with patch.object(research, "run_cell", return_value=recheck):
            with self.assertRaisesRegex(ValueError, "custom metric keys"):
                research.evaluate_gate(_skill(), {"a": _stats()}, None, None, False)

    def test_nonfinite_metric_is_harness_error(self):
        with self.assertRaisesRegex(ValueError, "non-finite"):
            research.evaluate_gate(
                _skill(), {"a": _stats(success=float("nan"))}, None, None, False
            )


class SavedCampaignIntegrity(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="research_selftest_")
        self.addCleanup(self.tmp.cleanup)
        self.path = self.tmp.name
        self.skill = _skill()

    def test_atomic_write_preserves_previous_record_on_serialization_error(self):
        original = research._load_results(self.path, self.skill)
        research._write_results(self.path, original)
        with self.assertRaises(ValueError):
            research._write_results(self.path, {"bad": float("nan")})
        self.assertEqual(research._load_results(self.path, self.skill), original)
        self.assertEqual(os.listdir(self.path), ["results.json"])

    def test_frozen_version_criteria_and_roles_cannot_change(self):
        original = research._load_results(self.path, self.skill)
        research._write_results(self.path, original)
        for changed in (
            replace(self.skill, version="2"),
            replace(
                self.skill,
                criteria=(replace(self.skill.criteria[0], bar=0.1),)
                + self.skill.criteria[1:],
            ),
            replace(
                self.skill,
                criteria=(replace(self.skill.criteria[0], kind="guard"),)
                + self.skill.criteria[1:],
            ),
        ):
            with self.assertRaises(ValueError):
                research._load_results(self.path, changed)
        # Older result files lack kind; loading cannot rewrite historical data.
        for criterion in original["targets_frozen"]:
            criterion.pop("kind")
        research._write_results(self.path, original)
        before = Path(self.path, "results.json").read_bytes()
        self.assertEqual(research._load_results(self.path, self.skill), original)
        self.assertEqual(Path(self.path, "results.json").read_bytes(), before)

    def test_frozen_cells_and_recheck_settings_cannot_change(self):
        skill = replace(self.skill, cells=self.skill.cells + (EvalCell("b", "dense"),))
        original = research._load_results(self.path, skill)
        research._write_results(self.path, original)
        before = Path(self.path, "results.json").read_bytes()
        changes = [
            replace(skill, cells=(replace(skill.cells[0], **fields), skill.cells[1]))
            for fields in (
                {"id": "other"},
                {"world": "moving"},
                {"speed": 0.6},
                {"n_seeds": 60},
                {"seed0": 12345},
                {"kwargs": {"solo": True}},
                {"role": "guard"},
            )
        ] + [
            replace(skill, recheck_n=120),
            replace(skill, recheck_margin=0.01),
            replace(skill, cells=skill.cells[::-1]),
            replace(skill, cells=skill.cells[:1]),
            replace(skill, cells=skill.cells + (EvalCell("c", None),)),
        ]
        for changed in changes:
            with (
                self.subTest(changed=changed),
                self.assertRaisesRegex(ValueError, "evaluation differs"),
            ):
                research._load_results(self.path, changed)
        self.assertEqual(Path(self.path, "results.json").read_bytes(), before)
        # Evaluation is frozen; adding a justified knob is still permitted.
        extended = replace(
            skill,
            max_knobs=3,
            knobs=skill.knobs
            + (Knob("KD1", "policy", "deviation", "fixture", {"timesteps": 1}),),
        )
        self.assertEqual(research._load_results(self.path, extended), original)

    def test_snapshot_is_detached_and_gate_rejects_mutation(self):
        kwargs = {"nested_fixture": [1, 2]}
        skill = replace(
            self.skill, cells=(replace(self.skill.cells[0], kwargs=kwargs),)
        )
        results = research._load_results(self.path, skill)
        research._prepare_measurement(self.path, results, skill)
        before = Path(self.path, "results.json").read_bytes()
        kwargs["nested_fixture"].append(3)
        self.assertEqual(
            results["evaluation_frozen"]["cells"][0]["kwargs"],
            {"nested_fixture": [1, 2]},
        )
        with self.assertRaisesRegex(ValueError, "evaluation differs"):
            research._record_gate(
                skill, skill.knobs[0], _block(), self.path, results, True
            )
        self.assertFalse(results["knobs"])
        self.assertEqual(Path(self.path, "results.json").read_bytes(), before)

    def test_first_measurement_freezes_before_interruption_in_both_routes(self):
        for cmd in ("step", "run"):
            path = Path(self.path, cmd)
            path.mkdir()
            results = research._load_results(str(path), self.skill)

            def interrupted(*args):
                saved = json.loads((path / "results.json").read_text())
                self.assertEqual(
                    saved["evaluation_frozen"], research._frozen_evaluation(self.skill)
                )
                self.assertEqual(saved["knobs"], [])
                raise RuntimeError("synthetic interrupted first fit")

            with patch.object(research, "run_knob", side_effect=interrupted) as run:
                with self.assertRaisesRegex(RuntimeError, "interrupted first fit"):
                    research._execute_campaign(
                        _args(cmd, knob=0), self.skill, str(path), results
                    )
            run.assert_called_once()
            self.assertEqual(research._load_results(str(path), self.skill), results)
            changed = replace(self.skill, recheck_n=120)
            with self.assertRaisesRegex(ValueError, "evaluation differs"):
                research._load_results(str(path), changed)

    def test_failed_initial_snapshot_prevents_training(self):
        results = research._load_results(self.path, self.skill)
        with (
            patch.object(research, "_write_results", side_effect=OSError("disk error")),
            patch.object(research, "run_knob") as run,
            self.assertRaisesRegex(OSError, "disk error"),
        ):
            research._execute_campaign(
                _args("step", knob=0), self.skill, self.path, results
            )
        run.assert_not_called()

    def test_legacy_records_are_readable_but_cannot_gain_new_measurements(self):
        legacy = research._load_results(self.path, self.skill)
        legacy.pop("evaluation_frozen")
        legacy["knobs"].append(_block())
        research._write_results(self.path, legacy)
        before = Path(self.path, "results.json").read_bytes()
        self.assertEqual(research._load_results(self.path, self.skill), legacy)
        for args in (_args(), _args("step", knob=1)):
            with patch.object(research, "run_knob") as run:
                with self.assertRaisesRegex(ValueError, "legacy campaign"):
                    research._execute_campaign(args, self.skill, self.path, legacy)
            run.assert_not_called()
        self.assertEqual(Path(self.path, "results.json").read_bytes(), before)

    def test_closed_legacy_campaign_remains_a_noop(self):
        legacy = research._load_results(self.path, self.skill)
        legacy.pop("evaluation_frozen")
        legacy["status"] = "passed"
        with patch.object(research, "run_knob") as run:
            with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as exit:
                research._execute_campaign(_args(), self.skill, self.path, legacy)
        self.assertEqual(exit.exception.code, 0)
        run.assert_not_called()

    def test_status_distinguishes_unsaved_frozen_and_legacy_settings(self):
        results = research._load_results(self.path, self.skill)
        for state in ("not_started", "frozen", "legacy_unrecorded"):
            if state == "frozen":
                research._write_results(self.path, results)
            elif state == "legacy_unrecorded":
                results.pop("evaluation_frozen")
                research._write_results(self.path, results)
            output = io.StringIO()
            with (
                patch.object(sys, "argv", ["research", "status", "fixture", "--json"]),
                patch("skills.base.load_skill", return_value=self.skill),
                patch.object(research, "_exp_dir", return_value=self.path),
                patch.object(research, "_quiet", return_value=nullcontext()),
                redirect_stdout(output),
                self.assertRaises(SystemExit) as exit,
            ):
                research._main()
            self.assertEqual(exit.exception.code, 0)
            self.assertEqual(
                json.loads(output.getvalue())["evaluation_identity"], state
            )

    def test_resume_skips_recorded_negative_and_retains_original_block(self):
        results = research._load_results(self.path, self.skill)
        first = _block()
        first["evidence"] = "original negative"
        results["knobs"].append(first)
        original = copy.deepcopy(first)
        with patch.object(research, "run_knob", return_value=_block("K1")) as run:
            with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as exit:
                research._execute_campaign(_args(), self.skill, self.path, results)
        self.assertEqual(exit.exception.code, 10)
        run.assert_called_once_with(self.skill, self.skill.knobs[1], self.path, False)
        saved = research._load_results(self.path, self.skill)
        self.assertEqual(saved["knobs"][0], original)
        self.assertEqual(saved["status"], "budget_exhausted")
        with patch.object(research, "run_knob") as run:
            with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
                research._execute_campaign(_args(), self.skill, self.path, saved)
        run.assert_not_called()

    def test_duplicate_step_is_rejected_before_training(self):
        results = research._load_results(self.path, self.skill)
        results["knobs"].append(_block())
        before = copy.deepcopy(results)
        with patch.object(research, "run_knob") as run:
            with self.assertRaisesRegex(ValueError, "already has a recorded"):
                research._execute_campaign(
                    _args("step", knob=0), self.skill, self.path, results
                )
        run.assert_not_called()
        self.assertEqual(results, before)

    def test_journal_failure_cannot_erase_or_repeat_a_completed_measurement(self):
        results = research._load_results(self.path, self.skill)
        with patch.object(
            research, "append_journal", side_effect=OSError("disk error")
        ):
            with self.assertRaises(OSError):
                research._record_gate(
                    self.skill, self.skill.knobs[0], _block(), self.path, results, True
                )
        saved = research._load_results(self.path, self.skill)
        self.assertEqual(saved["knobs"], [_block()])
        with patch.object(research, "run_knob") as run:
            with self.assertRaisesRegex(ValueError, "already has a recorded"):
                research._execute_campaign(
                    _args("step", knob=0), self.skill, self.path, saved
                )
        run.assert_not_called()

    def test_from_knob_does_not_exhaust_unmeasured_budget(self):
        results = research._load_results(self.path, self.skill)
        with patch.object(research, "run_knob", return_value=_block("K1")):
            with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
                research._execute_campaign(
                    _args(from_knob=1), self.skill, self.path, results
                )
        self.assertEqual(results["status"], "running")

    def test_campaign_lock_rejects_overlapping_worker(self):
        with research._campaign_lock(self.path):
            with self.assertRaisesRegex(RuntimeError, "another worker"):
                with research._campaign_lock(self.path):
                    self.fail("second worker acquired an active campaign")


class GitIntegrity(unittest.TestCase):
    def test_gate_commit_contains_current_json_and_excludes_unrelated_staging(self):
        with tempfile.TemporaryDirectory(prefix="research_selftest_git_") as root:

            def git(*args):
                return subprocess.run(
                    ["git", *args],
                    cwd=root,
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout.strip()

            git("init", "-q")
            git("config", "user.name", "Research Selftest")
            git("config", "user.email", "selftest@example.invalid")
            git("config", "commit.gpgsign", "false")
            Path(root, "base").write_text("base\n")
            git("add", "base")
            git("commit", "-qm", "base")
            parent = git("rev-parse", "HEAD")
            Path(root, "unrelated").write_text("staged user draft\n")
            git("add", "unrelated")
            exp = Path(root, "experiments", "integrity_selftest")
            exp.mkdir(parents=True)
            (exp / "journal.md").write_text("recorded gate\n")
            skill, block = _skill(), _block()
            with patch.object(research, "ROOT", root):
                results = research._load_results(str(exp), skill)
                sha = research._record_gate(
                    skill, skill.knobs[0], block, str(exp), results, False
                )
            changed = git("show", "--pretty=", "--name-only", sha).splitlines()
            self.assertEqual(
                set(changed),
                {
                    "experiments/integrity_selftest/journal.md",
                    "experiments/integrity_selftest/results.json",
                },
            )
            committed = json.loads(
                git("show", f"{sha}:experiments/integrity_selftest/results.json")
            )
            self.assertEqual(committed, results)
            self.assertEqual(committed["knobs"][0]["git"]["parent_commit"], parent)
            self.assertEqual(git("diff", "--cached", "--name-only"), "unrelated")
            self.assertEqual(git("diff", "HEAD", "--name-only", "--", str(exp)), "")


class WorldModelIntegrity(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="research_selftest_wm_")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.exp = self.root / "experiments" / "integrity_selftest"
        (self.exp / "artifacts").mkdir(parents=True)
        self.patcher = patch.object(research, "ROOT", str(self.root))
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def _fake_loader(self, tiny=True):
        fake = SimpleNamespace(MODEL="original model path")

        def load_or_train(device):
            self.assertEqual(device, "cpu")
            path = Path(fake.MODEL)
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"synthetic stand-in bytes")
            return None, None, None, None, {"autotrained_tiny": tiny}

        fake.load_or_train = load_or_train
        return fake

    def test_real_gate_without_world_model_fails_before_loading_or_training(self):
        with self.assertRaisesRegex(FileNotFoundError, "world model missing"):
            with research._world_model_scope(str(self.exp), False):
                self.fail("a real gate entered without a WM")
        self.assertFalse((self.root / "output").exists())

    def test_dry_world_model_is_scoped_and_hashed(self):
        import eval

        fake = self._fake_loader()
        with patch.object(eval, "eval_closed_loop", fake, create=True):
            with research._world_model_scope(str(self.exp), True) as provenance:
                self.assertIn("selftest", provenance["path"])
                self.assertEqual(len(provenance["sha256"]), 64)
        self.assertEqual(fake.MODEL, "original model path")
        self.assertFalse((self.root / "output").exists())

    def test_real_gate_rejects_tiny_world_model(self):
        import eval

        output = self.root / "output"
        output.mkdir()
        (output / "world_model.pth").write_bytes(b"tiny")
        with patch.object(eval, "eval_closed_loop", self._fake_loader(), create=True):
            with self.assertRaisesRegex(ValueError, "tiny selftest"):
                with research._world_model_scope(str(self.exp), False):
                    self.fail("real gate accepted a tiny WM")

    def test_gate_detects_changes_to_either_protected_world_model(self):
        import eval

        output = self.root / "output"
        output.mkdir()
        for name in ("world_model.pth", "world_model_unified.pth"):
            (output / name).write_bytes(b"pinned")
        for name in ("world_model.pth", "world_model_unified.pth"):
            with patch.object(
                eval, "eval_closed_loop", self._fake_loader(tiny=False), create=True
            ):
                with self.assertRaisesRegex(RuntimeError, "world model changed"):
                    with research._world_model_scope(str(self.exp), False):
                        (output / name).write_bytes(b"changed")
            (output / name).write_bytes(b"pinned")


def selftest():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print(f"RESEARCH-INTEGRITY OK: {result.testsRun} isolated regression tests")


if __name__ == "__main__":
    selftest()

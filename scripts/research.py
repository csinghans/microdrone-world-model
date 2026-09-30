"""The autonomous research loop: one command, gates all the way down.

    python -m scripts.research skills/gap_flight            # full loop (run)
    python -m scripts.research step skills/gap_flight --knob 1
    python -m scripts.research step skills/gap_flight --knob-json deviation.json
    python -m scripts.research status skills/gap_flight
    python -m scripts.research --selftest                   # --dry K0, asserts

Encodes the house discipline: one knob per run; pre-registered criteria are
immutable (the skill file froze them); guards protect everything the
champion already does; any cell landing within ±recheck_margin of its bar
gets a fresh recheck_n block POOLED with the original (judged at combined
n — replacement would re-roll the die; see experiments/sweep2_noise);
negative results are recorded, never retried into passing. Every gate
appends a mechanical block to experiments/<skill>/journal.md, updates
results.json, and (unless --no-commit) commits the experiments/<skill>/
paths.

Exit codes: 0 = all targets met · 10 = gate recorded, campaign continues ·
2 = harness error.
"""

import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timezone

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _exp_dir(skill_name: str, dry: bool) -> str:
    slug = skill_name.replace("-", "_") + ("_selftest" if dry else "")
    d = os.path.join(ROOT, "experiments", slug)
    os.makedirs(os.path.join(d, "artifacts"), exist_ok=True)
    return d


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _frozen_criteria(skill) -> list:
    return [
        {
            "cell": c.cell,
            "metric": c.metric,
            "op": c.op,
            "bar": c.bar,
            "kind": c.kind,
        }
        for c in skill.criteria
    ]


def _frozen_evaluation(skill) -> dict:
    """Detached JSON snapshot; nested cell kwargs must not alias the live skill."""
    return json.loads(
        json.dumps(
            {
                "cells": [asdict(cell) for cell in skill.cells],
                "recheck_n": skill.recheck_n,
                "recheck_margin": skill.recheck_margin,
            },
            allow_nan=False,
        )
    )


def _require_frozen_evaluation(results, skill):
    if "evaluation_frozen" not in results:
        print(
            "RESEARCH WARNING: legacy campaign has no frozen evaluation "
            "specification; continuing with current settings recorded only on "
            "the new measurement. Historical evaluation remains unrecorded.",
            file=sys.stderr,
        )
        return
    if results["evaluation_frozen"] != _frozen_evaluation(skill):
        raise ValueError("campaign evaluation differs from the frozen specification")


def _prepare_measurement(exp_dir, results, skill):
    _require_frozen_evaluation(results, skill)
    if not os.path.exists(os.path.join(exp_dir, "results.json")):
        # Persist before the first fit/flight, so an interrupted first knob
        # cannot silently acquire a new exam on resumption.
        _write_results(exp_dir, results)


def _load_results(exp_dir: str, skill) -> dict:
    p = os.path.join(exp_dir, "results.json")
    if os.path.exists(p):
        with open(p) as f:
            results = json.load(f)
        if (results["skill"], results["skill_version"]) != (skill.name, skill.version):
            raise ValueError("campaign skill/version differs from the saved record")
        frozen = results["targets_frozen"]
        current = _frozen_criteria(skill)
        # Historical records omitted kind. Preserve those records, while
        # checking every field they actually froze; new campaigns freeze it too.
        comparable = [{k: c[k] for k in old} for old, c in zip(frozen, current)]
        if len(frozen) != len(current) or frozen != comparable:
            raise ValueError("campaign criteria differ from the frozen record")
        if "evaluation_frozen" in results:
            _require_frozen_evaluation(results, skill)
        ids = [b["id"] for b in results["knobs"]]
        if len(ids) != len(set(ids)):
            raise ValueError("campaign contains duplicate recorded knob ids")
        return results
    return {
        "skill": skill.name,
        "skill_version": skill.version,
        "status": "running",
        "targets_frozen": _frozen_criteria(skill),
        "evaluation_frozen": _frozen_evaluation(skill),
        "knobs": [],
    }


def _write_results(exp_dir: str, results: dict) -> None:
    """An interrupted write must not destroy earlier measurements."""
    path = os.path.join(exp_dir, "results.json")
    fd, temporary = tempfile.mkstemp(prefix=".results-", dir=exp_dir)
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(results, f, indent=1, allow_nan=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextmanager
def _world_model_scope(exp_dir: str, dry: bool):
    """Real gates require a real WM; dry stand-ins stay inside selftest paths."""
    paths = [
        os.path.join(ROOT, "output", name)
        for name in ("world_model.pth", "world_model_unified.pth")
    ]

    def snapshot():
        return {p: _sha256(p) if os.path.exists(p) else None for p in paths}

    before = snapshot()
    wm_path = paths[0]
    if not dry and before[wm_path] is None:
        raise FileNotFoundError(
            f"world model missing: {wm_path}; fetch champions before a real gate"
        )
    from eval import eval_closed_loop

    previous = eval_closed_loop.MODEL
    if dry and before[wm_path] is None:
        wm_path = os.path.join(exp_dir, "artifacts", "world_model_selftest.pth")
    eval_closed_loop.MODEL = wm_path
    try:
        loaded = eval_closed_loop.load_or_train(device="cpu")
        if not dry and loaded[-1].get("autotrained_tiny"):
            raise ValueError("a tiny selftest world model cannot support a real gate")
        wm_sha = _sha256(wm_path)
        yield {"path": os.path.relpath(wm_path, ROOT), "sha256": wm_sha}
        if _sha256(wm_path) != wm_sha:
            raise RuntimeError("the evaluation world model changed during the gate")
    finally:
        eval_closed_loop.MODEL = previous
        if snapshot() != before:
            raise RuntimeError("a protected world model changed during the gate")


def train_knob(skill, knob, exp_dir: str, dry: bool) -> str:
    """Produce (or locate) the policy artifact for a knob."""
    if knob.kind == "zero_shot":
        if knob.policy_path.startswith("builtin:"):
            # not a zip: a named baseline (the duel skills bench the
            # reactive / hand-MPC contenders on the same cells and seeds)
            return knob.policy_path
        path = os.path.join(ROOT, knob.policy_path)
        if dry and not os.path.exists(path):
            # CI runners have no real champions (output/ is git-ignored) and
            # a dry gate judges plumbing, not skill — train a tiny stand-in
            # into the *_selftest dir so real artifacts are never touched.
            # Real campaigns keep the hard assert below: a missing champion
            # must fail loudly, never silently substitute.
            from planner.learned_policy import train

            path = os.path.join(exp_dir, "artifacts", "ppo_dry_standin_selftest.zip")
            if not os.path.exists(path):
                train(1024, out=path)
            return path
        assert os.path.exists(path), f"zero-shot policy missing: {path}"
        return path
    if knob.kind == "world_model":
        raise ValueError("world_model knobs are reserves — run them by hand for now")
    from planner.learned_policy import train

    kwargs = dict(knob.train_kwargs)
    if dry:
        kwargs["timesteps"] = 1024
    suffix = "_recurrent" if kwargs.get("recurrent") else ""  # load_policy sniffs it
    out = os.path.join(
        exp_dir,
        "artifacts",
        f"ppo_{skill.name.replace('-', '_')}_{knob.id}{suffix}.zip",
    )
    train(out=out, **kwargs)
    return out


def _policy_factory(zip_path: str, *, wm_path: str | None = None):
    from eval.eval_closed_loop import load_or_train
    from planner.learned_policy import LearnedPolicy, load_policy

    if wm_path is None:
        enc, pred, cheads, nhead, meta = load_or_train(device="cpu")
    else:
        from world_model.training import load_model

        enc, pred, cheads, nhead, meta = load_model(wm_path, device="cpu")
        if meta.get("autotrained_tiny"):
            raise ValueError("a tiny selftest world model cannot support a real gate")
    if zip_path == "builtin:reactive":
        # the privileged-direction danger-now baseline: it can only lose
        # on timing (run_scenario_episode live-refreshes its .pillars)
        from planner.latent_mpc import ReactivePolicy

        return lambda speed: ReactivePolicy(enc, nhead)
    if zip_path == "builtin:wm_mpc":
        from planner.latent_mpc import WMPolicy

        return lambda speed: WMPolicy(enc, pred, cheads, meta, speed=speed)
    if zip_path.startswith("builtin:"):
        raise ValueError(f"unknown builtin policy: {zip_path}")
    model = load_policy(zip_path)
    return lambda speed: LearnedPolicy(model, enc, pred, cheads, meta, speed=speed)


def run_cell(factory, cell, skill, env, n=None, seed0=None) -> dict:
    """Fly one eval cell; aggregate crash/reached/success/custom metrics."""
    from eval.episode import run_scenario_episode

    n = n or cell.n_seeds
    seed0 = seed0 if seed0 is not None else cell.seed0
    agg = {"crash": 0, "reached": 0, "success": 0, "clear": []}
    custom_sums: dict = {}
    for i in range(n):
        pol = factory(cell.speed)
        if cell.world is None:
            from eval.eval_closed_loop import run_episode

            ep = run_episode(env, pol, seed0 + i, speed=cell.speed, **cell.kwargs)
            ep.setdefault("scenario_meta", {})
            ep.setdefault("path", np.zeros((1, 3)))
        else:
            ep = run_scenario_episode(env, pol, seed0 + i, cell.world, cell.speed)
        agg["crash"] += int(ep["crashed"])
        agg["reached"] += int(ep["reached"])
        agg["clear"].append(float(ep["min_clear"]))
        if skill.episode_metrics:
            for k, v in skill.episode_metrics(ep).items():
                custom_sums[k] = custom_sums.get(k, 0.0) + float(v)
        agg["success"] += int(bool(skill.success(ep)))
    out = {
        "n": n,
        "seed0": seed0,
        "crash": agg["crash"] / n,
        "reached": agg["reached"] / n,
        "success": agg["success"] / n,
        "clearance_mean": float(np.mean(agg["clear"])),
        "custom": {k: v / n for k, v in custom_sums.items()},
    }
    return out


def evaluate_gate(skill, cells_results: dict, factory, env, dry: bool) -> dict:
    """Apply criteria; any cell within ±recheck_margin of a bar gets a fresh
    recheck_n block whose result is **pooled** with the original (judged at
    combined n). Pooling, never replacement: on a binomial cell a
    replacement recheck just re-rolls the die — measured the hard way in
    experiments/sweep2_noise (a passing 6.7 % first read was replaced by
    the one 13.3 % block in ten). Semantics changed 2026-07-05, prospective."""

    def measurement(cr):
        res = cells_results[cr.cell]
        value = float(res["custom"].get(cr.metric, res.get(cr.metric)))
        if not np.isfinite(value):
            raise ValueError(f"non-finite metric: {cr.cell} {cr.metric}")
        return value

    # Choose rechecks from the ORIGINAL measurements, before any pooling.
    # Otherwise a later criterion can pool a cell after an earlier criterion
    # has already been judged, leaving a stale (even falsely passing) verdict.
    rechecked = {
        cr.cell
        for cr in skill.criteria
        if abs(measurement(cr) - cr.bar) < skill.recheck_margin
    }
    for cell in skill.cells:
        if cell.id not in rechecked:
            continue
        res = cells_results[cell.id]
        n2 = 3 if dry else skill.recheck_n
        re = run_cell(
            factory,
            cell,
            skill,
            env,
            n=n2,
            seed0=res["seed0"] + max(1000, res["n"]),
        )
        if res["custom"].keys() != re["custom"].keys():
            raise ValueError(f"custom metric keys changed in recheck: {cell.id}")
        res["initial"] = dict(res)
        res["recheck"] = re
        n1, tot = res["n"], res["n"] + re["n"]
        for key in ("crash", "reached", "success", "clearance_mean"):
            res[key] = (res[key] * n1 + re[key] * re["n"]) / tot
        res["custom"] = {
            k: (res["custom"][k] * n1 + v * re["n"]) / tot
            for k, v in re["custom"].items()
        }
        res["n"] = tot
        res["pooled"] = True

    verdicts = []
    for cr in skill.criteria:
        measured = measurement(cr)
        verdicts.append(
            {
                "name": f"{cr.cell} {cr.metric}{cr.op}{cr.bar}",
                "kind": cr.kind,
                "measured": float(measured),
                "pass": bool(cr.check(float(measured))),
                "rechecked": cr.cell in rechecked,
            }
        )
    targets_ok = all(v["pass"] for v in verdicts if v["kind"] == "target")
    guards_ok = all(v["pass"] for v in verdicts if v["kind"] == "guard")
    verdict = (
        "passed"
        if (targets_ok and guards_ok)
        else ("guard_regression" if not guards_ok else "continue")
    )
    return {"verdict": verdict, "criteria": verdicts, "guards_ok": guards_ok}


def append_journal(exp_dir: str, skill, knob, cells: dict, gate: dict) -> None:
    config = json.dumps(knob.train_kwargs) if knob.train_kwargs else knob.policy_path
    lines = [
        f"\n## {knob.id} — {knob.desc} ({_now()})",
        f"Hypothesis: {knob.hypothesis}",
        f"Config: {config}",
        "",
        "| cell | n | crash | success | clearance | custom |",
        "|---|---|---|---|---|---|",
    ]
    for cid, r in cells.items():
        cust = " ".join(f"{k}={v:.2f}" for k, v in r["custom"].items())
        lines.append(
            f"| {cid} | {r['n']} | {r['crash']:.0%} | {r['success']:.0%} "
            f"| {r['clearance_mean']:.2f} | {cust} |"
        )
    for v in gate["criteria"]:
        mark = "PASS" if v["pass"] else "FAIL"
        re = " (rechecked)" if v["rechecked"] else ""
        lines.append(f"- {v['name']}: {v['measured']:.2f} {mark}{re}")
    lines.append(f"\n**Gate verdict: {gate['verdict']}**")
    lines.append("\n### Researcher notes\n(unattended run)\n")
    with open(os.path.join(exp_dir, "journal.md"), "a") as f:
        f.write("\n".join(lines))


def git_commit_gate(skill, knob, gate, exp_dir: str) -> str:
    rel = os.path.relpath(exp_dir, ROOT)
    msg = f"gate({skill.name}): {knob.id} — {gate['verdict']}"
    try:
        subprocess.run(["git", "add", rel], cwd=ROOT, check=True, capture_output=True)
        command = ["git", "commit", "-q", "-m", msg]
        # The runner is agent-agnostic: whoever drives the gate declares the
        # trailer (e.g. RESEARCH_GATE_COAUTHOR="Codex <noreply@openai.com>").
        coauthor = os.environ.get("RESEARCH_GATE_COAUTHOR", "").strip()
        if coauthor:
            command += ["-m", f"Co-Authored-By: {coauthor}"]
        subprocess.run(
            command + ["--only", "--", rel],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
        sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        return sha
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "gate files were saved, but their path-scoped commit failed; "
            "repair and commit the saved files without rerunning the measurement"
        ) from exc


def run_knob(skill, knob, exp_dir: str, dry: bool) -> dict:
    started = _now()
    with _world_model_scope(exp_dir, dry) as wm:
        from sim.envs import make_env

        zip_path = train_knob(skill, knob, exp_dir, dry)
        factory = _policy_factory(zip_path)
        env = make_env()
        cells = {}
        try:
            for cell in skill.cells:
                n = 2 if dry else None
                cells[cell.id] = run_cell(factory, cell, skill, env, n=n)
                print(f"  [{knob.id}] {cell.id}: {cells[cell.id]}")
            gate = evaluate_gate(skill, cells, factory, env, dry)
        finally:
            env.close()
    block = {
        "id": knob.id,
        "kind": knob.kind,
        "desc": knob.desc,
        "hypothesis": knob.hypothesis,
        "config": knob.train_kwargs or {"policy_path": knob.policy_path},
        "artifacts": (
            {"policy": zip_path, "sha256": None}  # builtin baseline, no file
            if zip_path.startswith("builtin:")
            else {
                "policy_zip": os.path.relpath(zip_path, ROOT),
                "sha256": _sha256(zip_path),
            }
        ),
        "cells": cells,
        "gate": gate,
        "world_model": wm,
        "timing": {"started": started, "ended": _now()},
    }
    return block


def _record_gate(skill, knob, block, exp_dir, results, no_commit):
    _require_frozen_evaluation(results, skill)
    if any(b["id"] == block["id"] for b in results["knobs"]):
        raise ValueError(f"{block['id']} already has a recorded measurement")
    if "evaluation_frozen" not in results:
        block["evaluation_at_measurement"] = _frozen_evaluation(skill)
    results["knobs"].append(block)
    if block["gate"]["verdict"] == "passed":
        results["status"] = "passed"
    else:
        done = {b["id"] for b in results["knobs"]}
        results["status"] = (
            "budget_exhausted"
            if all(k.id in done for k in skill.knobs[: skill.max_knobs])
            else "running"
        )
    if not no_commit:
        # A commit cannot contain its own hash. Record its parent revision
        # in JSON; emit the resulting gate commit only after saving the JSON.
        block["git"] = {
            "parent_commit": subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        }
    _write_results(exp_dir, results)
    # Persist the measurement before ancillary journal/Git writes. If either
    # fails, resuming must still see this knob as measured, never fly it again.
    append_journal(exp_dir, skill, knob, block["cells"], block["gate"])
    if not no_commit:
        return git_commit_gate(skill, knob, block["gate"], exp_dir)
    return None


def _invalidate_measurement(skill, exp_dir, results, knob_id, reason, no_commit):
    """Retain the exact invalid measurement; release only an explicit repair."""
    if not reason or not reason.strip():
        raise ValueError("harness invalidation requires a concrete --reason")
    original = next((b for b in results["knobs"] if b["id"] == knob_id), None)
    if original is None:
        raise ValueError(f"no active measurement for {knob_id}")
    updated = copy.deepcopy(results)
    updated.setdefault("invalidated_measurements", []).append(
        {
            "id": knob_id,
            "reason": reason.strip(),
            "invalidated_at": _now(),
            "previous_results_sha256": _sha256(os.path.join(exp_dir, "results.json")),
            "record": copy.deepcopy(original),
        }
    )
    updated["knobs"] = [b for b in updated["knobs"] if b["id"] != knob_id]
    updated["status"] = (
        "passed"
        if any(b["gate"]["verdict"] == "passed" for b in updated["knobs"])
        else "running"
    )
    _write_results(exp_dir, updated)
    results.clear()
    results.update(updated)
    with open(os.path.join(exp_dir, "journal.md"), "a") as stream:
        stream.write(
            f"\n## Harness invalidation: {knob_id} ({_now()})\n\n"
            f"{reason.strip()}\n\nOriginal numbers retained verbatim in "
            "results.json / invalidated_measurements. Repair the harness, then "
            "use step for the same knob; scientific negatives remain final.\n"
        )
    if not no_commit:
        from types import SimpleNamespace

        return git_commit_gate(
            skill,
            SimpleNamespace(id=knob_id),
            {"verdict": "harness-invalidated"},
            exp_dir,
        )
    return None


@contextmanager
def _campaign_lock(exp_dir):
    """Prevent concurrent workers from replacing each other's saved gates."""
    import fcntl

    key = hashlib.sha256(os.path.realpath(exp_dir).encode()).hexdigest()
    path = os.path.join(tempfile.gettempdir(), f"microdrone-research-{key}.lock")
    with open(path, "a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("another worker is running this campaign") from exc
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


class _Forward:
    """The doctor's crash-test dummy: cruise straight, decide nothing.
    It only has to prove a world spawns and an episode completes."""

    def begin(self, pillars) -> None:
        del pillars

    def decide(self, frame, state) -> int:
        del frame, state
        from planner.action_set import FORWARD

        return FORWARD


class _quiet:
    """FD-level stdout silencer: pybullet's C-side chatter (build-time
    banner at import, URDF dumps at env creation) prints straight to
    fd 1 and would corrupt --json output otherwise."""

    def __enter__(self):
        sys.stdout.flush()  # legit prior output goes out before the swap
        self._saved = os.dup(1)
        self._null = os.open(os.devnull, os.O_WRONLY)
        os.dup2(self._null, 1)
        return self

    def __exit__(self, *exc):
        # flush BEFORE restoring: chatter buffered during the quiet window
        # must drain to devnull, not to the restored real stdout
        sys.stdout.flush()
        os.dup2(self._saved, 1)
        os.close(self._saved)
        os.close(self._null)
        return False


_HUSH: _quiet | None = None  # active whole-process hush in --json mode


def _print_unhushed(text: str) -> None:
    """Restore fd 1 (if hushed) and emit machine-readable output — the
    guarantee --json consumers rely on: stdout is ONE parseable object."""
    global _HUSH
    if _HUSH is not None:
        _HUSH.__exit__(None, None, None)
        _HUSH = None
    sys.stdout.flush()
    print(text)


def doctor(skill, as_json: bool) -> int:
    """Preflight for newcomers and operator-mode agents: everything a
    campaign needs, checked in seconds — before hours burn. Exit 0 when
    every hard check passes (warnings allowed), 2 otherwise."""
    import time

    from eval.episode import run_scenario_episode
    from sim.envs import make_env

    checks: list = []  # (name, "pass"|"warn"|"fail", detail)
    checks.append(
        (
            "skill schema",
            "pass",
            f"{skill.name} v{skill.version}: {len(skill.cells)} cells, "
            f"{len(skill.knobs)} knobs (max {skill.max_knobs})",
        )
    )

    # every unique world spawns and flies one episode with a dumb policy
    # (fd-silenced: pybullet's URDF chatter would corrupt --json output)
    ep_secs = []
    with _quiet():
        env = make_env()
        for cell in {c.world: c for c in skill.cells}.values():
            t0 = time.time()
            try:
                if cell.world is None:
                    from eval.eval_closed_loop import run_episode

                    run_episode(
                        env, _Forward(), cell.seed0, speed=cell.speed, **cell.kwargs
                    )
                else:
                    run_scenario_episode(
                        env, _Forward(), cell.seed0, cell.world, cell.speed
                    )
                ep_secs.append(time.time() - t0)
                checks.append(
                    (
                        f"world '{cell.world or 'classic'}' flies",
                        "pass",
                        f"1 episode in {ep_secs[-1]:.1f}s",
                    )
                )
            except Exception as e:  # noqa: BLE001 — the report IS the product
                checks.append(
                    (f"world '{cell.world or 'classic'}' flies", "fail", str(e))
                )
        env.close()

    # zero-shot artifacts exist (builtins are always available)
    for k in skill.knobs:
        if k.kind == "zero_shot" and not k.policy_path.startswith("builtin:"):
            p = os.path.join(ROOT, k.policy_path)
            if os.path.exists(p):
                checks.append((f"{k.id} policy zip", "pass", k.policy_path))
            else:
                checks.append(
                    (
                        f"{k.id} policy zip",
                        "fail",
                        f"{k.policy_path} missing — run: python -m "
                        f"scripts.fetch_champions",
                    )
                )

    # Missing WMs are a hard error for research; only --dry may make a stand-in.
    wm = os.path.join(ROOT, "output", "world_model.pth")
    checks.append(
        ("world model checkpoint", "pass" if os.path.exists(wm) else "fail")
        + (
            (wm,)
            if os.path.exists(wm)
            else (
                "missing — real research gates require the checkpoint; "
                "run: python -m scripts.fetch_champions",
            )
        )
    )

    # convention lint: the fast-solo cell is noisy — n=60 is the paid-for lesson
    for c in skill.cells:
        if "sweep@2.0" in c.id and c.n_seeds < 60:
            checks.append(
                (
                    f"{c.id} sample size",
                    "warn",
                    f"n={c.n_seeds} < 60 — this cell's n=30 reads bounced "
                    f"27/22/8/17 across one campaign (see docs/GLOSSARY.md)",
                )
            )

    # the runner makes path-scoped commits; a dirty tree muddies them
    import subprocess

    dirty = subprocess.run(
        ["git", "status", "--porcelain"], capture_output=True, text=True, cwd=ROOT
    ).stdout.strip()
    checks.append(
        ("git tree", "pass" if not dirty else "warn")
        + (
            ("clean",)
            if not dirty
            else (f"{len(dirty.splitlines())} uncommitted paths",)
        )
    )

    # the bill, before it is paid
    sec = sum(ep_secs) / max(len(ep_secs), 1)
    eps_per_knob = sum(c.n_seeds for c in skill.cells)
    est = {
        "episodes_per_knob": eps_per_knob,
        "est_minutes_per_eval_knob": round(eps_per_knob * sec / 60, 1),
        "training_knobs": [
            {"id": k.id, "timesteps": k.train_kwargs.get("timesteps")}
            for k in skill.knobs
            if k.kind == "policy"
        ],
        "note": "training adds ~30-60 min per 450k steps on Apple Silicon "
        "(slower on CPU); rechecks add n=60 reruns per borderline cell",
    }

    ok = all(s != "fail" for _n, s, _d in checks)
    if as_json:
        payload = json.dumps(
            {
                "skill": skill.name,
                "ok": ok,
                "checks": [{"name": n, "status": s, "detail": d} for n, s, d in checks],
                "estimate": est,
            },
            indent=1,
        )
        _print_unhushed(payload)
    else:
        mark = {"pass": "ok  ", "warn": "WARN", "fail": "FAIL"}
        for n, s, d in checks:
            print(f"  [{mark[s]}] {n}: {d}")
        print(
            f"  estimate: ~{est['episodes_per_knob']} episodes/knob "
            f"(~{est['est_minutes_per_eval_knob']} min eval) + "
            f"{len(est['training_knobs'])} training knob(s); {est['note']}"
        )
        print(f"DOCTOR {'OK' if ok else 'FAIL'}: {skill.name}")
    return 0 if ok else 2


def _main() -> None:
    argv = sys.argv[1:]
    if "--selftest" in argv:
        rc = _selftest()
        sys.exit(rc)
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?", default="run")
    ap.add_argument("skill", nargs="?")
    ap.add_argument("--knob", type=int, default=None)
    ap.add_argument("--knob-json", default=None)
    ap.add_argument("--knob-id", help="recorded knob ID for harness invalidation")
    ap.add_argument("--reason", help="concrete harness fault, never a failed bar")
    ap.add_argument("--from-knob", type=int, default=0)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--no-commit", action="store_true")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()
    if args.cmd not in ("run", "step", "status", "doctor", "invalidate"):
        args.cmd, args.skill = "run", args.cmd

    global _HUSH
    if args.json:  # imports below chatter on fd 1 (pybullet's banner)
        _HUSH = _quiet()
        _HUSH.__enter__()

    from skills.base import load_skill

    if args.skill is None:
        ap.error("a skill is required")
    skill = load_skill(args.skill)
    exp_dir = _exp_dir(skill.name, args.dry)
    results = _load_results(exp_dir, skill)

    if args.cmd == "doctor":
        sys.exit(doctor(skill, args.json))

    if args.cmd == "status":
        evaluation_identity = (
            "not_started"
            if not os.path.exists(os.path.join(exp_dir, "results.json"))
            else "frozen" if "evaluation_frozen" in results else "legacy_unrecorded"
        )
        done = {kb["id"] for kb in results["knobs"]}
        nxt = next(
            (
                {"index": i, "id": k.id}
                for i, k in enumerate(skill.knobs[: skill.max_knobs])
                if k.id not in done
            ),
            None,
        )
        if results["status"] in ("passed", "budget_exhausted"):
            nxt = None
        if args.json:
            _print_unhushed(
                json.dumps(
                    {
                        "skill": results["skill"],
                        "status": results["status"],
                        "evaluation_identity": evaluation_identity,
                        "knobs": [
                            {"id": kb["id"], "verdict": kb["gate"]["verdict"]}
                            for kb in results["knobs"]
                        ],
                        "next_knob": nxt,
                    },
                    indent=1,
                )
            )
            sys.exit(0)
        print(json.dumps({k: results[k] for k in ("skill", "status")}, indent=1))
        if "evaluation_frozen" not in results:
            print("  evaluation: legacy_unrecorded; new measurements record settings")
        for kb in results["knobs"]:
            print(f"  {kb['id']}: {kb['gate']['verdict']}")
        if nxt:
            print(f"  next: --knob {nxt['index']} ({nxt['id']})")
        sys.exit(0)

    with _campaign_lock(exp_dir):
        # Read again under the lock: status/doctor are read-only, but a
        # campaign must never train against another worker's stale record.
        _execute_campaign(args, skill, exp_dir, _load_results(exp_dir, skill))


def _execute_campaign(args, skill, exp_dir, results):
    from skills.base import Knob

    if args.cmd == "invalidate":
        commit = _invalidate_measurement(
            skill, exp_dir, results, args.knob_id, args.reason, args.no_commit
        )
        print(f"RESEARCH HARNESS INVALIDATED: {args.knob_id}; original record retained")
        if commit:
            print(f"GATE-COMMIT {commit}")
        sys.exit(0)

    done = {b["id"] for b in results["knobs"]}
    if args.cmd == "step":
        if args.knob_json:
            with open(args.knob_json) as f:
                spec = json.load(f)
            assert spec.get("rationale"), "a deviation knob requires a rationale"
            knob = Knob(
                spec["id"],
                spec.get("kind", "policy"),
                spec["desc"],
                spec.get("hypothesis", spec["rationale"]),
                train_kwargs=spec.get("train_kwargs", {}),
                policy_path=spec.get("policy_path"),
            )
        else:
            if args.knob is None or not 0 <= args.knob < len(skill.knobs):
                raise ValueError("step requires --knob with a valid schedule index")
            knob = skill.knobs[args.knob]
        if knob.id in done:
            raise ValueError(
                f"{knob.id} already has a recorded measurement; "
                "negative results cannot be retried or replaced"
            )
        _prepare_measurement(exp_dir, results, skill)
        block = run_knob(skill, knob, exp_dir, args.dry)
        commit = _record_gate(skill, knob, block, exp_dir, results, args.no_commit)
        print(f"RESEARCH-GATE {knob.id}: {block['gate']['verdict']}")
        if commit:
            print(f"GATE-COMMIT {commit}")
        sys.exit(0 if block["gate"]["verdict"] == "passed" else 10)

    # run: the full loop
    if results["status"] in ("passed", "budget_exhausted"):
        print(f"RESEARCH OK: {skill.name} already {results['status']}")
        sys.exit(0 if results["status"] == "passed" else 10)
    for i, knob in enumerate(skill.knobs[: skill.max_knobs]):
        if i < args.from_knob or knob.id in done:
            continue
        _prepare_measurement(exp_dir, results, skill)
        block = run_knob(skill, knob, exp_dir, args.dry)
        commit = _record_gate(skill, knob, block, exp_dir, results, args.no_commit)
        print(f"RESEARCH-GATE {knob.id}: {block['gate']['verdict']}")
        if commit:
            print(f"GATE-COMMIT {commit}")
        if block["gate"]["verdict"] == "passed":
            print(f"RESEARCH OK: {skill.name} targets met at {knob.id}")
            sys.exit(0)
    # --from-knob may intentionally leave earlier experiments unmeasured.
    # Do not label the whole budget exhausted merely because the loop ended.
    print(f"RESEARCH OK: {skill.name} {results['status']} — see journal")
    sys.exit(10)


def main() -> None:
    try:
        _main()
    except Exception as exc:
        print(f"RESEARCH HARNESS ERROR: {exc}", file=sys.stderr)
        sys.exit(2)


def _selftest() -> int:
    """--dry K0 end-to-end on gap-flight: schema + plumbing asserts."""
    from unittest.mock import patch

    argv = ["research", "step", "gap-flight", "--knob", "0", "--dry", "--no-commit"]
    with tempfile.TemporaryDirectory(prefix="research_selftest_") as exp:
        os.makedirs(os.path.join(exp, "artifacts"))
        with (
            patch.object(sys, "argv", argv),
            patch(__name__ + "._exp_dir", return_value=exp),
        ):
            try:
                main()
            except SystemExit as e:
                assert e.code in (0, 10), f"unexpected exit {e.code}"
        with open(os.path.join(exp, "results.json")) as f:
            res = json.load(f)
        assert res["knobs"] and res["knobs"][-1]["id"] == "K0"
        assert "gap@1.0" in res["knobs"][-1]["cells"]
        assert os.path.exists(os.path.join(exp, "journal.md"))
    print("RESEARCH OK: dry K0 gate end-to-end, journal + results schema assert")
    return 0


if __name__ == "__main__":
    main()

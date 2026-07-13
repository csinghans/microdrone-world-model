"""transit_gate_v2 R1 — per-state fidelity at seam-visited states.

K1's verdict named the surviving suspect: the pooled BC val is dominated
by native-start states, and the clone's fidelity ON the states a seam
actually visits was never measured. This probe rides the RECORD lineup
over the standing exam block and, at every slalom-stage decision,
records the executed action against the OracleWeave counterfactual at
the same state (weave is a pure function of (x, y) vs its begin()-built
gate ladder, so counterfactual queries are exact), plus a mirror
ObsBuilder vec (collect_hot's exact construction) so BOTH clones can be
scored offline on the SAME states — the v2 clone never flies the exam.

The journal (experiments/transit_gate_v2/journal.md, R1) owns the frozen
contrasts. Agreement is label-match, not correctness — the CONTRASTS
are the read, not the absolute level.

Run:
  python -m eval.eval_seam_fidelity --capture          # n=100 exam block
  python -m eval.eval_seam_fidelity --selftest
"""

import argparse
import json
import os

import numpy as np

STAGE_LEN = 3.0  # sim.composite's constant (asserted at capture time)
RECORD_GATE = "experiments/integration_ft/hybrid4_n100.json"
V2_ZIP = "experiments/transit_gate_v2/artifacts/ppo_slalom_bigpot_v2.zip"
OUT_JSON = "experiments/transit_gate_v2/r1_seam_fidelity.json"
OUT_NPZ = "experiments/transit_gate_v2/artifacts/r1_capture.npz"

# frozen in the journal before any number
PRIMARY_CONFIRM = 0.03  # A_seam <= A_cold - this -> CONFIRMED
PRIMARY_REFUTE = 0.01  # A_seam >= A_cold - this -> REFUTED
CO_CONFIRM = 0.05  # A_broke <= A_cleared - this -> CONFIRMED
CO_REFUTE = 0.02
MIRROR_FLOOR = 0.99  # offline record-clone must reproduce executed
MATCH_EXPECT = 0.95  # per-seed outcome match vs the gate of record
MIN_BROKE_STAGES = 6  # co-primary readability floor
EARLY_WINDOW = 12  # decisions after stage entry


def _stage_window(pillars, k: int, stage_len: float = STAGE_LEN):
    """OracleRelay._stage_pillars, verbatim semantics."""
    lo, hi = k * stage_len - 0.2, (k + 1) * stage_len + 0.2
    return [p for p in pillars if lo <= float(p[0]) < hi]


def _branch(a_low: float, a_high: float, confirm: float, refute: float) -> str:
    """The suspected-deficit side vs its comparator, frozen thresholds.
    The 1e-9 keeps exact-boundary reads out of float purgatory (0.95 -
    0.03 is 0.9199... in binary; equality must count as CONFIRMED)."""
    if a_low <= a_high - confirm + 1e-9:
        return "CONFIRMED"
    if a_low >= a_high - refute - 1e-9:
        return "REFUTED"
    return "GRAY"


def _row_outcome(k: int, success: bool, break_at: int) -> str:
    """cleared / broke / postmortem for a stage-k row. Post-break stages
    in failed episodes are phantom flight (the runner judges crashes
    post-hoc and keeps stepping) — excluded from every read."""
    if success or k < break_at:
        return "cleared"
    if k == break_at:
        return "broke"
    return "postmortem"


class SeamProbe:
    """run_composite_episode probe: mirrors the target pilot's own view
    (StageLocal reset, executed-prev, stage-local x). For the slalom
    target it also queries weave counterfactually with the relay's
    stage-window pillars; for other targets (terminal_commit_v1) the
    weave column mirrors the executed action — the pot labels are the
    EXECUTED behavior."""

    def __init__(self, enc, pred, cheads, meta, target="slalom3_fixed"):
        self._stack = (enc, pred, cheads, meta)
        self.target = str(target)
        self.rows: list = []
        self.vecs: list = []

    def begin_course(self, seed: int, names) -> None:
        from planner.learned_policy import ObsBuilder

        self.seed, self.names = int(seed), tuple(names)
        self.ob = ObsBuilder(*self._stack, 1.0, x_progress=True)
        self._stage, self._prev, self._weave, self._dec = -1, 0, None, 0
        self._active = False

    def __call__(self, t, frame, state, a, scenario) -> None:
        x = float(state[0])
        k = int(np.clip(x // STAGE_LEN, 0, len(self.names) - 1))
        if k != self._stage:
            self._stage, self._prev, self._weave, self._dec = k, 0, None, 0
            self.ob.reset()
            self._active = self.names[k] == self.target
            if self._active and self.target == "slalom3_fixed":
                from eval.eval_arena_ceiling import OracleWeave

                self._weave = OracleWeave()
                self._weave.begin(_stage_window(scenario.positions(), k))
        if not self._active:
            return  # only target stages are recorded
        vec = self.ob.push(frame, float(state[1]), self._prev, x=x - k * STAGE_LEN)
        menu_exec = self.ob.ids.index(int(a))
        menu_weave = (
            self.ob.ids.index(int(self._weave.decide(frame, state)))
            if self._weave is not None
            else menu_exec
        )
        stage_pil = _stage_window(scenario.positions(), k)
        plane = (
            float(np.median([float(p[0]) for p in stage_pil])) if stage_pil else -1.0
        )
        self.rows.append(
            {
                "seed": self.seed,
                "k": k,
                "t": int(t),
                "dec": self._dec,
                "upstream": self.names[k - 1] if k > 0 else "",
                "exec": menu_exec,
                "weave": menu_weave,
                "x": x,
                "plane_x": plane,
            }
        )
        self.vecs.append(vec)
        self._prev = menu_exec
        self._dec += 1


def _agree(rows) -> float:
    return float(np.mean([r["exec"] == r["weave"] for r in rows])) if rows else -1.0


def _clustered(rows) -> float:
    """Mean of per-stage-instance agreement means."""
    by: dict = {}
    for r in rows:
        by.setdefault((r["seed"], r["k"]), []).append(r["exec"] == r["weave"])
    return float(np.mean([np.mean(v) for v in by.values()])) if by else -1.0


def _stages(rows) -> int:
    return len({(r["seed"], r["k"]) for r in rows})


def capture(
    n: int = 100,
    seed0: int = 110000,
    out_json: str = OUT_JSON,
    out_npz: str = OUT_NPZ,
    slalom_zip: str | None = None,
    target_stage: str = "slalom3_fixed",
    thread_commit: bool = False,
    course_k: int = 3,
    commit_hysteresis: bool = False,
) -> int:
    import torch  # noqa: F401  (torch before SB3 policies)

    from eval.eval_closed_loop import load_or_train
    from eval.eval_integration import (
        HYBRID,
        PerStageExperts,
        _load_all_skills,
        run_composite_episode,
    )
    from planner.action_set import FORWARD
    from sim.composite import STAGE_LEN as REAL_L
    from sim.composite import (
        course_for_seed,
        integration_metrics,
        integration_success,
        register_course,
    )
    from sim.envs import make_env

    assert float(REAL_L) == STAGE_LEN, "stage length drifted"
    _load_all_skills()
    enc, pred, cheads, _n, meta = load_or_train()
    probe = SeamProbe(enc, pred, cheads, meta, target=target_stage)
    from planner.learned_policy import ObsBuilder

    ids = ObsBuilder(enc, pred, cheads, meta, 1.0, x_progress=True).ids
    assert ids.index(FORWARD) == 0, "mirror entry-prev convention broken"

    experts = dict(HYBRID)
    if slalom_zip:  # R3+: the student is a later-round clone
        experts["slalom3_fixed"] = slalom_zip
    env = make_env()
    outcomes = []
    for i in range(n):
        seed = seed0 + i
        names = course_for_seed(seed, k=course_k)
        world = register_course(seed, k=course_k)
        probe.begin_course(seed, names)
        pol = PerStageExperts(names, 1.0, experts=dict(experts))
        if thread_commit:  # terminal_commit_v1: the privileged teacher
            from eval.eval_integration import ThreadCommitOracle

            pol = ThreadCommitOracle(pol, names, hysteresis=commit_hysteresis)
        ep = run_composite_episode(
            env,
            pol,
            seed,
            world,
            k=course_k,
            probe=probe,
        )
        ok = integration_success(ep)
        m = integration_metrics(ep)
        outcomes.append(
            {
                "seed": seed,
                "course": list(names),
                "success": bool(ok),
                "stages_cleared": int(m.get("stages_cleared", 0)),
                "stage_break_at": int(m.get("stage_break_at", -1)),
                "crash_t": int(ep["min_clear_step"]) if ep["crashed"] else -1,
            }
        )
        print(
            f"  [{i + 1}/{n}] seed={seed} {'PASS' if ok else 'fail'} "
            f"rows={len(probe.rows)}",
            flush=True,
        )
    env.close()
    if probe.target != "slalom3_fixed" or thread_commit:
        # collection mode (terminal_commit_v1): no R1 verdict semantics
        return _save_collection(probe, outcomes, n, seed0, out_json, out_npz)
    return _score(
        probe, outcomes, n, seed0, out_json, out_npz, experts["slalom3_fixed"]
    )


def _save_collection(probe, outcomes, n, seed0, out_json, out_npz) -> int:
    """Persist a pot-collection capture: rows with a cleared-stage kept
    mask (only stages cleared before any crash feed a pot — the
    collect_hot rule), outcomes, and basic stats. No contrasts."""
    by_seed = {o["seed"]: o for o in outcomes}
    for r in probe.rows:
        o = by_seed[r["seed"]]
        r["outcome"] = _row_outcome(r["k"], o["success"], o["stage_break_at"])
    kept = [r["outcome"] == "cleared" for r in probe.rows]
    os.makedirs(os.path.dirname(out_npz), exist_ok=True)
    np.savez_compressed(
        out_npz,
        vecs=np.asarray(probe.vecs, dtype=np.float32),
        seed=np.asarray([r["seed"] for r in probe.rows]),
        k=np.asarray([r["k"] for r in probe.rows]),
        t=np.asarray([r["t"] for r in probe.rows]),
        dec=np.asarray([r["dec"] for r in probe.rows]),
        exec_menu=np.asarray([r["exec"] for r in probe.rows]),
        weave_menu=np.asarray([r["weave"] for r in probe.rows]),
        upstream=np.asarray([r["upstream"] for r in probe.rows]),
        x=np.asarray([r["x"] for r in probe.rows]),
        plane_x=np.asarray([r["plane_x"] for r in probe.rows]),
        kept=np.asarray(kept),
        outcome=np.asarray([r["outcome"] for r in probe.rows]),
    )
    report = {
        "mode": "collection",
        "target": probe.target,
        "n": n,
        "seed0": seed0,
        "n_rows": len(probe.rows),
        "n_kept": int(sum(kept)),
        "success_rate": float(np.mean([o["success"] for o in outcomes])),
        "outcomes": outcomes,
    }
    with open(out_json, "w") as f:
        json.dump(report, f, indent=1)
    print(
        f"[collect] target={probe.target} rows={len(probe.rows)} "
        f"kept={sum(kept)} success={report['success_rate']:.3f} | "
        f"saved {out_json} + npz"
    )
    return 0


def _score(
    probe,
    outcomes,
    n: int,
    seed0: int,
    out_json: str,
    out_npz: str,
    flew_zip: str | None = None,
) -> int:
    from planner.dispatch import _model

    by_seed = {o["seed"]: o for o in outcomes}

    # annotate rows: outcome class + post-crash exclusion inside the
    # break stage (the runner keeps stepping after the judged crash)
    kept, postmortem = [], 0
    for r in probe.rows:
        o = by_seed[r["seed"]]
        cls = _row_outcome(r["k"], o["success"], o["stage_break_at"])
        if cls == "postmortem" or (
            cls == "broke" and o["crash_t"] >= 0 and r["t"] > o["crash_t"]
        ):
            postmortem += 1
            continue
        r["outcome"] = cls
        kept.append(r)

    cold = [r for r in kept if r["k"] == 0]
    seam = [r for r in kept if r["k"] > 0]
    a_cold, a_seam = _agree(cold), _agree(seam)
    c_cold, c_seam = _clustered(cold), _clustered(seam)
    primary = _branch(a_seam, a_cold, PRIMARY_CONFIRM, PRIMARY_REFUTE)
    primary_cl = _branch(c_seam, c_cold, PRIMARY_CONFIRM, PRIMARY_REFUTE)
    if primary_cl != primary:
        primary = "GRAY"  # pooled and clustered must agree, else recheck

    s_broke = [r for r in seam if r["outcome"] == "broke"]
    s_clear = [r for r in seam if r["outcome"] == "cleared"]
    n_broke_stages = _stages(s_broke)
    a_broke, a_clear = _agree(s_broke), _agree(s_clear)
    co = _branch(a_broke, a_clear, CO_CONFIRM, CO_REFUTE)
    co_readable = n_broke_stages >= MIN_BROKE_STAGES
    if not co_readable:
        co = "UNREADABLE"

    # verdict synthesis, frozen: lesion iff EITHER confirms; dead iff
    # BOTH refute; anything else -> recheck block
    if "CONFIRMED" in (primary, co):
        verdict = "FIDELITY-IS-THE-LESION"
    elif primary == "REFUTED" and co == "REFUTED":
        verdict = "FIDELITY-STORY-DEAD"
    else:
        verdict = "GRAY-RECHECK"

    # instrument: the clone that FLEW must reproduce its executed acts
    # offline from the mirror vecs (R3+: that is a later-round clone)
    V = np.asarray(probe.vecs, dtype=np.float32)
    keep_ix = [i for i, r in enumerate(probe.rows) if "outcome" in r]
    from eval.eval_integration import HYBRID

    rec_zip = flew_zip or HYBRID["slalom3_fixed"]
    execs = np.asarray([r["exec"] for r in kept])
    weaves = np.asarray([r["weave"] for r in kept])
    rec_pred, _ = _model(rec_zip).predict(V[keep_ix], deterministic=True)
    mirror = float(np.mean(np.asarray(rec_pred).astype(int) == execs))
    v2 = {"readable": bool(mirror >= MIRROR_FLOOR)}
    if v2["readable"] and os.path.exists(V2_ZIP):
        v2_pred, _ = _model(V2_ZIP).predict(V[keep_ix], deterministic=True)
        v2m = np.asarray(v2_pred).astype(int) == weaves
        m_cold = [i for i, r in enumerate(kept) if r["k"] == 0]
        m_seam = [i for i, r in enumerate(kept) if r["k"] > 0]
        m_brk = [
            i for i, r in enumerate(kept) if r["k"] > 0 and r["outcome"] == "broke"
        ]
        v2.update(
            a_cold=round(float(v2m[m_cold].mean()), 4) if m_cold else -1,
            a_seam=round(float(v2m[m_seam].mean()), 4) if m_seam else -1,
            a_seam_broke=round(float(v2m[m_brk].mean()), 4) if m_brk else -1,
        )

    # exam-outcome match vs the gate of record (env was rebuilt — drift
    # is a reproducibility finding, not a probe-killer)
    match = -1.0
    if os.path.exists(RECORD_GATE):
        with open(RECORD_GATE) as f:
            rec = {r["seed"]: r["success"] for r in json.load(f)["records"]}
        both = [s for s in by_seed if s in rec]
        if both:  # fresh-seed blocks share no exam seeds — match unread
            match = float(np.mean([by_seed[s]["success"] == rec[s] for s in both]))

    # context reads (declared, not barred)
    per_up: dict = {}
    for u in sorted({r["upstream"] for r in seam}):
        per_up[u] = round(_agree([r for r in seam if r["upstream"] == u]), 4)
    early = [r for r in seam if r["dec"] < EARLY_WINDOW]
    late = [r for r in seam if r["dec"] >= EARLY_WINDOW]
    last10 = []
    for key in {(r["seed"], r["k"]) for r in s_broke}:
        inst = sorted(
            (r for r in s_broke if (r["seed"], r["k"]) == key),
            key=lambda r: r["dec"],
        )
        last10 += inst[-10:]

    report = {
        "n": n,
        "seed0": seed0,
        "instrument": {
            "exam_outcome_match": round(match, 4),
            "match_expected": MATCH_EXPECT,
            "mirror_fidelity": round(mirror, 4),
            "mirror_floor": MIRROR_FLOOR,
            "postmortem_rows_excluded": postmortem,
        },
        "primary": {
            "a_cold": round(a_cold, 4),
            "a_seam": round(a_seam, 4),
            "clustered_cold": round(c_cold, 4),
            "clustered_seam": round(c_seam, 4),
            "n_cold_rows": len(cold),
            "n_seam_rows": len(seam),
            "n_cold_stages": _stages(cold),
            "n_seam_stages": _stages(seam),
            "branch": primary,
        },
        "co_primary": {
            "a_seam_broke": round(a_broke, 4),
            "a_seam_cleared": round(a_clear, 4),
            "n_broke_stages": n_broke_stages,
            "n_broke_rows": len(s_broke),
            "branch": co,
        },
        "verdict": verdict,
        "secondary_v2": v2,
        "context": {
            "per_upstream": per_up,
            "early_seam": round(_agree(early), 4),
            "late_seam": round(_agree(late), 4),
            "last10_before_break": round(_agree(last10), 4),
            "cold_broke": round(
                _agree([r for r in cold if r["outcome"] == "broke"]), 4
            ),
        },
        "exam_outcomes": outcomes,
    }
    os.makedirs(os.path.dirname(out_npz), exist_ok=True)
    np.savez_compressed(
        out_npz,
        vecs=V,
        seed=np.asarray([r["seed"] for r in probe.rows]),
        k=np.asarray([r["k"] for r in probe.rows]),
        t=np.asarray([r["t"] for r in probe.rows]),
        dec=np.asarray([r["dec"] for r in probe.rows]),
        exec_menu=np.asarray([r["exec"] for r in probe.rows]),
        weave_menu=np.asarray([r["weave"] for r in probe.rows]),
        upstream=np.asarray([r["upstream"] for r in probe.rows]),
        x=np.asarray([r["x"] for r in probe.rows]),
        plane_x=np.asarray([r["plane_x"] for r in probe.rows]),
        kept=np.asarray(["outcome" in r for r in probe.rows]),
        outcome=np.asarray([r.get("outcome", "postmortem") for r in probe.rows]),
    )
    with open(out_json, "w") as f:
        json.dump(report, f, indent=1)
    print(
        f"[r1] cold {a_cold:.4f} vs seam {a_seam:.4f} -> {primary} | "
        f"broke {a_broke:.4f} vs cleared {a_clear:.4f} "
        f"({n_broke_stages} stages) -> {co} | VERDICT {verdict}"
    )
    print(
        f"[r1] instrument: match {match:.3f} mirror {mirror:.4f} | "
        f"v2 {v2} | saved {out_json} + npz"
    )
    return 0


def selftest() -> None:
    import inspect

    from eval.eval_integration import run_composite_episode

    assert inspect.signature(run_composite_episode).parameters["probe"].default is None
    # student-slot override and mirror target are opt-in (R3 machinery)
    assert inspect.signature(capture).parameters["slalom_zip"].default is None
    assert inspect.signature(_score).parameters["flew_zip"].default is None
    # terminal_commit_v1 machinery is opt-in: defaults bit-identical
    cp = inspect.signature(capture).parameters
    assert cp["target_stage"].default == "slalom3_fixed"
    assert cp["thread_commit"].default is False and cp["course_k"].default == 3
    assert inspect.signature(SeamProbe.__init__).parameters["target"].default == (
        "slalom3_fixed"
    )

    # stage-window filter, relay semantics (±0.2 overlap at boundaries
    # is BY DESIGN — near-edge obstacles belong to both stages)
    pil = [(0.5, 0.0), (3.6, 1.0), (4.5, -1.0), (6.1, 0.0), (7.0, 1.0)]
    assert [p[0] for p in _stage_window(pil, 0)] == [0.5]
    assert [p[0] for p in _stage_window(pil, 1)] == [3.6, 4.5, 6.1]
    assert [p[0] for p in _stage_window(pil, 2)] == [6.1, 7.0]

    # frozen branch logic, every cell
    assert _branch(0.90, 0.95, PRIMARY_CONFIRM, PRIMARY_REFUTE) == "CONFIRMED"
    assert _branch(0.92, 0.95, PRIMARY_CONFIRM, PRIMARY_REFUTE) == "CONFIRMED"
    assert _branch(0.945, 0.95, PRIMARY_CONFIRM, PRIMARY_REFUTE) == "REFUTED"
    assert _branch(0.93, 0.95, PRIMARY_CONFIRM, PRIMARY_REFUTE) == "GRAY"
    assert _branch(0.88, 0.94, CO_CONFIRM, CO_REFUTE) == "CONFIRMED"
    assert _branch(0.93, 0.94, CO_CONFIRM, CO_REFUTE) == "REFUTED"
    assert _branch(0.90, 0.94, CO_CONFIRM, CO_REFUTE) == "GRAY"

    # outcome classification incl. the post-break phantom exclusion
    assert _row_outcome(0, True, 3) == "cleared"
    assert _row_outcome(1, False, 1) == "broke"
    assert _row_outcome(0, False, 1) == "cleared"
    assert _row_outcome(2, False, 1) == "postmortem"

    # agreement + clustering arithmetic
    rows = [
        {"seed": 1, "k": 1, "exec": 0, "weave": 0},
        {"seed": 1, "k": 1, "exec": 1, "weave": 0},
        {"seed": 2, "k": 2, "exec": 0, "weave": 0},
    ]
    assert abs(_agree(rows) - 2 / 3) < 1e-9
    assert abs(_clustered(rows) - 0.75) < 1e-9  # (0.5 + 1.0) / 2
    assert _stages(rows) == 2 and _agree([]) == -1.0

    # frozen constants, as registered
    assert (PRIMARY_CONFIRM, PRIMARY_REFUTE) == (0.03, 0.01)
    assert (CO_CONFIRM, CO_REFUTE) == (0.05, 0.02)
    assert (MIRROR_FLOOR, MIN_BROKE_STAGES) == (0.99, 6)
    print(
        "SEAM-FIDELITY OK: probe default inert, stage window, branch "
        "cells, outcome classes, clustering, frozen constants"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--capture", action="store_true")
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--seed0", type=int, default=110000)
    ap.add_argument("--out-json", default=OUT_JSON)
    ap.add_argument("--out-npz", default=OUT_NPZ)
    ap.add_argument("--slalom-zip", default=None)
    ap.add_argument("--target", default="slalom3_fixed")
    ap.add_argument("--thread-commit", action="store_true")
    ap.add_argument("--commit-hysteresis", action="store_true")
    ap.add_argument("--course-k", type=int, default=3)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    if args.capture:
        raise SystemExit(
            capture(
                args.n,
                args.seed0,
                args.out_json,
                args.out_npz,
                args.slalom_zip,
                args.target,
                args.thread_commit,
                args.course_k,
                args.commit_hysteresis,
            )
        )
    ap.print_help()


if __name__ == "__main__":
    main()

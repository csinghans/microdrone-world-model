"""Verify and render cf_hard_pool_v1 from saved JSON, without fitting/scoring.

    python -m eval.eval_cf_sampler_report
    python -m eval.eval_cf_sampler_report --selftest
    python -m eval.eval_cf_sampler_report --audit-probe-support

All inputs are committed receipts. Raw model/data files and simulator state
are unnecessary. This does not regenerate an exam or rerun a bootstrap.
"""

import argparse
from copy import deepcopy

import numpy as np

from eval.eval_schedule_report import validate as validate_common
from scripts.schedule_layout_study import ROOT, read, sha, write_new

CAMPAIGN = ROOT / "experiments/cf_hard_pool_v1"
ROLES = ("baseline", "candidate")


def audit_probe_support(campaign=CAMPAIGN):
    """Post-hoc support accounting from hashed exports, with no model calls."""
    config = read(campaign / "registration.json")
    files, first = {}, None
    for arm in config["arms"]:
        for seed in config["seeds"]:
            stage = f"score_{arm}_{seed}"
            path = ROOT / "output" / config["campaign"] / stage / "scores.npz"
            receipt = read(campaign / f"records/{stage}.json")
            expected = [
                v for k, v in receipt["files"].items() if k.endswith("/scores.npz")
            ]
            if expected != [sha(path)]:
                raise ValueError("probe export changed or missing")
            files[str(path.relative_to(ROOT))] = expected[0]
            with np.load(path, allow_pickle=False) as blob:
                sample = {
                    k: blob[k] for k in ("veer_pairs", "veer_world_id", "world_names")
                }
            if first is None:
                first = sample
            elif any(not np.array_equal(first[k], sample[k]) for k in first):
                raise ValueError("probe support differs across model exports")
    pairs, ids, names = (
        first["veer_pairs"],
        first["veer_world_id"],
        first["world_names"],
    )
    rows = {}
    for wid, name in enumerate(names):
        mask = ids == wid
        rows[str(name)] = {
            "frames": int(mask.sum()),
            "rollouts": int(len(np.unique(pairs[mask, 0]))),
        }
    _, counts = np.unique(pairs[:, 0], return_counts=True)
    return {
        "scope": "Post-hoc support accounting only; no fitting, model scoring, "
        "bootstrap, alternative gate or changed eligibility.",
        "source_exports": files,
        "n_frames": len(pairs),
        "n_rollouts": len(counts),
        "by_world": rows,
        "frames_per_rollout_range": [int(counts.min()), int(counts.max())],
    }


def validate(result, config, training, pools):
    validate_common(result, config)
    first = result["pairs"][0]["baseline"]
    for pair in result["pairs"]:
        seed = str(pair["seed"])
        comparison = result["comparisons"][seed]
        probe = comparison["veer"]
        if comparison["seed"] != config["bootstrap"]["seed"]:
            raise ValueError("unexpected bootstrap seed")
        lo, hi = probe["ci95"]
        if not np.isfinite([lo, hi]).all() or not -1 <= lo <= hi <= 1:
            raise ValueError("invalid veer interval")
        if probe["valid_bootstraps"] != config["bootstrap"]["n_boot"]:
            raise ValueError("incomplete veer bootstrap")
        metas, splits = [], []
        for role, arm in zip(ROLES, config["arms"]):
            scores = pair[role]
            fit = training[f"{arm}_{seed}"]
            meta, metrics = fit["meta"], fit["metrics"]
            if scores != comparison[role] or scores["checkpoint_meta"] != meta:
                raise ValueError("comparison/score/fit metadata differs")
            if meta["training_dataset_sha256"] != config["training_source"]["sha256"]:
                raise ValueError("different training corpus")
            if meta["cf_hard_pool"] != arm or meta["seed"] != pair["seed"]:
                raise ValueError("wrong recipe or training seed")
            if metrics["cf_hard_pool_frames"] != pools[seed][arm]:
                raise ValueError("fit used a different hard pool")
            if metrics["cf_hard_pool_fallback"] != (pools[seed][arm] == 0):
                raise ValueError("incorrect hard-pool fallback")
            if (
                probe["n_samples"] != scores["veer_all"][1]
                or probe["n_rollouts"] != scores["veer_rollouts"]
                or scores["veer_rollouts"] != first["veer_rollouts"]
            ):
                raise ValueError("different veer support")
            # The historical scalar uses float32; raw boolean means use
            # float64. This tolerance prices representation, not a gate.
            if not np.isclose(
                probe[f"accuracy_{role}"], scores["veer_all"][0], rtol=0, atol=1e-7
            ):
                raise ValueError("raw veer correctness/aggregate differs")
            for key in ("label_counts_by_world", "now_label_counts", "label_counts_h"):
                if scores[key] != first[key]:
                    raise ValueError("common-exam labels differ")
            metas.append({k: v for k, v in meta.items() if k != "cf_hard_pool"})
            splits.append((metrics["n_train"], metrics["n_val"]))
        if metas[0] != metas[1] or splits[0] != splits[1]:
            raise ValueError("paired training recipe/split differs beyond the knob")
        if probe["delta"] != probe["accuracy_candidate"] - probe["accuracy_baseline"]:
            raise ValueError("incorrect veer delta")


def load_evidence():
    """Reconcile the report with immutable individual receipts, portably."""
    verification = read(CAMPAIGN / "verification.json")
    manifest_hash = sha(CAMPAIGN / "manifest.json")
    if verification["manifest_sha256"] != manifest_hash:
        raise ValueError("verification belongs to another manifest")
    original_config = [
        digest
        for path, digest in read(CAMPAIGN / "manifest.json")["sources"].items()
        if path.endswith("/experiments/cf_hard_pool_v1/registration.json")
    ]
    if original_config != [sha(CAMPAIGN / "registration.json")]:
        raise ValueError("frozen registration changed")
    for original, expected in verification["receipt_hashes"].items():
        # Original paths describe the research machine; JSON-only checking
        # must also work in a fresh CI checkout without its output directory.
        name = original.rsplit("/", 1)[-1]
        path = CAMPAIGN / "records" / name
        if sha(path) != expected:
            raise ValueError(f"receipt changed after verification: {name}")
        if read(path)["manifest_sha256"] != manifest_hash:
            raise ValueError(f"receipt belongs to another manifest: {name}")
    config = read(CAMPAIGN / "registration.json")
    result = read(CAMPAIGN / "records/report.json")["result"]
    training = {}
    for pair in result["pairs"]:
        for role, arm in zip(ROLES, config["arms"]):
            suffix = f"{arm}_{pair['seed']}"
            raw = read(CAMPAIGN / f"records/score_{suffix}.json")["result"]
            fit = read(CAMPAIGN / f"records/train_{suffix}.json")
            if raw["scores"] != pair[role] or raw["budget"] != pair[f"{role}_budget"]:
                raise ValueError("report differs from individual score receipt")
            model = raw["scores"]["provenance"]["checkpoint"]
            if fit["files"].get(model["path"]) != model["sha256"]:
                raise ValueError("scored checkpoint differs from fit output")
            training[suffix] = fit["result"]
    pools = read(CAMPAIGN / "records/training_data.json")["result"]["hard_pools"]
    validate(result, config, training, pools)
    return result, config, training, pools


def summary(result, config, training, pools, support):
    validate(result, config, training, pools)
    decision, bars = result["decision"], config["bars"]
    first = result["pairs"][0]["baseline"]
    lines = [
        f"# cf_hard_pool_v1 — {decision['verdict']}",
        "",
        "Generated by `python -m eval.eval_cf_sampler_report` from the saved",
        "[raw report](records/report.json) and individual receipts. No new",
        "training, scoring or resampling. [Frozen registration](registration.json).",
        "",
        "The sole knob is the CF hard-pool rule: `legacy_masked` control versus",
        "`answerable` candidate. Six fresh 80-epoch fits share the same hashed",
        "192-rollout training corpus, with matched seeds 0/1/2 and identical",
        "within-pair splits, executed windows and optimizer steps. D64, four",
        "strips, 64px, one frame. Every model scores the same new 186-course",
        f"exam ({first['n_val_samples']:,} overlapping valid windows).",
        "",
        f"Mean veer delta **{decision['veer_mean']:+.4f}**, below the registered",
        f"**+{bars['veer_mean_delta_min']:.4f}** minimum. Seed 1 also regresses",
        "in ranking; seed 0 fails classic, moving, room and danger-now guards.",
        "A favorable mean or seed 2 cannot override those per-seed failures.",
        "The default remains `legacy_masked`; no candidate is promoted.",
        "",
        "![All seeds and registered guards](../../docs/figures/cf_hard_pool_v1.png)",
        "",
        "## Primary: action ranking",
        "",
        "| Seed | Control | Candidate | Delta | Paired course-bootstrap 95% interval |",
        "|---|---:|---:|---:|---:|",
    ]
    for pair in result["pairs"]:
        seed = pair["seed"]
        row = result["comparisons"][str(seed)]["veer"]
        lo, hi = row["ci95"]
        lines.append(
            f"| {seed} | {pair['baseline']['veer_all'][0]:.4f} | "
            f"{pair['candidate']['veer_all'][0]:.4f} | "
            f"{decision['veer_deltas'][config['seeds'].index(seed)]:+.4f} | "
            f"[{lo:+.4f}, {hi:+.4f}] |"
        )
    lines += [
        "",
        f"Each reading has **{first['veer_all'][1]} probe frames from "
        f"{first['veer_rollouts']} independent courses**, exceeding the registered",
        "20-frame / six-course support bars. Frames within a course are correlated.",
        "The three-draw mean/range describes these training draws, not a",
        "training-population confidence interval. Paired, world-stratified",
        "rollout-bootstrap intervals (2,000 draws, seed 0) condition on each",
        "fixed model pair. They are descriptive; they do not change the gates.",
        "The stored gate uses float32 mean accuracy; exported boolean means",
        "use float64. They agree within 1e-7 and give the same displayed values.",
        "",
        "A post-hoc [support accounting](probe_support.json), with unchanged",
        "eligibility, reconciles all six hashed exports:",
        "",
        "| Probe world | Frames | Independent courses |",
        "|---|---:|---:|",
    ]
    for world, row in support["by_world"].items():
        lines.append(f"| {world} | {row['frames']} | {row['rollouts']} |")
    lines += [
        "",
        "The pooled primary is dominated by dense frames; moving contributes",
        "only two independent probe courses and the pillar-kinematic probe",
        "does not cover room geometry. This limits interpretation of ranking",
        "by world. It does not invalidate the pre-registered pooled support",
        "bar or permit expanding the completed exam. All four worlds still",
        "have their separately guarded collision AUC on the full exam.",
        "",
        "## Every collision guard, every seed",
        "",
        "Candidate minus control AUC. **Bold** fails the frozen −0.02 guard.",
        "",
        "| Seed | Classic | Dense | Moving | Room | Danger-now |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    worlds = config["bars"]["guard_worlds"]
    for pair in result["pairs"]:
        seed, a, b = pair["seed"], pair["baseline"], pair["candidate"]
        deltas = [(w, b["auc_by_world"][w] - a["auc_by_world"][w]) for w in worlds]
        deltas.append(("now_auc", b["now_auc"] - a["now_auc"]))
        cells = []
        for key, delta in deltas:
            cell = f"{delta:+.4f}"
            cells.append(
                cell if decision["checks"][f"seed{seed}/{key}_guard"] else f"**{cell}**"
            )
        lines.append(f"| {seed} | " + " | ".join(cells) + " |")
    budget = result["pairs"][0]["candidate_budget"]
    lines += [
        "",
        "All guarded AUC readings have both classes. Per-world AUC intervals",
        "and pooled AUC are preserved in the raw report. No danger-now",
        "bootstrap was registered or added after observing these readings.",
        "",
        "## Embedded bill",
        "",
        f"All six models: **{budget['total_kb']:.2f} KB** analytic int8 memory",
        f"({budget['weights_kb']:.2f} KB weights + {budget['peak_act_kb']:.0f} KB",
        f"peak activations + {budget['workspace_kb']:.0f} KB workspace).",
        f"{budget['macs_decision']:,} MACs/decision imply "
        f"**{budget['macs_decision'] / 500000:.2f} ms** at the existing assumed",
        "0.5 GMAC/s. Memory/MAC bills are identical within and across pairs.",
        "These are analytic estimates, not hardware timings or int8 parity",
        "results. No closed-loop flight gate was run.",
        "",
        "## Training support and endpoint diagnostics",
        "",
        "| Seed | Windows train / val, each arm | Control hard frames | Candidate |",
        "|---|---:|---:|---:|",
    ]
    for seed in config["seeds"]:
        m = training[f"legacy_masked_{seed}"]["metrics"]
        row = pools[str(seed)]
        lines.append(
            f"| {seed} | {m['n_train']:,} / {m['n_val']:,} | "
            f"{row['legacy_masked']:,} | {row['answerable']:,} |"
        )
    lines += [
        "",
        "Only the hard half's membership changes. Both arms retain the uniform",
        "half, visibility-masked CF loss and shared danger-now sampled frames.",
        "",
        "| Arm | Seed | MSE@32 | Own no-op@32 | "
        "Std median | Std max | Mean abs latent |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for arm in config["arms"]:
        for seed in config["seeds"]:
            m = training[f"{arm}_{seed}"]["metrics"]
            values = [
                m["mse"][-1],
                m["noop"][-1],
                m["zstd_med"],
                m["zstd_max"],
                m["zabs"],
            ]
            lines.append(
                f"| {arm} | {seed} | " + " | ".join(f"{v:.4f}" for v in values) + " |"
            )
    lines += [
        "",
        "These are internal-validation endpoints, not common-exam metrics.",
        "Every fit beats its own no-op MSE@32; learned latent scales differ",
        "between fits. This does not certify common-exam ranking or collision",
        "prediction. Control seed 2's large absolute latent value accompanies",
        "weak readings, but the candidate still loses ranking at seed 1 without",
        "that symptom. Endpoint associations do not identify a training cause.",
        "",
        "The hypothesis did not meet its registered joint improvement test.",
        "This is evidence about the tested recipe, not proof that every",
        "answerable-contrast curriculum must fail. Preserve all three pairs,",
        "the original NO-GO and the separate schedule-layout NO-GO. No seed",
        "replacement, exam expansion, bar change or champion overwrite.",
        "",
    ]
    return "\n".join(lines)


def figure(
    result,
    config,
    *,
    primary="veer",
    title_prefix="CF sampler",
    subtitle=None,
    xlim=(-0.22, 0.38),
):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 3, figsize=(12.5, 7.5), sharex=True, sharey=True)
    keys = (primary,) + tuple(
        k
        for k in ("classic", "dense", "moving", "room", "veer", "now_auc")
        if k != primary
    )
    for ax, key in zip(axes.flat, keys):
        threshold = (
            0
            if key == primary
            else (
                config["bars"]["guard_each_veer_delta_min"] if key == "veer" else -0.02
            )
        )
        ax.axvline(0, color="#bdc7cf", lw=1)
        ax.axvline(threshold, color="#a44642", lw=1, ls="--")
        for pair in result["pairs"]:
            seed = pair["seed"]
            comp = result["comparisons"][str(seed)]
            if key == "veer":
                row = comp["veer"]
                delta, interval = row["delta"], row["ci95"]
                check = (
                    f"seed{seed}/veer_nonnegative"
                    if primary == "veer"
                    else f"seed{seed}/veer_guard"
                )
            elif key == "now_auc":
                delta = pair["candidate"][key] - pair["baseline"][key]
                interval, check = None, f"seed{seed}/now_auc_guard"
            else:
                row = comp["worlds"][key]
                delta, interval = row["delta"], row["ci95"]
                check = f"seed{seed}/{key}_guard"
                if key == primary:
                    check = f"seed{seed}/moving_positive"
            color = "#267187" if result["decision"]["checks"][check] else "#b54540"
            if interval:
                ax.plot(interval, [seed, seed], lw=2, color=color, alpha=0.7)
            ax.scatter(delta, seed, s=38, color=color, zorder=3)
            ax.annotate(
                f"{delta:+.3f}",
                (delta, seed),
                xytext=(0, 9),
                textcoords="offset points",
                ha="center",
                fontsize=9,
                color=color,
            )
        title = {
            "veer": "Veer ranking"
            + (" · primary" if primary == "veer" else " · points only"),
            "now_auc": "Danger-now · points only",
        }
        if primary == "moving":
            title["moving"] = "Moving · primary"
        ax.set_title(title.get(key, key.capitalize()), loc="left", fontsize=12)
        ax.set_xlim(*xlim)
        ax.set_ylim(2.6, -0.6)
        ax.set_xticks([-0.2, 0, 0.2] if primary == "veer" else [-0.1, 0, 0.2, 0.4])
        ax.set_yticks([0, 1, 2], ["Seed 0", "Seed 1", "Seed 2"])
        ax.tick_params(length=0, pad=7, labelbottom=True)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.grid(axis="x", alpha=0.12)
        ax.set_xlabel("Candidate − control " + ("accuracy" if key == "veer" else "AUC"))
    d = result["decision"]
    fig.suptitle(
        f"{title_prefix}: {d['verdict']} across three paired seeds",
        x=0.07,
        y=0.98,
        ha="left",
        fontsize=18,
    )
    fig.text(
        0.07,
        0.91,
        subtitle
        or (
            f"Mean ranking delta {d['veer_mean']:+.4f} < +0.0500 required. "
            "Seed 1 ranking and seed 0 collision guards fail."
        ),
        fontsize=10.5,
        color="#475569",
    )
    first = result["pairs"][0]["baseline"]
    interval_note = (
        "Lines: paired rollout-bootstrap 95% intervals, conditional on fixed models. "
        "Danger-now has no interval.\n"
        if primary == "veer"
        else "Lines: paired course-bootstrap 95% intervals, "
        "conditional on fixed models. "
        "Veer / danger-now: points only.\n"
    )
    fig.text(
        0.07,
        0.035,
        interval_note
        + "Red points fail a per-seed bar (dashed). Common exam: 186 courses; "
        f"ranking probe: {first['veer_all'][1]} frames from "
        f"{first['veer_rollouts']} courses.\n"
        "All six analytic bills: 137.29 KB, 7.71 ms at assumed 0.5 GMAC/s. "
        "No hardware or flight certification.",
        fontsize=9,
        color="#475569",
        linespacing=1.5,
    )
    fig.subplots_adjust(
        left=0.07, right=0.98, top=0.84, bottom=0.2, hspace=0.6, wspace=0.2
    )
    return fig


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--selftest", action="store_true")
    mode.add_argument("--audit-probe-support", action="store_true")
    args = ap.parse_args()
    support_path = CAMPAIGN / "probe_support.json"
    if args.audit_probe_support:
        support = audit_probe_support()
        if support_path.exists():
            if read(support_path) != support:
                raise ValueError("saved probe support differs; preserve and inspect")
        else:
            write_new(support_path, support)
        print("CF-PROBE-SUPPORT OK: all six exports, unchanged eligibility")
        return
    result, config, training, pools = load_evidence()
    support = read(support_path)
    first = result["pairs"][0]["baseline"]
    if (support["n_frames"], support["n_rollouts"]) != (
        first["veer_all"][1],
        first["veer_rollouts"],
    ) or any(
        sum(row[key] for row in support["by_world"].values()) != support[total]
        for key, total in (("frames", "n_frames"), ("rollouts", "n_rollouts"))
    ):
        raise ValueError("probe support totals differ")
    document = summary(result, config, training, pools, support)
    if args.selftest:
        mutations = (
            lambda r: r["decision"].update(verdict="GO"),
            lambda r: r["comparisons"]["0"]["veer"].update(n_rollouts=208),
            lambda r: r["comparisons"]["1"]["veer"].update(accuracy_candidate=0.9),
            lambda r: r["comparisons"]["2"].update(seed=99),
        )
        for mutate in mutations:
            bad = deepcopy(result)
            mutate(bad)
            try:
                validate(bad, config, training, pools)
            except ValueError:
                pass
            else:
                raise AssertionError("altered evidence accepted")
        assert "NO-GO" in document and "**-0.0742**" in document
        assert "208 probe frames from 23 independent courses" in document
        assert "**137.29 KB**" in document
        print("CF-REPORT OK: receipts, one knob, common exam, all seeds and guards")
        return
    (CAMPAIGN / "summary.md").write_text(document)
    fig = figure(result, config)
    path = ROOT / "docs/figures/cf_hard_pool_v1.png"
    fig.savefig(path, dpi=180, facecolor="white")
    print(f"CF-REPORT OK: {CAMPAIGN / 'summary.md'} and {path}")


if __name__ == "__main__":
    main()

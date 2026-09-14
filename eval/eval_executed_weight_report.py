"""Render executed_weight_v1 from saved evidence, with no model calls.

    python -m eval.eval_executed_weight_report
    python -m eval.eval_executed_weight_report --selftest
    python -m eval.eval_executed_weight_report --audit-probe-support

Default/selftest need only committed JSON. The optional support audit reads
hashed score exports, never fits, scores, resamples or changes eligibility.
"""

import argparse
from copy import deepcopy

import numpy as np

from eval.eval_cf_sampler_report import audit_probe_support, figure
from eval.eval_schedule_report import validate as validate_common
from scripts.schedule_layout_study import ROOT, read, sha, write_new

CAMPAIGN = ROOT / "experiments/executed_weight_v1"


def validate(result, config, training, plans, support):
    validate_common(result, config)
    first = result["pairs"][0]["baseline"]
    if (support["n_frames"], support["n_rollouts"]) != (
        first["veer_all"][1],
        first["veer_rollouts"],
    ):
        raise ValueError("probe support totals differ")
    for key, total in (("frames", "n_frames"), ("rollouts", "n_rollouts")):
        if sum(r[key] for r in support["by_world"].values()) != support[total]:
            raise ValueError("world probe support does not sum to pooled support")
    for pair in result["pairs"]:
        seed = str(pair["seed"])
        comp, metas, counts = result["comparisons"][seed], [], []
        probe = comp["veer"]
        if comp["seed"] != config["bootstrap"]["seed"]:
            raise ValueError("bootstrap seed differs from registration")
        if probe["ci95"] is None:
            if not any(r["rollouts"] == 1 for r in support["by_world"].values()):
                raise ValueError("missing interval without a singleton probe stratum")
            if (
                probe.get("reason")
                != "fewer than two probe rollouts in a world stratum"
            ):
                raise ValueError("missing interval reason differs")
        else:
            lo, hi = probe["ci95"]
            if not np.isfinite([lo, hi]).all() or not -1 <= lo <= hi <= 1:
                raise ValueError("invalid veer interval")
            if any(r["rollouts"] == 1 for r in support["by_world"].values()):
                raise ValueError("fabricated interval for singleton probe stratum")
        for role, arm in zip(("baseline", "candidate"), config["arms"]):
            scores, fit = pair[role], training[f"{arm}_{seed}"]
            meta, m = fit["meta"], fit["metrics"]
            if scores != comp[role] or scores["checkpoint_meta"] != meta:
                raise ValueError("score/comparison/fit identity differs")
            if meta["executed_moving_weight"] != config["weights"][arm]:
                raise ValueError("wrong executed weight")
            if meta["cf_hard_pool"] != "legacy_masked":
                raise ValueError("CF sampler changed alongside executed weight")
            if meta["training_dataset_sha256"] != config["training_source"]["sha256"]:
                raise ValueError("training corpus differs")
            if m["executed_loss_weighting"] != plans[seed][arm]:
                raise ValueError("fit weighting differs from preflight plan")
            if (probe["n_samples"], probe["n_rollouts"]) != (
                scores["veer_all"][1],
                scores["veer_rollouts"],
            ):
                raise ValueError("raw/aggregate veer support differs")
            if not np.isclose(
                probe[f"accuracy_{role}"], scores["veer_all"][0], rtol=0, atol=1e-7
            ):
                raise ValueError("raw/aggregate veer accuracy differs")
            for key in ("label_counts_by_world", "label_counts_h", "now_label_counts"):
                if scores[key] != first[key]:
                    raise ValueError("common-exam label support differs")
            metas.append(
                {k: v for k, v in meta.items() if k != "executed_moving_weight"}
            )
            counts.append([m[k] for k in ("n_train", "n_val", "cf_hard_pool_frames")])
        if metas[0] != metas[1] or counts[0] != counts[1]:
            raise ValueError("paired recipe/counts differ beyond the registered weight")
        if probe["delta"] != probe["accuracy_candidate"] - probe["accuracy_baseline"]:
            raise ValueError("incorrect veer delta")


def load_evidence():
    config = read(CAMPAIGN / "registration.json")
    verification, manifest = read(CAMPAIGN / "verification.json"), read(
        CAMPAIGN / "manifest.json"
    )
    manifest_hash = sha(CAMPAIGN / "manifest.json")
    if verification["manifest_sha256"] != manifest_hash:
        raise ValueError("verification manifest differs")
    expected = [
        v
        for k, v in manifest["sources"].items()
        if k.endswith("/experiments/executed_weight_v1/registration.json")
    ]
    if expected != [sha(CAMPAIGN / "registration.json")]:
        raise ValueError("frozen registration changed")
    for path, digest in verification["receipt_hashes"].items():
        local = CAMPAIGN / "records" / path.rsplit("/", 1)[-1]
        if sha(local) != digest or read(local)["manifest_sha256"] != manifest_hash:
            raise ValueError("stage receipt changed after verification")
    result = read(CAMPAIGN / "records/report.json")["result"]
    training = {}
    for pair in result["pairs"]:
        for role, arm in zip(("baseline", "candidate"), config["arms"]):
            suffix = f"{arm}_{pair['seed']}"
            raw = read(CAMPAIGN / f"records/score_{suffix}.json")["result"]
            fit = read(CAMPAIGN / f"records/train_{suffix}.json")
            if raw["scores"] != pair[role] or raw["budget"] != pair[f"{role}_budget"]:
                raise ValueError("report differs from individual score receipt")
            model = raw["scores"]["provenance"]["checkpoint"]
            if fit["files"].get(model["path"]) != model["sha256"]:
                raise ValueError("scored checkpoint differs from fitted checkpoint")
            training[suffix] = fit["result"]
    plans = read(CAMPAIGN / "records/training_data.json")["result"][
        "executed_loss_weights"
    ]
    support = read(CAMPAIGN / "probe_support.json")
    validate(result, config, training, plans, support)
    return result, config, training, plans, support


def summary(result, config, training, plans, support):
    validate(result, config, training, plans, support)
    d, first = result["decision"], result["pairs"][0]["baseline"]
    lines = [
        f"# executed_weight_v1 — {d['verdict']}",
        "",
        "Generated by `python -m eval.eval_executed_weight_report` from the",
        "[raw report](records/report.json) and immutable individual receipts.",
        "No new fitting, scoring, bootstrap or changed gate.",
        "",
        "Six fresh 80-epoch fits share the same 192-course training corpus.",
        "Only moving executed prediction/collision loss weight changes:",
        "1.0 control versus 2.25 candidate, divided by the training partition's",
        "mean raw weight. Batches, CF/now/variance recipes, splits and optimizer",
        "step counts stay fixed. D64, four strips, 64px, one input frame.",
        "All six score the same new 186-course exam "
        f"({first['n_val_samples']:,} valid windows).",
        "",
        f"Moving mean AUC delta **{d['moving_mean']:+.4f}** passes the **+0.0300**",
        "mean bar, but seed 0 fails the strictly-positive moving requirement.",
        "Seed 1 also fails dense AUC and pooled veer guards. Therefore the",
        "registered joint improvement test is **NO-GO**, despite the mean gain.",
        "The default weight stays 1.0; no candidate is promoted.",
        "",
        "![All seeds and guards](../../docs/figures/executed_weight_v1.png)",
        "",
        "## Primary: moving collision AUC@32",
        "",
        "| Seed | Control | Candidate | Delta | Paired course-bootstrap 95% interval |",
        "|---|---:|---:|---:|---:|",
    ]
    for pair in result["pairs"]:
        row = result["comparisons"][str(pair["seed"])]["worlds"]["moving"]
        lo, hi = row["ci95"]
        lines.append(
            f"| {pair['seed']} | {row['auc_baseline']:.4f} | "
            f"{row['auc_candidate']:.4f} | {row['delta']:+.4f} | "
            f"[{lo:+.4f}, {hi:+.4f}] |"
        )
    lines += [
        "",
        "Every moving AUC uses all 42 moving exam courses and both classes.",
        "Intervals resample paired whole courses (2,000 draws, seed 0),",
        "conditional on each fixed model pair. They are descriptive, not",
        "gating or training-population confidence intervals. A good three-draw",
        "mean cannot erase a failed per-seed criterion.",
        "",
        "## Every guard, every seed",
        "",
        "Candidate minus control. **Bold** fails the frozen guard.",
        "",
        "| Seed | Classic AUC | Dense AUC | Room AUC | "
        "Danger-now AUC | Veer accuracy |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for pair in result["pairs"]:
        seed, a, b = pair["seed"], pair["baseline"], pair["candidate"]
        readings = [
            (w, b["auc_by_world"][w] - a["auc_by_world"][w])
            for w in ("classic", "dense", "room")
        ]
        readings += [
            ("now_auc", b["now_auc"] - a["now_auc"]),
            ("veer", b["veer_all"][0] - a["veer_all"][0]),
        ]
        cells = [
            f"{v:+.4f}" if d["checks"][f"seed{seed}/{k}_guard"] else f"**{v:+.4f}**"
            for k, v in readings
        ]
        lines.append(f"| {seed} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "AUC guards require ≥−.02; the pooled veer guard requires ≥−.05.",
        "Each veer reading uses **190 frames from 20 independent courses**:",
        "",
        "| Probe world | Frames | Courses |",
        "|---|---:|---:|",
    ]
    for world, row in support["by_world"].items():
        lines.append(f"| {world} | {row['frames']} | {row['rollouts']} |")
    lines += [
        "",
        "The registered pooled support bar (20 frames / six courses) passes.",
        "However, moving contributes only one probe course. The pre-existing",
        "world-stratified bootstrap refuses an interval when a stratum has fewer",
        "than two courses, so all three veer intervals remain **undefined**,",
        "with the reason recorded. No interval was fabricated or exam expanded.",
        "This limits ranking uncertainty; it does not change the separate",
        "42-course moving AUC or the frozen pooled guard. Room geometry is",
        "outside the pillar-kinematic veer probe. Danger-now has point estimates",
        "only; no additional post-hoc bootstrap was introduced.",
        "",
        "## What was weighted",
        "",
        "The executed window counts are identical within each pair. Weight",
        "mass changes; no extra windows or independent observations appear.",
        "",
        "| Seed | Training windows | Normalizer | "
        "Moving weight share, control → candidate |",
        "|---|---:|---:|---:|",
    ]
    for seed in config["seeds"]:
        a, b = [plans[str(seed)][arm] for arm in config["arms"]]
        before = a["by_world"]["moving"]["weight_mass_share"]
        after = b["by_world"]["moving"]["weight_mass_share"]
        lines.append(
            f"| {seed} | {a['train_windows']:,} | {b['normalizer']:.6f} | "
            f"{before:.2%} → {after:.2%} |"
        )
    lines += [
        "",
        "The coefficient changes both executed latent prediction and collision",
        "objectives. It does not isolate either loss's contribution or restore",
        "the older corpus's action/label support. Error magnitudes, derivatives",
        "and Adam state prevent equating weight mass with gradient contribution.",
        "",
        "## Embedded bill and endpoint limits",
        "",
    ]
    bill = result["pairs"][0]["candidate_budget"]
    lines += [
        f"Every model has the same **{bill['total_kb']:.2f} KB** analytic int8 bill:",
        f"{bill['weights_kb']:.2f} KB weights + "
        f"{bill['peak_act_kb']:.0f} KB activations + "
        f"{bill['workspace_kb']:.0f} KB workspace.",
        f"{bill['macs_decision']:,} MACs/decision estimate "
        f"**{bill['macs_decision']/500000:.2f} ms** at assumed",
        "0.5 GMAC/s. No hardware timing, quantization-parity test or flight gate.",
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
        "Every fit beats its own no-op MSE@32. These are internal-validation",
        "endpoints on learned latent scales, not a certificate of exam decision",
        "quality. Control seed 2's large absolute latent value accompanies",
        "weak scores; that association does not establish a failure mechanism.",
        "The mean moving gain motivates a hypothesis about objective allocation,",
        "but this factor/recipe fails the required consistency and guards.",
        "No seed selection, replacement, extra exam, altered bar or promotion.",
        "",
    ]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--selftest", action="store_true")
    mode.add_argument("--audit-probe-support", action="store_true")
    args = ap.parse_args()
    if args.audit_probe_support:
        measured = audit_probe_support(CAMPAIGN)
        path = CAMPAIGN / "probe_support.json"
        if path.exists():
            if read(path) != measured:
                raise ValueError("saved support differs; inspect without overwrite")
        else:
            write_new(path, measured)
        print("EXECUTED-PROBE-SUPPORT OK: six exports, unchanged eligibility")
        return
    result, config, training, plans, support = load_evidence()
    document = summary(result, config, training, plans, support)
    if args.selftest:
        for mutate in (
            lambda r: r["decision"].update(verdict="GO"),
            lambda r: r["comparisons"]["0"]["veer"].update(ci95=[0.0, 0.0]),
            lambda r: r["comparisons"]["1"]["veer"].update(n_rollouts=190),
        ):
            bad = deepcopy(result)
            mutate(bad)
            try:
                validate(bad, config, training, plans, support)
            except ValueError:
                pass
            else:
                raise AssertionError("altered/fabricated evidence accepted")
        assert "**+0.0598**" in document and "**-0.0293**" in document
        assert "**undefined**" in document and "**137.29 KB**" in document
        print(
            "EXECUTED-WEIGHT-REPORT OK: frozen verdict, one knob, "
            "support, missing intervals"
        )
        return
    (CAMPAIGN / "summary.md").write_text(document)
    chart = figure(
        result,
        config,
        primary="moving",
        title_prefix="Executed-loss weight",
        subtitle=(
            f"Mean moving AUC {result['decision']['moving_mean']:+.4f} ≥ +0.0300. "
            "Seed 0 moving and seed 1 dense / veer fail."
        ),
        xlim=(-0.12, 0.54),
    )
    chart.savefig(
        ROOT / "docs/figures/executed_weight_v1.png", dpi=180, facecolor="white"
    )
    print(
        "EXECUTED-WEIGHT-REPORT OK: summary.md and docs/figures/executed_weight_v1.png"
    )


if __name__ == "__main__":
    main()

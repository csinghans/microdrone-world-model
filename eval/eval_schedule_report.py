"""Verify and render the completed schedule_layout_v1 evidence, without fitting.

    python -m eval.eval_schedule_report
    python -m eval.eval_schedule_report --selftest

Reads only committed JSON records. Large model/data files are not required
to reproduce the summary and figure. This never reruns a draw or bootstrap.
"""

import argparse
import json
from copy import deepcopy
from pathlib import Path

import numpy as np

from scripts.schedule_layout_study import plain, verdict

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "experiments/schedule_layout_v1"
WORLDS = ("classic", "dense", "moving", "room")


def read(path):
    return json.loads(Path(path).read_text())


def validate(result, registration):
    """A generated chart must agree with the raw paired readings and bars."""
    calculated = plain(verdict(result["pairs"], registration))
    if calculated != result["decision"]:
        raise ValueError("stored decision differs from raw readings/frozen bars")
    exam_hashes = set()
    first = result["pairs"][0]["baseline"]
    budget = result["pairs"][0]["baseline_budget"]
    for pair in result["pairs"]:
        seed = str(pair["seed"])
        for arm in ("baseline", "candidate"):
            scores = pair[arm]
            if scores["split"] != "independent_holdout_all":
                raise ValueError("requires independent common exam")
            if (
                scores["va_rolls"] != first["va_rolls"]
                or scores["n_val_samples"] != first["n_val_samples"]
                or scores["veer_all"][1] != first["veer_all"][1]
            ):
                raise ValueError("common-exam sample support differs between models")
            if pair[f"{arm}_budget"] != budget:
                raise ValueError("not every model has the same memory/MAC bill")
            exam_hashes.add(scores["provenance"]["dataset"]["sha256"])
        comparison = result["comparisons"][seed]
        if comparison["n_boot"] != registration["bootstrap"]["n_boot"]:
            raise ValueError("unexpected bootstrap count")
        for world in WORLDS:
            row = comparison["worlds"][world]
            for arm in ("baseline", "candidate"):
                if row[f"auc_{arm}"] != pair[arm]["auc_by_world"][world]:
                    raise ValueError("bootstrap record differs from raw AUC")
            if row["delta"] != row["auc_candidate"] - row["auc_baseline"]:
                raise ValueError("incorrect paired delta")
            if row["ci95"] is not None:
                lo, hi = row["ci95"]
                if not np.isfinite([lo, hi]).all() or lo > hi:
                    raise ValueError("invalid interval")
    if len(exam_hashes) != 1 or not next(iter(exam_hashes)):
        raise ValueError("models were scored on different exams")
    for world in WORLDS + ("all",):
        deltas = [
            result["comparisons"][str(seed)]["worlds"][world]["delta"]
            for seed in registration["seeds"]
        ]
        expected = {
            "paired_deltas": deltas,
            "mean": float(np.mean(deltas)),
            "range": [min(deltas), max(deltas)],
        }
        if result["paired_auc_summary"][world] != expected:
            raise ValueError("summary does not preserve every registered draw")


def summary(result, registration, training):
    validate(result, registration)
    decision = result["decision"]
    recipe, exam = registration["train_data"], registration["holdout"]
    first = result["pairs"][0]["baseline"]
    lines = [
        f"# schedule_layout_v1 — {decision['verdict']}",
        "",
        "Generated from [the complete raw report](records/report.json) by",
        "`python -m eval.eval_schedule_report`. No new scoring or resampling.",
        "",
        f"{len(registration['seeds'])} paired training seeds; legacy control versus",
        f"world_balanced candidate. Each fit uses {recipe['n_transit']} transit +",
        f"{recipe['n_indoor']} shared room rollouts and "
        f"{registration['train']['epochs']} epochs. All six models score the same",
        f"{exam['n_transit'] + exam['n_indoor']} independent courses "
        f"({first['n_val_samples']:,} overlapping valid windows).",
        f"D{registration['train']['latent_d']}, {registration['img_res']}px, "
        "single-frame input.",
        "",
        f"Moving mean AUC delta **{decision['moving_mean']:+.4f}**;",
        f"registered minimum **+{registration['bars']['moving_mean_delta_min']:.4f}**.",
        "Every seed also needs positive moving delta and every per-seed guard.",
        "",
        "| Seed | Moving control | Candidate | Delta | Course-bootstrap 95% interval |",
        "|---|---:|---:|---:|---:|",
    ]
    for pair in result["pairs"]:
        row = result["comparisons"][str(pair["seed"])]["worlds"]["moving"]
        ci = row["ci95"]
        interval = f"[{ci[0]:+.4f}, {ci[1]:+.4f}]" if ci else "undefined"
        lines.append(
            f"| {pair['seed']} | {row['auc_baseline']:.4f} | "
            f"{row['auc_candidate']:.4f} | {row['delta']:+.4f} | {interval} |"
        )
    lines += [
        "",
        "Intervals resample whole courses, paired between the fixed models",
        "and stratified by world (2,000 resamples, seed 0). They describe",
        "test-course uncertainty, not uncertainty across training draws.",
        "The three-seed mean/range is descriptive, not a confidence interval.",
        "",
        "| World | Mean paired delta | Range across three training seeds |",
        "|---|---:|---:|",
    ]
    for world, row in result["paired_auc_summary"].items():
        lo, hi = row["range"]
        lines.append(f"| {world} | {row['mean']:+.4f} | [{lo:+.4f}, {hi:+.4f}] |")
    lines += [
        "",
        "## Every guard, every seed",
        "",
        "Candidate minus control; **bold** means a failed registered guard.",
        "",
        "| Seed | Classic | Dense | Room | Danger-now | Veer ranking |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for pair in result["pairs"]:
        seed, a, b = pair["seed"], pair["baseline"], pair["candidate"]
        items = [
            (w, b["auc_by_world"][w] - a["auc_by_world"][w])
            for w in ("classic", "dense", "room")
        ] + [
            ("now_auc", b["now_auc"] - a["now_auc"]),
            ("veer", b["veer_all"][0] - a["veer_all"][0]),
        ]
        cells = []
        for key, delta in items:
            cell = f"{delta:+.4f}"
            if not decision["checks"][f"seed{seed}/{key}_guard"]:
                cell = f"**{cell}**"
            cells.append(cell)
        lines.append(f"| {seed} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "Minimum deltas: classic/dense/room and danger-now −0.02; veer −0.05.",
        f"Each veer reading uses the same {first['veer_all'][1]} "
        "independent-exam probe frames.",
        "These selected frames are not independent flights.",
        "",
        "## Full embedded bill",
        "",
    ]
    budget = result["pairs"][0]["candidate_budget"]
    lines += [
        f"All six models have the same **{budget['total_kb']:.2f} KB** analytic",
        f"int8 bill: {budget['weights_kb']:.2f} KB weights + "
        f"{budget['peak_act_kb']:.0f} KB peak activations +",
        f"{budget['workspace_kb']:.0f} KB workspace, within 512 KB.",
        f"{budget['macs_decision']:,} MACs/decision give an estimated",
        f"**{budget['macs_decision'] / 500000:.2f} ms** at the existing assumed",
        "0.5 GMAC/s. This is an analytic int8 estimate; no hardware timing,",
        "quantization-parity evaluation or closed-loop promotion was performed.",
        "",
        "## End-of-training instruments",
        "",
        "These are internal training-validation diagnostics, not common-exam",
        "metrics. Latent MSE has a different learned scale in each model.",
        "",
        "| Arm | Seed | MSE@32 | No-op@32 | Std median | Std max | Mean abs latent |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for arm in registration["arms"]:
        for seed in registration["seeds"]:
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
        "Balanced seed 2 has a large endpoint absolute latent value and",
        "breaks every behavioral guard. This association does not identify a",
        "cause: balanced seed 1 also loses moving/room/now performance while",
        "its absolute latent value is smaller than its control's. All six",
        "fits improve their own MSE@32 over their own no-op, which therefore",
        "does not certify common-exam decision quality.",
        "",
        "The role-coverage repair remains verified. This fixed-rollout,",
        "fixed-epoch learning recipe failed its improvement test. It changes",
        "generator RNG consumption, held-window support and internal splits",
        "as well as roles, so the study does not isolate a universal causal",
        "effect of role balance. Preserve the NO-GO, every draw and all bars.",
        "No seed replacement, sample expansion or champion promotion.",
        "",
    ]
    return "\n".join(lines)


def figure(result, registration):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    validate(result, registration)
    fig, axes = plt.subplots(1, 4, figsize=(12, 4.4), sharex=True, sharey=True)
    for ax, world in zip(axes, ("moving", "classic", "dense", "room")):
        ax.axvline(0, color="#56616b", lw=1)
        if world != "moving":
            ax.axvline(-0.02, color="#b34b48", lw=1, ls="--")
        for seed in registration["seeds"]:
            row = result["comparisons"][str(seed)]["worlds"][world]
            delta, interval = row["delta"], row["ci95"]
            key = f"seed{seed}/{world}_guard"
            if world == "moving":
                key = f"seed{seed}/moving_positive"
            color = "#276c8e" if result["decision"]["checks"][key] else "#b34b48"
            if interval:
                ax.plot(interval, [seed, seed], color=color, lw=2, alpha=0.7)
            ax.scatter(delta, seed, color=color, s=42, zorder=3)
            ax.annotate(
                f"{delta:+.3f}",
                (delta, seed),
                xytext=(0, 10),
                textcoords="offset points",
                ha="center",
                fontsize=9,
                color=color,
            )
        ax.set_title(world.capitalize(), fontsize=12, loc="left")
        ax.set_xlim(-0.28, 0.16)
        ax.set_xticks([-0.2, -0.1, 0, 0.1])
        ax.set_ylim(2.5, -0.5)
        ax.set_yticks([0, 1, 2], ["Seed 0", "Seed 1", "Seed 2"])
        ax.grid(axis="x", alpha=0.13)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.tick_params(axis="both", length=0, pad=8)
        ax.set_xlabel("Candidate − control AUC", labelpad=10)
    fig.suptitle(
        f"Schedule layout: {result['decision']['verdict']} on the common exam",
        x=0.06,
        ha="left",
        fontsize=17,
    )
    fig.text(
        0.06,
        0.87,
        f"Moving mean Δ = {result['decision']['moving_mean']:+.3f}; "
        f"registered target ≥ +{registration['bars']['moving_mean_delta_min']:.3f}. "
        "Guard failures remain visible for every seed.",
        fontsize=10,
        color="#475569",
    )
    fig.text(
        0.06,
        0.045,
        "Lines: 95% paired rollout-bootstrap intervals for fixed models, "
        "not training-draw confidence intervals.\n"
        "Dashed line: −0.02 per-seed guard. Red points fail a per-seed criterion. "
        "186 independent courses; 3 paired training seeds.",
        fontsize=9,
        color="#475569",
        linespacing=1.6,
    )
    fig.subplots_adjust(left=0.075, right=0.98, top=0.75, bottom=0.27, wspace=0.2)
    return fig


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    registration = read(CAMPAIGN / "registration.json")
    result = read(CAMPAIGN / "records/report.json")["result"]
    training = {
        f"{arm}_{seed}": read(CAMPAIGN / "records" / f"train_{arm}_{seed}.json")[
            "result"
        ]
        for arm in registration["arms"]
        for seed in registration["seeds"]
    }
    for pair in result["pairs"]:
        for role, arm in zip(("baseline", "candidate"), registration["arms"]):
            raw = read(CAMPAIGN / "records" / f"score_{arm}_{pair['seed']}.json")[
                "result"
            ]
            if pair[role] != raw["scores"] or pair[f"{role}_budget"] != raw["budget"]:
                raise ValueError("report differs from the individual scoring receipt")
    document = summary(result, registration, training)
    if args.selftest:
        for field in ("decision", "paired_auc_summary"):
            bad = deepcopy(result)
            if field == "decision":
                bad[field]["verdict"] = "GO"
            else:
                bad[field]["moving"]["mean"] = 0.1
            try:
                validate(bad, registration)
            except ValueError:
                pass
            else:
                raise AssertionError("altered report accepted")
        assert "NO-GO" in document and "**-0.1171**" in document
        assert "**137.29 KB**" in document
        print(
            "SCHEDULE-REPORT OK: raw readings, common exam, frozen verdict, all draws"
        )
        return
    (CAMPAIGN / "summary.md").write_text(document)
    fig = figure(result, registration)
    directory = ROOT / "docs/figures"
    directory.mkdir(exist_ok=True)
    fig.savefig(directory / "schedule_layout_v1.png", dpi=180, facecolor="white")
    print("SCHEDULE-REPORT OK: summary.md and docs/figures/schedule_layout_v1.png")


if __name__ == "__main__":
    main()

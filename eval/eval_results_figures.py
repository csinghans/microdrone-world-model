"""Render the campaign record as figures — the repo's results, at a glance.

Two kinds of output, both regenerable from committed data (figures are
campaign records, so they must be mechanically reproducible, never
hand-drawn):

  * **Per-skill gate charts** — read straight from each campaign's
    `results.json` (the runner's mechanical record): every criterion's
    measured value per knob, colored by pass/fail, with the frozen bar
    drawn as a black tick. Failures render exactly as prominently as
    wins — the scoreboard voice.
  * **Arc charts** — the cross-campaign stories (the slalom wall and
    its fall, the fine-tune safety curve, the dodgeball speed
    inversion, the teacher/student lines). Their series are curated
    from GATED records only; each number cites its journal in the
    source comments.

Run:
  python -m eval.eval_results_figures --out docs/figures
  python -m eval.eval_results_figures --selftest
"""

import argparse
import glob
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

GREEN, RED, GREY = "#2e7d32", "#c62828", "#9e9e9e"


def skill_gate_figure(results: dict):
    """One chart per skill: criteria x knobs, measured vs the frozen bar."""
    crits = [
        (c["cell"], c["metric"], c["op"], c["bar"]) for c in results["targets_frozen"]
    ]
    knobs = [k for k in results["knobs"] if k.get("gate")]
    fig, ax = plt.subplots(figsize=(max(6, 1.5 * len(crits)), 3.6))
    width = 0.8 / max(len(knobs), 1)
    for ki, k in enumerate(knobs):
        by_name = {c["name"]: c for c in k["gate"]["criteria"]}
        xs, ys, cols = [], [], []
        for ci, (cell, metric, op, bar) in enumerate(crits):
            name = f"{cell} {metric}{op}{bar}"
            c = by_name.get(name) or by_name.get(
                f"{cell} {metric}{op}{bar:g}"
            )  # runner prints bare floats
            if c is None:
                continue
            xs.append(ci + ki * width)
            ys.append(c["measured"])
            cols.append(GREEN if c["pass"] else RED)
        ax.bar(xs, ys, width=width * 0.92, color=cols, zorder=2)
    verdicts = " · ".join(f"{k['id']}: {k['gate']['verdict']}" for k in knobs)
    ax.set_title(verdicts, fontsize=7, color=GREY, pad=4)
    for ci, (cell, metric, op, bar) in enumerate(crits):
        ax.hlines(bar, ci - 0.08, ci + 0.8, colors="black", linewidth=1.4, zorder=3)
    ax.set_xticks([i + 0.4 - width / 2 for i in range(len(crits))])
    ax.set_xticklabels([f"{c}\n{m} {o} {b:g}" for c, m, o, b in crits], fontsize=7)
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("measured")
    order = "/".join(k["id"] for k in knobs)
    fig.suptitle(
        f"{results['skill']} v{results['skill_version']} — gate record "
        f"(bars per cell, left→right: {order}; black tick = frozen bar; "
        f"green pass / red fail)",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    return fig


# ---- arc charts: curated from GATED records only (citations inline) ----

# slalom3@1.0, the same exam cell across every sitting. Sources:
# experiments/corridor_slalom_v2/journal.md (K0-K2), experiments/horizon
# (h48), experiments/chain_learning (K1-K3), experiments/bcft_generalist
# (K0-K1), experiments/chain_distill (BC), experiments/distill_generalist
# (BC2 pots), experiments/conservative_ft (anchored).
SLALOM_SITTINGS = (
    ("v2 K0\n(v1 best)", 0.00, "RL"),
    ("v2 K1\n900k", 0.00, "RL"),
    ("v2 K2\n1350k", 0.00, "RL"),
    ("h48\nhorizon", 0.033, "RL"),
    ("cl K1\ngate pay", 0.067, "RL"),
    ("cl K2\ngraded", 0.00, "RL"),
    ("cl K3\nboth", 0.00, "RL"),
    ("bcft K0\nnaive FT", 0.00, "FT"),
    ("bcft K1\ntargeted FT", 0.00, "FT"),
    ("BC clone\nspecialist", 0.967, "BC"),
    ("BC2 pot\ngeneralist", 0.933, "BC"),
    ("anchored\nFT@1.0", 0.933, "BC"),
    ("sched+edge\nCROWN n=120", 0.700, "BC"),
)


def slalom_wall_figure():
    fig, ax = plt.subplots(figsize=(9.5, 3.8))
    xs = range(len(SLALOM_SITTINGS))
    cols = {"RL": GREY, "FT": RED, "BC": GREEN}
    ax.bar(
        xs,
        [s[1] for s in SLALOM_SITTINGS],
        color=[cols[s[2]] for s in SLALOM_SITTINGS],
        zorder=2,
    )
    ax.axhline(0.70, color="black", linewidth=1.4)
    ax.text(0.1, 0.72, "frozen bar 0.70 (probe-priced)", fontsize=8)
    ax.set_xticks(list(xs))
    ax.set_xticklabels([s[0] for s in SLALOM_SITTINGS], fontsize=7)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("slalom3@1.0 success")
    ax.set_title(
        "The slalom wall: five RL eliminations and two fine-tune erasures "
        "(grey/red) vs imitation (green) — same exam, same seeds; last bar "
        "= the crowned artifact (pooled n=120, ALL guards green)",
        fontsize=9,
    )
    fig.tight_layout()
    return fig


# Fine-tune safety: chain vs repairs across dose, from the BC2 prior.
# Sources: experiments/distill_generalist (dose 0), experiments/
# conservative_ft (25k/75k/225k + anchored), experiments/bcft_generalist
# (450k).
FT_DOSES = (0, 25_000, 75_000, 225_000, 450_000)
FT_CHAIN = (0.933, 0.00, 0.133, 0.20, 0.00)
FT_GAP = (0.70, 0.90, 0.967, 0.967, 0.967)
FT_MGAP = (0.43, 0.833, 0.933, 0.867, 0.90)
ANCHOR = {"chain": 0.933, "gap": 0.80, "mgap": 0.433}  # 450k @ kl=1.0


def finetune_safety_figure():
    fig, ax = plt.subplots(figsize=(7.5, 4))
    xs = range(len(FT_DOSES))
    ax.plot(xs, FT_CHAIN, "o-", color=RED, label="chain (RL-unlearnable)")
    ax.plot(xs, FT_GAP, "s-", color=GREEN, label="gap (repair target)")
    ax.plot(xs, FT_MGAP, "^-", color="#1565c0", label="mgap (repair target)")
    for key, y, c in (
        ("chain", ANCHOR["chain"], RED),
        ("gap", ANCHOR["gap"], GREEN),
        ("mgap", ANCHOR["mgap"], "#1565c0"),
    ):
        ax.scatter([len(FT_DOSES) - 1], [y], marker="*", s=170, color=c, zorder=5)
    ax.annotate(
        "stars: KL-anchored @450k\n(decoupling measured)",
        xy=(3.6, 0.6),
        fontsize=8,
    )
    ax.set_xticks(list(xs))
    ax.set_xticklabels(["0\n(BC2)", "25k", "75k", "225k", "450k"], fontsize=8)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("fine-tune dose (PPO steps on the five-world diet)")
    ax.set_ylabel("success")
    ax.set_title(
        "Fine-tune safety: corrosion outruns repair (the chain dies inside "
        "25k) — only the KL anchor decouples",
        fontsize=9,
    )
    ax.legend(fontsize=8, loc="center right")
    fig.tight_layout()
    return fig


# Dodgeball: success by ball speed per contender + the oracle ceiling.
# Sources: experiments/dodgeball (K3), experiments/wm48_defense (K1),
# experiments/dodge_distill (K0 clone), experiments/dodgeball_feasibility
# (oracle ceiling.json).
DODGE_SPEEDS = ("0.6", "1.0", "1.4", "1.8")
DODGE_LINES = (
    ("RL + station tick (K3)", (0.467, 0.60, 0.20, 0.133), GREY),
    ("WM48 eyes (wm48-defense)", (0.20, 0.60, 0.267, 0.167), "#6a1b9a"),
    ("imitation clone (dodge-distill)", (0.333, 0.367, 0.50, 0.60), GREEN),
)
DODGE_ORACLE = (0.90, 0.80, 0.80, 0.80)
DODGE_BARS = (0.65, 0.55, 0.55, 0.55)


def dodge_inversion_figure():
    fig, ax = plt.subplots(figsize=(7, 4))
    xs = range(4)
    ax.plot(xs, DODGE_ORACLE, "k--", label="oracle ceiling (privileged)")
    for i, (label, ys, col) in enumerate(DODGE_LINES):
        ax.plot(xs, ys, "o-", color=col, label=label)
    for x, b in zip(xs, DODGE_BARS):
        ax.hlines(b, x - 0.18, x + 0.18, colors="black", linewidth=1.6)
    ax.set_xticks(list(xs))
    ax.set_xticklabels([f"{s} m/s" for s in DODGE_SPEEDS])
    ax.set_ylim(0, 1.0)
    ax.set_xlabel("ball speed (head-on)")
    ax.set_ylabel("dodge success (survive + hold station)")
    ax.set_title(
        "Dodgeball: the speed curve INVERTS under imitation — fast balls "
        "convert decision accuracy directly (ticks = frozen bars)",
        fontsize=9,
    )
    ax.legend(fontsize=8)
    fig.tight_layout()
    return fig


# moving_gap@1.0, n=200, virgin seeds. Source: experiments/surpass_teacher
# (+ the mgap champion context line from its n=200 promotion-era record).
MGAP_LINES = (
    ("teacher\n(scripted oracle)", 0.885, GREY),
    ("student BC\n(open-loop val .908)", 0.585, "#1565c0"),
    ("student BC+FT\n(450k PPO)", 0.880, GREEN),
    ("pure-RL champion\n(context, other seeds)", 0.82, "#8d6e63"),
)


def mgap_lines_figure():
    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    xs = range(len(MGAP_LINES))
    ax.bar(xs, [m[1] for m in MGAP_LINES], color=[m[2] for m in MGAP_LINES])
    for x, m in zip(xs, MGAP_LINES):
        ax.text(x, m[1] + 0.015, f"{m[1]:.3f}", ha="center", fontsize=9)
    ax.set_xticks(list(xs))
    ax.set_xticklabels([m[0] for m in MGAP_LINES], fontsize=8)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("moving_gap@1.0 success (n=200)")
    ax.set_title(
        "Surpass-the-teacher: imitation buys the skill, on-policy RL buys "
        "back the 30-point closed-loop drift — and ties the teacher",
        fontsize=9,
    )
    fig.tight_layout()
    return fig


# The climb to the deployment gate: every n=100 integration record, in
# order. Sources: experiments/integration_v1 (clone), experiments/
# integration_ft (anchored FT, hybrid, +hot specialist, +big pot).
CLIMB = (
    ("slalom clone\n(single BC)", 0.33),
    ("anchored\ncourse-FT", 0.39),
    ("flight-plan\nhybrid", 0.55),
    ("+hot slalom\nspecialist", 0.62),
    ("+big-pot\nspecialist", 0.72),
)


def integration_climb_figure():
    fig, ax = plt.subplots(figsize=(7.5, 4))
    xs = range(len(CLIMB))
    cols = [GREY] * (len(CLIMB) - 1) + [GREEN]
    ax.bar(xs, [c[1] for c in CLIMB], color=cols, zorder=2)
    for x, (_l, v) in zip(xs, CLIMB):
        ax.text(x, v + 0.015, f"{v:.2f}", ha="center", fontsize=10)
    ax.axhline(0.70, color="black", linewidth=1.6)
    ax.text(0.05, 0.715, "deployment gate 0.70 (n=100 random courses)", fontsize=8)
    ax.set_xticks(list(xs))
    ax.set_xticklabels([c[0] for c in CLIMB], fontsize=8)
    ax.set_ylim(0, 0.85)
    ax.set_ylabel("integration success (n=100)")
    ax.set_title(
        "The climb to the deployment gate — five lineups, each built from "
        "the previous one's failure analysis",
        fontsize=9,
    )
    fig.tight_layout()
    return fig


ARCS = {
    "arc_integration_climb": integration_climb_figure,
    "arc_slalom_wall": slalom_wall_figure,
    "arc_finetune_safety": finetune_safety_figure,
    "arc_dodgeball_inversion": dodge_inversion_figure,
    "arc_surpass_teacher": mgap_lines_figure,
}


def render_all(out_dir: str) -> list:
    os.makedirs(out_dir, exist_ok=True)
    written = []
    for path in sorted(glob.glob("experiments/*/results.json")):
        if "_selftest" in path:
            continue
        with open(path) as f:
            results = json.load(f)
        if not results.get("knobs"):
            continue
        fig = skill_gate_figure(results)
        name = results["skill"].replace("-", "_")
        p = os.path.join(out_dir, f"gate_{name}.png")
        fig.savefig(p, dpi=110)
        plt.close(fig)
        written.append(p)
    for name, fn in ARCS.items():
        fig = fn()
        p = os.path.join(out_dir, f"{name}.png")
        fig.savefig(p, dpi=110)
        plt.close(fig)
        written.append(p)
    return written


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs/figures")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        import tempfile

        synth = {
            "skill": "synthetic",
            "skill_version": "1",
            "targets_frozen": [
                {"cell": "a@1.0", "metric": "success", "op": ">=", "bar": 0.7},
                {"cell": "guard:b", "metric": "crash", "op": "<=", "bar": 0.1},
            ],
            "knobs": [
                {
                    "id": "K0",
                    "gate": {
                        "verdict": "continue",
                        "criteria": [
                            {
                                "name": "a@1.0 success>=0.7",
                                "kind": "target",
                                "measured": 0.9,
                                "pass": True,
                            },
                            {
                                "name": "guard:b crash<=0.1",
                                "kind": "guard",
                                "measured": 0.2,
                                "pass": False,
                            },
                        ],
                    },
                }
            ],
        }
        with tempfile.TemporaryDirectory() as td:
            fig = skill_gate_figure(synth)
            p1 = os.path.join(td, "synth.png")
            fig.savefig(p1)
            plt.close(fig)
            ps = []
            for name, fn in ARCS.items():
                fig = fn()
                p = os.path.join(td, name + ".png")
                fig.savefig(p)
                plt.close(fig)
                ps.append(p)
            for p in [p1] + ps:
                assert os.path.getsize(p) > 10_000, f"figure too small: {p}"
        # curated series must stay inside [0, 1] and cite real sittings
        assert len(SLALOM_SITTINGS) == 13 and all(
            0 <= s[1] <= 1 for s in SLALOM_SITTINGS
        )
        assert len(FT_DOSES) == len(FT_CHAIN) == len(FT_GAP) == len(FT_MGAP)
        print(
            "RESULTS-FIGURES OK: gate chart renders from the runner schema, "
            "all four arc charts render, curated series sane"
        )
        return

    written = render_all(args.out)
    print(f"[figures] wrote {len(written)} files to {args.out}")
    for p in written:
        print("  ", p)


if __name__ == "__main__":
    main()
    sys.exit(0)

# stability_v3 — the BLOCKER's actual question, asked directly

Opened 2026-08-31, from stability_v2's close-out. Two campaigns priced the
band; neither ever measured the thing the temporal gate needs: **does a
ceiling stop the 160-epoch explosion?** K1/K1' were both correctly held
back by their K0 gates — gates whose apex-preservation framework
stability_v2's C0 control then measured to be un-gradable at n=1 (any code
change reshuffles the draw; single-draw spread at 96-res reaches ~0.02
dense). This registration drops the un-gradable bar and asks the stability
question with stability instruments.

## Pre-registration (committed before any number)

### The arm (single; no new knob — the code is exactly what main ships)

`python -m scripts.train --epochs 160 --batch 64 --seed 0 --latent-d 128
--data output/combined_96.npz
--out experiments/stability_v3/artifacts/wm_96d128_g3_e160.pth`
under the two-sided guard [1.0, 8.0] already in `world_model/losses.py`.
The 80-epoch reference pair under this exact code is g3
(`experiments/stability_v2/artifacts/wm_96d128_g3.pth`): MSE 3.750 /
no-op 5.930, val z-std med/max 1.89/4.00.

### Bars (frozen — stability-level only)

The broken pair this must beat: the one-sided 160-epoch run destabilized
at no-op 7.6 -> 99.4 (13x), z-std max 12.05, train-val rows incoherent.

- no-op MSE@32 <= 2x g3's no-op (<= 11.86)
- val z-std max <= 8.5
- self-consistency on the holdout instrument: dense >= 0.90 AND
  veer val >= 0.90
- budget unchanged (264.2 KB / est 17 ms)

Explicitly NOT graded: apex preservation at n=1 (measured un-gradable in
stability_v2; per-world rows are RECORDED with draw-noise language, and
any future certification of ranking cost goes through >=3-draw means).

### GO / NO-GO (frozen)

- All four bars pass -> **GO: the variance guard is closed for the
  temporal gate's purpose** — duration no longer destabilizes the recipe;
  perception_v3's prerequisite is satisfied by measurement. The guard
  stays [1.0, 8.0].
- The no-op or z-std bar breaks -> **NO-GO**: a ceiling alone does not
  stabilize the EMA chase; the next registrations are target-side
  (normalization, momentum schedule), each its own campaign. The
  two-sided guard still stays (strictly safer; zero loss-level cost at
  healthy points).
- Self-consistency breaks with no-op/z-std green -> **NO-GO, different
  lesson**: bounded scale without usable rankings — record what the row
  shows; do not iterate inside this campaign.

### Honesty clauses

Inherited from stability_v1/v2 (unguarded `z_c_last`, mean-offset drift,
journal-side artifacts, no deployment); plus: this campaign makes no
claim about ranking quality vs the apex — that comparison is draw-noise
limited and out of scope by measurement, not by convenience.

---

(verdict lands below when the run completes)

---

## Final verdict — 2026-08-31: NO-GO — the ceiling is the wrong lever, and the runaway finally shows its face

(One harness note first, rule 6: the first queue launch silently no-oped —
zsh does not word-split an unquoted `$PY`, so every stage printed "command
not found" and nothing trained. Rewritten as a bash script file, rerun,
same knob. The reads below are from the real run, logs `output/sv3_*`.)

| read (160 ep, band [1.0, 8.0]) | value | bar | verdict |
|---|---|---|---|
| no-op MSE@32 | **275.9** | <= 11.86 (2x g3) | **FAIL** — worse than the one-sided run's 99.4 |
| val z-std max (med) | **15.85** (5.48) | <= 8.5 | **FAIL** — the hinge is overpowered, not obeyed |
| holdout dense / veer val | 0.5917 / **0.125** | both >= 0.90 | FAIL (widened veer 0.46; rows destroyed) |
| budget | 264.2 KB / 17 ms | unchanged | pass (irrelevant) |
| **mean abs z** (recorded) | **42.15** | — | g3 pair was 4.31; the apex 6.7 |

**The mechanism, finally named:** |z| = 42 against std ~5.5-15.9 — the
runaway is DOMINATED by the latent's CENTER drifting, which no std hinge
constrains by construction. This is exactly the suspect stability_v1's
honesty clause pre-registered ("the latent's CENTER wanders"). The
LAMBDA_VAR=1.0 hinge at 8 is a soft penalty the EMA-chase gradient simply
out-pulls (std max 15.85 with the hinge ACTIVE the whole way) — and the
chase itself appears to ride on the mean, not the spread. Two-sided
variance guarding is the wrong lever for the dominant failure mode.

**stability_v3 closes NO-GO.** The two-sided guard stays in the code
(pre-registered clause: strictly safer than one-sided, zero loss-level
cost at healthy operating points) but the temporal gate's prerequisite —
a 160-epoch-stable recipe — remains OPEN. The named next registrations
(each its own campaign, none flown here): a center hinge (|z.mean(dim=0)|
penalty — the symmetric twin of the std hinge), target-side latent
normalization, or an EMA momentum schedule.

### The stability arc's standing state (three campaigns, three honest negatives)

- v1 [1,4]: ceiling binds at the recipe's healthy point -> space contracts
  onto the lower hinge; apex ranking pays. Rule: the band must clear the
  recipe's own operating point.
- v2 [1,8] + C0: dead ops are not draw-neutral on MPS (recipe identity
  includes the op graph); same-code determinism reconfirmed at the tensor
  level; first measured 96-res draw spread (~0.02 dense) — single-draw
  apex-preservation bars are un-gradable.
- v3 [1,8] @ 160: the explosion is center-drift dominated (|z| 42), the
  std hinge is overpowered and orthogonal to the main mode. The lever for
  "duration stability" lives on the MEAN / the EMA target, not the spread.

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

# The Wall Eats Pixels: A Sweet Spot, a Pincer, and the Residue's Name

*Article 16 of a series on building a latent world model that fits in
512 KB. Article 15 closed the cheap tier by exhaustion — nothing that
reallocates information moves dense separation. This one opens the
spigot instead: give the model MORE pixels, and watch the wall finally
move — then map exactly where it stops moving, and read the name of
what remains. Everything reruns from
[microdrone-world-model](https://github.com/csinghans/microdrone-world-model).*

---

> **The simple version.** Give a near-sighted pilot their first real
> pair of glasses and a cluttered street may come into focus. Our first
> camera sweep looked like that: sharper pictures helped, until the
> next setting made things worse. We suspected that remembering the
> previous glance would repair what remained. The follow-up did not
> meet its improvement bar, and repeating the recipe exposed large
> differences between runs. Before declaring which glasses work best,
> we need to give every pilot the same eye chart.

*Evidence update, 2026-09-13.* The original July article named temporal
input as the residual hypothesis. The August temporal and stability
campaigns did not validate that explanation. This revision keeps the
recorded results and narrows the conclusions; it does not change any
campaign's bars or verdict. The
[evidence audit](../../docs/RESEARCH-AUDIT-2026-09-13.md) identifies
the remaining comparison and provenance limits.

## Where article 15 left us

The cheap tier died by exhaustion: capacity, pooling resolution, data
scale, curriculum composition and isolation — all priced against
frozen bars, all NO-GO, one law banked (contrast is the curriculum).
The surviving hypothesis was almost embarrassing in its simplicity:
maybe a 64x64 camera just cannot see a pillar three metres out. Maybe
the wall eats pixels.

One preliminary detour mattered. The representation program had parked
`wm_3x` — the best offline generalist ever measured. Run through the
full v0.8 gate as a candidate general WM, it was **refused
spectacularly**: false-evasion 100 %, closed-loop crash doubled. The
best-ranking model was the worst-flying one, and the program banked
v0.5's law one level down: **instruments predict; only the closed loop
certifies.** Every claim below is an offline claim, and says so.

## The sweet spot

`perception_v1` changed pixels and nothing else — same seeds, same
courses, same recipe, the camera dialed from 64 to 96 to 128. The
recorded seed-0 dense rankings formed an inverted U:

| camera (pixels : latent dims) | dense AUC@32 |
|---|---|
| 64 (192 : 1) | 0.9177 |
| **96 (432 : 1)** | **0.9947** |
| 128 (768 : 1) | 0.6999 |

At 96, dense separation — the number nothing in nine prior arms could
move — jumped +0.077 to near-perfect, and every dense-side calibration
metric moved with it. This was evidence worth pursuing for the sensor
resolution hypothesis, on this particular training draw.

At 128 the same architecture drowned. And the failure had structure:
the veer-ranking probe (a relative, left-vs-right judgment) snapped
back to perfect exactly where dense ranking (an absolute,
close-vs-colliding judgment) collapsed. Limited representation capacity
is a plausible explanation for that trade. Compression ratio alone was
not isolated as its cause, and this resolution curve has not been
replicated across training draws.

## The pincer

Three campaigns now triangulated one design point. The trilogy: at
starved input, capacity only reallocates. 96-res: at rich input, the
small latent starves the easy worlds. 128: at richer input, it starves
everything. So `perception_v2` held the measured sweet spot and
widened the latent — capacity returning WITH input worth spending on —
and pre-registered three recoveries.

All three landed. Veer: 0.375 back to double-perfect. Dense: held at
0.9965. Saturation: 0.62 → 0.52 → **0.31**, through the bar. The
first arm in the program required to pass everything at once came
within 0.013 of its classic guard. That margin was only one failed
criterion: moving, open-space calibration and overall AUC also failed.
The arm passed one of three primary bars and closed NO-GO; the classic
margin does not measure its distance from a full pass.

## Two cheap deaths, and a mechanism each

`perception_v3` spent the last two cheap hypotheses against that
residue, one knob per arm.

*Maybe the bigger net is under-trained at the frozen 80 epochs.*
Doubling to 160 did not under-deliver — it **destabilized**: the
no-op latent MSE rose from 7.563 to 99.4, about 13x. That is a squared
error ratio, not a measured 13x increase in latent standard deviation.
The later `stability_v3` run with a two-sided variance penalty failed
too: no-op MSE 275.9, maximum latent std 15.85, mean absolute latent
value 42.15. A variance penalty cannot constrain a uniform translation
of the latent, so a drifting center is a plausible contributor. Neither
a ceiling nor any proposed center/EMA fix has stabilized this recipe
in the recorded 160-epoch tests.

*Maybe the open-space over-warn is bearing aliasing — pool finer.*
Finer horizontal pooling has now been refuted at two operating points
(strips 8 at 64-res cost dense −0.19 in the trilogy; strips 6 at
96×D128 cost −0.37 and broke the veer probe). It has never once
helped. (A harness lesson rode along: MPS demands divisible pool
sizes, so the registered strips-8 arm was impossible at a 12-column
feature map — the tool now fails loud with the valid divisors, and the
deviation to strips 6 was registered with its rationale.)

## The residue's hypothesis, tested

The July hypothesis was that temporal input could repair moving-world
ranking and open-space over-warning. Two August campaigns tested
specific forms of that idea:

| campaign | recorded moving AUC comparison | verdict |
|---|---|---|
| frozen-latent probe | single-frame control 0.8986; difference 0.8810; GRU 0.9015 | NO-GO: neither gains the required 0.03 |
| pixel input, three reported seeds | single-frame mean 0.8164; two-frame mean 0.7899 | NO-GO: primary and veer guard fail |

These negatives apply to the tested heads, frame spacing and recipes.
They do not establish that a frozen latent destroys all motion
information, or that time is either the cause or an impossible remedy.

The pixel campaign also exposed a comparison problem. Its single-frame
rows span 0.143 on moving and 0.228 on dense, but each checkpoint seed
selects a different subset of an independently generated holdout. Those
spans mix training variation with evaluation-set variation. In addition,
the reused seed-0 control came from the old one-sided variance recipe,
whereas the fresh controls and two-frame arms used the new band.
The original NO-GO stands; attributing the spread requires another
instrument. A range from three rows is not a confidence interval or
evidence that every affordable experiment is underpowered.

The next useful comparison fixes an independent holdout across all
checkpoints and records recipe provenance and uncertainty by rollout.
That can distinguish evaluation variation from model variation before
spending on a larger training diet. The 96-px closed-loop gate is a
separate missing measurement.

## The standing state

`wm_96d128` is the recorded offline dense apex: 0.9965 dense,
double-perfect veer, saturation 0.31, at 264 KB and an estimated 17 ms.
That estimate fits the campaign's 83 ms decision-period bar while
exceeding the project's approximately 8 ms baseline compute target;
it is not a hardware timing measurement. It is not deployed or
certified: the full bars are unmet and no closed-loop row exists.
Nor does its selected seed-0 row establish the recipe's expected
performance.

Sources: [perception_v1](../../experiments/perception_v1/journal.md),
[perception_v2](../../experiments/perception_v2/journal.md),
[perception_v3](../../experiments/perception_v3/journal.md),
[stability_v3](../../experiments/stability_v3/journal.md),
[temporal probe results](../../experiments/temporal_probe_v1/probe_results.json),
[temporal pixel journal](../../experiments/temporal_v1_pixel/journal.md).
The pixel and stability model rows are committed journal tables; their
checkpoint files and raw training logs are not tracked in Git.

## The lessons

1. **Test added information as well as capacity.** The resolution sweep
   produced a useful candidate, with measured tradeoffs.
2. **Keep checkpoint results separate from recipe claims.** A sweep on
   one training seed does not establish a reproducible optimum.
3. **Give comparisons the same exam.** Report rollout uncertainty and
   training variation separately.
4. **Measure the failure a guard actually controls.** A soft std penalty
   is neither a hard bound nor a constraint on the latent center.
5. **Keep a hypothesis revisable.** The temporal NO-GOs narrow the
   tested options; they do not name the residual cause.

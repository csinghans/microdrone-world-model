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
> pair of glasses and the cluttered street snaps into focus — that was
> our 96-pixel camera. Hand them binoculars instead and they walk into
> a lamppost: too much image for the brain behind it — that was 128.
> Give the stronger glasses AND a bigger visual memory and almost
> everything comes back: the clutter stays sharp, the left-right
> instinct returns, the panic fades. Almost. One thing never comes
> back with sharper glasses: things that MOVE. Because seeing motion
> was never about resolution — it is about remembering the previous
> glance. Our model has no previous glance. That, at the end of
> fifteen retrains, is the residue's name.

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
dense ranking wrote an inverted U with a cliff:

| camera (pixels : latent dims) | dense AUC@32 |
|---|---|
| 64 (192 : 1) | 0.9177 |
| **96 (432 : 1)** | **0.9947** |
| 128 (768 : 1) | 0.6999 |

At 96, dense separation — the number nothing in nine prior arms could
move — jumped +0.077 to near-perfect, and every dense-side calibration
metric moved with it. The sensor was the bottleneck. **The wall eats
pixels.**

At 128 the same architecture drowned. And the failure had structure:
the veer-ranking probe (a relative, left-vs-right judgment) snapped
back to perfect exactly where dense ranking (an absolute,
close-vs-colliding judgment) collapsed. The 64-d latent triages, and
what it keeps rotates with the dose. The governing variable is the
compression ratio — how many pixels each latent dimension must carry.

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
within 0.013 of its classic guard — the closest full pass in fifteen
retrains — and still closed NO-GO, because the deficit had rotated
once more: the moving world (stuck at ~0.89 in every 96-res arm), the
open-space over-warn, the all-row.

## Two cheap deaths, and a mechanism each

`perception_v3` spent the last two cheap hypotheses against that
residue, one knob per arm.

*Maybe the bigger net is under-trained at the frozen 80 epochs.*
Doubling to 160 did not under-deliver — it **destabilized**: the
target latent's scale exploded ~13x, because the variance guard bounds
the latent's spread only from BELOW while the EMA target chases the
inflating online encoder. A one-sided guard plus a chase dynamic,
compounding with duration. The model it produced was not worse-trained
but internally inconsistent. Banked: any future long-memory recipe
must close that guard first.

*Maybe the open-space over-warn is bearing aliasing — pool finer.*
Finer horizontal pooling has now been refuted at two operating points
(strips 8 at 64-res cost dense −0.19 in the trilogy; strips 6 at
96×D128 cost −0.37 and broke the veer probe). It has never once
helped. (A harness lesson rode along: MPS demands divisible pool
sizes, so the registered strips-8 arm was impossible at a 12-column
feature map — the tool now fails loud with the valid divisors, and the
deviation to strips 6 was registered with its rationale.)

## The residue's name

What survives every knob this program owns is one cluster with one
plausible cause:

* the moving world sits at ~0.89 in every 96-res arm, down from 0.956
  at 64 — **motion was traded for detail**;
* a single-frame latent cannot rank what it cannot see move;
* the open-space over-warn fits the same shape — without temporal
  context, sharp detail everywhere reads as threat everywhere.

The residue's name is **time**. Not more pixels, not wider latents,
not finer pooling: the previous glance. And the program already owns
the two facts any temporal attempt must respect — the v0.2/trilogy
finding that memory without rich input bought nothing, and this
campaign's finding that the training dynamic destabilizes at duration
unless the variance guard is closed.

## The standing state

`wm_96d128` is the offline dense apex: 0.9965 dense, double-perfect
veer, saturation 0.31, at 264 KB and ~17 ms — comfortably inside the
512 KB / 83 ms envelope. It is NOT deployed and NOT certified: the
full bars are unmet, no closed-loop row exists, and this series has
twice measured what offline records are worth in the air. It stands as
the map's highest surveyed point, with the flag planted one ridge
short of the summit and the remaining ridge named.

## The lessons

1. **When reallocation is exhausted, add information.** Nine arms
   moved nothing; the first information-adding knob moved everything.
2. **Dose matters.** The same knob that produced the breakthrough at
   96 produced a collapse at 128. Sweep before you conclude.
3. **The latent triages.** Watch WHICH skills die as you push a
   bottleneck — the rotation pattern (relative vs absolute judgments)
   is the diagnosis.
4. **Match capacity to input** — in both directions.
5. **Guards must bound both sides.** A variance floor without a
   ceiling is a slow explosion with a fuse measured in epochs.
6. **Name your residue.** A campaign that ends in NO-GO but converts
   "the wall" into "the previous glance" has moved the program.

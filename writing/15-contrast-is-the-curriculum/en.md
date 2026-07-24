# Contrast Is the Curriculum: The Specialist That Couldn't

*Article 15 of a series on building a latent world model that fits in
512 KB. Article 13 proved the dense wall is kinematic for the autonomous
pilot; article 14 found the assisted chapter blocked by the same eyes.
This one is the story of one day spent throwing every cheap thing we had
at those eyes — sharper pooling, a bigger latent, three times the data,
a rebalanced curriculum, and finally a pure specialist — and watching
the dense skill fall after every single one. The last corpse named the
mechanism. Everything reruns from
[microdrone-world-model](https://github.com/csinghans/microdrone-world-model).*

---

> **The simple version.** Train a radiologist only on cancer scans and
> something strange happens: they get WORSE at reading cancer scans.
> Knowing what sick looks like requires knowing what healthy looks
> like — take away the healthy scans and every image starts to look
> malignant, which is the same as none of them looking malignant. We
> spent four campaigns trying to make our drone better at its hardest
> scenes: sharper vision, a bigger brain, three times more flying,
> extra hard scenes in the mix, and finally a specialist that studied
> nothing but the hard scenes. Every step made it worse, and the
> specialist was the worst of all. The easy scenes were never padding
> in the curriculum. They were the definition of safe that danger is
> measured against.

## One wall, two chapters

By v0.15 the repo had two independently-measured versions of the same
complaint. The autonomy chapter: dense-world crashes are kinematically
committed by the time any trigger fires, and the heads' warn
probabilities are miscalibrated exactly where clutter peaks. The
assisted chapter: the guardian's imminent veto fires on ordinary
gap-threading, because in clutter the collision heads cannot separate
*close-but-threading* from *about-to-hit*. Same eyes, same failure,
measured from two cockpits.

The instruments made it concrete. On the frozen baseline (the unified
WM), 62 % of dense warn predictions sit pinned past 0.95/0.05
(saturation), and the signed warn gap is **anti-monotone in clutter**:
+0.165 of over-warn in open space, −0.057 of under-warn where the world
is thick. The architecture suspect was equally concrete: the encoder
pools the whole scene into **four horizontal strips** — 15° of bearing
per bin — so in a dense field several pillars share a bin, and the
latent cannot say which one is on the flight line.

So we pre-registered a program: fix the eyes with the cheap knobs
first, offline (an 80-epoch retrain is ~30 minutes on a laptop; a
closed-loop probe is hours), with the bars frozen from the baseline row
before any candidate trained. Dense AUC@32 ≥ 0.9335 (recover the
specialist's ranking); saturation ≤ 0.4658; high-clutter |gap| ≤
0.0284; veer-ranking stays perfect; 512 KB stands.

One gift arrived before any science: the control arm — the same recipe
through the new plumbing — reproduced the baseline checkpoint **to four
decimals on every instrument**. Training is deterministic on this
machine. Every delta below is exact, not a draw.

## Tier 1: sharper eyes, bigger brain (architecture)

Double the lateral resolution (eight strips, 7.5° per bin) — the
mechanism-matched knob. Result: dense AUC **0.918 → 0.727**, and
saturation got *worse* (0.62 → 0.71). The coarse pooling we blamed was
quietly acting as a regularizer: sharper per-bin evidence pins the
heads harder.

Double the latent (D=128, the capacity control): dense **→ 0.762**.
Both knobs improved classic and perfected the veer-ranking probe — and
paid for it in dense. At 120 transit rollouts, extra representational
freedom flows to the easy world's features. The budget never bound
(153/194 KB of 512). The binding resource was data.

## Tier 2: three times the world (scale)

So we tripled the diet — same architecture, same recipe, 360 transit +
240 room rollouts, dense rollouts included, tripled from 40 to 120.

The result is the program in miniature: the 3× model is the **best
general anticipator ever measured here** (overall AUC 0.951, classic
+0.10, the high-clutter calibration gap 4.7× tighter) — and dense
ranking **fell** to 0.842. More dense data made the model worse at
dense, because the global objective spent the new capacity everywhere
else. Dense was not starved. It was **outcompeted**.

## Tier 3: rebalance the curriculum (composition)

Fine — pay dense with someone else's rollouts. Same 3× total, dense
share doubled to 50 % (180/90/90). Dense recovered a third of what
scaling lost (0.865), never approached the baseline — and the program
recorded its first broken guard: veer-ranking fell off perfect
(0.875), the moving row dropped below its bar, and open-space
over-warn inflated 1.4-2×.

Three tiers in, a curve was forming: dense share 22 % → 33 % → 50 %
gives dense skill 0.918 → 0.842 → 0.865. An inverted U, peaking at
*low* share. The curriculum hypothesis was dying; something else was
load-bearing.

## Tier 4: the specialist that couldn't

The org-chart road: if dense loses every fight for a shared latent,
stop sharing. Train a WM on **dense only** — the full data budget, the
full capacity, one world. The existence bar was generous: beat the best
shared-latent dense row by one point (≥ 0.9435) and a router campaign
unlocks (the two-WM residency and the dispatch router are shipped
precedents; the three-resident bill came to 299.9 KB — silicon was
never the problem).

The specialist scored **0.6436**.

Not "failed to beat the champion" — catastrophically worse at its own
world than every mixed model in the table. Its open-space over-warn
exploded to +0.56: everything it had ever seen was cluttered, so
"warn" was almost always right, so the heads saturated toward yes and
stopped ranking anything. And its veer probe was perfect — both
splits, 1.000 — because left-versus-right is a *relative* judgment,
learnable anywhere. What died was the *absolute* judgment:
close-but-safe versus about-to-hit. The specialist had never seen what
safe looks like.

## The one figure

| dense share of diet | dense AUC@32 |
|---|---|
| 22 % (the 1× mixed models) | **0.918 – 0.934** |
| 33 % (uniform 3×) | 0.842 |
| 50 % (dense-heavy 3×) | 0.865 |
| 100 % (the specialist) | **0.644** |

Eight trained arms, one instrument, one bar never met. The mixed 1×
models are the apex of this architecture family, and every departure —
capacity, resolution, scale, composition, isolation — falls off it.

The mechanism, named by the last corpse: **the mixed diet was never
diluting dense knowledge; it was supplying the negatives.** Dense
discrimination is a *contrastive property of the curriculum* — the
model learns what dangerous-in-clutter means only against a live
definition of safe-and-open. Remove the contrast and the concept
dissolves; drown the contrast in more of everything and it thins.

## What remains, and what it must carry

The cheap tier is now closed **by exhaustion, not assumption**:
architecture knobs, data knobs, curriculum knobs and the org chart are
all priced against the same frozen bars, four pre-registrations, four
recorded negatives. What remains is the perception tier — input
resolution above 64×64, deeper convolutions, depth-supervised
features: the first knobs that would give the latent *more
information* rather than reallocating the information it has.

And the program's finding travels with it as a design constraint:
whatever sees more must still be trained against the mixed curriculum.
**Contrast is not the garnish. Contrast is the curriculum.**

## The lessons

1. **Let a control arm price your noise floor.** Ours reproduced the
   baseline to four decimals and made every subsequent delta exact.
2. **A skill that degrades under every enrichment is telling you what
   it is made of.** Dense skill fell under capacity, resolution,
   scale, composition AND isolation — the only invariant of the apex
   models was the *mixture*.
3. **Specialization is not isolation.** The best "dense specialist"
   in the table is a generalist that also saw dense.
4. **Buy your verdicts offline when you can.** Eight arms cost a day
   because the instruments were checkpoint-parametrized and the
   closed-loop phase stayed gated behind a GO that never fired.
5. **Exhaustion is a result.** The expensive road is now the *proven*
   next road, not the assumed one — which is exactly what makes it
   fundable.

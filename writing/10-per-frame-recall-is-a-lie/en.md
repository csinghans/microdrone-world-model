# Per-Frame Recall Is a Lie: Detection as Sequential Evidence

*Article 10 of a series on building a latent world model that fits in
512 KB. Article 9 was about hand-offs between flight experts; this one
is about a different kind of hand-off — from a detector's per-frame
score to a mission's verdict — and how that translation lies in both
directions. It ends with a theoretically optimal sequential test
losing, on the record, to a two-frame rule, and the reason is the same
law we keep meeting everywhere. Everything reruns from
[microdrone-world-model](https://github.com/csinghans/microdrone-world-model).*

---

> **The simple version.** A security guard doesn't need every glance to be right — they look again. Our detector misses the target in a third of single frames, yet the mission finds it 93 % of the time, because the search is built to take many deliberately different looks. But the opposite trick fails: a rule that accumulates suspicion FOREVER ends up flagging every passerby, because tiny errors pile up without limit. The working recipe: look many times, remember briefly.


## The number that flies is not the number on the bench

Our indoor missions find their target at ~0.93. The detection head
they ride recalls the target in **0.5–0.76 of individual frames**. Both
numbers are honest; the gap between them is choreography. The shipped
search does not ask one frame to be right: it yaw-scans a full circle,
approaches to sub-metre range, faces the candidate, and requires two
consecutive hits before it declares. Give a mediocre per-frame
detector many *deliberately different* looks at the same target and
the mission-level recall compounds toward one.

So per-frame recall lies downward: it understates what a mission built
around it achieves. If we had gated on per-frame numbers, we would
have thrown away a working system. That is the comfortable half of the
story.

## It lies upward, too

Every one of those detection scores was measured the same way: hover,
grab a frame, score it. Stationary imaging. Nobody had ever asked what
the same head does on frames harvested DURING flight — so we
instrumented both search runners with behaviour-preserving trace hooks
and recorded every frame the missions actually saw: 40 flights,
**10,542 labelled frames**.

The stationary bench said AUC **0.9818**, recall 0.758 at the deployed
threshold. The in-flight corpus said AUC **0.8888** — and recall at
the same threshold **collapsed to 0.182** while false alarms stayed at
0.002. Read those together and the diagnosis is precise: **motion
breaks the operating point, not the ranking.** Scores shift down; the
ordering survives; the threshold calibrated on stills is simply the
wrong number in the air.

The deployed missions are insulated — the shipped choreography detects
while hovering, which is exactly the regime the head was trained in.
But the debt is now priced instead of invisible: any future
cruise-detection design pays −0.093 AUC and a broken threshold, and
the one released knob (retrain the head on moving frames — escalation
stops at heads, never the world model) is named in the ledger, not
run.

## The seductive fix: stop trusting frames, accumulate evidence

If single frames are unreliable and thresholds are fragile, theory has
a beautiful answer: sequential evidence. Calibrate each frame's score
into a log-likelihood ratio, accumulate, fire when the sum crosses a
boundary — Wald's SPRT and its CUSUM variant are provably optimal in
expected time-to-decision. The 10,542-frame corpus recorded by the
in-flight campaign is exactly the replay bench such a rule needs, so
we ran the duel properly: incumbent confirm-k against CUSUM-SPRT,
configurations selected on one block under the deployed false-alarm
budget (FA ≤ 0.10), scored frozen on the other block, both directions.

| direction | rule (train-selected) | correct | FA | miss |
|---|---|---|---|---|
| b1→b2 | confirm-k (k=2, thr 0.4) | 0.200 | 0.250 | 0.550 |
| b1→b2 | CUSUM-SPRT (A=6) | 0.000 | **0.850** | 0.150 |
| b2→b1 | confirm-k (k=1, thr 0.8) | 0.250 | **0.100** | 0.650 |
| b2→b1 | CUSUM-SPRT (A=6) | 0.150 | **0.600** | 0.250 |

**Refuted, both directions.** The optimal-in-theory rule does not lose
narrowly; its false-alarm rate explodes to 0.85 and 0.60 against an
incumbent that holds 0.25 and 0.10.

## Why: the horizon

The mechanism is worth more than the table. CUSUM's accumulator
resets at zero and otherwise remembers everything — an **unbounded
lookback**. This corpus, like any honest search corpus, is 94 %
negative frames; on imperfectly calibrated scores those negatives
carry a slightly positive drift, and a drift integrated over hundreds
of frames must eventually cross ANY finite boundary. Optimality
assumed the likelihoods were true; deployment guarantees they are not.
confirm-k, by contrast, can only fire on evidence contained in its
last k frames — a fixed window that BOUNDS the false-alarm mass any
single decision can draw on.

**The horizon's boundedness beats the accumulation's optimality.**

Readers of article 8 have met this law wearing different clothes: the
quantized margin-trigger that flipped every run to false-evasion was
an any-over-run MAX statistic — one noisy margin anywhere flips the
whole flight — while confirm-k's consensus suppressed false positives
and paid in recall instead. Max statistics, unbounded accumulators,
consensus windows: **choose who may fire, over how much history, and
you have chosen which error explodes.**

## What actually ships

The configuration of record stays what it was: hover-scan plus
confirm-2 — a choreography that *manufactures* independent looks and a
firing rule that only ever reads a bounded window of them. On its
flight gate: correct 0.70 / FA 0.10 / miss 0.20 / collision 0 / return
1.0, against a camera-locked baseline that could not turn to confirm
and drowned at FA 0.95.

And the honest boundaries, from the same ledger: on this corpus the
best any firing rule achieved is correct ~0.25 — **when the head is
weak on moving frames, no decision layer rescues the mission**, so the
in-flight head retrain outranks any cleverer rule; and both rules'
selected configurations were unstable across 20-flight blocks
(confirm-k's own train pick blew the FA budget on the other block) —
model selection needs pooled blocks, another instance of article 9's
"a block is a draw, not a rate". A bounded-window LLR — the middle
point between confirm-k and CUSUM — is named in the ledger as the one
untried candidate, registered before it is ever run.

## Rerun the numbers

```bash
python -m eval.eval_inflight_detect --n 20 --seed0 620000   # the in-flight corpus + AUC
python -m eval.eval_evidence --duel                         # confirm-k vs CUSUM-SPRT, cross-fit
python -m eval.eval_person_pose --probe                     # per-frame vs mission recall, five poses
```

Bars, decision rules and every verdict, committed before the numbers:
`experiments/detect_inflight_v1/journal.md` (the debt, priced) and
`experiments/evidence_v1/journal.md` (the duel and the horizon law).

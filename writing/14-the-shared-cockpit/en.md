# The Shared Cockpit: What the Guardian Is Worth

*Article 14 of a series on building a latent world model that fits in
512 KB. Article 13 proved the dense wall is kinematic, closing the
autonomy chapters' oldest frontier. This one opens a new chapter by
changing who holds the stick: a pilot flies, the world model watches,
and we measure — pair by pair, same course, same pilot — what a
guardian is actually worth. Everything reruns from
[microdrone-world-model](https://github.com/csinghans/microdrone-world-model).*

---

> **The simple version.** Imagine a driving instructor with a second
> brake pedal. A good one saves you maybe twice a lesson — a short
> stab of the brake, then your wheel again. Now imagine one who
> stomps that pedal at every parked car, and who, when nervous
> enough, grabs the whole wheel — even though in exactly those
> streets they can't see any better than you, and drive rather
> worse. We built the instructor: a brake pedal (the momentary
> veto), a wheel-grab (the takeover), and a strict rule for giving
> the wheel back. Then we ran the same lesson twice, with and
> without the instructor, hundreds of times, and counted crashes.
> With OUR instructor, there were more. With an instructor who has
> perfect eyes, there were fewer. The pedal was never the problem —
> what matters is whether the instructor can see, and how well they
> drive once they've grabbed the wheel.

## The turn

Every chapter of this project so far has been Level 4, in the
driver-assistance sense: the AI flies from launch to landing —
transit through pillar fields, indoor search for beacons and people.
The new chapter asks the Level 3 question. A pilot — a human at a
keyboard, or a seeded synthetic stand-in — flies the drone. The world
model runs anyway, spending its one question on someone else's
intent: *and if THIS command is held?* When the answer is bad enough,
the machine intervenes.

The wedge does not change: 512 KB, one body-fixed camera, ~8 ms of
compute in an 83 ms decision period, 0.67 s of anticipation. What
changes is the customer. For four versions the model anticipated for
itself. Now it anticipates for you.

## The ladder

Authority moves along a ladder, never a cliff
(`planner/authority.py`):

* **PILOT** — your command executes; the guardian only watches.
* **OVERRIDE** — the momentary veto. Fires only on the *absolute*
  imminent backstop (crit within ~170 ms on YOUR command) or the
  geofence; substitutes the safest menu action for ~0.5 s, then hands
  back. The relative danger margin — the trigger the autonomous MPC
  uses freely — is deliberately demoted here: it only accumulates
  *escalation evidence* (3 of the last 5 decisions), because a signal
  with a known context-dependent floor should never grab a human's
  stick on a single reading.
* **AUTO** — the autopilot flies. Entered instantly when the pilot
  asks (handing the machine the stick is always granted, same
  decision), or by escalation when danger persists. Left only through
  a **gated handback**: the pilot asks, and the last 12 decisions
  were clear. A handback request during danger is latched, not
  granted — the AEB that will not release the brake mid-event.

The mechanics were certified before any science: four new rows in the
safety suite assert the veto lands on the same decision its trigger
crosses, the toggle transfers on its own decision, the handback waits
for exactly 12 clear decisions with zero authority chatter, and a
fence-seeking pilot gets capped at the same boundary as the
autonomous filter. On the embedded bill the guardian costs nothing:
+0.0 KB of weights, and the deployed decision path is literally the
MPC's own shared-encoder sweep (~3.9 M MACs) — the pilot's command is
just one row of a matrix the model was already scoring.

## The student

You cannot pre-register a campaign around a human hand, so the pilot
is an instrument: a privileged gap-tracker (it sees the whole scene,
as a human does) wrapped in a frozen imperfection pipeline —
distraction windows that hold a stale command, fat-thumb noise,
a reaction-latency FIFO. Three personas (expert / average / novice,
83–333 ms reaction) are constants frozen with the tool.

The protocol is the track's one non-negotiable trick: **every seed is
flown twice** — bare, then guardian-wrapped — with the same pilot
random stream. "Prevented", "added", "false intervention" become
per-seed attributable facts, not rate arithmetic. (The unassisted arm
later reproduced bit-for-bit across two campaigns — the pairing is as
solid as the sim's replay determinism.)

An honest wrinkle surfaced immediately: in dense worlds the *expert*
persona crashes more than the average one (0.30 vs 0.15 at cruise).
The expert's tight deadband tracks gap centres aggressively and buys
lateral exposure; the sloppier pilot flies straighter and lives
longer. The skill dial inverts in clutter. The instrument is honest
about it, and the personas stayed frozen.

## Campaign one: the full ladder

`assist_v1` pre-registered the whole thing before any number: cells,
arms, a usable band for the pilot map, and two selection rules — a
cell only counts if a *privileged oracle guardian* (perfect eyes,
same ladder) can cut at least half its crash mass; a WM arm only
qualifies if it adds **zero** crashes on paired clean seeds.

The probe's verdict was a clean NO-GO. On the two cells the oracle
certified as recoverable, both WM arms — unified and champion —
*added* 18–20 crashes out of 40 paired seeds, overriding 40–50 % of
clean-flight decisions. The margin sweeps (0.3 / 0.5) barely moved
any of it: this is not a threshold you can tune your way out of.

The oracle told the other half of the story. Same ladder, same
triggers, perfect eyes: 7 crashes prevented, zero added, moving
333–880 ms before the counterfactual impact — comfortably inside the
model's own 0.67 s horizon. Anticipation-for-a-pilot *works*. And at
dense × 1.2 m/s even the oracle cannot halve the novice's 0.80 crash
rate: article 13's kinematic floor, re-measured from the assistance
side.

Two mechanisms, named from the data. First, **the ladder escalates a
better flyer into a worse one**: the pilots are privileged by
construction, the takeover autopilot is vision-only, and vision-only
autonomy crashes at 0.40–0.45 in dense on the same seeds — worse than
every unassisted persona at cruise. Second, **the dense over-report
fires the triggers**: the same context-conditional miscalibration a
head-recalibration campaign measured (and failed to fix cheaply) a
version ago, now surfacing as imminent alarms on ordinary
gap-threading veers.

## Campaign two: pricing the rungs

The two mechanisms were confounded in the full ladder, so `assist_v2`
un-confounded them with one zero-training knob: `escalate=False`.
The veto stays; the wheel-grab never happens. Same grid, and —
deliberately — the *same seeds*, so full-ladder versus veto-only is
itself a paired comparison.

The attribution came back sharp:

* **The takeover owned about half the harm.** Added crashes fell from
  64 to 29 across the twelve static cells the moment the ladder
  stopped grabbing the wheel — and the catastrophic tail vanished
  (one cell went from 10 added to 0).
* **The naked veto's price scales with speed.** At 0.8 m/s the veto
  is near break-even — zero added across every classic-at-cruise
  cell, 7 prevented against 5 added overall. At 1.2 m/s it prevented
  9 and added 24. A 0.5 s substitution hold displaces ~0.6 m at that
  speed: the intervention is itself a trajectory perturbation of the
  same magnitude as the errors it means to fix.
* **Perfect eyes flip the ladder's sign.** In dense at cruise, the
  full-ladder oracle *beat* the veto-only oracle (0/3/0 added by
  persona versus 3/4/1). When the takeover pilot is good, escalation
  protects; when it is bad, it is the dominant poison.
* One prediction inverted honestly: we expected braking in front of
  moving obstacles to be its own hazard. For the WM arm it wasn't —
  the v2 latent carries no velocity, so it barely fires on movers,
  and what barely fires barely harms. The hazard surfaced in the
  oracle arm instead, whose constant-velocity forward sim is exactly
  wrong geometry for a crosser. Blindness, honestly accounted, can
  look like restraint.

## The law

One sentence survived both campaigns, and it is the chapter's
banked result:

> **A guardian is only as good as (a) its eyes in the context it
> guards, and (b) the pilot it swaps in.**

Neither half is optional. v1 showed a sound ladder with bad eyes and
a worse relief pilot is *net harmful* — not useless, harmful. v2
showed that fixing the ladder cannot rescue the eyes, and the oracle
showed that fixing the eyes rehabilitates the ladder. The automotive
industry learned this the slow way; a 512 KB drone can measure it in
an afternoon of paired seeds.

## What ships anyway

No WM-triggered intervention clears the added==0 sacred guard today,
so nothing is *certified*. But the chapter does not close empty:

* the authority machine, certified and chatter-proof, wrapping any
  pilot behind the standard policy contract;
* the `assisted` flight mode (zero new lock entries) and a keyboard
  cockpit — fly it yourself; the GIF's border narrates the ladder
  (green PILOT, red OVERRIDE, blue AUTO);
* the instrument set — personas, paired runner, oracle ceiling — that
  turns any future guardian claim into an afternoon's measurement;
* the priced roads: a certified takeover artifact (the champion
  policy, latent-consistent, as the AUTO rung), eyes-before-authority
  (the dense over-report is representation-class work, not a
  threshold), and speed-scoped assistance (the veto's break-even
  pocket at 0.8 m/s is real).

## The lessons

1. **Wrap the pilot, never the runner.** The guardian is a policy;
   the frozen episode runner never learned this chapter happened.
2. **Let perfect eyes price the ceiling before you blame the
   ladder.** One privileged arm split "the design is wrong" from
   "the eyes are wrong" for the cost of a probe.
3. **An intervention is a trajectory perturbation.** Its price scales
   with speed, and it must be measured against the crashes it causes,
   not just the ones it prevents. `added == 0` is the sacred guard.
4. **Escalation needs humility.** Never hand the stick to a relief
   pilot you haven't certified *for this context* — the ladder's sign
   lives there.
5. **Same seeds, paired, always.** The whole chapter's evidence is
   differences between flights that were identical until the guardian
   spoke.

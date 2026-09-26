# Early-intervention paired support pilot

Registered before generating or inspecting either arm. This is a bounded
development-data pilot, not another sitting of any closed model exam.
Earlier audits found that recovering repeated-command windows did not add
training action/class courses. We now ask whether beginning interventions
earlier supplies the missing safe steering courses.

## Frozen comparison

Generate both arms unconditionally: 180 transit rollouts each, 160 steps,
64 px, classic/dense/moving in that order, world_balanced roles, no domain
randomization, and the same registered seed. The only varied knob is the
start of nonpassive interventions: the existing 24–48-step approach versus
step zero. Passive courses remain passive. Keep speed range, six commands,
40–56-step holds, geometry, camera, physics, labels and index unchanged.

Both arms use the same new per-rollout RNG isolation: SeedSequence([seed,
rollout_index]).spawn(3), in scene/schedule/noise order. The scene stream
owns env reset seed, speed and spawn; schedule owns approach length, hold
length and action draws; noise owns latency and actuation noise. Consume
the approach draw in both arms even when its length is replaced by zero.
This makes the command sequence a time shift on nonpassive courses. It
prevents differing schedule lengths from changing later scene identities.
The existing shared-stream generator remains the default. Neither arm is
compared numerically with old corpora as if they were paired.

## Instrument prerequisites

Before either arm, pass simulator-free schedule/default compatibility
tests and the existing rendered-versus-removed fixture check for each
transit world (plus its room fixture), using the registered seed and bars.
Preserve fixture PNGs, full logs, source/runtime/registration hashes and
protected artifact hashes. Check the existing shared recipe against the
pre-change generator on small, separately seeded simulator fixtures; these
are instrument checks, never extra pilot support samples.

Before interpreting counts, assert paired world IDs, in-path/passive roles,
speeds, initial pillars/velocities, initial positions and initial pixels
are exactly equal (NaN padding compares equal). Assert each intervention
command/segment sequence equals the corresponding shifted control prefix;
all passive trajectories are identical. Require 60 courses per world,
20 passive per world, and both classic threat roles. Any mismatch is a
harness error: retain failure evidence, repair, replay only the same inputs.

## Frozen outputs and decision

Use the unchanged training index and inclusive horizon-32 warn labels
(radius 0.7). Produce a full-corpus support report for each arm and a table
of positive/negative windows and distinct rollout IDs for every world and
all six commands, including zeros. Report differences, but do not count
overlapping windows or courses as independent observations.

The candidate is structurally sufficient only if BOTH veers in BOTH dense
and moving have at least 20 positive and 20 negative windows, from at least
3 positive and 3 negative distinct courses EACH. These deliberately modest
pilot minima test presence of support; they are not power or model gates.
Apply the same requirements to the control for context; its insufficiency
must not prevent generating/analyzing the candidate. Report both statuses
and every deficit without selecting favorable actions or worlds.

No fitting, model inference, bootstrap, promotion, release, extra seed,
extra rollout or repeated exam follows either outcome. An insufficient
candidate closes this pilot as an honest negative. A sufficient candidate
only informs a future separately registered study. Keeping no deployed
model changes means this pilot adds no on-device RAM or inference work;
it does not establish the 512 KB / 8 ms deployment targets.

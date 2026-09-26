# Timing-pilot split support audit

Retrospective audit registered before inspecting partition counts. The
full-corpus timing pilot is already known: candidate sufficient, control
insufficient under its fixed steering minima. That result stays unchanged.
This audit asks whether the SAME count minima survive the actual training
split. It is not a new model gate or permission to enlarge the pilot.

## Frozen scope

- Only the two exact pilot corpora in registration.json, no regeneration,
  extra courses, new simulation, fitting, inference or bootstrap.
- Split seeds 0, 1 and 2, unchanged `_split_rollouts`: stratified by world,
  in-path flag and passive role, with its existing 20% validation rule.
  Analyze all seeds and both partitions unconditionally. Do not select,
  reorder courses, rebalance by action/label or search for a favorable seed.
- Reuse the training index, horizon-32 inclusive warn labels (radius 0.7),
  action catalogs and unchanged metadata-support producer. Print all six
  actions in all three worlds, including zero-supported actions.
- Apply the existing pilot's minima (20 positive/negative windows, each
  from 3 positive/negative course IDs) to BOTH dense veers and BOTH moving
  veers in EACH train/val partition. The committed requirements expand to
  24 action cells per arm. This is a diagnostic of retaining the original
  structural support, not a power calculation or an adopted training gate.
- Report geometric veer-probe support for all courses and each partition,
  by world: frames, contributing original course IDs, and safer-left/right
  truth counts. Use `world_model.veer_probe.select` unchanged; assert direct
  partition selection equals filtering the full selection. Count zero and
  singleton worlds explicitly; no new probe gate is introduced.
- Record forward and danger-now support from the generic report as context.
  These transit-only data contain no room trials and cannot establish room
  guard support. No inference about room performance follows.

## Invariants and interpretation

Before interpreting support, verify frozen dataset hashes and source pilot
receipts. Reuse their prior rendering and exact pair checks: this audit
reads no pixels. Train and validation must be disjoint, exhaust all 180
original course IDs, and have exactly equal membership between arms for
each seed. Reconcile partition windows/classes with whole-corpus counts;
course counts need not sum because classes/actions overlap. Recompute the
original full-corpus support counts to confirm unchanged inputs/index.

Pass simulator-free instrument tests before the real audit. Preserve
source/runtime identities, complete logs, all deficits and genuine exits.
The whole audit must finish even if any requirement is insufficient.
Such a result closes this audit as a support limitation, not a harness
failure. A passed diagnostic still authorizes no training. Any future
model study needs its own registration, independent exam and frozen guards.

No seed retries, reassignment, new draws or relaxed bars follow failure.
Keep the original full-corpus pilot conclusion and all closed model NO-GOs.
This offline metadata work changes no deployed parameters, RAM or inference
work and proves nothing new about the 512 KB / approximately 8 ms target.

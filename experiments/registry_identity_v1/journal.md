# Stable scenario registration — 2026-09-21

At `18fe875`, `register()` accepted a custom world at builtin ID 0. The
classic spec still returned ID 0, but `world_names_array()[0]` now named the
custom world. It also accepted reassignment of an existing custom or
builtin name to another ID, truncated 3.9 to 3, converted `True` to 1 and
accepted negative/string IDs. These are isolated synthetic reproductions;
they do not establish corruption of any archived research corpus.

The [before receipt](before.json) pins the original source and outcomes.
Reproduce them in an isolated in-memory registry with:

```bash
bash experiments/registry_identity_v1/verify_before.sh
```

Registration now validates everything before changing the registry. IDs
must be nonnegative integers (Python/NumPy integer scalars are supported),
unique across names and stable for an already registered name. Builtin
classic/dense/moving retain 0/1/2, even if a builtin entry is temporarily
absent. A skill can still update its callable factory under the same name
and ID, including through repeated `load_skill` calls.

Names must be nonempty trimmed strings. Numeric names are reserved for
unregistered slots in sparse catalogs; `all` is reserved for pooled metric
rows. Factories must be callable. A rejected registration leaves all prior
entries intact. This does not freeze factory behavior or assign universal
dynamic IDs across different fresh-process registration orders: saved data
must still carry and use its own `world_names` table.

The [compatibility receipt](compatibility.json) compares the old and current
registry in fresh processes. Both load all 15 existing skill declarations
in the same sorted order and produce identical catalogs and IDs for all
17 registered worlds. Reloading all skills in reverse order retains those
identities. The skill declarations and loader match the baseline byte for
byte. No scenario factory is called for this compatibility check. Recheck
the committed receipt without replacing it with:

```bash
bash experiments/registry_identity_v1/verify.sh
```

Validation is recorded in [verification.json](verification.json):

- `python -m sim.scenario_registry` covers 18 rejected registrations,
  no mutation on rejection, callable replacement under a stable ID,
  sparse/automatic allocation, unambiguous name roundtrips and restoration
  of the caller's registry after its selftest. The command is already in CI.
- Skill-schema and environment-free composite-geometry selftests pass;
  policy recipe/evaluation, all 23 research-runner regressions, combined
  world identity and all ten corpus publication regressions also pass.
- Both frozen-before and skill-compatibility checks pass. All 13 commands
  exit 0 in `output/research_integrity_selftest/registry_identity_v1.log`,
  including whole-repository Black (176 files), Ruff and diff-whitespace.
- All nine locked artifact hashes match before and after the work. Checks
  ran on local macOS/Python 3.14, not remote Linux/Python 3.12 CI.

This repairs an upstream identity boundary complementing the
[combined-catalog repair](../combined_world_identity_v1/journal.md). It
changes no training knob, seed schedule, model architecture or deployed
inference work against the 512 KB / approximately 8 ms target. No training,
new research corpus, model scoring, flight gate, archived result, remote
push or release was performed.

# Combined-corpus world identity — 2026-09-21

At `47668fc`, the combiner discarded both source catalogs, retained transit
IDs and assigned every indoor row to fixed ID 3 under the catalog
`classic/dense/moving/room`. A registered transit world at ID 3 therefore
became room. Reordered transit catalogs silently changed builtin identities,
and a non-room indoor input was also silently renamed room. The synthetic
[before receipt](before.json) records all three cases without simulation,
model inference or training. Reproduce the original behavior with:

```bash
bash experiments/combined_world_identity_v1/verify_before.sh
```

`datasets.combine_rollouts.combine` now decodes each source's own catalog
and remaps by name. Output classic/dense/moving remain 0/1/2; extra transit
names follow, then room. For the standard catalog, room remains 3. For
`classic/dense/moving/gap`, gap stays 3 and room becomes 4. Reordered source
catalogs are accepted without changing the meaning of their rows. Unused
transit catalog entries are retained, except room is placed at the end.
Consumers must read the embedded catalog rather than assume room is ID 3.

Before concatenation, both catalogs must contain unique, nonempty, trimmed
Unicode names. World IDs must be one-dimensional nonnegative integers within
their own catalog, with the same rollout count as every stacked array. The
transit input cannot contain room rows; observed indoor rows must name room.
Invalid or missing identity is rejected rather than inferred from position.
The CLI's transit/room summary now counts decoded names, including when
custom transit worlds occupy IDs above 2.

The builder recipe, both generators, action arrays, labels, schedule rules
and model code are unchanged. Existing corpora are not rewritten. This is
an identity repair, not evidence of improved prediction or flight. Preserving
a custom world's name does not register its semantics in every downstream
audit: for example, the action-support checker still requires a known action
catalog and rejects unsupported worlds explicitly.

Validation is recorded in [verification.json](verification.json):

- `python -m datasets.combine_rollouts --selftest` covers canonical IDs,
  custom/repeated worlds, reordered catalogs, unchanged inputs and stacked
  arrays, plus 15 malformed/wrong-source identity cases.
- `python -m scripts.dataset_publication_selftest` passes all ten artifactless
  regressions. The added test follows the real parser, builder, combiner and
  NPZ publisher with only the two generators mocked; the saved names remain
  `classic/gap/room` and the CLI reports two transit rows and one room row.
- `bash experiments/combined_world_identity_v1/verify.sh` compares six
  canonical synthetic corpora (uniform, weighted and subset worlds, each
  with legacy/balanced provenance) against the frozen old combiner. Every
  array's shape, dtype and bytes, dictionary order and serialized compressed
  NPZ bytes match. The builder AST and both generator files also match the
  baseline. This is fixture parity, not a regenerated historical corpus.
- Dataset-support and scenario-registry selftests pass. Both changed selftest
  commands are already in manual CI's fast groups; no CI expansion is needed.
- Whole-repository Black (176 files), Ruff and diff-whitespace checks pass.
  All nine locked artifact hashes match before and after this repair. The
  full log is `output/research_integrity_selftest/combined_world_identity_v1.log`;
  all nine commands exited 0. This is local macOS/Python 3.14 validation.

No optimizer, new research corpus, model score, flight, scientific bar,
archived result, remote push or release was changed. The repair adds no
deployed parameters, RAM requirement or inference work to the 512 KB /
approximately 8 ms target.

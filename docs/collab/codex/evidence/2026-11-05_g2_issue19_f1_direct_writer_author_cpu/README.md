# G2-I19-F1 — direct-writer root guard, author CPU evidence

Formal implementation Root: `5e6903b9dd09828f725dc61dcd6e98012fae87b3`.
Child/Gitlink unchanged: `1069fe78841228cadbbfbe6afbd767eaed6225da`.
Previous implementation: `fbe578908a840a5f4e5b351f1c2e8fb019def6e5`.
Review authority: `99ad0de0249a660d46642c3ae849129733b3c503`, G2-I19-F1 only.
Pre-fix parent `8d3a5b297d9b3339c16a873a7e1e04941a20a745` merges the independent
review document into the PR branch without changing the fbe57890 production code.

## Results

- **Old production: expected RED5** (5 failure, 0 error/skip; 2 positive cases
  deselected). `red/frozen_before.json` records cache.py and new regression hashes
  before execution. The cache.py Blob was checked against fbe57890, and both
  inputs were unchanged after RED. The failure is DID NOT RAISE: old code really
  exports into the unversioned root, rather than a collection/import failure.
- **New exact pair: 181 PASS**, 0 failure/error/skip, 5.65 seconds. Original
  53+83+38=174 cases preserved, plus 7 new preflight cases. New tests are byte-
  identical to the RED inputs. The only existing-test edit initializes a valid
  v2 root in the incomplete-target fixture; all original assert ASTs are equal.
- Ruff **0.12.7** check/format all13 G2 Python files, AST13 and source diff check
  PASS. Clean before/after exact-pair snapshots and source content hashes match.
- `green/` retains the earlier working-tree181 PASS; `final/` is the clean,
  version-bound result. Do not sum these repeated executions as different cases.
- Previous Issue19 evidence20 hashes still match; it is preserved unchanged.

Final argv/cwd/environment/versions are in `final/commands.json` and
`final/runtime.json`. `final/incremental_scope.json` verifies the exact three G2
file changes, unchanged original assertions and frozen new regressions. Source
Git Blobs/SHA256, raw JUnit/logs and the focused remediation diff are included.
Raw traceback and unified-diff whitespace is retained verbatim. The passing diff
check concerns the implementation commit, not normalization of archived output.

`run_author_cpu.py` is the exact external runner. Reproduction requires a clean
checkout at the Formal Root, equivalent installed CPU dependencies and adapting
actual author paths as needed. Its output directory must not already exist.
The new refusal fixtures fingerprint files and directories including mtimes, and
check that no model/environment factory is called. Positive fixtures cover absent
and pre-existing empty roots, schema publication and immutable verified skip.

## Native/production boundary

This increment executes synthetic author CPU only. The independent review at
99ad0de0 already accepts174 CPU tests, native real736 frames73/74 with4/4 spatial
groups, and read-only7-episode/2353-frame/308412416-pixel legacy bitmap equality.
Those are reviewer executions on fbe57890, not new Codex executions. `not_run`
in final/gate.json describes **this author run**, not a reversal of those passes.
The depth encoder, replay, source mapping, verifier and Child are byte-identical
to that reviewed implementation and no native rerun was performed.

No real source data or server files were accessed/transferred, no migration,
production export/resume, GPU, V3/V2 merge or training action occurred. No claim
of independent Code Gate approval is made. Stop at fresh review of this pair.

Only text evidence is archived. Temporary synthetic NPZ/parquet and caches are
excluded. SHA256SUMS covers every other file in this directory.

# Authority-root config grammar CPU/static remediation design v0.2

**Gate**：`G0-R09-B-TTT-V035-AUTHORITY-ROOT-CONFIG-GRAMMAR-CPU-STATIC-REMEDIATION-DESIGN`

v0.2 supersedes the rejected v0.1 only for the three same-pair review findings. It remains docs-only and cannot authorize implementation, Stage-1 retry/materialization, real source I/O, child changes, GPU or training.

## Frozen parser contract

The outer `-I -S -B -c` payload and bootstrap adapter each carry an **inline**, stdlib-only equivalent lexical parser. They must not import one another or any new module. For the same raw config, both return the same ordered canonical sequence of `(section_name, subsection_or_none, variable_name, raw_value)` UTF-8 tuples, or both fail with the same category; the test witness compares serialized canonical tuples byte-for-byte.

A section header is exactly either `[section]` or `[section "subsection"]`. `section` is ASCII `[A-Za-z][A-Za-z0-9-]*` and is ASCII-lowercased. `subsection`, if present, is nonempty ASCII `[A-Za-z0-9_-]+` and is **preserved byte-for-byte and case-sensitive**; it is never lowercased, unescaped, interpolated or flattened into a dotted key. `variable` is ASCII `[A-Za-z][A-Za-z0-9-]*` and is ASCII-lowercased. Whitespace is allowed only around the complete header and around `=`. Escapes, a second quote, dots, slashes, whitespace/control bytes in subsection, comments appended to a header, `include`/`includeIf`, duplicate exact triples and every unknown triple fail-close.

The allowlist is a set of exact `(section, subsection, variable, value)` tuples. Thus `[branch "V2"]` and `[branch "v2"]` are distinct; only the former appears below. No case folding can merge two quoted subsection identities.

## Complete frozen real-config allowlist

The complete current bound config is exactly the following 14 tuples; a missing tuple, extra tuple, duplicate, changed value or changed quoted-subsection spelling fails.

| section | subsection | variable | exact value |
| --- | --- | --- | --- |
| `core` | none | `repositoryformatversion` | `0` |
| `core` | none | `filemode` | `true` |
| `core` | none | `bare` | `false` |
| `core` | none | `logallrefupdates` | `true` |
| `remote` | `origin` | `url` | `https://github.com/wxwy/psm_wma.git` |
| `remote` | `origin` | `fetch` | `+refs/heads/*:refs/remotes/origin/*` |
| `branch` | `main` | `remote` | `origin` |
| `branch` | `main` | `merge` | `refs/heads/main` |
| `submodule` | `cosmos-framework` | `active` | `true` |
| `submodule` | `cosmos-framework` | `url` | `https://ghfast.top/github.com/wxwy/cosmos-framework.git` |
| `branch` | `V2` | `vscode-merge-base` | `origin/main` |
| `branch` | `V2` | `remote` | `origin` |
| `branch` | `V2` | `merge` | `refs/heads/V2` |
| `rerere` | none | `enabled` | `true` |

The existing raw SHA-256 binding is retained as an independent identity requirement. Descriptor identity, no-symlink route, `config.worktree`/`commondir` absence and all pre-existing Git isolation flags remain unchanged; this exact allowlist adds no executable config authority.

## CPU/static implementation and acceptance

Only the root frozen payload source, `tools/psm_wma/materialize_immutable_source_authority_root.py`, and their direct temporary-fixture tests may change. Tests must prove: the exact table passes both parsers; `[branch "v2"]`, unknown/escaped/dotted/path subsection, changed remote/submodule URL, unknown key, duplicate triple, include and each existing route-drift negative fail; and equivalent-parser canonical output/failure category is byte-identical. Tests use temporary local Git fixtures only and must not create production worktree/ref/evidence or read real source/checkpoint/manifest/data/cache.

After implementation, the corrected payload must receive independent close review. Only then may a new freshness observation bind a new request and obtain a new one-shot Stage-1 materialization approval; v1.3 remains consumed and unretryable.

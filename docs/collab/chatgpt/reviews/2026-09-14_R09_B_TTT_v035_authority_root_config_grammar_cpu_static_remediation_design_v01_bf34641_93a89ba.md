# ChatGPT Independent Review — R09-B TTT v0.3.5 Authority-root Config Grammar CPU/static Remediation Design v0.1

**Date:** 2026-09-14  
**Formal root:** `bf34641f2451b43c3c335bb747ef3c842768a382`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CONFIG-GRAMMAR-CPU-STATIC-REMEDIATION-DESIGN`

## 1. Pair / scope lock

- Re-locked remote `V2` and re-read live `docs/collab/chatgpt/CODEX_INBOX.md`; the effective request binds exact pair `bf34641f2451b43c3c335bb747ef3c842768a382` / `93a89ba61306d840a008813f62f26a34d54850f4`.
- Independently verified the formal root resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Formal technical scope is docs-only: `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_config_grammar_cpu_static_remediation_design_v0.1.md`; no production or child/runtime modification is in this pair.
- The prior v1.3 Stage-1 execution authority was single-attempt and is already consumed. This Gate cannot authorize a retry or materialization.

## 2. Positive observations

The design correctly narrows the remediation to the config parser seam that failed before mutation:

1. It requires both the outer launcher parser and `materialize_immutable_source_authority_root.py::_parse_config_raw()` to use the same lexical/allowlist semantics, avoiding outer/bootstrap divergence.
2. It keeps the existing raw-config digest, retained descriptor/identity, anti-symlink, `config.worktree` / `commondir`, and unknown-key fail-close barriers.
3. It does not generalize to arbitrary Git config syntax: only ordinary sections plus one quoted ASCII subsection are intended, with exact allowlisted keys/values and explicit rejection of include/includeIf/hooks/filter/alias and drifted remote/branch/submodule/rerere values.
4. CPU/static acceptance remains temporary-fixture only, and the post-implementation path correctly requires a new fresh-bound exact Stage-1 request and a new single-attempt materialization approval.

## 3. Blocking finding

### HIGH-1 — quoted-subsection case semantics / canonical-key construction are not frozen

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_config_grammar_cpu_static_remediation_design_v0.1.md:19`

The design explicitly names the real frozen section `[branch "V2"]`, and the lexical contract allows uppercase ASCII letters in quoted subsections. But the allowlist table names the corresponding keys as `branch.v2.remote`, `branch.v2.merge`, and `branch.v2.vscode-merge-base`, while the document never specifies how `(section, subsection, key)` becomes that canonical key.

That leaves two incompatible implementations both apparently conforming to the current text:

- **case-preserving subsection:** `[branch "V2"]` canonicalizes as something equivalent to `branch.V2.*`, which does not match the table's `branch.v2.*` and risks repeating the same fail-close on the real frozen config;
- **case-folded subsection:** `V2 -> v2`, which collapses quoted subsection identity and can treat distinct subsection spellings as one authority namespace.

For this authority parser, subsection identity must not be inferred from an unspecified normalization rule. Section names / variable names may be normalized under the frozen lexical contract, but quoted subsection spelling must have an explicit, deterministic treatment, and the allowlist must be expressed against that exact treatment.

**Exact acceptance:** refreeze the parser contract so both outer and bootstrap implementations:

1. parse a section into an explicit tuple such as `(section_name, subsection_or_none)` rather than a lossy flattened string;
2. preserve quoted subsection bytes/case exactly for authority matching (in particular exact `"V2"`, `"main"`, `"origin"`, and `"cosmos-framework"` as applicable), or otherwise state and justify one exact canonicalization rule without collapsing distinct accepted subsection identities;
3. express the allowlist against exact section/subsection/key triples (or an unambiguous equivalent representation), including the exact `branch "V2"` entries;
4. add positive witness for exact `[branch "V2"]` and negative witness showing a case-different subsection such as `[branch "v2"]` is not silently accepted as the same authority unless the frozen raw config itself exactly uses that spelling;
5. keep every existing raw-digest, descriptor, anti-symlink, unknown-key/value, include/config.worktree/commondir and downstream-scope barrier unchanged.

No production redesign beyond this lexical/canonicalization clarification is requested.

## 4. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_config_grammar_cpu_static_remediation_design_v0.1.md:19)`

Current blockers: **1 HIGH Design/Authority**.  
Production implementation blockers: **0**.  
Evidence-only blockers: **0**.  
Child/runtime blockers: **0**.

## 5. Scope reminder

This verdict binds only exact pair `bf34641f2451b43c3c335bb747ef3c842768a382` / `93a89ba61306d840a008813f62f26a34d54850f4` and the config-grammar docs-only design Gate above.

It does **not** authorize implementation, materialization/retry, source/checkpoint/manifest/data/cache I/O, collection/receipt/source-evidence/record/package/publication, child/runtime/config mutation, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1.

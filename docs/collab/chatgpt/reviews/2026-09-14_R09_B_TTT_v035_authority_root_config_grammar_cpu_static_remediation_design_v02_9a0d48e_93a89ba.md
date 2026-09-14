# ChatGPT Independent Review — R09-B TTT v0.3.5 Authority-root Config Grammar CPU/static Remediation Design v0.2

**Date:** 2026-09-14  
**Formal root:** `9a0d48efc59d6e50e3d0ed2e80f670779d3fad64`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CONFIG-GRAMMAR-CPU-STATIC-REMEDIATION-DESIGN`

## 1. Pair / scope lock

- Re-locked remote `V2` and re-read live `docs/collab/chatgpt/CODEX_INBOX.md`; the effective remediation request binds exact pair `9a0d48efc59d6e50e3d0ed2e80f670779d3fad64` / `93a89ba61306d840a008813f62f26a34d54850f4`.
- Independently verified the formal root resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Relative to rejected v0.1 pair `bf34641f2451b43c3c335bb747ef3c842768a382` / same child, the technical remediation is docs-only: new `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_config_grammar_cpu_static_remediation_design_v0.2.md`; coordination/review/session files are bookkeeping.
- The consumed v1.3 single-attempt materialization authority remains consumed. This design Gate does not authorize retry/materialization.

## 2. Prior HIGH disposition

The v0.1 review retained one HIGH Design/Authority blocker: quoted subsection identity was not frozen. The real config contains `[branch "V2"]`, while the v0.1 allowlist flattened that authority to `branch.v2.*` without defining whether quoted subsections were preserved or lowercased.

**Disposition: CLOSED.**

v0.2 now freezes an explicit non-lossy parser contract:

- section names are ASCII-normalized to lowercase;
- variable names are ASCII-normalized to lowercase;
- quoted subsection bytes are preserved exactly and remain case-sensitive;
- subsection identity is not unescaped, interpolated, lowercased or flattened into a dotted key;
- both outer and bootstrap parsers return ordered `(section_name, subsection_or_none, variable_name, raw_value)` tuples;
- the allowlist is expressed against exact tuples, so `[branch "V2"]` and `[branch "v2"]` are distinct authorities and only exact `V2` is accepted.

The design also freezes the complete current bound configuration as exactly 14 tuples, including exact `branch / V2`, remote, submodule and rerere values.

## 3. Fresh design audit

No new blocking issue was found.

Positive authority properties:

1. **No authority broadening.** The complete real-config tuple set is finite and exact. Missing, extra, duplicate, value-drifted or subsection-spelling-drifted entries fail closed.
2. **Outer/bootstrap equivalence is reviewable.** Each parser must be inline and stdlib-only, with no import dependency between them; same raw config must produce byte-identical serialized canonical tuples or the same failure category.
3. **Case-sensitive subsection identity is preserved.** The exact negative `[branch "v2"]` witness prevents silent case collapsing.
4. **Existing route barriers remain independent.** Raw SHA-256 binding, descriptor identity, no-symlink route, `config.worktree` / `commondir` absence, and Git isolation flags remain unchanged rather than being replaced by the new grammar.
5. **Implementation scope is narrow.** Only the frozen root payload source, `tools/psm_wma/materialize_immutable_source_authority_root.py`, and direct temporary CPU/static tests may change.
6. **Execution authority remains separated.** After implementation, the corrected payload still requires independent implementation-close review, then a newly observed freshness binding and a new exact Stage-1 request with new one-shot materialization approval.

Because v0.2 states that it supersedes v0.1 only for the three same-pair findings, all non-superseded v0.1 acceptance obligations remain binding, including that the actual frozen current config must pass both parsers to the next non-config precondition. Implementation review should therefore verify the real-format assignment whitespace/indentation handling in addition to the exact tuple semantics; this is an inherited acceptance check, not a current design blocker.

## 4. Formal verdict

`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_CONFIG_GRAMMAR_CPU_STATIC`

Current blockers: **0**.  
Design/Authority blockers: **0**.  
Production implementation blockers: **0**.  
Evidence-only blockers: **0**.  
Child/runtime blockers: **0**.

## 5. Scope / next action

This approval binds only exact pair `9a0d48efc59d6e50e3d0ed2e80f670779d3fad64` / `93a89ba61306d840a008813f62f26a34d54850f4` and the design Gate above.

It authorizes only root CPU/static implementation and temporary-fixture witnesses under the frozen v0.2 contract. It does **not** authorize Stage-1 materialization or retry, source/checkpoint/manifest/data/cache I/O, collection/receipt/source-evidence/record/package/publication, child/runtime/config mutation, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.

After implementation closes independently, a new fresh-bound exact Stage-1 request and a new separate single-attempt materialization approval are still mandatory; v1.3 cannot be retried.

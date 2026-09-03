# ChatGPT Independent Re-review — R09-B TTT v0.3.2 Memory Prefix Source/ABI Audit Remediation @ 54ea4ce

**Date:** 2026-09-03  
**Reviewer:** ChatGPT (independent code / design / evidence reviewer)  
**Task/Gate:** `G0-R09-B-TTT-V032-MEMORY-PREFIX-SOURCE-ABI-AUDIT`

## 1. Review identity

- **remediation/design SHA under verdict:** `54ea4cea9ba0eb513080b9505cf23b2446b5d86a`
- **request/ledger SHA supplied by user:** `b521b0305bdfbad9f9d4abc6960c64922adb6693`
- **latest dispatch/ledger SHA observed at review:** `0866dc6ee2242b3cde5e61b57c73704c5892ebbb`
- **child/Gitlink read-only baseline:** `1d90361aeb21db53129ac27ddcaa1285b258fbbc`
- **superseded initial C3 design SHA:** `26bd78d4f3feb9659c63459393c61780bc0b94e7`
- **pre-design/source root baseline:** `2a08f4e37ddfa98038b35965fb4b9f79c1b90806`

The required literal `git fetch origin V2` was attempted in a temporary local repository and failed because the reviewer environment cannot resolve `github.com` (`Could not resolve host: github.com`). Freshness, ancestry, root Gitlink and source files were therefore re-read through the connected GitHub repository interface. Current remote `V2` at review start was `0866dc6ee2242b3cde5e61b57c73704c5892ebbb`.

`b521b03...` is not the remediation/design commit: it only appends the C3 re-review request to `CODEX_INBOX.md` and has `54ea4ce...` as its parent. `0866dc6...` is another Inbox-only dispatch commit. Formal verdict therefore applies only to `54ea4ce... + 1d90361...`.

## 2. Verdict

**REQUEST_CHANGES**

The prior architectural/source conclusions remain accepted. This re-review is blocked only by remaining source/provenance inaccuracies in the docs/dispatch layer. No child/runtime implementation is requested or authorized.

## 3. Accepted remediation

The prior missing ABI facts are now substantively present and correct:

1. The child packer can accept a Local payload with shape `[K_local,D_local]`, pack K rows, assign the current Local GEN-path text-style mRoPE and intentionally not advance the native Vision/Action cursor.
2. `LocalHistoryRuntime.forward()` still exposes the production-facing compatibility shape `[B,1,D]`.
3. The design correctly states that packer multi-row capacity does not prove production multi-slot fast-state/readout integration.
4. The target Memory Prefix must not silently inherit the existing ordinary-GEN Local RoPE/position policy.
5. Remediation scope is root docs/status only; the exact root still pins child `1d90361aeb21db53129ac27ddcaa1285b258fbbc`.

## 4. HIGH-1 — review-target / request-ledger identity is still inconsistent

**Severity:** HIGH  
**Files:**
- `docs/build/PSM-WMA_R09_B_TTT_v032_memory_prefix_source_abi_audit_v0.1_2026-09-03.md:5`
- `docs/collab/chatgpt/CODEX_INBOX.md:944-948` (latest corrected dispatch at `0866dc6...`)

### Finding

The remediated design header still labels `26bd78d...` as **“C3 设计提交（本轮审核对象）”**, but the current remediated document being reviewed is the state introduced by `54ea4cea...`. Separately, the latest Inbox dispatch says the exact review pair is root `b521b03... + child 1d90361...`, even though `b521b03...` is an Inbox-only request/ledger commit and contains no remediation changes.

This recreates the same implementation-vs-ledger ambiguity the project review discipline explicitly forbids.

### Root cause

The documentation does not use distinct immutable roles for:
- superseded/original design SHA;
- current remediation/design SHA;
- request/ledger SHA;
- latest dispatch/ledger SHA.

### Acceptance criteria

A docs-only remediation must:

1. stop calling `26bd78d...` “本轮审核对象”; label it as the **original/superseded initial C3 design SHA**;
2. ensure the re-review request created *after* the remediation commit names the actual remediation/design commit as the exact verdict target;
3. explicitly label the request commit itself as **ledger/request only** and never ask reviewers to bind the formal verdict to it;
4. preserve `2a08f4e...` only as the pre-design/source root baseline and `1d90361...` as child source baseline;
5. submit the new remediation SHA for fresh same-SHA review.

Do not attempt to self-embed a commit's own SHA in the file content. The current remediation SHA can be bound by the subsequent Inbox/request entry; the design body only needs to avoid falsely naming an older SHA as the current review target.

## 5. MEDIUM-1 — newly added packer source anchor uses a non-existent tracked path

**Severity:** MEDIUM  
**Files:**
- `docs/build/PSM-WMA_R09_B_TTT_v032_memory_prefix_source_abi_audit_v0.1_2026-09-03.md:35`
- `docs/collab/chatgpt/CODEX_INBOX.md:928` (C3 remediation request summary)

### Finding

The remediation cites:

`cosmos_framework/model/generator/mot/sequence_packing/sequence.py:545-588`

but the tracked child source at `1d90361...` is actually:

`cosmos_framework/data/generator/sequence_packing/sequence.py:545-588`

The claimed semantics are correct, but the provenance path is not reproducible as written. This directly violates C3 Section 5's requirement that every source anchor be reproducible from the pinned child SHA.

### Root cause

The new source fact was copied with the wrong package prefix (`model/generator/mot/...` instead of `data/generator/...`).

### Acceptance criteria

- replace every occurrence of the bad path with the exact tracked path:
  `cosmos_framework/data/generator/sequence_packing/sequence.py:545-588`;
- retain the accepted facts: `[K_local,D_local]` capacity, K-row Local GEN packing, text-style mRoPE and no native cursor advance;
- keep the correct `local_evidence.py:616-657::LocalHistoryRuntime.forward()` anchor and `[B,1,D]` boundary;
- verify every C3 source anchor resolves at child `1d90361...` before resubmission.

## 6. Scope decision

No child source change is required to close this review. The next allowed action is only a root docs/status provenance correction and a new exact remediation request.

Still prohibited:
- Memory Prefix/runtime/attention implementation;
- `local_memory2llm`, LayerNorm/KV projection, mask/position/RoPE/packer code changes;
- chronology/native-loss integration;
- config/optimizer/checkpoint migration or refreeze;
- GPU/CUDA/torchrun, model/data/cache/checkpoint runtime access;
- training/evaluation/inference;
- P4/P5 real operations and B2-T.

# ChatGPT Independent Review — R09-B TTT v0.3.2 Memory Prefix Source/ABI Audit Design @ 26bd78d

**Date:** 2026-09-03  
**Reviewer:** ChatGPT (independent code / design / evidence reviewer)  
**Task/Gate:** `G0-R09-B-TTT-V032-MEMORY-PREFIX-SOURCE-ABI-AUDIT`

## 1. Review identity

- **root design SHA under verdict:** `26bd78d4f3feb9659c63459393c61780bc0b94e7`
- **request/ledger SHA:** `ae4bd2320a69e2da4f747ff3034d9eb093459ffe`
- **read-only Cosmos child/Gitlink baseline:** `1d90361aeb21db53129ac27ddcaa1285b258fbbc`
- **pre-design/source root baseline named by the document:** `2a08f4e37ddfa98038b35965fb4b9f79c1b90806`
- **design:** `docs/build/PSM-WMA_R09_B_TTT_v032_memory_prefix_source_abi_audit_v0.1_2026-09-03.md`
- **upstream C2 closure:** root `8b0ea2fb289a4bced803148a51ac562165cc2f8d`, child `1d90361aeb21db53129ac27ddcaa1285b258fbbc`

The exact root `26bd78d...` independently resolves `cosmos-framework` to the declared child `1d90361...`.

The required literal `git fetch origin V2` was attempted in a temporary local repository. The reviewer environment still cannot resolve `github.com` (`Could not resolve host: github.com`), so no claim is made that shell fetch succeeded. Current remote `V2`, target ancestry, the exact root Gitlink, current Inbox/SESSION/TODO, and source blobs were instead re-read through the connected GitHub repository interface immediately before this verdict.

## 2. Verdict

**REQUEST_CHANGES**

This is a docs/provenance-only block. The proposed K/V-only Memory Prefix direction remains accepted, and no runtime implementation is authorized or requested by this review.

## 3. Accepted parts

The following current-source observations in the design are supported by the pinned child `1d90361...`:

1. `cosmos3_vfm_network.py` registers `local_memory2llm` and `local_memory_modality_embed` when Local is enabled and zero-initializes them.
2. `_encode_local_memory()` currently projects Local payloads into ordinary packed hidden tokens and writes them at `local_memory.sequence_indexes`.
3. Local indexes are currently added to `all_gen_indexes`, so the existing path is an ordinary GEN-stream query/output path rather than the v0.3.2 K/V-only Memory Prefix.
4. `build_packed_sequence()` and current `two_way_attention()` have no separate MEM K/V stream in their ABI; current two-way behavior is GEN full attention plus UND causal attention.
5. The existing batch path can carry a Local payload into `x0_tokens_local_memory`, but that fact alone does not establish persistent fast-state, K/V-only Prefix insertion, or continual-TTT runtime ownership.
6. The proposed C3 static topics—Prefix owner, norm/projection, packed layout, visibility, position/RoPE, state lifecycle, checkpoint/optimizer—are the correct categories to freeze before any runtime implementation.
7. The scope boundary is correct: this Gate is docs/static only and must not modify child/runtime/attention/config/optimizer/checkpoint or run GPU/training/evaluation/inference.

## 4. HIGH-1 — C3 design SHA and pre-design source baseline are conflated as one “root” identity

**Severity:** HIGH  
**Files:**
- `docs/build/PSM-WMA_R09_B_TTT_v032_memory_prefix_source_abi_audit_v0.1_2026-09-03.md:5-6`
- `SESSION.md:9`
- `TODO.md:101`

### Finding

The formal review target and the request ledger correctly identify the C3 audit/design SHA as:

`26bd78d4f3feb9659c63459393c61780bc0b94e7`

However, the design header labels `2a08f4e...` as **“根仓基线”**, and both SESSION/TODO record this C3 design as `root=2a08f4e...`.

`2a08f4e...` is an earlier source/status baseline; it does **not** contain the new C3 design file. Therefore a later reviewer following the status row cannot reconstruct the exact document under review from the recorded “root”. This repeats the same class of provenance ambiguity previously blocked for stale Gitlink authority.

The source baseline itself is valid and useful, but it must not substitute for the design SHA.

### Root cause

One field is being used for two different immutable identities:

1. the **C3 audit/design commit** that contains the authority being reviewed; and
2. the **pre-design root/source baseline** from which current source facts are being audited.

### Acceptance criteria

Docs-only remediation must explicitly separate the identities, for example:

- `C3 design SHA: 26bd78d...`
- `pre-design/source root baseline: 2a08f4e...`
- `child source baseline/Gitlink: 1d90361...`

and SESSION/TODO must record the C3 request using `26bd78d...` as the exact design/root SHA while retaining `2a08f4e...` only as a separately labeled source baseline.

No child change is required.

## 5. MEDIUM-1 — current Local packing/cardinality/RoPE source map omits two decisive existing ABI facts

**Severity:** MEDIUM  
**Files:**
- `docs/build/PSM-WMA_R09_B_TTT_v032_memory_prefix_source_abi_audit_v0.1_2026-09-03.md:15-35` (current-source map / C3 freeze inputs)
- missing source anchor: `cosmos-framework@1d90361:cosmos_framework/data/generator/sequence_packing/sequence.py:545-588`
- missing source anchor: `cosmos-framework@1d90361:cosmos_framework/model/generator/mot/local_evidence.py:616-657`

### Finding

The design correctly says the target Prefix layout/RoPE/state lifecycle are unresolved, but its current-source map omits two already-implemented Local GEN-path behaviors that materially constrain that audit.

### Existing fact A — the sequence packer already accepts multi-token Local payloads

`PackedSequenceBuilder.pack_local_memory_tokens()` accepts an exact rank-2 payload `[K_local,D_local]`, derives `local_split_len = K_local`, stores that cardinality, and appends all Local indexes. It also generates current Local position IDs with `get_3d_mrope_ids_text_tokens(num_tokens=K_local, temporal_offset=local_temporal_offset)` and intentionally discards the returned next offset so native Vision/Action mRoPE positions are unchanged.

Therefore the current packer already has **multi-row capacity and an existing Local GEN-path mRoPE policy**. Those are current facts, not future Prefix semantics.

### Existing fact B — the production Local history owner is still single-slot

`LocalHistoryRuntime.forward()` explicitly documents and returns:

`tokens [B,1,D]`

and uses the current stateless/recurrent replay path. The newly closed `ContinualTTTLocalMemoryCore` is not installed as this production owner by C2.

Therefore current source has an important split:

- packer can physically pack `K_local > 1` Local rows;
- the production history/runtime owner still emits exactly one Local row;
- neither fact proves the target K/V-only Memory Prefix or multi-slot continual-TTT runtime integration.

The current C3 document says the `local_memory2llm` entry “能表达 K_local 行 token” and generally defers layout/RoPE/state to later audit, but without these two anchors a downstream audit can incorrectly collapse “packer supports K” into “current runtime supports multi-slot”, or accidentally inherit the existing GEN-path text-style mRoPE policy as Prefix authority.

### Acceptance criteria

The C3 design/source map must explicitly record both facts and their boundary:

1. cite `sequence.py::pack_local_memory_tokens` and freeze the **current** Local GEN-path cardinality + position behavior as observed source, not target Prefix authority;
2. cite `LocalHistoryRuntime.forward()` and record the current production history output as `[B,1,D]`;
3. explicitly state that packer multi-row capacity does **not** mean the production Local runtime is multi-slot or that `ContinualTTTLocalMemoryCore` is wired;
4. explicitly state that target Memory Prefix position/RoPE semantics must be independently chosen/audited and must not silently inherit the existing Local GEN-path text-style mRoPE behavior;
5. C3 static closure must later provide exact owner/shape/negative contracts for the transition from the single-slot production owner to `[B,K_local,32]`, and for whether existing `pack_local_memory_tokens()` is bypassed, reused only as payload metadata, or replaced by a separate Prefix context.

No runtime implementation is required to close this design finding.

## 6. Required remediation scope

Allowed remediation is root docs/status only:

- the C3 audit/design document;
- `SESSION.md`;
- `TODO.md`;
- request/ledger bookkeeping if needed.

Do not modify `cosmos-framework` for this remediation.

After remediation, submit the new exact root SHA with the same child baseline `1d90361...` for a fresh same-SHA review.

## 7. Still prohibited

This `REQUEST_CHANGES` does not authorize:

- Memory Prefix runtime/attention implementation;
- `local_memory2llm`, Prefix norm or K/V projection changes;
- position/RoPE/mask/packer changes;
- chronology/native-loss integration;
- config/optimizer/checkpoint migration or refreeze;
- GPU/CUDA/torchrun;
- model/data/cache/checkpoint runtime access;
- training, evaluation or inference;
- P4/P5 real operations;
- B2-T.

The accepted C2 closure remains valid and is not reopened by this C3 docs finding.
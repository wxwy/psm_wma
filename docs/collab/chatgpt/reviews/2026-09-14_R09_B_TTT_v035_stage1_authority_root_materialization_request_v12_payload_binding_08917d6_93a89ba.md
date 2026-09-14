# ChatGPT Independent Review — R09-B TTT v0.3.5 Stage-1 Authority-root Materialization Request v1.2 Payload-binding Correction

**Date:** 2026-09-14  
**Formal root:** `08917d6dba3bde5ab284fd57d00b35b337fd1ea1`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-EXECUTION-REQUEST-INSTANCE-CONSTRUCTION-AND-REVIEW`

## 1. Pair / scope lock

- Re-locked remote `V2` and re-read live `docs/collab/chatgpt/CODEX_INBOX.md`; the effective request binds exact pair `08917d6dba3bde5ab284fd57d00b35b337fd1ea1` / `93a89ba61306d840a008813f62f26a34d54850f4`.
- Independently verified the formal root resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Relative to approved v1.1 pair `3802c51bb156636d53842cefa8e4519f6dfabe81` / same child, the technical delta is root docs-only: new v1.2 Markdown request plus its canonical JSON; coordination/review/session files are bookkeeping. No production code or child/runtime change is in formal scope.
- The controlling authority remains the approved Stage-split refreeze v0.3 (`5a668ad8871798a0c252ce9c05dbf167c36ba839` / same child), which requires every future Stage-1 exact request to carry same-round fresh observations plus immutable canonical request bytes before approval; runtime revalidation is additive only.
- No materialization or other real project mutation is authorized by this review while blockers remain.

## 2. v1.1 payload-binding correction

The v1.2 request correctly fails closed on the previously approved-but-nonreproducible v1.1 byte binding. It does not attempt to reuse the v1.1 approval for different bytes.

The new formal request freezes an ordered replay from exact base blob `615d6b117f810c4cb8c9459971caa32589352c93`:

1. parse the original `RAW[2]` parser array before source replacement;
2. apply the FD8/formal-root edits and owner-FD insertion to that array, then canonical JSON serialize it;
3. splice those parser bytes once into the formal base source;
4. only then apply the literal formal-root/clean-suffix/adapter/collection mappings;
5. replace the bootstrap identity, parser expected identity and bootstrap-contract identity literals;
6. bind the final parser / observed argv / contract / outer payload byte lengths and SHA-256 values.

The formal v1.2 JSON carries this replay algorithm and its corrected identities:

- parser: `2336 / f50e925c55fc3e953649fe5311a300f1fd67fd35ceb5bd1a93ef202b99f821c8`;
- bootstrap observed argv: `2341 / 2b4fa86035a8d6a90e602ec496e54ee39fcdf97e894cabfcc8f6b8db98716861`;
- bootstrap contract: `182 / 2b8ccfa6b5f3ed5c2a812749f915f965771d4c740875f30aee34d766e90a1580`;
- outer `-c` payload: `17389 / f3171fc64911e33be643a392854c3dc20c808c9dd1b02f5e091769655806f9a9`.

The request also preserves the canonical Stage-1-only hard stop and does not expand into collection / receipt / source-evidence / publication / child / GPU / training scope.

No separate payload-replay Design or Production blocker was found from the formal specification itself.

## 3. Blocking finding

### HIGH — v1.2 is a new exact request instance but reuses v1.1's old freshness snapshot instead of carrying a v1.2 same-round observation

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_authority_root_materialization_request_v1.2.md:12`

The v1.2 request explicitly says that its `route snapshot` remains v1.1 unchanged. Its canonical JSON confirms the reused snapshot: the same `.git` / `.git/config` identities, the same local-ref `absent_rc_1`, remote-ref `absent_zero_lines`, and the same clean/index/evidence/pending absence set are carried forward.

That is insufficient under the controlling v0.3 Stage-1 refreeze. v0.3 requires the **request being reviewed** to bind in the same construction round:

- formal-tree/tool/route identities;
- cwd/index/evidence identity;
- fixed-ref local/remote dual-end absence observation;
- canonical whole-request bytes/SHA.

This was also the rationale used to reject v1.0: execution-time revalidation may only reject an already-fresh reviewed instance; it cannot substitute for construction-time freshness.

v1.2 is not merely an editorial correction to the already-approved v1.1 bytes. It is a new request instance with a different canonical JSON, different parser/contract/payload identities, and therefore must independently satisfy the same-round freshness condition before it can receive an execution verdict. The fact that v1.1 never executed and runtime will recheck the route is useful but does not convert the old snapshot into a v1.2 same-round observation.

### Exact acceptance

1. Re-observe in the same v1.2 replacement construction round the root `.git` identity, `.git/config` identity/bytes, clean/index/evidence/pending absence, and fixed authority ref at both local and remote endpoints.
2. Put those new concrete observations in the v1.2 canonical JSON (or a new v1.3 replacement canonical JSON) instead of inheriting the v1.1 snapshot.
3. Recompute the canonical request byte length/SHA after updating the snapshot and submit that new exact pair for review.
4. Preserve the v1.2 ordered payload replay and its corrected parser/bootstrap/contract/payload identities unless the fresh reconstruction itself proves they drift.
5. Runtime revalidation remains mandatory and fail-closed, but only as an additive barrier.
6. Preserve the Stage-1 tuple-only hard stop and every Stage-2/downstream prohibition.

## 4. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_authority_root_materialization_request_v1.2.md:12)`

Current blockers: **1 HIGH Design/Authority**.  
Production implementation blockers: **0**.  
Evidence-only blockers: **0**.  
Child/runtime blockers: **0**.

## 5. Scope reminder

This verdict binds only exact pair `08917d6dba3bde5ab284fd57d00b35b337fd1ea1` / `93a89ba61306d840a008813f62f26a34d54850f4` and the Gate above.

No Stage-1 materialization is authorized for this pair. No source/checkpoint/manifest/data/cache I/O, collection/receipt/source-evidence/record/package/publication mutation, Stage-2 execution, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, LIBERO4IN1, sidecar, or checkpoint write is authorized by this review.

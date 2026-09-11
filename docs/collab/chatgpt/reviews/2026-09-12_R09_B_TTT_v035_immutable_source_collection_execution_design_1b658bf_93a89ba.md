# ChatGPT Independent Review — R09-B TTT v0.3.5 Immutable Source Collection Execution Design v0.1 authority-root remediation

**Date:** 2026-09-12  
**Formal root:** `1b658bfbf7068a05dc6b409414ba2c98b7b03cc8`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-EXECUTION-DESIGN`

## 1. Pair / scope

- Re-locked remote `V2`, re-read the live `docs/collab/chatgpt/CODEX_INBOX.md`, and verified the submitted formal pair is the current remediation target for this Gate.
- Independently verified formal root `1b658bfbf7068a05dc6b409414ba2c98b7b03cc8` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Incremental technical change from prior rejected pair `c6336a54442c9117823d3ff30da1cba91d46833b` is one authority-contract paragraph in `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_design_v0.1.md`; child/runtime is unchanged.
- This remains docs-only. No real source selection/read/hash, collection/receipt creation, publication, root audit, child/runtime modification, GPU or training action is authorized here.

## 2. Prior HIGH closure

### Prior HIGH-1 — selection request authority: CLOSED

The prior prose-only `execution-authority record` has been replaced by an exact non-circular **execution-authority root** contract. Before any entry resolve/open, that root must exist and contain only the two fixed canonical blobs:

- `docs/build/PSM-WMA_immutable_source_selection_request_v1.json`
- `docs/build/PSM-WMA_immutable_source_canonical_model_config_v1.json`

The root cannot contain self revision/tree/blob claims or a receipt. Independent three-party review must bind the exact tuple `(authority_root_revision, selection_path, selection_blob_native_oid, selection_raw_sha256, config_path, config_blob_native_oid, config_raw_sha256)`, and downstream closure may accept only that reviewed tuple. The transported `--selection-request` must be byte-for-byte equal to the reviewed selection blob before any source entry can be resolved or opened. This makes the CLI request transport-only rather than caller-selected source authority.

### Prior HIGH-2 — resolved canonical config authority: CLOSED

The same execution-authority root now persists the exact resolved 15-key `canonical_native_local_ttt_config_v2` bytes at a fixed root-owned path and binds them through Git blob OID plus raw SHA-256 in the reviewed tuple. Candidate config bytes must byte-match that reviewed blob, and caller/environment/default/working-tree selection remains forbidden. The concrete resolved values may be fixed when the authority root itself is created and independently reviewed; this design Gate correctly freezes the authority mechanism without reading or selecting real source bytes.

### Previously closed HIGH-3 — source-byte TOCTOU: remains CLOSED

The design retains root-directory-FD traversal, descriptor-safe no-symlink component open, same opened regular-file FD streaming, pre/post `fstat` identity/size/mtime/ctime equality, rewind, and a second complete same-FD hash. Any open/fstat/read/rewind/hash/stability mismatch fails before candidate authority creation.

## 3. Fresh audit

No new Design/Authority blocker was found.

- The execution-authority root is non-circular and its externally reviewed tuple is sufficient to machine-bind both selection and resolved config without self-reference.
- `--source-root` remains relocatable transport only; absolute root/path labels and raw source bytes are excluded from downstream authority payloads.
- Five-artifact canonical derivation, isolated preflight zero-live-mutation semantics, and downstream `IMMUTABLE-SOURCE-COLLECTION-CLOSURE` boundary remain unchanged.
- Existing source-evidence controlled-write / post-commit receipt / publication materializer / read-only root-audit progression is preserved.

The actual authority-root revision/blob tuple is intentionally not instantiated by this docs-only design. It must be independently bound before any real source entry is opened, exactly as this contract requires.

## 4. Formal verdict

`APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_EXECUTION`

Current blockers: **0**.  
Design/Authority blockers: **0**.  
Production blockers: **0**.  
Evidence-only blockers: **0**.

## 5. Scope / next action

This approval only closes the docs-only execution design and allows the next independently reviewed docs-only collection closure design / authority-root binding step required by the frozen progression.

Still not authorized: any real source selection/read/hash, collection/receipt creation, source-evidence record/package/witness creation or write, publication materialization, real root source-audit execution, child/runtime modification, real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference or LIBERO4IN1.
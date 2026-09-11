# ChatGPT Independent Review — R09-B TTT v0.3.5 Immutable Source Collection Execution Design authority remediation

**Date:** 2026-09-12  
**Formal root:** `c6336a54442c9117823d3ff30da1cba91d46833b`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-EXECUTION-DESIGN`

## 1. Pair / scope

- Re-locked remote `V2`, re-read the live `docs/collab/chatgpt/CODEX_INBOX.md`, and verified this exact pair is the current formal request for the Gate.
- Independently verified formal root `c6336a54442c9117823d3ff30da1cba91d46833b` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Incremental authority is prior rejected pair `cd4cced4c0cd875b88f98af4fc1bbdad7cad8cf6` / `93a89ba61306d840a008813f62f26a34d54850f4` and its canonical review.
- The substantive remediation is docs-only and limited to the execution design's source-selection/config authority and descriptor-safe source-read semantics. No real source selection/read/hash, collection mutation, child/runtime modification, publication, GPU or training action is authorized.

## 2. Prior HIGH closure

### Prior HIGH-3 — race-safe source-byte snapshot: CLOSED

The design now opens the source root as a directory FD, resolves each path component with descriptor-safe no-symlink traversal, hashes from the same opened regular-file FD, requires pre/post `fstat` identity/size/mtime/ctime equality, rewinds that same FD, and requires a second complete hash to match. Any identity/metadata/read/hash mismatch is fail-closed before candidate authority creation. This closes the prior path-stat / same-size in-place mutation gap at the design level.

## 3. Findings

### HIGH-1 — Design/Authority — selection authority is still delegated to an undefined “execution-authority record”

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_design_v0.1.md:15`

The remediation correctly states that the supplied selection request must byte-match an independently reviewed authority before any entry is opened. However, the object that is supposed to provide that authority is only named in prose as an “independent reviewed execution-authority record.” This design does not freeze that record's schema, fixed persistence path, formal-root/parent relationship, blob identity/raw SHA-256 binding, or the exact rule by which the later execution/closure Gate identifies the one reviewed instance.

Therefore the core old authority problem has only moved one level upward. A later caller can still choose a different canonical selection request and accompany it with an ad hoc “execution-authority record” unless a separate reviewer happens to impose stronger rules that are not frozen here. The prior approved collection-design notice explicitly required this Gate to freeze the concrete approved real-source selection/read contract before any real source bytes are read.

**Acceptance:** freeze the selection authority as an exact machine-verifiable object now. At minimum define a fixed root-owned `immutable_source_selection_request_v1` artifact path plus canonical raw bytes/SHA-256/blob identity and a non-circular reviewed formal-root binding (or an equivalently exact external receipt). Define exactly which formal revision/path/blob tuple the later closure may accept. The CLI `--selection-request` must remain transport-only and must byte-match that one reviewed authority before any path resolve/open. Do not rely on a generic future “record” whose schema/source is left to later interpretation.

### HIGH-2 — Design/Authority — resolved production config authority is likewise delegated to the same undefined object

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_design_v0.1.md:17`

The remediation now requires exact resolved `canonical_native_local_ttt_config_v2` bytes and SHA-256 to be fixed before execution, which is the correct direction. But the values are again said to come from the same unspecified “execution-authority record.” The design does not freeze the formal source that owns those exact 15-key resolved bytes or the non-circular root/path/blob binding that prevents a schema-valid but reviewer-unapproved mapping from being substituted.

This matters because inherited schema constraints still do not determine all resolved production values. The later collection root is supposed to carry the exact config artifact that downstream publication/training identity consumes; it cannot become authoritative merely because a future prose-named record says so.

**Acceptance:** freeze exact resolved config authority with the same machine-verifiable rigor as the selection request: exact canonical 15-key bytes, SHA-256, fixed root-owned path, blob identity, and reviewed formal-root binding. The transport/config candidate used by execution must be byte-for-byte equal to that reviewed artifact before candidate collection blobs are constructed. Caller/environment/default/working-tree selection remains forbidden.

## 4. Positive findings

- The prior source-read TOCTOU blocker is closed by rooted descriptor-safe same-FD double-hash semantics.
- `--source-root` remains relocatable transport rather than authority.
- The five approved collection artifacts and canonical derivation chain remain unchanged.
- Downstream collection closure, source-evidence controlled write/record/post-commit receipt, publication materializer/verifier and read-only root audit remain separate Gates.
- Formal root resolves exactly to the requested reachable child/Gitlink and child is unchanged.

## 5. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_design_v0.1.md:15)`

Current blockers: **2 HIGH**.  
Design/Authority blockers: **2**.  
Production blockers: **0**.  
Evidence-only blockers: **0**.

## 6. Scope

No real source selection/read/hash, collection/receipt creation, source-evidence record/package/witness creation or write, publication materialization, real root source-audit execution, child/runtime modification, real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference or LIBERO4IN1 is authorized by this verdict. Remediation should remain docs-only for this Gate.
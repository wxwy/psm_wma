# ChatGPT Independent Review — R09-B TTT v0.3.5 Stage-1 Authority Parent Rebind Design v0.1

**Date:** 2026-09-14  
**Formal root:** `3e0c1657644b2b3c03f93c25ad910fa5d50a9ebd`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-STAGE1-AUTHORITY-PARENT-REBIND-DESIGN`

## 1. Pair / scope lock

- Fresh-locked remote `V2` and re-read live `docs/collab/chatgpt/CODEX_INBOX.md`; the effective request binds the exact pair above.
- Verified the formal root resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Formal technical scope is docs-only: `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_authority_parent_rebind_design_v0.1.md` plus task/session bookkeeping. It does not construct or execute a request.
- The previously approved v1.3 Stage-1 execution authority is consumed and cannot be reused.

## 2. Positive findings

The design correctly identifies the authority discontinuity introduced by the config-grammar repair:

1. `08d5828cdb4c12afa3b798ff01826c91ceb8755a` is a descendant of the old Stage-1 parent `b3595395427114f73ff53a19a0c2b9180e39905f` (merge-base is exactly `b359...`), while the child Gitlink remains unchanged.
2. The authority adapter and frozen launcher source changed after `b359...`; using the old parent would therefore reconstruct the old parser rather than the closed exact 14-tuple grammar.
3. The design correctly requires a new request instance, fresh same-round observations, a newly computed canonical whole-request SHA, and a new independent approval before any Stage-1 attempt.
4. The fixed-ref, authority-tuple-only hard stop, Stage-2 prohibition and no-real-I/O/GPU/child boundaries remain preserved.
5. Old v1.1-v1.3 derived values are explicitly historical only and cannot be treated as execution authority for the rebound request.

## 3. Blocking finding

### HIGH-1 — the rebound contract does not explicitly bind the new parent’s launcher payload base identity

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_authority_parent_rebind_design_v0.1.md:25`

The approved v1.3 canonical request treated the launcher source itself as first-class request authority under `payload`:

- `base_path = docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py`
- `base_blob = 615d6b117f810c4cb8c9459971caa32589352c93`
- `base_sha256 = 3a5b4cd99730ddb01098ed53d4278f1f7b8ef142bc234405095df54de4ec7ea5`

Those values were bound to the old formal parent `b359...`. The `b359... -> 08d...` comparison shows that the frozen launcher payload file itself changed, not only the adapter module. Therefore the new parent changes the replay *source bytes* as well as the derived parser/bootstrap/payload identities.

Section 2 currently requires `outer payload replay` to be re-derived, but it does not explicitly require the rebound request to bind the launcher base source from the `08d...` formal tree by exact path + blob OID + raw SHA-256. Without that explicit authority, a constructor could still combine `formal_parent=08d...` with the old `615d6b.../3a5b4cd...` launcher base and then apply a new overlay. That would create a mixed-parent request even though the document intends to prohibit overlay-based repair of the old parser.

**Exact acceptance:** refreeze §2 so the next request must:

1. resolve `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py` from the exact new formal parent `08d5828c...`;
2. bind that source as exact `payload.base_path`, `payload.base_blob` and `payload.base_sha256` (and byte length if carried by the request schema);
3. require the ordered replay to consume exactly those new-parent bytes, never the old `615d6b.../3a5b4cd...` base;
4. fail construction/review on any base-source path/blob/raw mismatch rather than attempting an overlay or fallback reconstruction;
5. recompute from that base all parser argv, bootstrap raw/argv, bootstrap contract, outer payload bytes/SHA and canonical whole-request SHA;
6. preserve the already-frozen four-module closure, fresh route/ref observations, Stage-1 hard stop and all downstream prohibitions.

No production parser redesign is requested.

## 4. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_authority_parent_rebind_design_v0.1.md:25)`

Current blockers: **1 HIGH Design/Authority**.  
Production implementation blockers: **0**.  
Evidence-only blockers: **0**.  
Child/runtime blockers: **0**.

## 5. Scope reminder

This verdict binds only exact pair `3e0c1657644b2b3c03f93c25ad910fa5d50a9ebd` / `93a89ba61306d840a008813f62f26a34d54850f4` and this docs-only parent-rebind Design Gate.

It does **not** authorize request construction under the current v0.1 text, Stage-1 materialization/retry, source/checkpoint/manifest/data/cache I/O, collection/receipt/record/package/publication, child/runtime/config mutation, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.

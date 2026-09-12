# ChatGPT Review — Authority Root Materialization Execution Request Design

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST-DESIGN`

## Exact formal pair

- root design SHA: `1eb08dea015c1c3c64d504d96a52f02de4665dbd`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The current `V2` head observed at review start was bookkeeping/review-delivery head `bcb2aab2a35407554af86d693c25b652e73d44af`, not the formal target. The formal root commit is independently reachable. Its `cosmos-framework` entry is an actual submodule/Gitlink and resolves exactly to `93a89ba61306d840a008813f62f26a34d54850f4`; that child commit is independently reachable in `wxwy/cosmos-framework`.

This is a new formal pair and therefore a fresh design review. The formal commit itself is docs-only: the new design plus project status bookkeeping; it does not change child/runtime production code.

## Effective authority chain

The effective authority is not this request text alone:

1. `PSM-WMA_Local_Memory_v0.3.5_authority_root_real_adapter_execution_request_design_v0.1.md` §1 froze a two-stage progression: implement/close the real adapter, then **immediately generate one exact execution request**, freeze the formal-tree tool identity / interpreter+Git identity / argv / raw bytes, obtain tri-review approval, execute once, then submit the authority tuple and continue into the already-approved controlled collection flow. It explicitly says no extra provenance Gate is inserted.
2. v0.3–v0.6 only supersede local adapter/evidence/finalizer semantics. v0.6 explicitly supersedes only the v0.5 finalizer outcome dispatch and retains the remaining v0.3/v0.5 contract; none supersedes the v0.1 two-stage progression.
3. The exact real-adapter CPU/static implementation was closed at `ad9e0110494a582e707ed5f041610d4cc40a82df / 93a89ba...`.
4. `MEMORY/DECISIONS.md` D024 is still effective: finish the already-approved source-evidence closure in its approved order, do not add new checkpoint-authority/publication-evidence/same-binding provenance sub-Gates, and after that closure move to single-GPU TTT smoke.

## Blockers

### HIGH-1 — the design inserts an additional pre-request Gate that the frozen two-stage progression did not authorize

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_materialization_execution_request_design_v0.1.md:13`

The document states that after this design is approved, the only next document is a one-shot execution request, and that the one-shot request must then receive `APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT` before execution.

That creates three review layers after the original adapter design: real-adapter implementation closure -> this new request-design Gate -> exact one-shot execution request -> execution. The already-approved v0.1 authority froze only two stages: real-adapter implementation closure -> **immediate exact execution request** -> approved one-shot execution. The phrase in the current document that this is "not a horizontal provenance Gate" cannot itself create authority to insert another Gate. D024 independently forbids continuing to split the same authority/publication binding into additional provenance sub-Gates.

This is not a cosmetic naming issue: approving the current literal would authorize a progression step that the controlling design never authorized.

**Exact acceptance:** do not add an intermediate request-design approval. The next fresh formal target should be the actual one-shot execution request itself, with all concrete immutable values filled and the requested verdict exactly `APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT` (or `REQUEST_CHANGES(file:line)`). If the project intends to change the two-stage progression, that requires an explicit higher-authority refreeze/supersession; ordinary bookkeeping or this design cannot do it, and D024 currently points the other way.

### HIGH-2 — the proposed bootstrap allows transitive project code to execute before its source identity is proven

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_materialization_execution_request_design_v0.1.md:41`

The document freezes a clean-root path/HEAD observation and then proposes:

`python -I -S -B -c '<stdlib bootstrap: require clean-root realpath; prepend exactly that root; run module tools.psm_wma.materialize_immutable_source_authority_root as __main__>' ...`

It then delegates formal-tree source verification to the adapter's existing preflight after the project module is imported. That ordering is not fail-closed for real execution.

The actual production import graph at the closed formal root proves why:

- `tools/psm_wma/materialize_immutable_source_authority_root.py` imports `tools.psm_wma.immutable_source_authority_root` and `tools.psm_wma.immutable_source_collection` at module import time;
- `tools/psm_wma/immutable_source_authority_root.py` itself imports both `tools.g0.audit_r09_b_ttt_root_gitlink_authority` and `tools.psm_wma.immutable_source_collection` at module import time;
- `tools/psm_wma/immutable_source_collection.py` imports `tools.g0.audit_r09_b_ttt_root_gitlink_authority` at module import time.

But §2 freezes blob/raw identity only for the adapter and authority module, and §3's formal-tree module-byte checks happen inside the already-imported adapter. A drifted/shadowed `immutable_source_collection.py` or `audit_r09_b_ttt_root_gitlink_authority.py` can therefore execute before `preflight_authority_invocation()` gets a chance to reject anything. Merely saying the approved path is a "clean worktree" or that its `HEAD` was observed as `ad9e011...` is not an execution-time source authority; the path can drift after review.

This violates the intended fail-closed property that the reviewed formal-tree implementation, rather than mutable working-tree code, is the thing being authorized to perform the one real materialization.

**Exact acceptance:** the exact one-shot bootstrap must, **before adding the project root to `sys.path` or importing any project module**, independently prove execution-time source identity against the approved formal root. Acceptable forms include either:

1. verify every project module in the transitive import closure that can execute before adapter preflight by exact formal-tree path/blob/raw identity, rejecting symlink/type/path/shadowing drift; or
2. prove the controlled worktree is byte-for-byte/type-for-type equivalent to the approved formal root for the importable project namespace using a deterministic pre-import check strong enough that untracked/shadowing files, modified tracked files, mode/type drift, and alternate module resolution cannot pass.

The bootstrap itself must be fully frozen in the one-shot request/argv authority. Any source-identity failure must terminate before project import and before Git/ref/evidence mutation. The one-shot request should also include a direct adversarial witness where a transitive dependency such as `immutable_source_collection.py` is changed while the two currently-frozen module files remain unchanged, and the bootstrap rejects before any project code executes.

## Non-blocking observations

- The formal root/Gitlink pair is valid.
- The frozen adapter blob OID `ade7c872...` and authority-module blob OID `9937f74c...` match the corresponding files at the closed `ad9e011...` tree.
- The design correctly keeps the authority candidate parent at the closed materialization formal root rather than the request/design/bookkeeping SHA.
- The fixed ref and expected-zero local/remote admission are consistent with the closed adapter contract.
- The current Gate remains docs-only and does not itself authorize real source I/O, publication, GPU, or training.

## Blocker summary

- design/authority blockers: `2 HIGH`
- production blocker in the already-closed CPU/static pair: `0` (not reopened by this review)
- total current blockers: `2 HIGH`

## Final verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_materialization_execution_request_design_v0.1.md:13)`

This verdict binds only the exact formal pair `1eb08dea015c1c3c64d504d96a52f02de4665dbd / 93a89ba61306d840a008813f62f26a34d54850f4`.

No real materialization, source/checkpoint I/O, collection/receipt, publication/root audit, child/runtime change, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1 is authorized by this review.
# ChatGPT Independent Review — R09-B TTT v0.3.5 Immutable Source Collection Execution Design v0.1

**Date:** 2026-09-12  
**Formal root:** `cd4cced4c0cd875b88f98af4fc1bbdad7cad8cf6`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-EXECUTION-DESIGN`

## 1. Pair / scope

- Re-locked remote `V2` and re-read the live `docs/collab/chatgpt/CODEX_INBOX.md`.
- Independently verified formal root `cd4cced4c0cd875b88f98af4fc1bbdad7cad8cf6` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Prerequisite Immutable Source Collection Design is approved at `885956cb6cddf57f04b3ed5097cf87a176779403` / `93a89ba61306d840a008813f62f26a34d54850f4` with `APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION`.
- Incremental technical scope is docs-only: the new 43-line execution design plus root bookkeeping. No real source bytes were read or selected; no collection/receipt/publication/audit/GPU/training action is authorized or reviewed here.

## 2. Positive findings

- The design preserves the approved downstream progression: closure, source-evidence controlled write/record/post-commit receipt, publication materializer/verifier and read-only root audit remain separate Gates.
- `--source-root` is explicitly transport-only and cannot itself become accepted authority.
- Source files are intended to be streamed as raw bytes without loading model/checkpoint payloads, and live root/index/HEAD/authority remain unchanged on preflight failure.
- The approved five collection artifacts and canonical hash derivation are retained; source paths/raw bytes are kept out of downstream authority payloads.

## 3. Findings

### HIGH-1 — Design/Authority — the canonical selection request is still caller-selected source authority

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_design_v0.1.md:15`

The design says `--source-root` and `--selection-request` are merely transport and not accepted authority. That is true for the root path, but not for the selection request as currently frozen: its `entries[].relative_path` determines exactly which files are opened and hashed, and there is no independently reviewed expected request bytes/digest/root-owned artifact against which the supplied request is checked before the first source read.

Canonical syntax alone does not solve this authority problem. A caller can submit a different, perfectly canonical selection request selecting different regular files under the same source root; the resulting input descriptor/manifest/identifier/descriptor/collection chain would be internally self-consistent and later immutable, but it would represent a caller-selected checkpoint source rather than a reviewed one.

**Acceptance:** freeze one exact externally reviewed selection authority before any source file is opened. For example, the later execution/closure approval may bind exact canonical `immutable_source_selection_request_v1` bytes plus SHA-256 in a fixed root-owned artifact or formal Gate record. `--selection-request` must then remain transport-only: recompute its canonical bytes/SHA-256 and require byte/digest equality to that approved authority before resolving or opening any entry. `--source-root` may remain a relocatable transport directory; caller/env/working-tree discovery must not alter the approved entry set/order.

### HIGH-2 — Design/Authority — resolved canonical model config has no concrete reviewed execution input

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_design_v0.1.md:21`

The executor is required to construct the approved fixed-path `canonical_native_local_ttt_config_v2` artifact, but the only invocation inputs defined by this design are `--source-root` and `--selection-request`. The inherited source-audit schema constrains the 15 keys and several values, but fields such as resolved `local_history_evidence_dim`, `ttt_tbptt_steps`, `ttt_inner_lr` and `k_local` are not fixed by schema alone; they must be the exact resolved production values.

Therefore the execution design currently has no machine-verifiable source from which those resolved values are derived. A future implementation must either invent them, use defaults/environment/current working tree, or accept an arbitrary schema-valid caller mapping — all of which violate the already-approved config-authority contract.

**Acceptance:** freeze an exact reviewed config-input authority before candidate blobs are constructed. It may be a fixed root-owned canonical config-input artifact or an exact canonical bytes/digest binding in the formal execution approval, but it must contain the resolved 15-key `canonical_native_local_ttt_config_v2` mapping, bind its raw bytes/SHA-256 to an approved formal root/path/source, and prohibit caller/environment/working-tree selection. The collection config artifact must be byte-for-byte derived from that authority and independently rehashed.

### HIGH-3 — Design/Authority — `pre/post stat identity/size` does not freeze a race-safe byte source

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_design_v0.1.md:29`

The current race rule only says source-byte read races are detected when pre/post `stat` identity/size differ. That is not sufficient to bind the computed SHA-256 to one stable opened file. Path-based stat/open/stat has a classic replacement window: a path can be swapped between pre-stat and open and restored before post-stat. Same-size in-place modification can also change bytes while preserving inode and size. In either case a hash can be produced from bytes that are not uniquely bound to the checked path state.

This matters because the raw source bytes are the root of every downstream source identity digest. Once committed, later tree/receipt verification cannot recover whether those bytes were read from a stable approved source snapshot.

**Acceptance:** freeze descriptor-safe open/read semantics, not only path stat semantics. At minimum: resolve/open from a root directory FD with symlink traversal rejected according to the approved path contract; hash only from the same opened regular-file FD; use `fstat` identity on that FD before/after; and require a stability mechanism that detects same-size in-place changes (for example, a second full read/hash of the same FD plus unchanged size/mtime/ctime identity, or an equivalently strong immutable snapshot/private-copy contract). Any open/fstat/read/rewind/hash/stability mismatch must fail before candidate authority creation. The implementation design may choose the exact stdlib/OS mechanism, but the execution contract must make the source-byte snapshot unambiguous.

## 4. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_design_v0.1.md:15)`

Current blockers: **3 HIGH**.  
Design/Authority blockers: **3**.  
Production blockers: **0**.  
Evidence-only blockers: **0**.

## 5. Scope

This verdict does not authorize any real source selection/read/hash, collection or receipt creation, source-evidence record/package/witness write, publication materialization, real root source audit, child/runtime modification, real checkpoint/data/cache I/O beyond a future separately approved collection execution, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference or LIBERO4IN1. Remediation should remain docs-only for this Gate.

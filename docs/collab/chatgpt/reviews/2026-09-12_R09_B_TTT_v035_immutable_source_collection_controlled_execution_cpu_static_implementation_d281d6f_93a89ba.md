# ChatGPT Independent Review — R09-B TTT v0.3.5 Immutable Source Collection Controlled Execution CPU/static Implementation remediation

**Date:** 2026-09-12  
**Formal root:** `d281d6f3079602632000b1576c47fd4546de22e6`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-IMPLEMENTATION-DESIGN`

## 1. Pair / scope

- Re-locked remote `V2` and re-read live `docs/collab/chatgpt/CODEX_INBOX.md` before review.
- Independently verified formal root `d281d6f3079602632000b1576c47fd4546de22e6` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- This is a new formal pair relative to my prior reviewed pair `08afbed4e1843c23a1cc3542f0184a1898c1772c` / same child, so a fresh incremental review is required.
- Incremental technical delta is confined to `tools/psm_wma/immutable_source_collection.py` and `tools/psm_wma/test_immutable_source_collection.py`; intervening Session/Inbox/governance edits are bookkeeping and do not become the technical target.
- I did not inherit MM/Kimi approval or treat `32/32` as sufficient evidence; review is based on frozen acceptance from the prior canonical review, formal-tree production source, and direct CPU/static witnesses.

## 2. Prior blocker closure

### HIGH-1 CLOSED — exact Git tree entry identity

Prior defect: `GitTransaction.tree_entries()` exposed only `path -> OID`, so mode/type-only drift with unchanged OID could evade exact tree-delta verification.

Current implementation closes this materially:

- introduces `TreeEntry = tuple[str, str, str]` for Git mode, object type and native OID;
- `_tree()` validates exact tuple shape, mode/type compatibility and lowercase 40-hex OID;
- `_authority_tree()` computes the exact parent/root changed-path set using the full tuple, so inherited mode/type/OID drift is visible;
- the two fixed authority paths are additionally required to be exact `100644/blob` entries;
- collection and receipt parent/child preservation checks now compare full tree entries, not bare OIDs;
- `_receipt_from_collection()` and final receipt checks require fixed generated artifacts to be exact `100644/blob/<expected OID>` entries.

Direct CPU/static evidence covers authority inherited and fixed-path mode/type drift, including a Gitlink inherited entry, plus collection/receipt fixed and inherited mode-only mutation with rollback.

This satisfies the prior acceptance requirement that exact Git-tree identity, not only blob identity, be preserved and revalidated.

### HIGH-2 CLOSED — selection-request transport raw bytes

Prior defect: the executor accepted a parsed caller `paths` mapping and only compared path sets, so it could not prove that caller transport bytes were the reviewed authority selection object.

Current implementation closes this materially:

- `collect_synthetic()` now requires `selection_request: bytes`;
- `_bound_source_inputs()` loads the exact reviewed selection blob from the authority tree and verifies blob OID plus raw SHA-256;
- before any `RootFdOpener.open_regular()` call, it rejects any non-`bytes` value or any byte sequence not exactly equal to the authority selection blob;
- only after exact raw-byte binding does it parse the authority blob and derive the ordered source-entry list; the old caller parsed-mapping/set-equality path is removed.

Direct CPU/static witnesses reject semantic-equivalent transport drift including trailing newline, pretty-printed JSON and Unicode-escape variation, reject a parsed mapping object, and accept the exact reviewed bytes. The failure witness uses an opener that would raise if any source read occurred, proving the rejection boundary is pre-source-open.

This satisfies the prior acceptance requirement that transport-byte authority live inside the unchanged executor seam rather than being delegated to a future adapter.

## 3. Regression / new-finding review

No new blocker found in the effective remediation delta.

Positive checks:

- authority parent binding, exact two-path delta, inherited entry preservation and late authority revalidation remain intact;
- source order is derived only from the byte-bound reviewed selection blob;
- fixed generated JSON artifacts remain regular `100644/blob` entries;
- same-opened-handle source identity/hash checks, canonical candidate derivation, one-shot handoff, five-plus-one transaction, receipt relookup, exact evidence ABI, atomic sink contract and rollback/`ROLLBACK_INCOMPLETE` behavior remain unchanged in substance;
- the child/Gitlink is unchanged and no child/runtime behavior is modified;
- no real source/checkpoint/cache I/O, authority-root materialization, publication, GPU/model/training action is authorized by this CPU/static Gate.

The stated `32/32` suite is consistent with the direct witnesses inspected, but the verdict does not rely on test count alone.

## 4. Formal verdict

`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_CONTROLLED_EXECUTION_CPU_STATIC`

Current blockers: **0**.  
Prior HIGH-1: **CLOSED**.  
Prior HIGH-2: **CLOSED**.  
New findings: **0**.

## 5. Scope reminder

This approval binds only exact formal pair `d281d6f3079602632000b1576c47fd4546de22e6` / `93a89ba61306d840a008813f62f26a34d54850f4` for this CPU/static implementation Gate.

It does **not** authorize real authority-root materialization, real source selection/read/hash, collection/receipt mutation, source-evidence record/package/witness creation or write, publication materialization, real root audit, child/runtime modification, checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler/scaler step, sidecar, training, evaluation, inference or LIBERO4IN1.

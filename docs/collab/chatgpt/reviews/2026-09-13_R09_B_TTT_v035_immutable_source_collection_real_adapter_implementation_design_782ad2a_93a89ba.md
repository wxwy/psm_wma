# ChatGPT Independent Review — R09-B TTT v0.3.5 Immutable Source Collection Real Adapter Implementation Design v0.1

**Date:** 2026-09-13  
**Formal root:** `782ad2a14dd67d40c84dcd8e4adf4e887ce081f0`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-REAL-ADAPTER-IMPLEMENTATION-DESIGN`

## 1. Pair / scope lock

- Re-locked remote `V2` and re-read live `docs/collab/chatgpt/CODEX_INBOX.md`; the current formal request binds exact pair `782ad2a14dd67d40c84dcd8e4adf4e887ce081f0` / `93a89ba61306d840a008813f62f26a34d54850f4` for this Gate.
- Independently verified formal root `782ad2a14dd67d40c84dcd8e4adf4e887ce081f0` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Formal technical scope is root docs-only: `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_real_adapter_implementation_design_v0.1.md` plus `SESSION.md` / `TODO.md`; child/runtime is unchanged.
- I inspected the frozen predecessor contracts, especially controlled-execution design formal root `2c73ad0bf9f49d1dd13f0803046ac75f3cd9449c`, prior executor implementation design, the approved CPU/static executor remediation `d281d6f3079602632000b1576c47fd4546de22e6`, collection execution/closure contracts, and current `tools/psm_wma/immutable_source_collection.py` seam.
- This Gate remains non-executing. No real source/checkpoint/manifest/data/cache I/O, authority/collection/receipt/evidence/publication mutation, child/runtime change, GPU, training, evaluation, inference or LIBERO4IN1 is authorized.

## 2. Fresh finding

### HIGH-1 — new production entrypoint conflicts with the frozen unique-executor authority

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_real_adapter_implementation_design_v0.1.md:28` (and §2 allowlist)

**Root cause**

The new design authorizes a new production adapter path:

`tools/psm_wma/execute_immutable_source_collection.py`

and intends future controlled execution to enter through that adapter. However, the already-approved authority chain explicitly froze the unique executor identity to:

`tools/psm_wma/immutable_source_collection.py`

Controlled-execution v0.2 §2 states that this is the **unique executor path** and requires its path/Git blob/raw SHA-256 identity to be frozen before source open. The approved executor implementation design repeats that the **unique production executor** is `immutable_source_collection.py`, with the implementation/test allowlist built around that identity. The later approved CPU/static remediation also closed selection transport authority specifically inside the unchanged executor seam rather than delegating authority to a future wrapper.

The present v0.1 real-adapter design does not explicitly supersede/refreeze those executor-path and allowlist clauses. Calling the new file merely a “root-owned real adapter” is insufficient: it becomes code executed before/around the canonical algorithm, parses/owns the real CLI and identities, instantiates native Git/FD/evidence capabilities, and therefore is part of the production authority boundary. Under the current frozen contract, a future request cannot honestly approve that new entrypoint without contradicting the previously reviewed unique-executor identity.

**Violated frozen contract**

- `PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_controlled_execution_design_v0.2.md` §2: unique executor path is `tools/psm_wma/immutable_source_collection.py`; path/source/interpreter/allowlist drift must fail before source open.
- `PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_executor_implementation_design_v0.1.md` Scope: unique production executor is `tools/psm_wma/immutable_source_collection.py`; implementation identity/allowlist is frozen around that file and its direct test.
- Exact approved CPU/static review for formal root `d281d6f3079602632000b1576c47fd4546de22e6`: transport-byte authority was accepted because it lives inside the unchanged executor seam rather than being delegated to a future adapter.

**Why current evidence is insufficient**

Formal-tree scope, design SHA, unchanged child/Gitlink, and any future CPU/static adapter tests cannot resolve a normative authority conflict. Tests can prove a new adapter behaves correctly, but they cannot authorize a production path that the prior approved contract explicitly excludes. The execution request would still lack a valid reviewed identity chain for code that runs before source open and Git mutation.

**Exact acceptance**

Remediate the docs-only design before implementation using one of these authority-safe routes:

1. **Preserve the frozen unique executor path:** implement the real CLI/native `GitTransaction`/`RootFdOpener`/`EvidenceSink` binding inside `tools/psm_wma/immutable_source_collection.py` and retain the previously frozen executor identity/allowlist; **or**
2. **Explicitly refreeze/supersede the predecessor clauses:** state exactly that this design supersedes controlled-execution v0.2 §2 and the prior executor implementation-design clauses *only for production entrypoint identity/allowlist*, then freeze the new runtime chain as a reviewed two-source authority:
   - entrypoint/adapter `tools/psm_wma/execute_immutable_source_collection.py` exact path + committed Git blob OID + raw SHA-256;
   - canonical algorithm `tools/psm_wma/immutable_source_collection.py` exact path + committed Git blob OID + raw SHA-256;
   - exact interpreter/bootstrap/import route that can load the canonical algorithm only from the approved formal tree, never ambient `PYTHONPATH`, cwd, caller mapping or an unreviewed module;
   - pre-source-open fail-close if either source identity, formal root, bootstrap/import route, interpreter identity, child Gitlink or allowlist drifts;
   - future exact execution request must bind this refrozen chain before it may invoke the adapter, open any source entry, or perform Git/evidence mutation.

The adapter may still remain limited to instantiating the three existing protocols and calling the unchanged canonical algorithm exactly once; no duplicated validation/derivation/receipt/rollback semantics are required or authorized.

## 3. Other review dimensions

No additional blocker was found in the docs-only delta once the executor-identity conflict is isolated:

- the design correctly keeps canonical validation, candidate derivation, one-shot handoff, receipt and rollback semantics in `immutable_source_collection.py` rather than copying them;
- native Git is constrained to non-shell explicit argv, identity-bound executable, sanitized environment and temporary index;
- source traversal remains directory-FD rooted with no-follow/regular-file/same-FD identity discipline;
- evidence sink is required to be atomic and to exclude raw source bytes/absolute source paths/URL/secrets/credentials;
- the Gate explicitly forbids real I/O/mutation/GPU/training and limits implementation evidence to temporary synthetic fixtures/local-bare Git.

Production blockers: **0** at this docs-only Gate.  
Evidence-only blockers: **0**.  
Design/Authority blockers: **1 HIGH**.

## 4. Review-transport note

During this review, the reviewer connector accidentally created transient `README.md` commits on `V2`; the file was immediately removed. A direct compare from the pre-incident branch head `4f9e52ba622c141a949d28587bc9674487ce7736` to repair commit `d520e750a8814484c5467a01b9aa983a0078ca8c` reports `files=[]`, so the net repository tree was restored exactly. The formal target `782ad2a14dd67d40c84dcd8e4adf4e887ce081f0` and child `93a89ba61306d840a008813f62f26a34d54850f4` were never modified. These repair-only commits are non-target branch history and convey no technical authority.

## 5. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_real_adapter_implementation_design_v0.1.md:28)`

Current blockers: **1 HIGH Design/Authority**.  
Production blockers: **0**.  
Evidence-only blockers: **0**.

This verdict binds only exact formal pair `782ad2a14dd67d40c84dcd8e4adf4e887ce081f0` / `93a89ba61306d840a008813f62f26a34d54850f4` and this Gate. No implementation or real execution is approved by this review.

# ChatGPT Independent Review — R09-B TTT v0.3.5 Immutable Source Collection Real Adapter Implementation Design v0.2

**Date:** 2026-09-13  
**Formal root:** `6ec9d2db564102c7546ceb1c44bc06ccb3c8de31`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-REAL-ADAPTER-IMPLEMENTATION-DESIGN`

## 1. Pair / scope lock

- Re-locked remote `V2` and re-read live `docs/collab/chatgpt/CODEX_INBOX.md`; the effective remediation request binds exact pair `6ec9d2db564102c7546ceb1c44bc06ccb3c8de31` / `93a89ba61306d840a008813f62f26a34d54850f4` for this Gate.
- Independently verified formal root `6ec9d2db564102c7546ceb1c44bc06ccb3c8de31` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Formal technical remediation is root docs-only: `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_real_adapter_implementation_design_v0.2.md` plus bookkeeping in `SESSION.md`; child/runtime is unchanged.
- This is a new formal pair relative to rejected pair `782ad2a14dd67d40c84dcd8e4adf4e887ce081f0` / same child, so a fresh incremental review is required.
- This Gate remains non-executing. No implementation, real source/checkpoint/manifest/data/cache I/O, authority/collection/receipt/record/package/publication mutation, child/runtime/config change, GPU, training, evaluation, inference or LIBERO4IN1 is authorized here.

## 2. Prior HIGH closure

### HIGH-1 CLOSED — preserve the frozen unique executor identity

The prior v0.1 defect was normative rather than evidentiary: it introduced a new production entrypoint `tools/psm_wma/execute_immutable_source_collection.py`, conflicting with the already-approved chain that froze the unique production executor as `tools/psm_wma/immutable_source_collection.py`.

The v0.2 remediation takes the exact authority-safe route required by the prior review:

- explicitly states that v0.2 replaces v0.1 while retaining all unaffected CPU/static, FD/no-follow, native-Git, atomic-evidence, one-shot-handoff, rollback and acceptance constraints;
- reaffirms the sole production executor as `tools/psm_wma/immutable_source_collection.py`;
- explicitly forbids adding or invoking `execute_immutable_source_collection.py`;
- requires the future real CLI, import-free bootstrap binding, `NativeCollectionGit`, `FdRootOpener` and `AtomicCollectionEvidenceSink` to live in the existing unique executor and only connect its already-reviewed injected seams;
- restores the implementation allowlist to exactly `tools/psm_wma/immutable_source_collection.py` and `tools/psm_wma/test_immutable_source_collection.py`;
- requires pre-source-open / pre-Git-evidence-mutation fail-close on formal-tree identity, bootstrap/import route, interpreter, child Gitlink or two-file allowlist drift;
- requires the later exact execution request to bind the same executor path, committed blob OID, raw SHA-256 and import route, rejecting ambient `PYTHONPATH`, cwd, caller mapping or unreviewed module loading.

This closes the prior conflict without refreezing a two-source runtime chain and preserves the previously reviewed unique-executor authority.

## 3. Fresh audit

No new Design/Authority blocker was found in the remediation delta.

- The canonical validation, candidate construction, one-shot handoff, receipt and rollback semantics remain owned by the existing `immutable_source_collection.py` rather than being duplicated into a wrapper.
- The v0.1 constraints that remain inherited continue to limit the future native Git adapter to non-shell explicit argv, identity-bound Git executable, sanitized environment and temporary index; source traversal remains FD-rooted/no-follow/regular-file/same-FD checked; evidence persistence remains atomic and excludes raw source bytes, absolute source paths, URL, secrets and credentials.
- The later CPU/static implementation remains limited to temporary synthetic fixtures/local-bare Git and must not access the project root as real source/checkpoint/cache authority or perform real collection/publication execution.
- The subsequent source-evidence closure execution request instance remains a separate non-executing review boundary; this approval does not skip request-instance review or the independently reviewed post-commit receipt-root boundary.

Production blockers: **0** at this docs-only Gate.  
Evidence-only blockers: **0**.  
Design/Authority blockers: **0**.

## 4. Formal verdict

`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_REAL_ADAPTER_CPU_STATIC`

Current blockers: **0**.  
Prior HIGH-1: **CLOSED**.  
New findings: **0**.

## 5. Scope / next action

This approval binds only exact formal pair `6ec9d2db564102c7546ceb1c44bc06ccb3c8de31` / `93a89ba61306d840a008813f62f26a34d54850f4` and this Design Gate.

It authorizes only the next root-only CPU/static implementation and direct temporary-fixture evidence within the exact two-file allowlist:

- `tools/psm_wma/immutable_source_collection.py`
- `tools/psm_wma/test_immutable_source_collection.py`

Still not authorized: real source/checkpoint/manifest/data/cache I/O; authority-root materialization; real collection/receipt/source-evidence/record/package/publication mutation; request execution; child/runtime/config changes; DCP; CUDA/GPU; `torchrun`; model forward/loss/backward; optimizer/scheduler/scaler step; sidecar; training; evaluation; inference; LIBERO4IN1; or downstream smoke execution.

# ChatGPT Independent Review — R09-B TTT v0.3.5 Immutable Source Collection Real Adapter CPU/static Final-Path-Continuity Remediation

**Date:** 2026-09-14  
**Formal root:** `d806a9c8bcd04a57fe705c5716fe79e554e4d590`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-REAL-ADAPTER-CPU-STATIC`

## 1. Pair / scope lock

- Re-locked remote `V2` and re-read live `docs/collab/chatgpt/CODEX_INBOX.md`; the effective request binds exact pair `d806a9c8bcd04a57fe705c5716fe79e554e4d590` / `93a89ba61306d840a008813f62f26a34d54850f4`.
- Independently verified formal root `d806a9c...` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- This is a new formal pair relative to prior reviewed `77564a85c07a6c936c52fd0b63810994a879b5fc` / same child, so a fresh incremental review is required.
- Compared with the prior pair, the only implementation/test delta for this Gate is `+4` lines in `tools/psm_wma/immutable_source_collection.py` plus one direct stdlib race witness in `tools/psm_wma/test_immutable_source_collection.py`; intervening review/inbox/session files are bookkeeping/persistence, not implementation authority.
- Frozen authority remains the already-locked real-adapter implementation-design chain. This review does not authorize real source/checkpoint/manifest/data/cache I/O, live collection/receipt/publication execution, execution-request activation, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1.

## 2. Prior blocker disposition

The prior exact-pair review for `77564a85... / 93a89ba...` had one remaining HIGH at `AtomicFileEvidenceSink.emit()`:

- staging authority from the original `O_CREAT|O_EXCL` FD: **already CLOSED** in the prior pair;
- parent relocation during `.pending` cleanup: **already CLOSED** for that timing;
- remaining blocker: after cleanup, the global frozen-parent check occurred before the final retained-parent destination leaf open/read, so parent relocation during that final leaf verification could still allow successful return with the frozen request pathname gone.

That prior exact acceptance required: after final retained-parent inode+canonical-byte verification, perform one final global request-path continuity validation immediately before normal return, and add a direct witness relocating/replacing the parent during the final leaf verification.

## 3. Remediation review

### Production behavior — CLOSED

`tools/psm_wma/immutable_source_collection.py` now performs the final sequence as:

1. verify first published leaf identity/bytes;
2. verify global frozen parent;
3. remove `.pending` through retained `parent_fd`;
4. verify global frozen parent again;
5. reopen the frozen destination leaf relative to retained `parent_fd`, verify exact published inode and canonical bytes;
6. **after that final leaf verification completes**, perform a final global `os.stat(self._destination.parent, follow_symlinks=False)` and require exact retained `(st_dev, st_ino)` directory identity;
7. no further namespace mutation or pathname lookup occurs on the success path before return; only descriptor closes remain in `finally`.

This matches the prior exact acceptance boundary. A parent relocation during the final leaf open/read is now observed by the final global parent-identity check and enters the existing exception path, where the sink removes only the identity-proven final link created by this emission through the retained parent capability.

### Direct Evidence — CLOSED

`test_atomic_sink_rejects_parent_relocation_during_final_leaf_validation` directly targets the prior remaining window:

- it counts destination-leaf opens and relocates the approved parent immediately after the second/final `evidence.json` open;
- it installs a replacement directory at the frozen parent pathname;
- `AtomicFileEvidenceSink.emit()` must raise `CollectionError`;
- the witness asserts no accepted evidence remains at the replacement frozen pathname or under the relocated old parent.

This is a direct production-path witness of the exact race required by the previous review. The previously closed witnesses for retained staging FD authority, same-byte foreign hardlink replacement, cleanup-time parent relocation, link-time relocation, snapshot/source continuity, native composition/rollback/mode/type, and visible-preflight rollback remain intact.

Reported suite evidence for this pair is `56/56 PASS`, with `py_compile` and `git diff --check` PASS. These counts are supporting evidence; the approval is based on the production delta plus the direct causal witness above.

## 4. Findings

No blocking Production, Evidence, child, or runtime findings remain within this Gate and exact pair.

Current blockers: **0**.  
Child/runtime blockers: **0**.

## 5. Formal verdict

`APPROVE_TO_CLOSE_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_REAL_ADAPTER_CPU_STATIC`

This approval closes only exact formal pair `d806a9c8bcd04a57fe705c5716fe79e554e4d590` / `93a89ba61306d840a008813f62f26a34d54850f4` for Gate `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-REAL-ADAPTER-CPU-STATIC` and its already-approved CPU/static two-file implementation/test scope.

It does **not** authorize real source/checkpoint/manifest/data/cache I/O, live collection/receipt/publication execution, execution-request activation, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, LIBERO4IN1, sidecar, or checkpoint write.
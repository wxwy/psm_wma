# ChatGPT Independent Review — R09-B TTT v0.3.5 Immutable Source Collection Real Adapter CPU/static Retained-Staging Remediation

**Date:** 2026-09-14  
**Formal root:** `77564a85c07a6c936c52fd0b63810994a879b5fc`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-REAL-ADAPTER-CPU-STATIC`

## 1. Pair / scope lock

- Re-locked remote `V2` and re-read live `docs/collab/chatgpt/CODEX_INBOX.md`; the effective request binds exact pair `77564a85c07a6c936c52fd0b63810994a879b5fc` / `93a89ba61306d840a008813f62f26a34d54850f4`.
- Independently verified formal root `77564a8...` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- This is a new formal pair relative to prior reviewed `831be4b99f8564bb3695e445dcdfeb1770d7e7f0` / same child, so a fresh incremental review is required.
- Relevant implementation delta remains the approved adapter/test surface; `SESSION.md` is task-record bookkeeping and is not treated as implementation authority.
- Frozen authority remains the real-adapter implementation design chain already locked for this Gate. This review authorizes no real source/checkpoint/manifest/data/cache I/O, live collection/receipt/publication execution, execution-request activation, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1.

## 2. Prior blocker disposition

- Prior HIGH-1 — staging identity learned only after closing the emission-owned write FD: **CLOSED**. The remediation retains the original `O_CREAT|O_EXCL` FD, writes/fsyncs through a duplicate, derives `staged_identity` from the original retained FD, and keeps it open through publication verification. The new same-byte foreign-hardlink witness attacks the former close→reopen seam and is rejected without a surviving destination.
- Prior HIGH-2 — parent relocation during `.pending` cleanup: **materially improved but not fully CLOSED**. Cleanup now occurs before a new frozen-parent pathname check, and the new cleanup-time relocation witness correctly expects failure with no retained destination in either old or replacement parent.
- Snapshot/source continuity, native composition/rollback/mode/type evidence, link-time relocation handling, known foreign-final cleanup, and visible-preflight rollback remain closed from prior exact pairs.

## 3. Current blocking finding

### HIGH-1 — final frozen-parent continuity check still precedes the final leaf verification and can be raced during that verification

**Location:** `tools/psm_wma/immutable_source_collection.py:316` (`AtomicFileEvidenceSink.emit`)

**Root cause**

After `.pending` cleanup, the code now checks the global request-bound parent pathname and then performs another retained-parent final-leaf open/read:

```python
os.unlink(temporary_name, dir_fd=parent_fd)
current_parent = os.stat(self._destination.parent, follow_symlinks=False)
... verify retained parent identity ...
published = os.open(self._destination.name, ..., dir_fd=parent_fd)
... verify published inode and canonical bytes ...
# normal return
```

The second parent check is therefore **not** the last authority validation before success. A concurrent actor can rename/replace `self._destination.parent` after that global `os.stat(...)` succeeds but while the subsequent `os.open(..., dir_fd=parent_fd)` / final read is executing. Because the leaf verification is anchored to the retained old `parent_fd`, it still sees the previously verified published inode and canonical bytes and can return success even though the frozen request-bound destination pathname now resolves through a replacement parent or no longer exists.

This is the same pathname-authority class as the prior relocation findings; the race window has moved from `.pending` cleanup into the final leaf-verification step.

**Violated frozen contract / prior exact acceptance**

- Normal return must mean the canonical validated record exists at the exact frozen fresh request-bound destination.
- The prior exact acceptance required the request-path authority check to be the final validation immediately before successful return, after all cleanup and final publication verification.
- A retained parent-FD/leaf authority does not silently replace the frozen pathname contract.

**Why submitted Evidence does not close it**

`test_atomic_sink_rejects_parent_relocation_during_staging_cleanup` relocates the parent inside `os.unlink("evidence.json.pending", ...)`; the newly added parent check that follows cleanup catches exactly that timing. It does not relocate the parent after that check, during the final `os.open(self._destination.name, ..., dir_fd=parent_fd)` / read. Thus `55/55 PASS` does not witness the remaining success window.

**Exact acceptance**

- After the final retained-parent destination inode+byte verification completes, perform one last request-path continuity validation immediately before normal return. At minimum the global parent pathname must still name the retained `parent_fd` inode; if the design wants an even stronger explicit path proof, also verify the request-bound leaf against the exact published inode without weakening no-follow semantics.
- If this final request-path validation fails, remove only the identity-proven final link created by this emission through the retained parent capability, then raise so the caller rolls back/fail-stops.
- Add a direct temporary-directory witness that relocates/replaces the parent **after the current post-cleanup parent check, during the final leaf open/read**. `emit()` must raise and leave no accepted evidence in the relocated old parent or the replacement request path.

## 4. Closed / non-blocking observations

- The retained staging FD remediation correctly closes the former close→reopen authority bug.
- The same-byte foreign-hardlink witness is materially stronger than the previous staged replacement test and demonstrates that a foreign inode cannot be adopted merely because its bytes are canonical.
- The cleanup-time relocation witness correctly proves the newly added post-cleanup check.
- No child/runtime blocker was found; Gitlink remains exact and child commit reachable.
- Reported `55/55`, `py_compile`, and `git diff --check` are useful auxiliary evidence but do not cover the final parent-relocation timing above.

## 5. Formal verdict

`REQUEST_CHANGES(tools/psm_wma/immutable_source_collection.py:316)`

Current blockers: **1 HIGH Production/Authority+Evidence**.  
Child/runtime blockers: **0**.

## 6. Scope reminder

This verdict binds only exact formal pair `77564a85c07a6c936c52fd0b63810994a879b5fc` / `93a89ba61306d840a008813f62f26a34d54850f4` and Gate `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-REAL-ADAPTER-CPU-STATIC`.

Remediation remains limited to the already-approved two-file CPU/static implementation/test surface and temporary fixtures. No real source/checkpoint/manifest/data/cache access, live collection/receipt/publication execution, execution-request activation, child/runtime/config change, GPU, training, evaluation, inference, or LIBERO4IN1 action is authorized.
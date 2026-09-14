# ChatGPT Independent Review — R09-B TTT v0.3.5 Immutable Source Collection Real Adapter CPU/static Authority-Race Remediation

**Date:** 2026-09-14  
**Formal root:** `a0e9d294320ad37cb127d45118b3f67107bfef7f`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-REAL-ADAPTER-CPU-STATIC`

## 1. Pair / scope lock

- Re-locked live `V2` and re-read current `docs/collab/chatgpt/CODEX_INBOX.md`; the effective new request binds exact pair `a0e9d294320ad37cb127d45118b3f67107bfef7f` / `93a89ba61306d840a008813f62f26a34d54850f4`.
- Independently verified formal root `a0e9d29...` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- This is a new formal pair relative to prior reviewed `99bafeb060054da29052fcc4bd1121f075e85ad5` / same child, so fresh incremental review is required.
- Formal implementation commit changes only the approved two-file allowlist: `tools/psm_wma/immutable_source_collection.py` and `tools/psm_wma/test_immutable_source_collection.py`.
- Frozen authority remains real-adapter design v0.1 plus v0.2 executor-identity supersession; v0.2 preserves v0.1 FD/no-follow, race rejection, native-Git, atomic-evidence, rollback and CPU/static acceptance requirements.
- This review does not authorize real source/checkpoint/manifest/data/cache I/O, live collection/receipt/publication mutation, execution-request activation, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.

## 2. Prior blocker disposition

- Prior HIGH-1 — intermediate-directory replacement for direct `NativeRootFd.open_regular()`: **materially improved / direct source path witness CLOSED for replacement-to-new-directory**. The implementation now retains parent guards and reopens each guarded component after the final leaf open, comparing no-follow `(st_dev, st_ino, type)` against the originally opened child. The new direct native witness replaces `dir` after it is opened and correctly expects `CollectionError`.
- Prior HIGH-1 — analogous `NativeCollectionGit.snapshot()` ancestor-race closure: **still OPEN**. `open_optional_regular(..., allow_absent=True)` shares the same broad `FileNotFoundError` handler and can downgrade a continuity failure during guard revalidation to ordinary `None/absent`; the required direct snapshot ancestor-race witness is still absent.
- Prior HIGH-2 — staged-file identity: **partially CLOSED**. The sink now records staged inode identity and verifies the published inode and bytes after `os.link`.
- Prior HIGH-2 — frozen request-bound destination continuity / failure cleanup: **still OPEN**. Parent identity is checked only before `os.link`, and the old parent-relocation test still treats relocation during `os.link` as success. Publication mismatch can also leave a foreign final destination because failure cleanup removes only `.pending`.

## 3. Current blocking findings

### HIGH-1 — `allow_absent=True` converts ancestor continuity loss into authoritative `absent` snapshot state

**Location:** `tools/psm_wma/immutable_source_collection.py:153` (`NativeRootFd._open_regular`), consumed by `NativeCollectionGit.snapshot()`.

**Root cause**

The new continuity guards run inside the same `try` block as the initial traversal/open. Any `FileNotFoundError` from either phase is handled by:

```python
except FileNotFoundError:
    if allow_absent:
        return None
```

For direct source collection, `open_regular(..., allow_absent=False)` correctly fail-closes. But native snapshot uses `open_optional_regular(..., allow_absent=True)`.

A tracked snapshot path can therefore be opened successfully from the retained old subtree, then have an intermediate component renamed away before guard revalidation. Reopening the guarded component raises `FileNotFoundError`; `_open_regular()` returns `None` instead of raising authority drift. `NativeCollectionGit.snapshot()` then encodes that path as:

```json
{"mode": null, "kind": "absent", "sha256": null}
```

without checking that the path was already present in the controlled index. This turns a causal namespace race into an apparently valid `target_snapshot_v1` state rather than fail-closing. Because the early `return None` occurs after the final leaf descriptor may already have been opened, that branch also bypasses the later descriptor-close path.

**Violated frozen contract**

- The inherited FD/no-follow contract requires symlink/escape/type/**race** drift to fail closed.
- The prior exact acceptance required the analogous native snapshot ancestor-directory replacement witness; the remediation request claims authority-race closure.
- Snapshot authority must not reinterpret post-open namespace drift as ordinary initial absence.

**Why submitted Evidence does not close it**

The new test `test_native_root_fd_rejects_intermediate_directory_replacement_during_traversal` calls `open_regular()` (`allow_absent=False`) and replaces the old directory with a new directory, producing an inode mismatch. It does not exercise the snapshot path, does not exercise disappearance/rename-away with no replacement, and does not prove that `allow_absent=True` distinguishes initial absence from continuity failure.

**Exact acceptance**

- Distinguish initial-path absence from post-open continuity failure. `allow_absent=True` may return `None` only when the requested path is genuinely absent before any retained ancestor/leaf authority has been accepted for that lookup.
- Once an intermediate guard or final descriptor has been opened, any revalidation `ENOENT`, symlink/type mismatch, or inode mismatch must raise `CollectionError` and close every opened FD.
- Add a direct `NativeCollectionGit.snapshot()` temporary-worktree witness: after an intermediate component is opened, rename it away (with no replacement) before continuity revalidation. Snapshot must raise and must not emit an authoritative `absent` entry.
- Preserve the existing replacement-to-new-directory witness; add explicit cleanup/FD-lifetime assertions if practical.

### HIGH-2 — evidence publication can still succeed after frozen parent relocation, and verification failure can leave a foreign final destination

**Location:** `tools/psm_wma/immutable_source_collection.py:244` (`AtomicFileEvidenceSink.emit`).

**Root cause A — request-parent continuity is checked only before publication**

The remediation captures the parent inode and checks the pathname immediately before `os.link`. However there is still a race window between that check and the link. The existing test `test_atomic_sink_parent_replacement_cannot_redirect_publication` deliberately renames the approved parent inside the patched `os.link`, creates a replacement parent at the frozen pathname, and expects `emit()` to return success while the record exists only in the renamed old directory.

That is the exact behavior the prior canonical review rejected: the current authority freezes a request-bound destination pathname. A retained parent-FD/leaf authority that remains valid after global pathname relocation would be a contract change requiring separate refreeze; this implementation Gate cannot silently adopt it.

**Root cause B — foreign final link survives post-link identity failure**

The staged inode check detects a `.pending` replacement if the replacement is linked to the final name: the later `published` inode/byte check will fail. But the exception cleanup only unlinks `temporary_name`; it does not remove the final destination created by the just-completed `os.link`.

Thus a race can produce this terminal state:

1. canonical bytes are written/fsynced to staging inode A;
2. `.pending` is replaced by foreign inode B before `os.link`;
3. final destination is hard-linked to B;
4. post-link identity check detects `B != A` and raises;
5. failure cleanup removes `.pending` but leaves the foreign final destination visible.

This violates the evidence-sink interface guarantee that failed publication leaves no newly accepted visible/persistent record and undermines retry/freshness authority.

**Violated frozen contract**

- Normal return must mean the canonical validated record exists at the exact frozen fresh destination.
- Any parent/destination/staging race must fail closed.
- Failed evidence publication must not leave an accepted foreign/partial final record; `collect_synthetic()` relies on sink failure to trigger rollback rather than preserve a misleading PASS artifact.

**Why submitted Evidence does not close it**

- The parent-relocation test still asserts success and explicitly proves the frozen destination pathname is absent after return.
- No test replaces `.pending` after staged identity capture and verifies that a foreign final destination is removed before failure returns.
- The new published-inode/byte verification proves detection, but not atomic cleanup or frozen-path authority preservation.

**Exact acceptance**

- Revalidate the request-bound parent/destination authority again after publication and immediately before successful return. If the parent pathname no longer names the retained approved parent inode, `emit()` must fail.
- On any post-link verification failure or parent-authority drift, remove only the final link proven to have been created by this emission (using retained parent capability and exact inode identity), then raise. Do not leave a foreign final record.
- Retain sufficient staging identity/capability until final publication is verified; staged-entry replacement must never become a surviving accepted destination.
- Change the parent-relocation witness to require failure and no accepted destination at either the replacement parent or relocated old parent.
- Add a direct `.pending` replacement race witness after staged identity capture and before link; the sink must raise and leave no final evidence file.

## 4. Closed / non-blocking observations

- Formal tree → Gitlink is exact and child commit is reachable.
- The direct source `NativeRootFd` replacement-to-new-directory witness is directionally correct and closes the previous simplest detached-subtree acceptance case for `allow_absent=False`.
- Same-FD native snapshot hashing, tracked mode capture, direct native `collect_synthetic()` composition, rollback equality, and final symlink/directory matrix remain closed from the prior pair.
- Staged inode plus final inode/byte verification is a real improvement; the remaining blocker is the success/cleanup authority around those checks, not the basic comparison itself.
- Reported `51/51`, `py_compile`, and `git diff --check` are auxiliary evidence only and do not override the two authority contradictions above.

## 5. Formal verdict

`REQUEST_CHANGES(tools/psm_wma/immutable_source_collection.py:153)`

Current blockers: **2 HIGH Production/Authority+Evidence**.  
Child/runtime blockers: **0**.

## 6. Scope reminder

This verdict binds only exact formal pair `a0e9d294320ad37cb127d45118b3f67107bfef7f` / `93a89ba61306d840a008813f62f26a34d54850f4` and Gate `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-REAL-ADAPTER-CPU-STATIC`.

Remediation remains limited to the already-approved two-file CPU/static allowlist and temporary fixtures. No real source/checkpoint/manifest/data/cache access, live collection/receipt/publication execution, execution-request activation, child/runtime/config change, GPU, training, evaluation or inference action is authorized.
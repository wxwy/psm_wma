# ChatGPT Independent Review — R09-B TTT v0.3.5 Immutable Source Collection Real Adapter CPU/static Publication-Race Remediation

**Date:** 2026-09-14  
**Formal root:** `831be4b99f8564bb3695e445dcdfeb1770d7e7f0`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-REAL-ADAPTER-CPU-STATIC`

## 1. Pair / scope lock

- Re-locked remote `V2` and re-read live `docs/collab/chatgpt/CODEX_INBOX.md`; the effective request binds exact pair `831be4b99f8564bb3695e445dcdfeb1770d7e7f0` / `93a89ba61306d840a008813f62f26a34d54850f4`.
- Independently verified formal root `831be4b...` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- This is a new formal pair relative to prior reviewed `a0e9d294320ad37cb127d45118b3f67107bfef7f` / same child, so a fresh incremental review is required.
- Relevant implementation delta is limited to `tools/psm_wma/immutable_source_collection.py` and `tools/psm_wma/test_immutable_source_collection.py`; `SESSION.md` / `TODO.md` entries are task-record bookkeeping and are not treated as implementation authority.
- Frozen authority remains the real-adapter implementation design chain previously locked for this Gate. No real source/checkpoint/manifest/data/cache I/O, live collection/receipt/publication execution, execution-request activation, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1 is authorized by this review.

## 2. Prior blocker disposition

- Prior HIGH-1 — `allow_absent=True` swallowing post-open ancestor continuity loss: **CLOSED**. `_open_regular()` now distinguishes pre-leaf absence from post-open continuity failure via `descriptor < 0`, revalidates retained ancestor guards before returning `None`, and closes a leaf descriptor whenever continuity has not completed. The new native snapshot witness renames the opened `docs` ancestor away and correctly requires `CollectionError` rather than an authoritative `absent` snapshot entry.
- Prior HIGH-2A — link-time parent relocation accepted as success: **materially improved but not fully CLOSED**. The sink now revalidates the frozen parent pathname after publication and before staging cleanup, and the updated link-time relocation witness expects failure with no retained final record.
- Prior HIGH-2B — post-link foreign final residue: **CLOSED for the submitted after-identity-capture `.pending` replacement case**. The sink now records the opened published inode, verifies inode+canonical bytes, and removes only a final link whose retained-parent entry still has that exact published inode when a later check fails.
- Additional preflight leakage guard: the first collection preflight now compares the live snapshot before/after, rolls back on visible mutation, and the submitted witness proves that injected leakage is rejected and restored. This is a useful strengthening and is not itself blocking below.

## 3. Current blocking findings

### HIGH-1 — staging inode authority is still acquired only after the original write FD has been closed

**Location:** `tools/psm_wma/immutable_source_collection.py:289` (`AtomicFileEvidenceSink.emit`)

**Root cause**

The sink creates `<destination>.pending`, writes/fsyncs canonical bytes through `descriptor`, and exits the `os.fdopen(...)` context, which closes that authoritative staging FD. Only afterwards does it reopen the mutable staging pathname and derive `staged_identity`:

```python
with os.fdopen(descriptor, "wb") as handle:
    handle.write(raw)
    handle.flush()
    os.fsync(handle.fileno())

staged = os.open(temporary_name, ..., dir_fd=parent_fd)
info = os.fstat(staged)
staged_identity = (info.st_dev, info.st_ino)
```

Therefore the code still has a close→reopen namespace gap. An actor able to mutate the controlled directory can replace `.pending` after the original write FD closes but before the read-only reopen. The replacement inode is then adopted as the authoritative `staged_identity`.

The later `published_identity == staged_identity` and byte check do not prove that the published inode is the inode that this emission created and fsynced. In particular, a foreign replacement containing the same canonical bytes can pass all current checks. If that foreign inode also has another retained hardlink, it can be mutated after `emit()` returns and thereby mutate the accepted destination without ever touching the destination directory entry.

**Violated frozen contract / prior exact acceptance**

The prior exact acceptance required retaining authoritative staging-file identity/capability through publication, and explicitly required that staged-entry replacement must never become a surviving accepted destination. Normal return must prove the accepted evidence is the canonical record staged by this emission, not merely a same-byte inode discovered later through a mutable name.

**Why submitted Evidence does not close it**

`test_atomic_sink_rejects_staged_entry_replacement_without_final_residue` performs the replacement inside the patched `os.link`. That occurs **after** `staged_identity` has already been captured. It proves the later identity mismatch/cleanup path, but it does not exercise the earlier close→reopen gap where a replacement can become the new `staged_identity`.

**Exact acceptance**

- Capture the staging inode identity from the exact FD that was created with `O_CREAT|O_EXCL` and used for write/fsync, before that FD is closed; preferably retain that FD (or a duplicate of it) until publication is fully verified.
- Publication must compare the final entry against this original emission-owned staging inode, not against an inode learned by reopening `.pending` after the write FD has been released.
- Add a direct witness that replaces `.pending` after write/fsync/close boundary but before any current pathname-based staging reopen. Use a foreign inode with the exact canonical bytes and a retained second hardlink; `emit()` must fail, no final destination may survive, and the foreign inode/hardlink must not become the accepted evidence authority.

### HIGH-2 — the final frozen-parent continuity check is not the last operation before successful return

**Location:** `tools/psm_wma/immutable_source_collection.py:307` (`AtomicFileEvidenceSink.emit`)

**Root cause**

The new code correctly performs a second global parent-path identity check after final inode/byte verification. However it then executes another mutable operation before returning success:

```python
current_parent = os.stat(self._destination.parent, follow_symlinks=False)
... verify parent identity ...
os.unlink(temporary_name, dir_fd=parent_fd)
# function then returns normally
```

A parent relocation can therefore occur **after** the second parent check but during the final `.pending` unlink. Because the unlink is relative to the retained old `parent_fd`, it succeeds in the renamed old directory; no subsequent global pathname revalidation occurs. `emit()` then returns success while the frozen request-bound destination pathname can be absent and the accepted evidence remains only under the relocated old parent.

This is the same authority class as the prior link-time parent relocation blocker; the race window has merely moved to the final cleanup step.

**Violated frozen contract / prior exact acceptance**

The prior exact acceptance required revalidating the request-bound destination authority after publication and immediately before successful return. The current Gate freezes a pathname-bound destination; relocation of the retained parent is not implicitly authorized.

**Why submitted Evidence does not close it**

The updated `test_atomic_sink_parent_replacement_cannot_redirect_publication` injects relocation inside `os.link`, which is now caught by the post-link parent check. It does not relocate the parent during the final `os.unlink(temporary_name, dir_fd=parent_fd)` after that check has already passed.

**Exact acceptance**

- After all staging cleanup is complete, perform a final request-path authority validation as the last validation step before normal return: the global parent pathname must still name the retained parent inode, and the frozen destination leaf must still be the exact verified published inode with canonical bytes.
- If that final validation fails, remove only the identity-proven final link created by this emission via the retained parent capability, then raise so the caller rolls back/fail-stops.
- Add a direct witness that relocates/replaces the parent during the final `.pending` unlink (after the current second parent check). `emit()` must fail and leave no accepted evidence at either the replacement pathname or the relocated old parent.

## 4. Closed / non-blocking observations

- `NativeRootFd` direct intermediate-directory replacement rejection remains closed.
- `NativeCollectionGit.snapshot()` ancestor disappearance now fail-closes rather than converting post-open continuity loss to `absent`; the opened descriptor cleanup path is also materially corrected.
- Same-FD snapshot hashing, tracked mode capture, final symlink/directory rejection, native `collect_synthetic()` composition, and rollback-equality witnesses remain closed from prior pairs.
- The new identity-proven final cleanup is directionally correct and closes the specific post-link foreign-residue case where the foreign inode is discovered as `published_identity`.
- Reported `54/54 PASS`, `py_compile`, and `git diff --check` are useful auxiliary evidence but do not cover the two remaining causal windows above.
- Child/runtime blockers: **0**.

## 5. Formal verdict

`REQUEST_CHANGES(tools/psm_wma/immutable_source_collection.py:289)`

Current blockers: **2 HIGH Production/Authority+Evidence**.  
Child/runtime blockers: **0**.

## 6. Scope reminder

This verdict binds only exact formal pair `831be4b99f8564bb3695e445dcdfeb1770d7e7f0` / `93a89ba61306d840a008813f62f26a34d54850f4` and Gate `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-REAL-ADAPTER-CPU-STATIC`.

Remediation remains limited to the already-approved two-file CPU/static allowlist and temporary fixtures. No real source/checkpoint/manifest/data/cache access, live collection/receipt/publication execution, execution-request activation, child/runtime/config change, GPU, training, evaluation, inference, or LIBERO4IN1 action is authorized.
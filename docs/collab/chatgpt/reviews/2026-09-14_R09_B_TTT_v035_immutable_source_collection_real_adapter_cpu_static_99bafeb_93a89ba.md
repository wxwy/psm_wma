# ChatGPT Independent Review — R09-B TTT v0.3.5 Immutable Source Collection Real Adapter CPU/static Descriptor-Stable Remediation

**Date:** 2026-09-14  
**Formal root:** `99bafeb060054da29052fcc4bd1121f075e85ad5`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-REAL-ADAPTER-CPU-STATIC`

## 1. Pair / scope lock

- Re-locked live `V2` and re-read the current `docs/collab/chatgpt/CODEX_INBOX.md`; the effective request binds exact pair `99bafeb060054da29052fcc4bd1121f075e85ad5` / `93a89ba61306d840a008813f62f26a34d54850f4`.
- Independently verified the formal root resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- This is a new formal pair relative to the prior reviewed `24253e0c3789d46c0807944ec75d6dff108824f3` / same child, so a fresh incremental review is required.
- Formal implementation commit `99bafeb...` modifies only the approved two-file implementation allowlist: `tools/psm_wma/immutable_source_collection.py` and `tools/psm_wma/test_immutable_source_collection.py`. Intervening review/session/bookkeeping commits are non-target.
- Frozen authority remains real-adapter design v0.1 plus v0.2 executor-identity supersession; v0.2 preserves v0.1 FD/no-follow, native-Git, atomic-evidence, one-shot-handoff, rollback and CPU/static acceptance requirements.
- This review does not authorize real source/checkpoint/manifest/data/cache I/O, live collection/receipt/publication mutation, execution-request activation, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.

## 2. Prior blocker disposition

- Prior HIGH — pathname check/read TOCTOU in `NativeCollectionGit.snapshot()`: **leaf/file-FD portion CLOSED**. The remediation now opens the worktree root and final files through `NativeRootFd`, hashes from the same retained file FD, and compares pre/post descriptor identity.
- Prior MEDIUM — parent capability was not bound before staging/publication: **PARTIALLY CLOSED**. The sink now opens a retained parent directory FD before staging and uses dirfd-relative `os.link`/`os.unlink`, so a simple final-parent replacement can no longer redirect writes into the replacement directory.
- Prior MEDIUM Evidence — actual native object composition through canonical `collect_synthetic()`: **CLOSED for the requested composition/rollback/mode matrix**. The new temporary fixture directly wires actual `NativeCollectionGit` + actual `NativeRootFd` into `collect_synthetic()`, exercises late sink failure rollback equality, reaches PASS, and adds native mode/symlink/directory witnesses.
- Prior `NativeRootFd` component-race acceptance: **still OPEN**. Static intermediate-symlink rejection exists, but the frozen replacement-during-traversal behavior is neither implemented nor directly witnessed.

## 3. Current blocking findings

### HIGH-1 — `NativeRootFd` pins an opened ancestor but does not reject ancestor replacement during traversal

**Location:** `tools/psm_wma/immutable_source_collection.py:153` (`NativeRootFd._open_regular`)

**Root cause**

The implementation correctly opens each intermediate component with `O_DIRECTORY|O_NOFOLLOW` and then advances by replacing `current` with the opened directory FD. However, after an intermediate directory FD has been opened, there is no revalidation that the corresponding parent entry still names that same directory inode before the final file FD is accepted.

Therefore a component can be renamed out of the retained source-root namespace and replaced after its FD is opened. The subsequent final `os.open(..., dir_fd=current)` still succeeds against the detached original directory and returns a readable source FD. The final file descriptor may remain perfectly stable (`st_dev`, `st_ino`, size/mtime/ctime unchanged), so the existing same-FD checks do not detect this ancestor-path race.

An isolated local syscall probe matching the production sequence confirms the behavior: open `root/dir` as a directory FD, rename `dir` away, install a new `root/dir`, then open `file` relative to the retained old directory FD; the read returns the old file while `root/dir/file` names the replacement file.

`NativeCollectionGit.snapshot()` now reuses this same traversal primitive, so the same ancestor replacement can make `target_snapshot_v1` hash a detached old subtree while the current pathname resolves elsewhere.

**Violated frozen contract**

- Design v0.1 requires the FD-root opener to reject symlink, escape, directory **and race** conditions while reading selected source entries.
- The prior exact acceptance explicitly required a real `NativeRootFd` replacement-during-traversal witness where component replacement must not yield an accepted readable source FD.

**Why submitted Evidence does not close it**

- `test_native_root_fd_rejects_intermediate_symlink` is static; the symlink exists before traversal starts.
- `test_native_snapshot_hashes_retained_fd_when_path_is_replaced` replaces the final leaf after that file FD is open. Renaming the leaf changes the opened inode's ctime and is caught by the existing pre/post `fstat`; it does not exercise an ancestor directory rename, which leaves the descendant file inode unchanged.
- No test replaces an intermediate directory after its FD has been opened but before the next component/final file is opened.

**Exact acceptance**

- Preserve component-by-component no-follow traversal, but also prove path-to-FD continuity for every opened directory component through the traversal completion boundary. A renamed/replaced ancestor must fail closed rather than returning a source handle from a detached subtree.
- An acceptable implementation may retain parent and child FDs and revalidate the parent entry's no-follow `(st_dev, st_ino, type)` against the child FD before/after descending, or use an equivalent primitive whose semantics directly prove the frozen component-race requirement.
- Add a direct temporary-directory native witness that pauses after opening an intermediate component, renames/replaces that component, then continues. The call must raise `CollectionError`; neither old nor replacement bytes may be returned as an accepted source entry.
- Add the analogous native snapshot witness for an ancestor-directory replacement while snapshot traversal is in progress; it must not produce an authoritative snapshot from the detached subtree.

### HIGH-2 — atomic evidence publication does not retain the staged inode through publication and can return success for the wrong/frozen-away destination

**Location:** `tools/psm_wma/immutable_source_collection.py:221` (`AtomicFileEvidenceSink.emit`)

**Root cause**

The remediation correctly binds `destination.parent` to a directory FD and creates `<name>.pending` with `O_EXCL|O_NOFOLLOW` relative to that FD. But it then closes the staged file descriptor and later publishes by resolving the mutable staging **name** again:

`os.link(temporary_name, destination.name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd, ...)`.

There is no retained staged-inode identity check at link time and no post-link proof that the destination inode/bytes are the exact file that was written and fsynced. A concurrent actor with the same directory mutation capability can unlink/replace `<name>.pending` after the write FD is closed but before `os.link`; the sink can then hard-link the replacement inode to the final destination and return normally. `collect_synthetic()` would consequently retain the live collection/receipt transaction even though the visible evidence bytes are not the canonical record passed to `emit()`.

The submitted parent-replacement witness also codifies another authority mismatch: after the parent directory is renamed and replaced, `emit()` returns success while the frozen `destination` pathname does not exist; the record is instead visible under the renamed old parent. The current frozen design/request authority is a fresh request-bound evidence destination path, not an independently frozen parent-FD/leaf capability ABI.

**Violated frozen contract**

- Atomic evidence must publish the canonical validated record to the frozen fresh destination and normal return must mean that accepted evidence is exactly the submitted record.
- A failed/raced publication must not leave an accepted partial/foreign record, and PASS must not survive an unverified evidence publication.

**Why submitted Evidence does not close it**

- The destination-appears race proves no-replace only for the final name.
- The parent replacement test proves writes stay with the retained old directory inode, but it treats disappearance of the frozen path as success rather than fail-close.
- There is no race witness that replaces the deterministic `.pending` entry after fsync/close and before `os.link`, nor any post-publication inode/byte verification against the staged file that was actually written.

**Exact acceptance**

- Retain authoritative staging-file identity across publication. Publish from the retained inode/capability, or prove immediately after publication that the destination is the exact same staged inode and exact canonical bytes before `emit()` may return success.
- A replacement of `<name>.pending` after write/fsync and before final link must fail closed and must not leave a foreign accepted destination.
- Revalidate that the request-bound destination authority is still the approved one before successful return. If the intended contract is instead to bind a parent directory FD + leaf and allow global pathname relocation, that is a contract change requiring a separate design/request refreeze; it cannot be introduced implicitly in this implementation Gate.
- Add direct race witnesses for staged-entry replacement and request-parent relocation. On any authority drift, `emit()` must raise so `collect_synthetic()` rolls back or fail-stops according to the existing evidence-sink contract.

## 4. Non-blocking / closed observations

- The isolated native preflight remains observationally non-mutating to the live snapshot.
- Native tracked `100644/100755` mode capture, untracked allowlist rejection, out-of-allowlist porcelain rejection, final symlink/directory rejection, and same-FD leaf hashing are materially stronger than the previous pair.
- The direct native composition witness closes the earlier gap where all canonical `collect_synthetic()` PASS paths used only `TemporaryGitFixture`.
- Child/Gitlink remains unchanged and reachable; no child/runtime blocker was found.
- Reported `50/50`, `py_compile`, and `git diff --check` are useful auxiliary evidence but do not override the two authority/atomicity contradictions above.

## 5. Formal verdict

`REQUEST_CHANGES(tools/psm_wma/immutable_source_collection.py:153)`

Current blockers: **2 HIGH Production/Authority+Evidence**.  
Child/runtime blockers: **0**.

## 6. Scope reminder

This verdict binds only exact formal pair `99bafeb060054da29052fcc4bd1121f075e85ad5` / `93a89ba61306d840a008813f62f26a34d54850f4` and Gate `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-REAL-ADAPTER-CPU-STATIC`.

Remediation remains limited to the already-approved two-file CPU/static allowlist and temporary fixtures. No real source/checkpoint/manifest/data/cache access, live collection/receipt/publication execution, execution-request activation, child/runtime/config change, GPU, training, evaluation or inference action is authorized.
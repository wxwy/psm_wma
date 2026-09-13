# ChatGPT Independent Review — R09-B TTT v0.3.5 Immutable Source Collection Real Adapter CPU/static Implementation

**Date:** 2026-09-13  
**Formal root:** `34cedc9ff227c35b387666ae824d282b14d2b1f5`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-REAL-ADAPTER-CPU-STATIC`

## 1. Pair / scope lock

- Re-locked remote `V2` and re-read live `docs/collab/chatgpt/CODEX_INBOX.md`; the effective request binds exact pair `34cedc9ff227c35b387666ae824d282b14d2b1f5` / `93a89ba61306d840a008813f62f26a34d54850f4` for this CPU/static implementation Gate.
- Independently verified formal root `34cedc9ff227c35b387666ae824d282b14d2b1f5` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Design authority is the approved v0.2 real-adapter design formal pair `6ec9d2db564102c7546ceb1c44bc06ccb3c8de31` / same child. v0.2 explicitly preserves all unaffected v0.1 FD/no-follow, native-Git, atomic-evidence, one-shot-handoff, rollback and CPU/static acceptance requirements while keeping the sole executor path `tools/psm_wma/immutable_source_collection.py`.
- Technical implementation remains root-only in the approved two-file allowlist: `tools/psm_wma/immutable_source_collection.py` and its direct stdlib test. Session/review-delivery bookkeeping is non-target.
- This review does not authorize real source/checkpoint/manifest/data/cache I/O, real collection/receipt/publication mutation, request execution, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.

## 2. Blocking findings

### HIGH-1 — `NativeCollectionGit.preflight()` violates the canonical non-mutating preflight seam and cannot pass through the production algorithm

**Location:** `tools/psm_wma/immutable_source_collection.py:300` (`NativeCollectionGit.preflight`; mutation begins at lines 303-306)

**Root cause**

The canonical algorithm `_commit_candidates()` takes `before = _snapshot(git.snapshot())`, calls `git.preflight(...)`, and then requires `_snapshot(git.snapshot()) == before` before any live transaction proceeds. This is the already-frozen isolated-preflight contract.

`NativeCollectionGit.preflight()` uses the adapter's own `GIT_INDEX_FILE` and executes `read-tree`, `hash-object -w`, `update-index`, then `write-tree`, leaving that index at the candidate tree. `NativeCollectionGit.snapshot()` derives `index_tree_native_oid` from that same index with `git write-tree`. Therefore the native adapter changes the very snapshot field that `_commit_candidates()` immediately requires to remain unchanged.

On the real production object path `collect_synthetic(..., git=NativeCollectionGit(...))`, the first collection preflight necessarily changes `index_tree_native_oid`, so the canonical algorithm must fail with `isolated preflight 修改了 live snapshot` before it can enter the collection commit phase.

**Why existing evidence is insufficient**

The submitted `40/40` suite exercises `NativeCollectionGit.commit()` and `rollback()` directly, while the PASS-shaped end-to-end `collect_synthetic()` witness still uses `TemporaryGitFixture`. There is no direct witness that wires the actual `NativeCollectionGit` into the unchanged canonical algorithm. Test counts therefore do not cover the production seam that is being approved.

**Exact acceptance**

- Make `NativeCollectionGit.preflight()` observationally non-mutating with respect to the canonical `snapshot()` contract. Use a distinct isolated temporary index/tree capability for preflight, or save/restore the controlled index before returning; the caller's retained snapshot must compare byte-for-byte equal after preflight.
- Add a direct temporary-Git witness using the actual `NativeCollectionGit` through `collect_synthetic()` (not direct method calls) that reaches a PASS-shaped collection/receipt transaction while proving the preflight snapshot is unchanged.
- Add a failure witness showing any preflight index/tree leakage is detected before live collection commit.

### HIGH-2 — `NativeRootFd.open_regular()` follows intermediate symlink components, violating the frozen no-follow traversal contract

**Location:** `tools/psm_wma/immutable_source_collection.py:153-159`

**Root cause**

`NativeRootFd.open_regular()` validates lexical components and then performs one `os.open(path, O_RDONLY|O_CLOEXEC|O_NOFOLLOW, dir_fd=root_fd)`. On Linux, `O_NOFOLLOW` protects only the final path component; intermediate components may still be symbolic links. A selection such as `dir/file` can therefore escape the frozen source-root capability when `dir` is replaced by a symlink to another directory.

The inherited collection execution contract requires each component to be resolved descriptor-safely beneath the retained root FD with symlink traversal rejected. The v0.2 adapter design explicitly preserves this FD/no-follow requirement.

**Why existing evidence is insufficient**

The native test covers a regular file and lexical `../escape`. The only nested-symlink test is against `SyntheticRootFd`; it does not exercise `NativeRootFd` or the kernel path-resolution behavior.

**Exact acceptance**

- Traverse intermediate components one at a time relative to retained directory FDs with `O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC`, then open the final component with `O_RDONLY|O_NOFOLLOW|O_CLOEXEC`; alternatively use an equivalent beneath/no-symlink primitive whose semantics are directly witnessed.
- Reject intermediate symlink replacement, final symlink, directory, escape, and component race on the actual `NativeRootFd` object.
- Add direct temporary-directory witnesses for an intermediate symlink to an outside directory and for replacement during traversal; neither may return a readable source FD.

### HIGH-3 — `NativeCollectionGit.snapshot()` does not implement the frozen `target_snapshot_v1` authority and can produce false rollback/equality evidence

**Location:** `tools/psm_wma/immutable_source_collection.py:283-298`

**Root cause**

The frozen evidence/rollback contract requires the target snapshot to derive tracked mode from Git index state, detect untracked-present allowlist paths, reject symlink/directory/other path types, and fail on out-of-allowlist porcelain residue. The current native snapshot instead:

- scans only `SNAPSHOT_PATHS` with global `Path.is_file()` / `read_bytes()`;
- hard-codes every present file mode to `100644` rather than binding the tracked index mode;
- treats an untracked regular file at an allowlist path as an accepted `regular` entry;
- does not inspect porcelain state outside the allowlist at all;
- does not provide descriptor-anchored/no-follow traversal for the retained worktree evidence.

This means `verify_synthetic_rollback(before, after, completed=True)` can accept equality for a native snapshot that never represented the frozen worktree/index authority in the first place.

**Why existing evidence is insufficient**

The native rollback test checks only that the temporary ref resolves back to the prior revision. It does not exercise the exact snapshot schema against executable-mode drift, untracked allowlist entries, out-of-allowlist dirty residue, or symlink/directory replacement.

**Exact acceptance**

- Implement the exact frozen snapshot semantics on the native adapter: tracked mode from `git ls-files --stage`, full controlled-index tree identity, deterministic allowlist entry encoding, porcelain/untracked rejection, and no-follow type checks for worktree paths.
- Directly witness at least: `100755` vs `100644` mode drift, untracked-present allowlist path, out-of-allowlist porcelain residue, symlink/directory replacement, and a successful rollback whose recomputed `after_snapshot` exactly equals retained `before_snapshot`.

### MEDIUM-1 — atomic evidence publication is overwrite-capable after the freshness check

**Location:** `tools/psm_wma/immutable_source_collection.py:200-217`

`AtomicFileEvidenceSink` checks destination freshness only in `__init__`, stages to `<name>.pending`, then publishes with `os.replace()`. If another actor creates the destination after construction but before publication, `os.replace()` overwrites it instead of fail-closing. That violates the inherited requirement that evidence is emitted only to a fresh request-bound destination and that an existing accepted record is never replaced.

**Exact acceptance:** use a no-replace final publication primitive / directory-FD anchored equivalent, revalidate destination/parent authority at publication time, and add a race witness where the destination appears after sink construction; the foreign destination must remain untouched and the emit must fail.

## 3. Other checks

- The prior design blocker about a second production entrypoint remains closed: the implementation stays in the unique `tools/psm_wma/immutable_source_collection.py` executor and its direct test.
- The child/Gitlink is unchanged and reachable.
- The new native Git subprocess path is non-shell and uses a reduced explicit environment; this is directionally consistent with the design, but it does not compensate for the production-seam blockers above.
- `40/40`, `py_compile`, and `git diff --check` are auxiliary evidence only; they cannot override direct contradictions between the native adapter and the unchanged canonical algorithm / frozen evidence contract.

## 4. Formal verdict

`REQUEST_CHANGES(tools/psm_wma/immutable_source_collection.py:300)`

Current blockers: **3 HIGH Production/Authority + 1 MEDIUM Production/Evidence**.  
Child/runtime blockers: **0**.

## 5. Scope / next action

This verdict binds only exact formal pair `34cedc9ff227c35b387666ae824d282b14d2b1f5` / `93a89ba61306d840a008813f62f26a34d54850f4` and Gate `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-REAL-ADAPTER-CPU-STATIC`.

Remediation remains limited to the already-approved two-file CPU/static allowlist and temporary fixtures. No real source/checkpoint/data/cache access, live authority/collection/receipt/publication execution, child/runtime change, GPU or training action is authorized. A new formal pair is required for fresh review after these blockers are closed.

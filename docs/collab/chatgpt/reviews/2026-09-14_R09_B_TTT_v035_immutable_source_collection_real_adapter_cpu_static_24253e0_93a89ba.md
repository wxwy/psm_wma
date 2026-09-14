# ChatGPT Independent Review — R09-B TTT v0.3.5 Immutable Source Collection Real Adapter CPU/static Remediation

**Date:** 2026-09-14  
**Formal root:** `24253e0c3789d46c0807944ec75d6dff108824f3`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-REAL-ADAPTER-CPU-STATIC`

## 1. Pair / authority / scope lock

- Re-locked remote `V2`, re-read live `docs/collab/chatgpt/CODEX_INBOX.md`, and identified the latest effective collection-adapter remediation request as exact pair `24253e0c3789d46c0807944ec75d6dff108824f3` / `93a89ba61306d840a008813f62f26a34d54850f4`.
- Independently verified formal root `24253e0...` resolves `cosmos-framework` exactly to reachable child `93a89ba...`.
- This is a new formal pair relative to the prior reviewed pair `34cedc9ff227c35b387666ae824d282b14d2b1f5` / `93a89ba...`; fresh incremental review is therefore required.
- Authority chain: real-adapter implementation design v0.1 plus v0.2 explicit executor-identity supersession. v0.2 supersedes only the executor/allowlist point and preserves v0.1 CPU/static-only, FD/no-follow, native-Git, atomic-evidence, one-shot-handoff, rollback, and acceptance requirements.
- The effective implementation delta relevant to this Gate remains the approved two-file root allowlist: `tools/psm_wma/immutable_source_collection.py` and `tools/psm_wma/test_immutable_source_collection.py`. Intervening Session/TODO/reviewer bookkeeping is non-target historical/persistence state, not a scope violation.
- This review does not authorize real source/checkpoint/manifest/data/cache I/O, real collection/receipt/publication mutation, execution-request activation, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1.

## 2. Prior blocker disposition

- Prior HIGH-1 (`NativeCollectionGit.preflight` mutating the live index snapshot): **production CLOSED**. The remediation uses a distinct temporary index and the native unit witness confirms the retained live snapshot is unchanged.
- Prior HIGH-2 (`NativeRootFd` following intermediate symlink components): **production CLOSED**. The implementation now walks each intermediate component relative to retained directory FDs with `O_DIRECTORY|O_NOFOLLOW`, and opens the final component with `O_NOFOLLOW`.
- Prior HIGH-3 (`target_snapshot_v1` authority): **PARTIALLY CLOSED / still blocking**. Tracked index mode and porcelain/untracked rejection were added, but worktree-byte capture remains pathname check-then-read rather than a retained descriptor/no-follow capability.
- Prior MEDIUM-1 (destination overwrite after freshness check): **original overwrite defect CLOSED**. Final publication now uses no-replace `os.link`, and the submitted test covers a destination appearing after sink construction. A separate parent/staging authority defect remains below.

## 3. Current blocking findings

### HIGH-1 — `NativeCollectionGit.snapshot()` still has pathname TOCTOU and does not provide descriptor-anchored/no-follow retained worktree evidence

**Location:** `tools/psm_wma/immutable_source_collection.py:306` (`NativeCollectionGit.snapshot`)

**Root cause**

For every `SNAPSHOT_PATHS` entry, the implementation first walks intermediate names using `Path.is_symlink()`, then performs `os.lstat(candidate)`, then later calls `candidate.is_symlink()` and finally `candidate.read_bytes()`. These are separate pathname resolutions. No directory/file descriptor is retained across the type check and byte read.

An intermediate directory or final leaf can therefore be replaced after the checks and before `read_bytes()`. The final read may follow a newly installed symlink and hash bytes outside the retained target worktree, while the resulting object is still encoded as authoritative `target_snapshot_v1` worktree evidence. The later rollback equality check then compares snapshots that may never have represented the controlled worktree authority.

**Violated frozen contract**

- v0.2 explicitly preserves v0.1 FD/no-follow and rollback acceptance.
- The prior exact HIGH-3 acceptance required no-follow retained worktree semantics and direct symlink/directory replacement coverage; the remediation request claims that blocker closed.

**Why existing Evidence does not close it**

`test_native_snapshot_rejects_untracked_and_out_of_allowlist_residue` proves two static schema cases only. It does not establish handle-stable worktree byte capture, intermediate/leaf replacement rejection, or a causal race where pathname identity changes after validation but before the byte read.

**Exact acceptance**

- Capture each present `SNAPSHOT_PATHS` worktree file through a retained root/parent directory FD and per-component no-follow traversal (or an equivalent handle-stable beneath/no-symlink primitive).
- Derive regular-file/type/identity and bytes from the same opened file descriptor; no later pathname re-resolution may select the bytes being hashed.
- Add direct temporary-worktree witnesses for intermediate symlink, final symlink/directory, and a replacement between validation/open phases. External/foreign bytes must never be accepted into the snapshot.
- Recompute a native rollback `after_snapshot` through this same path and prove exact equality to the retained `before_snapshot`.

### MEDIUM-1 — `AtomicFileEvidenceSink.emit()` can stage through an unbound/replaced parent before parent authority is validated

**Location:** `tools/psm_wma/immutable_source_collection.py:200` (`AtomicFileEvidenceSink.emit`)

**Root cause**

The sink computes `<destination>.pending` and opens it by pathname before checking whether `destination.parent` is a symlink/controlled directory. Publication is also pathname-based: the parent is checked and then `os.link(temporary, destination)` performs another path resolution. Thus:

1. an already-symlinked parent can cause the staging write to occur outside the intended directory before the sink rejects the parent; and
2. a parent replacement after the check but before `os.link` can redirect final publication.

The no-replace property of `os.link` closes the old destination-overwrite race, but it does not bind the parent directory authority or make staging/publication race-free.

**Violated frozen contract**

The preserved atomic-evidence contract requires a fresh controlled destination, no visible partial record on failure, and fail-closed evidence-path drift. The prior acceptance also required destination/parent authority to be valid at publication time.

**Why existing Evidence does not close it**

`test_atomic_sink_does_not_replace_destination_race` injects only a foreign final destination immediately before `os.link`; it does not replace the parent directory or make the parent a symlink before staging. Therefore it cannot fail if staging/publication is redirected through a foreign parent.

**Exact acceptance**

- Bind the evidence parent to a stable directory capability before creating any staging object; reject symlink/non-directory parent before the first write.
- Stage and perform no-replace publication relative to the retained parent directory capability, or use an equivalent primitive that cannot be redirected by parent replacement.
- Add causal witnesses for (a) parent already symlinked before staging and (b) parent replacement immediately before publication. Neither case may create/overwrite a visible record outside the retained parent; failure must leave no accepted partial evidence.

### MEDIUM-2 — mandatory direct native-path Evidence is still missing

**Location:** `tools/psm_wma/test_immutable_source_collection.py` (`NativeCollectionGit` / `NativeRootFd` acceptance witnesses)

**Root cause**

The suite now contains direct unit tests for `NativeCollectionGit.commit`, `rollback`, `preflight`, `snapshot`, and static `NativeRootFd` intermediate-symlink rejection, but every `collect_synthetic(...)` PASS/failure witness still uses `TemporaryGitFixture` rather than the actual `NativeCollectionGit`. There is no direct witness wiring the real native adapter into the unchanged production algorithm.

The exact prior acceptance also required a `NativeRootFd` component-replacement race witness and a fuller native snapshot matrix. Those witnesses are not present: only the static native intermediate-symlink case and native untracked/out-of-allowlist snapshot case are directly covered.

**Violated frozen contract**

The Gate requires contract → production behavior → direct behavioral witness. The prior HIGH-1 exact acceptance specifically required actual `NativeCollectionGit` → `collect_synthetic()` → PASS-shaped collection/receipt execution; HIGH-2 required replacement-during-traversal evidence; HIGH-3 required native mode/type/symlink/directory/rollback witnesses.

**Why reported `44/44 PASS` is insufficient**

Test count and direct method tests do not prove the production object composition. A regression at the `collect_synthetic` ↔ `NativeCollectionGit` seam can still pass the current unit matrix.

**Exact acceptance**

- In a temporary local/bare Git fixture, instantiate the actual `NativeCollectionGit` and actual `NativeRootFd`, then call canonical `collect_synthetic()` directly and reach a PASS-shaped collection/receipt record with unchanged preflight snapshot and exact committed transaction identities.
- Add a late native-path failure witness proving the same actual adapter restores the exact retained snapshot or fail-stops as `ROLLBACK_INCOMPLETE`.
- Add the causal `NativeRootFd` replacement-during-traversal witness required by the prior review.
- Add native `target_snapshot_v1` witnesses for mode-only drift, symlink/directory replacement, and exact successful rollback equality after HIGH-1 is fixed.

## 4. Formal verdict

`REQUEST_CHANGES(tools/psm_wma/immutable_source_collection.py:306)`

Current blockers: **1 HIGH Production/Authority + 1 MEDIUM Production/Atomicity + 1 MEDIUM Evidence-only = 3 blockers**.  
Child/runtime blockers: **0**.

## 5. Scope reminder

This verdict binds only exact formal pair `24253e0c3789d46c0807944ec75d6dff108824f3` / `93a89ba61306d840a008813f62f26a34d54850f4` and Gate `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-REAL-ADAPTER-CPU-STATIC`.

Remediation remains limited to the already-approved two-file CPU/static allowlist and temporary fixtures. No real source/checkpoint/data/cache access, live collection/receipt/publication execution, child/runtime change, GPU, or training action is authorized.
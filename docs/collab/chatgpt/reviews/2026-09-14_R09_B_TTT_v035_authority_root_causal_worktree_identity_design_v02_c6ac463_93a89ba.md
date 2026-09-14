# ChatGPT Independent Review — R09-B TTT v0.3.5 Authority-root Causal Worktree Identity Design v0.2

**Date:** 2026-09-14  
**Formal root:** `c6ac4639d2abb6bb19263e1ee923902419844fd5`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-DESIGN`

## 1. Pair / scope lock

- Re-locked remote `V2` and re-read live `docs/collab/chatgpt/CODEX_INBOX.md`; the effective request binds exact pair `c6ac4639d2abb6bb19263e1ee923902419844fd5` / `93a89ba61306d840a008813f62f26a34d54850f4`.
- Independently verified formal root `c6ac463...` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- This is a new formal pair relative to prior reviewed `0dedec97f1d5e2c62ec980b6daffb7f9da472cda` / same child, so a fresh incremental review is required.
- Formal commit scope is docs-only: `SESSION.md`, `TODO.md`, and new replacement design `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_causal_worktree_identity_design_v0.2.md`. No project code or child changes are part of the formal commit.
- No real Git/worktree/materialization/source/checkpoint/manifest/data/cache I/O, collection/receipt/publication, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1 is authorized by this review.

## 2. Prior blocker disposition

- Prior HIGH — Git consumed mutable global `<absolute-clean-root>`: **PARTIALLY CLOSED**. v0.2 removes the global absolute CLEAN target and freezes a Git-only inherited `git_parent_fd=6`, exact `close_fds=True`, `pass_fds=(6,)`, CLOEXEC handling, and target bytes `/proc/self/fd/6/<clean_name>` with no global-path fallback.
- Global **parent-path** replacement is therefore materially improved: FD6 continues to name the retained parent directory inode even if its global pathname is renamed/replaced.
- However the previous exact acceptance also required the actual temporary-Git target-resolution witness to cover replacement of the **clean entry itself** before Git resolves its target, with proof that the foreign replacement is not mutated. That causal leaf guarantee is still not provided by the frozen mechanism below.

## 3. Current blocking finding

### HIGH-1 — `/proc/self/fd/6/<clean_name>` anchors the parent inode but still re-resolves the mutable clean entry, so Git can mutate a foreign replacement inside the retained parent

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_causal_worktree_identity_design_v0.2.md:26` (section 2, step 3)

**Root cause**

The replacement design freezes FD6 as a duplicate of `parent_fd` and passes Git this target:

```text
/proc/self/fd/6/<clean_name>
```

That is capability-derived with respect to the **parent**, but it is not capability-derived with respect to the already-created **clean-root inode** held by `clean_fd`. The final `<clean_name>` lookup still occurs at Git target-resolution time inside the retained parent directory namespace.

A causal race therefore remains even when the global parent pathname never changes:

1. launcher creates clean-root inode A with `mkdirat(parent_fd, clean_name, ...)` and retains `clean_fd(A)`;
2. launcher validates `/proc/self/fd/6/<clean_name>` currently resolves to A;
3. before the Git child resolves the target operand, another actor renames/removes the `clean_name` entry inside the same retained parent inode and installs foreign empty directory B at the same `clean_name`;
4. Git resolves `/proc/self/fd/6/<clean_name>` through FD6's retained parent to the **current** entry B and may populate B / register worktree metadata against B;
5. only after Git returns do `fstat(clean_fd)` and `fstatat(parent_fd, clean_name, ...)` detect `A != B` and fail closed.

The post-Git triple revalidation detects the drift but cannot prove that Git did not already write into B. This is detection-after-mutation, not causal binding of the mutating consumer to the launcher-owned clean-root inode.

**Internal design contradiction**

Section 4 explicitly requires a `target-resolution race` witness where replacement of either the global parent **or clean entry** before Git target resolution must result in Git filling only the retained owner inode or failing before any foreign mutation. The proposed target mechanism can satisfy the parent-replacement half, but not the clean-entry-replacement half: FD6+`clean_name` necessarily performs a fresh lookup of that mutable directory entry.

The design also explicitly says `clean_fd` is not inherited to Git. Therefore no retained leaf capability currently crosses the Git mutation boundary.

**Why the pre-call check is insufficient**

Step 4 requires verifying `/proc/self/fd/6/<clean_name>` points to `clean_fd` immediately before invocation. That check does not linearize Git's later pathname resolution. The entry may be replaced after the check and before Git dereferences it. No postcondition can retroactively establish that the foreign inode was not mutated.

**Exact acceptance**

The next replacement design must bind Git's actual mutation target to the retained **clean-root inode**, not only to its parent directory.

An acceptable design should freeze one mechanism whose semantics make clean-entry replacement unable to redirect Git, for example:

- inherit a dedicated Git-target FD that is a duplicate of `clean_fd` itself and make the exact Git target operand a procfd path for that leaf capability (if temporary real-Git fixtures prove Git accepts it and its administrative metadata remains valid); or
- use another explicitly frozen primitive that gives Git an immutable reference to the retained clean-root inode across target resolution and mutation.

The design must preserve exact `close_fds` / `pass_fds` / CLOEXEC lifetime, collision rules, and no-global-path fallback for that **leaf** capability. If Git cannot consume the retained leaf capability safely, the route must fail closed rather than falling back to parent+name or global CLEAN.

Future CPU/static implementation acceptance must include an actual temporary local-Git witness at the exact seam:

1. create owner inode A and retain its clean-root capability;
2. before Git resolves the target, replace `parent_fd/clean_name` inside the same retained parent with foreign empty directory B while keeping A reachable only through the retained capability;
3. invoke actual temporary `git worktree add` via the frozen leaf-capability target;
4. prove Git either populates A or fails before writing B;
5. prove B is not read/written/deleted by cleanup;
6. separately cover global parent rename/replacement and show it also cannot redirect the Git target;
7. verify Git administrative worktree metadata and all later owner checks without depending on an ephemeral procfd pathname after the Git-target capability lifetime ends.

## 4. Non-blocking / retained design improvements

- Replacing global absolute CLEAN with a procfd-derived target is directionally correct and closes the global-parent-path redirection class.
- Exact `close_fds=True`, `pass_fds=(6,)`, FD6 identity/CLOEXEC requirements, no PATH/shell/ambient fallback, and no FD3/4/5/clean_fd leakage are good constraints and should be retained.
- Owner-limited cleanup and `ROLLBACK_INCOMPLETE` on unprovable ownership remain correct fail-closed behavior.
- The requirement to keep the legacy v0.8 route as a negative witness is still appropriate.
- Child/Gitlink blockers: **0**.

## 5. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_causal_worktree_identity_design_v0.2.md:26)`

Current blockers: **1 HIGH Design/Authority**.  
Child/runtime blockers: **0**.

## 6. Scope reminder

This verdict binds only exact formal pair `c6ac4639d2abb6bb19263e1ee923902419844fd5` / `93a89ba61306d840a008813f62f26a34d54850f4` and Gate `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-DESIGN`.

Only a docs-only redesign is authorized by this verdict. No real Git/worktree/materialization, source/checkpoint/manifest/data/cache access, collection/receipt/publication, child/runtime/config modification, GPU, training, evaluation, inference, or LIBERO4IN1 action is authorized.
